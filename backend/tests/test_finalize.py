"""Tests for finalize memory curation: grade evaluation + memory write/merge."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from storage.db.models import Base, Session


@pytest.fixture
async def db() -> AsyncSession:
    """In-memory SQLite database."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def memory_root(tmp_path: Path) -> Path:
    """Temp memory directory."""
    return tmp_path / "memory"


@pytest.fixture
def session_with_notes(db: AsyncSession) -> Session:
    """Create a session with remember notes."""
    session = Session(
        id="sess-finalize-1",
        user_id="user-1",
        profile_id="interviewer",
        status="active",
        resume_id="res-1",
    )
    db.add(session)
    return session


class TestFinalizeMemory:
    """Test finalize generates grade eval and writes memory files."""

    async def test_finalize_writes_summary_and_memory(
        self, db: AsyncSession, memory_root: Path, session_with_notes: Session
    ) -> None:
        """Finalize: session notes → grade eval in summary + memory files written."""
        from service.session_service import SessionService
        from storage.memory.store import MemoryStore

        await db.commit()
        session = session_with_notes

        # Simulate session with remember notes
        store = MagicMock()
        store.read_events.return_value = []

        service = SessionService(db_session=db, session_store=store)

        # Mock the finalize subagent output
        finalize_result = {
            "summary": {
                "grade": "B",
                "evaluation": "及格",
                "highlights": ["Python 基础扎实"],
                "suggestions": ["加强系统设计"],
            },
            "capy_note": "# 强弱项\n## 强项\n- Python 熟练\n## 弱项\n- 系统设计需要加强",
            "user_md": "# 用户信息\n偏好中文面试",
        }

        memory_store = MemoryStore(root_dir=str(memory_root))

        # Run finalize
        await service.finalize_session(
            session.id,
            finalize_result["summary"],
            memory_store=memory_store,
            finalize_data=finalize_result,
        )

        # Verify summary stored in DB
        from sqlalchemy import select
        result = await db.execute(select(Session).where(Session.id == session.id))
        updated = result.scalar_one()
        assert updated.status == "completed"
        summary = json.loads(updated.summary)
        assert summary["grade"] == "B"
        assert summary["evaluation"] == "及格"

        # Verify memory files written
        assert memory_store.read_capy_note("user-1", "res-1") != ""

    async def test_finalize_no_memory_when_no_notes(
        self, db: AsyncSession, memory_root: Path
    ) -> None:
        """Finalize with no notes still works — empty memory is fine."""
        from service.session_service import SessionService
        from storage.memory.store import MemoryStore

        session = Session(
            id="sess-finalize-2",
            user_id="user-2",
            profile_id="interviewer",
            status="active",
            resume_id="res-2",
        )
        db.add(session)
        await db.commit()

        store = MagicMock()
        store.read_events.return_value = []

        service = SessionService(db_session=db, session_store=store)
        memory_store = MemoryStore(root_dir=str(memory_root))

        finalize_result = {
            "summary": {"grade": "A", "evaluation": "完美"},
            "capy_note": "",
            "user_md": "",
        }

        await service.finalize_session(
            session.id,
            finalize_result["summary"],
            memory_store=memory_store,
            finalize_data=finalize_result,
        )

        # Should not crash — empty memory is fine
        from sqlalchemy import select
        result = await db.execute(select(Session).where(Session.id == session.id))
        updated = result.scalar_one()
        assert updated.status == "completed"
