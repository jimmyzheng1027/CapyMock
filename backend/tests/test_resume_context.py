"""Tests for read_resume SQL, ContextBuilder injection, session resume_id, settings."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from storage.db.models import Base, Resume, Session
from tool.base import ToolContext, ToolResult


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


# --- 6.1/6.2: read_resume SQL tests ---


class TestReadResumeSQL:
    """Test read_resume reads from resume table."""

    async def test_read_resume_from_db(self, db: AsyncSession) -> None:
        """read_resume returns content from resume table."""
        from tool.builtins.read_resume import read_resume, ReadResumeArgs

        resume = Resume(id="res-1", user_id="user-1", content="My resume content")
        db.add(resume)
        await db.commit()

        ctx = ToolContext(user_id="user-1")
        ctx.db_session = db

        args = ReadResumeArgs(resume_id="res-1")
        result = await read_resume(args, ctx)

        assert result.status == "ok"
        assert result.data["content"] == "My resume content"

    async def test_read_resume_not_found(self, db: AsyncSession) -> None:
        """read_resume returns error for missing resume."""
        from tool.builtins.read_resume import read_resume, ReadResumeArgs

        ctx = ToolContext(user_id="user-1")
        ctx.db_session = db

        args = ReadResumeArgs(resume_id="nonexistent")
        result = await read_resume(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "not_found"

    async def test_read_resume_no_user_id(self, db: AsyncSession) -> None:
        """read_resume without user_id returns error."""
        from tool.builtins.read_resume import read_resume, ReadResumeArgs

        ctx = ToolContext(user_id="")
        ctx.db_session = db

        args = ReadResumeArgs(resume_id="res-1")
        result = await read_resume(args, ctx)

        assert result.status == "err"


# --- 6.3/6.4: ContextBuilder injection tests ---


class TestContextBuilderInjection:
    """Test ContextBuilder injects resume content and memory files."""

    @pytest.fixture
    def memory_root(self, tmp_path: Path) -> Path:
        """Create memory files for testing."""
        root = tmp_path / "memory"
        (root / "user-1").mkdir(parents=True)
        (root / "user-1" / "user.md").write_text(
            "# User prefs\nChinese interview", encoding="utf-8"
        )
        (root / "user-1" / "res-1").mkdir()
        (root / "user-1" / "res-1" / "CAPY_NOTE.md").write_text(
            "# Notes\nStrength: Python", encoding="utf-8"
        )
        (root / "user-1" / "res-1" / "REAL_QUES.md").write_text(
            "# Real questions\nByteDance: rate limiting", encoding="utf-8"
        )
        return root

    def test_inject_with_resume_and_memory(
        self, memory_root: Path
    ) -> None:
        """build_messages includes resume content and memory files."""
        from agent.context.builder import ContextBuilder
        from agent.context.skill_loader import SkillLoader
        from api.schemas import EventType, FrontendEvent

        skill_loader = SkillLoader(skills_dir=str(memory_root.parent / "nonexistent"))
        builder = ContextBuilder(skill_loader=skill_loader)

        profile = MagicMock()
        profile.id = "interviewer"
        profile.prompt_template = str(memory_root / "nonexistent_prompt.md")
        profile.skills = []
        profile.llm = MagicMock()
        profile.llm.provider = "deepseek"
        profile.llm.model = "test"

        builder._memory_root = str(memory_root)

        resume_content = "Python developer with 5 years experience"
        messages = builder.build_messages(
            profile,
            [],
            current_input="Hello",
            resume_content=resume_content,
            user_id="user-1",
            resume_id="res-1",
        )

        # Should have system + user messages
        assert len(messages) >= 2
        system_msg = messages[0]["content"]
        assert "Python developer" in system_msg
        assert "Chinese interview" in system_msg
        assert "Python" in system_msg  # from CAPY_NOTE
        assert "rate limiting" in system_msg  # from REAL_QUES

    def test_cold_start_no_memory(self, tmp_path: Path) -> None:
        """Cold start with no memory files doesn't crash."""
        from agent.context.builder import ContextBuilder
        from agent.context.skill_loader import SkillLoader

        skill_loader = SkillLoader(skills_dir=str(tmp_path / "nonexistent"))
        builder = ContextBuilder(skill_loader=skill_loader)
        builder._memory_root = str(tmp_path / "empty_memory")

        profile = MagicMock()
        profile.id = "interviewer"
        profile.prompt_template = str(tmp_path / "nonexistent.md")
        profile.skills = []

        messages = builder.build_messages(
            profile, [], current_input="Hello",
            resume_content="", user_id="new-user", resume_id="new-res",
        )

        assert len(messages) >= 1
        # Should not crash — empty memory is fine


# --- 6.5: Session resume_id tests ---


class TestSessionResumeId:
    """Test session creation records resume_id."""

    async def test_create_session_with_resume_id(self, db: AsyncSession) -> None:
        """create_session stores resume_id in Session."""
        from service.session_service import SessionService
        from api.schemas import CreateSessionRequest
        from storage.session.store import SessionStore

        store = MagicMock(spec=SessionStore)
        store.create.return_value = Path("/fake/path")

        service = SessionService(db_session=db, session_store=store)
        request = CreateSessionRequest(
            profile_id="interviewer",
            resume_id="res-1",
            user_id="user-1",
        )
        response = await service.create_session(request)

        result = await db.execute(select(Session).where(Session.id == response.session_id))
        session = result.scalar_one()
        assert session.resume_id == "res-1"


# --- 6.7: Settings tests ---


class TestSettings:
    """Test settings has REPO_ROOT and MEMORY_ROOT."""

    def test_settings_has_repo_root(self) -> None:
        from config.settings import settings

        assert hasattr(settings, "REPO_ROOT")
        assert isinstance(settings.REPO_ROOT, str)

    def test_settings_has_memory_root(self) -> None:
        from config.settings import settings

        assert hasattr(settings, "MEMORY_ROOT")
        assert isinstance(settings.MEMORY_ROOT, str)
