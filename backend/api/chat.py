from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.factory import AgentFactory
from agent.loop import CancelToken
from api.deps import get_agent_factory, get_session_store
from api.schemas import EventType, FrontendEvent
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


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    agent_factory: AgentFactory = Depends(get_agent_factory),
    session_store: SessionStore = Depends(get_session_store),
):
    """Send a user message and trigger agent processing (for SSE stream)."""
    state = _get_or_create_session_state(session_id)

    # Get session info
    events = session_store.read_events("default", session_id)
    if not events:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create user event
    user_event = FrontendEvent(
        type=EventType.USER_TEXT,
        payload={"text": request.text},
    )

    # Append to session
    session_store.append_event("default", session_id, user_event)

    # Put user event in queue for SSE
    await state["event_queue"].put(user_event)

    # Start agent processing if not already running
    if not state["is_running"]:
        state["is_running"] = True
        state["cancel_token"] = CancelToken()

        # Create agent
        try:
            agent = agent_factory.create(
                profile_id="interviewer-technical",
                session_id=session_id,
                mode="text",
                user_id="default",
            )
            agent.cancel_token = state["cancel_token"]

            # Run agent in background
            asyncio.create_task(
                _run_agent(agent, request.text, state, session_store, session_id)
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
    # Get session info
    events = session_store.read_events("default", session_id)
    if not events:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create user event
    user_event = FrontendEvent(
        type=EventType.USER_TEXT,
        payload={"text": request.text},
    )
    session_store.append_event("default", session_id, user_event)

    # Create agent
    try:
        agent = agent_factory.create(
            profile_id="interviewer-technical",
            session_id=session_id,
            mode="text",
            user_id="default",
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
                session_store.append_event("default", session_id, event)

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
                session_store.append_event("default", session_id, event)
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

    async def event_generator() -> AsyncIterator[str]:
        # First, replay existing events
        events = session_store.read_events("default", session_id)
        for event in events:
            yield f"data: {event.model_dump_json()}\n\n"

        # Then stream new events from queue
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
