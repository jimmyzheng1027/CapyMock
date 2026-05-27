from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    FinalizeResponse,
    SessionListResponse,
    SessionMetadata,
)
from service.session_service import SessionService
from storage.session.store import SessionStore

router = APIRouter()


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
    session_service: SessionService = Depends(get_session_service),
):
    """Finalize a session and generate summary."""
    try:
        # For now, return a placeholder summary
        # In production, this would trigger the summary-generator agent
        summary = {
            "overview": "Interview completed",
            "highlights": [],
            "suggestions": [],
        }
        return await session_service.finalize_session(session_id, summary)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
