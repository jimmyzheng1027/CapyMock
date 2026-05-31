from __future__ import annotations

import json
import logging

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
from storage.memory.store import MemoryStore
from storage.session.store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter()

_FALLBACK_SUMMARY: dict = {
    "overview": "面试已完成",
    "highlights": [],
    "suggestions": ["继续练习以提升面试表现"],
}


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
        if session_meta.status == "completed" and session_meta.summary:
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
            if event.type == EventType.USER_TEXT:
                transcript_lines.append(f"候选人: {event.payload.get('text', '')}")
            elif event.type == EventType.ASSISTANT_TEXT_DONE:
                text = event.payload.get("text", "")
                if text:
                    transcript_lines.append(f"面试官: {text}")

        transcript = "\n".join(transcript_lines)

        # Create summary-generator agent
        try:
            agent = agent_factory.create(
                profile_id="summary-generator",
                session_id=session_id,
                mode="text",
                user_id=session_meta.user_id,
                resume_id=session_meta.resume_id or "",
            )
        except Exception as e:
            logger.error(f"Failed to create summary agent: {e}")
            return await session_service.finalize_session(session_id, _FALLBACK_SUMMARY)

        # Run summary agent
        summary_text = ""
        try:
            async for event in agent.run(
                f"请为以下面试对话生成总结：\n\n{transcript}"
            ):
                if event.type == EventType.ASSISTANT_TEXT_DONE:
                    summary_text = event.payload.get("text", "")
        except Exception as e:
            logger.error(f"Summary agent error: {e}")
            return await session_service.finalize_session(session_id, _FALLBACK_SUMMARY)

        # Parse JSON summary from agent response
        summary = _parse_summary_json(summary_text)

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


def _parse_summary_json(text: str) -> dict:
    """Parse summary JSON from agent response, with fallback handling."""
    # Try to extract JSON from the response (may be wrapped in markdown code block)
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
        parsed = json.loads(json_str)
        # Ensure required fields exist
        return {
            "overview": parsed.get("overview", "面试已完成"),
            "highlights": parsed.get("highlights", []),
            "suggestions": parsed.get("suggestions", []),
            "technical_assessment": parsed.get("technical_assessment", ""),
            "behavioral_assessment": parsed.get("behavioral_assessment", ""),
        }
    except (json.JSONDecodeError, ValueError):
        logger.warning(f"Failed to parse summary JSON, using fallback. Response: {text[:200]}")
        return _FALLBACK_SUMMARY.copy()
