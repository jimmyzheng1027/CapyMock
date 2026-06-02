from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request

from api.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    EventType,
    FinalizeResponse,
    SessionListResponse,
    SessionMetadata,
)
from service.session_service import SessionService
from service.summary_utils import FALLBACK_SUMMARY, is_fallback_summary
from storage.memory.store import MemoryStore
from storage.session.store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter()


_SUMMARY_MAX_ATTEMPTS = 2


def get_session_store(request: Request) -> SessionStore:
    """Get session store from app state."""
    return request.app.state.session_store


def get_session_service(
    request: Request,
    session_store: SessionStore = Depends(get_session_store),
) -> SessionService:
    """Get session service with database session."""
    from storage.db.engine import async_session_factory

    # Create a new database session
    db_session = async_session_factory()
    return SessionService(db_session=db_session, session_store=session_store)


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    """Create a new interview session."""
    try:
        return await session_service.create_session(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user_id: str | None = None,
    status: str | None = None,
    profile_id: str | None = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    session_service: SessionService = Depends(get_session_service),
):
    """List sessions with filtering and sorting."""
    return await session_service.list_sessions(
        user_id=user_id,
        status=status,
        profile_id=profile_id,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=SessionMetadata)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """Get session metadata by ID."""
    session = await session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/events")
async def get_session_events(
    session_id: str,
    request: Request,
    session_store: SessionStore = Depends(get_session_store),
):
    """Get all events for a session."""
    # Get session to find user_id
    from sqlalchemy import select

    from storage.db.engine import async_session_factory
    from storage.db.models import Session

    async with async_session_factory() as db:
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    events = session_store.read_events(session.user_id, session_id)
    return {"events": [event.model_dump() for event in events]}


@router.post("/sessions/{session_id}/finalize", response_model=FinalizeResponse)
async def finalize_session(
    session_id: str,
    request: Request,
    session_service: SessionService = Depends(get_session_service),
):
    """Finalize a session and generate summary using summary-generator agent."""
    try:
        # Check if already finalized
        session_meta = await session_service.get_session(session_id)
        if session_meta is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if (
            session_meta.status == "completed"
            and session_meta.summary
            and not is_fallback_summary(session_meta.summary)
        ):
            return FinalizeResponse(session_id=session_id, summary=session_meta.summary)

        # Get agent factory and session store from app state
        agent_factory = request.app.state.agent_factory
        session_store = request.app.state.session_store

        # Read session events for context
        events = session_store.read_events(session_meta.user_id, session_id)
        if not events:
            raise HTTPException(status_code=400, detail="Session has no events")

        # Build conversation transcript from events
        transcript_lines = []
        for event in events:
            if event.type in (EventType.USER_TEXT, EventType.USER_TRANSCRIPT):
                text = (event.payload.get("text") or "").strip()
                if text:
                    transcript_lines.append(f"候选人: {text}")
            elif event.type in (EventType.ASSISTANT_TEXT_DONE, EventType.ASSISTANT_TRANSCRIPT_DONE):
                text = (event.payload.get("text") or "").strip()
                if text:
                    transcript_lines.append(f"面试官: {text}")

        transcript = "\n".join(transcript_lines)
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Session has no conversation to summarize")

        summary_session_id = f"{session_id}:summary"
        summary_prompt = f"请为以下面试对话生成总结：\n\n{transcript}"

        # Create agent once, retry only the run() call
        try:
            agent = agent_factory.create(
                profile_id="summary-generator",
                session_id=summary_session_id,
                mode="text",
                user_id=session_meta.user_id,
                resume_id=session_meta.resume_id or "",
            )
        except Exception as e:
            logger.error(f"Failed to create summary agent: {e}")
            raise HTTPException(status_code=503, detail="生成总结失败，请稍后重试")

        summary_text = ""
        last_error: Exception | None = None
        for attempt in range(1, _SUMMARY_MAX_ATTEMPTS + 1):
            try:
                async for event in agent.run(summary_prompt):
                    if event.type == EventType.ASSISTANT_TEXT_DONE:
                        summary_text = event.payload.get("text", "")
            except Exception as e:
                logger.error(
                    "Summary agent error (attempt %s/%s): %s",
                    attempt,
                    _SUMMARY_MAX_ATTEMPTS,
                    e,
                )
                last_error = e
                continue

            if summary_text.strip():
                break

            last_error = RuntimeError("Summary agent returned empty response")

        if not summary_text.strip():
            logger.error("Summary generation failed after retries: %s", last_error)
            raise HTTPException(status_code=503, detail="生成总结失败，请稍后重试")

        # Parse JSON summary from agent response
        summary = _parse_summary_json(summary_text)
        if summary is None:
            logger.error(
                "Summary JSON parse failed. Response preview: %s",
                summary_text[:200],
            )
            raise HTTPException(status_code=503, detail="生成总结失败，请稍后重试")

        # Extract memory fields from summary
        finalize_data = {
            "capy_note": summary.pop("capy_note", ""),
            "user_md": summary.pop("user_md", ""),
        }

        # Write memory files
        memory_store = MemoryStore()
        return await session_service.finalize_session(
            session_id, summary,
            memory_store=memory_store,
            finalize_data=finalize_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Finalize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _parse_summary_json(text: str) -> dict | None:
    """Parse summary JSON from agent response. Returns None on failure."""
    json_str = text.strip()

    # Handle markdown code blocks
    if "```json" in json_str:
        start = json_str.index("```json") + 7
        end = json_str.index("```", start)
        json_str = json_str[start:end].strip()
    elif "```" in json_str:
        start = json_str.index("```") + 3
        end = json_str.index("```", start)
        json_str = json_str[start:end].strip()

    try:
        return _normalize_summary_dict(json.loads(json_str))
    except (json.JSONDecodeError, ValueError):
        # Non-greedy brace extraction for prose-wrapped JSON
        first = json_str.find("{")
        last = json_str.rfind("}")
        if first != -1 and last > first:
            try:
                return _normalize_summary_dict(json.loads(json_str[first:last + 1]))
            except (json.JSONDecodeError, ValueError):
                pass
        logger.warning(f"Failed to parse summary JSON. Response: {text[:200]}")
        return None


def _normalize_summary_dict(parsed: dict) -> dict:
    """Ensure required summary fields exist with sane defaults."""
    return {
        "overview": parsed.get("overview", FALLBACK_SUMMARY["overview"]),
        "highlights": parsed.get("highlights", []),
        "suggestions": parsed.get("suggestions", []),
        "technical_assessment": parsed.get("technical_assessment", ""),
        "behavioral_assessment": parsed.get("behavioral_assessment", ""),
        "capy_note": parsed.get("capy_note", ""),
        "user_md": parsed.get("user_md", ""),
    }
