from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    EventType,
    FinalizeResponse,
    FrontendEvent,
    SessionListResponse,
    SessionMetadata,
)
from storage.db.models import Session
from storage.session.store import SessionStore


class SessionService:
    """Business logic for session management."""

    def __init__(self, db_session: AsyncSession, session_store: SessionStore) -> None:
        self.db = db_session
        self.store = session_store

    async def create_session(self, request: CreateSessionRequest) -> CreateSessionResponse:
        """Create a new interview session."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Create session in SQLite
        session = Session(
            id=session_id,
            user_id=request.user_id,
            profile_id=request.profile_id,
            status="active",
            mode=request.mode,
            created_at=now,
            updated_at=now,
            event_count=1,
            resume_id=request.resume_id,
        )
        self.db.add(session)
        await self.db.commit()

        # Create JSONL file and write session.started event
        self.store.create(request.user_id, session_id, request.profile_id)

        return CreateSessionResponse(
            session_id=session_id,
            profile_id=request.profile_id,
            created_at=now.isoformat(),
        )

    async def get_session(self, session_id: str) -> SessionMetadata | None:
        """Get session metadata by ID."""
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            return None

        return self._to_metadata(session)

    async def list_sessions(
        self,
        user_id: str | None = None,
        status: str | None = None,
        profile_id: str | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """List sessions with filtering and sorting."""
        query = select(Session)

        if user_id:
            query = query.where(Session.user_id == user_id)
        if status:
            query = query.where(Session.status == status)
        if profile_id:
            query = query.where(Session.profile_id == profile_id)

        # Sorting
        sort_column = getattr(Session, sort_by, Session.updated_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        # Get total count
        count_query = select(Session)
        if user_id:
            count_query = count_query.where(Session.user_id == user_id)
        if status:
            count_query = count_query.where(Session.status == status)
        if profile_id:
            count_query = count_query.where(Session.profile_id == profile_id)

        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())

        return SessionListResponse(
            sessions=[self._to_metadata(s) for s in sessions],
            total=total,
        )

    async def append_event(self, session_id: str, event: FrontendEvent) -> None:
        """Append an event to a session and update metadata."""
        # Get session to find user_id
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        # Append to JSONL
        self.store.append_event(session.user_id, session_id, event)

        # Update SQLite metadata
        now = datetime.utcnow()
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(
                updated_at=now,
                last_event_ts=now,
                event_count=Session.event_count + 1,
            )
        )
        await self.db.commit()

    async def finalize_session(
        self,
        session_id: str,
        summary: dict,
        memory_store: object | None = None,
        finalize_data: dict | None = None,
    ) -> FinalizeResponse:
        """Finalize a session with a summary.

        Args:
            session_id: Session ID
            summary: Summary dict to store
            memory_store: Optional MemoryStore for writing memory files
            finalize_data: Optional dict with capy_note, user_md, real_ques for memory
        """
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        if session.status == "completed":
            return FinalizeResponse(
                session_id=session_id,
                summary=json.loads(session.summary) if session.summary else {},
            )

        # Update session status and summary
        now = datetime.utcnow()
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(
                status="completed",
                summary=json.dumps(summary),
                updated_at=now,
            )
        )
        await self.db.commit()

        # Write memory files if provided
        if memory_store and finalize_data and session.user_id and session.resume_id:
            self._write_memory(
                memory_store, session.user_id, session.resume_id, finalize_data
            )

        # Append summary event to JSONL
        summary_event = FrontendEvent(
            type=EventType.TURN_DONE,
            payload={"summary": summary},
            ts=now.timestamp(),
        )
        self.store.append_event(session.user_id, session_id, summary_event)

        return FinalizeResponse(
            session_id=session_id,
            summary=summary,
        )

    def _write_memory(
        self,
        memory_store: object,
        user_id: str,
        resume_id: str,
        finalize_data: dict,
    ) -> None:
        """Write memory files from finalize data."""
        from storage.memory.store import MemoryStore

        store: MemoryStore = memory_store  # type: ignore[assignment]

        capy_note = finalize_data.get("capy_note", "")
        if capy_note:
            store.write_capy_note(user_id, resume_id, capy_note)

        user_md = finalize_data.get("user_md", "")
        if user_md:
            store.write_user(user_id, user_md)

        real_ques = finalize_data.get("real_ques", "")
        if real_ques:
            store.write_real_ques(user_id, resume_id, real_ques)

    async def pause_session(self, session_id: str) -> None:
        """Pause a session (called when WS disconnects)."""
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .where(Session.status == "active")
            .values(status="paused", updated_at=datetime.utcnow())
        )
        await self.db.commit()

    def _to_metadata(self, session: Session) -> SessionMetadata:
        """Convert SQLAlchemy model to Pydantic schema."""
        return SessionMetadata(
            id=session.id,
            user_id=session.user_id,
            profile_id=session.profile_id,
            status=session.status,
            mode=session.mode,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            last_event_ts=session.last_event_ts.isoformat() if session.last_event_ts else None,
            event_count=session.event_count,
            turn_count=session.turn_count,
            summary=json.loads(session.summary) if session.summary else None,
        )
