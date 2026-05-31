from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from agent.factory import AgentFactory
from agent.loop import CancelToken
from api.deps import get_agent_factory, get_session_store
from api.schemas import EventType, FrontendEvent
from storage.db.engine import async_session_factory
from storage.db.models import RepoAnalysis, Resume, Session
from storage.session.store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    """Request to send a user message."""
    text: str


class ChatRequest(BaseModel):
    """Request for synchronous chat."""
    text: str


class ChatResponse(BaseModel):
    """Response from synchronous chat."""
    text: str
    events: list[FrontendEvent]


# Store active agents and cancel tokens per session
_active_sessions: dict[str, dict] = {}


def _get_or_create_session_state(session_id: str) -> dict:
    """Get or create session state for SSE."""
    if session_id not in _active_sessions:
        _active_sessions[session_id] = {
            "cancel_token": CancelToken(),
            "event_queue": asyncio.Queue(),
            "is_running": False,
        }
    return _active_sessions[session_id]


async def _load_session_context(session_id: str) -> dict:
    """Load session metadata, resume content, and repo analyses from DB.

    Returns dict with user_id, profile_id, resume_id, resume_content, github_repos.
    Raises HTTPException if session not found.
    """
    async with async_session_factory() as db:
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        ctx = {
            "user_id": session.user_id,
            "profile_id": session.profile_id,
            "resume_id": session.resume_id,
            "resume_content": "",
            "github_repos": [],
        }

        # Load resume content if available
        if session.resume_id:
            resume_result = await db.execute(
                select(Resume).where(Resume.id == session.resume_id)
            )
            resume = resume_result.scalar_one_or_none()
            if resume and resume.content:
                ctx["resume_content"] = resume.content

        # Load GitHub repo analyses if available
        if session.github_repo_ids:
            repo_ids = json.loads(session.github_repo_ids)
            if repo_ids:
                repo_result = await db.execute(
                    select(RepoAnalysis).where(
                        RepoAnalysis.id.in_(repo_ids),
                        RepoAnalysis.status == "done",
                    )
                )
                repos = repo_result.scalars().all()
                ctx["github_repos"] = [
                    r.result_json for r in repos if r.result_json
                ]

    return ctx


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    agent_factory: AgentFactory = Depends(get_agent_factory),
    session_store: SessionStore = Depends(get_session_store),
):
    """Send a user message and trigger agent processing (for SSE stream)."""
    state = _get_or_create_session_state(session_id)

    # Load session context from DB
    ctx = await _load_session_context(session_id)

    # Get session events
    events = session_store.read_events(ctx["user_id"], session_id)
    if not events:
        raise HTTPException(status_code=404, detail="Session has no events")

    # Create user event
    user_event = FrontendEvent(
        type=EventType.USER_TEXT,
        payload={"text": request.text},
    )

    # Append to session
    session_store.append_event(ctx["user_id"], session_id, user_event)

    # Put user event in queue for SSE
    await state["event_queue"].put(user_event)

    # Start agent processing if not already running
    if not state["is_running"]:
        state["is_running"] = True
        state["cancel_token"] = CancelToken()

        # Create agent with actual session context
        try:
            agent = agent_factory.create(
                profile_id=ctx["profile_id"],
                session_id=session_id,
                mode="text",
                user_id=ctx["user_id"],
                resume_content=ctx["resume_content"],
                github_repos=ctx["github_repos"],
                resume_id=ctx["resume_id"],
            )
            agent.cancel_token = state["cancel_token"]

            # Run agent in background
            asyncio.create_task(
                _run_agent(
                    agent, request.text, state, session_store,
                    session_id, ctx["user_id"],
                )
            )
        except Exception as e:
            state["is_running"] = False
            raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok", "session_id": session_id}


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(
    session_id: str,
    request: ChatRequest,
    agent_factory: AgentFactory = Depends(get_agent_factory),
    session_store: SessionStore = Depends(get_session_store),
):
    """Synchronous chat - wait for complete response."""
    # Load session context from DB
    ctx = await _load_session_context(session_id)

    # Get session events
    events = session_store.read_events(ctx["user_id"], session_id)
    if not events:
        raise HTTPException(status_code=404, detail="Session has no events")

    # Create user event
    user_event = FrontendEvent(
        type=EventType.USER_TEXT,
        payload={"text": request.text},
    )
    session_store.append_event(ctx["user_id"], session_id, user_event)

    # Create agent with actual session context
    try:
        agent = agent_factory.create(
            profile_id=ctx["profile_id"],
            session_id=session_id,
            mode="text",
            user_id=ctx["user_id"],
            resume_content=ctx["resume_content"],
            github_repos=ctx["github_repos"],
            resume_id=ctx["resume_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Run agent and collect all events
    collected_events = []
    response_text = ""

    try:
        async for event in agent.run(request.text):
            collected_events.append(event)

            # Persist events that should be saved
            if session_store._should_persist(event):
                session_store.append_event(ctx["user_id"], session_id, event)

            # Capture the final text
            if event.type == EventType.ASSISTANT_TEXT_DONE:
                response_text = event.payload.get("text", "")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        text=response_text,
        events=collected_events,
    )


async def _run_agent(
    agent,
    user_input: str,
    state: dict,
    session_store: SessionStore,
    session_id: str,
    user_id: str,
):
    """Run agent and put events in queue."""
    try:
        async for event in agent.run(user_input):
            if state["cancel_token"].is_set():
                break

            # Put event in queue for SSE
            await state["event_queue"].put(event)

            # Persist events that should be saved
            if session_store._should_persist(event):
                session_store.append_event(user_id, session_id, event)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        error_event = FrontendEvent(
            type=EventType.ERROR,
            payload={"code": "agent_error", "message": str(e)},
        )
        await state["event_queue"].put(error_event)
    finally:
        state["is_running"] = False


@router.post("/sessions/{session_id}/interrupt")
async def interrupt_agent(
    session_id: str,
):
    """Interrupt the running agent."""
    state = _get_or_create_session_state(session_id)
    state["cancel_token"].cancel()
    return {"status": "ok", "session_id": session_id}


@router.get("/sessions/{session_id}/stream")
async def stream_events(
    session_id: str,
    session_store: SessionStore = Depends(get_session_store),
):
    """SSE endpoint for streaming events."""
    state = _get_or_create_session_state(session_id)

    # Load session to get actual user_id
    async with async_session_factory() as db:
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator() -> AsyncIterator[str]:
        # Stream new events only; history is loaded via GET /sessions/{id}/events
        while True:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    state["event_queue"].get(),
                    timeout=30.0,
                )
                yield f"data: {event.model_dump_json()}\n\n"

                # If turn is done, we can stop
                if event.type == EventType.TURN_DONE:
                    break
            except TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"
            except (asyncio.CancelledError, ConnectionResetError, OSError):
                # Client disconnected — stop cleanly
                break
            except Exception as e:
                logger.error(f"SSE error: {e}")
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
