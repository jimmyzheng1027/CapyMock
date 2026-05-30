"""Tests for RepoAnalysis, Resume models and Session.resume_id."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from storage.db.models import Base, RepoAnalysis, Resume, Session


@pytest.fixture
async def db() -> AsyncSession:
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class TestRepoAnalysis:
    """Test RepoAnalysis model CRUD."""

    async def test_create_repo_analysis(self, db: AsyncSession) -> None:
        """Create a RepoAnalysis row with all fields."""
        analysis = RepoAnalysis(
            id="ra-1",
            url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            status="pending",
        )
        db.add(analysis)
        await db.commit()

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == "ra-1"))
        row = result.scalar_one()
        assert row.url == "https://github.com/owner/repo"
        assert row.owner == "owner"
        assert row.repo == "repo"
        assert row.status == "pending"
        assert row.result_json is None
        assert row.error is None

    async def test_update_result_json(self, db: AsyncSession) -> None:
        """Update RepoAnalysis with result_json and set status=done."""
        analysis = RepoAnalysis(
            id="ra-2",
            url="https://github.com/owner/repo2",
            owner="owner",
            repo="repo2",
            status="pending",
        )
        db.add(analysis)
        await db.commit()

        analysis.status = "done"
        analysis.result_json = '{"overview": "test"}'
        analysis.analyzed_at = datetime.utcnow()
        await db.commit()

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == "ra-2"))
        row = result.scalar_one()
        assert row.status == "done"
        assert row.result_json == '{"overview": "test"}'
        assert row.analyzed_at is not None

    async def test_url_unique_constraint(self, db: AsyncSession) -> None:
        """Duplicate URL should raise IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        a1 = RepoAnalysis(
            id="ra-3", url="https://github.com/owner/repo", owner="owner", repo="repo"
        )
        db.add(a1)
        await db.commit()

        a2 = RepoAnalysis(
            id="ra-4", url="https://github.com/owner/repo", owner="owner", repo="repo"
        )
        db.add(a2)
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()

    async def test_update_error(self, db: AsyncSession) -> None:
        """Update RepoAnalysis with error and status=failed."""
        analysis = RepoAnalysis(
            id="ra-5",
            url="https://github.com/owner/repo5",
            owner="owner",
            repo="repo5",
            status="running",
        )
        db.add(analysis)
        await db.commit()

        analysis.status = "failed"
        analysis.error = "Repository is private"
        await db.commit()

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == "ra-5"))
        row = result.scalar_one()
        assert row.status == "failed"
        assert row.error == "Repository is private"


class TestResume:
    """Test Resume model CRUD."""

    async def test_create_resume(self, db: AsyncSession) -> None:
        """Create a Resume row."""
        resume = Resume(
            id="res-1",
            user_id="user-1",
            content="My resume content",
        )
        db.add(resume)
        await db.commit()

        result = await db.execute(select(Resume).where(Resume.id == "res-1"))
        row = result.scalar_one()
        assert row.user_id == "user-1"
        assert row.content == "My resume content"
        assert row.parsed_json is None

    async def test_create_resume_with_parsed_json(self, db: AsyncSession) -> None:
        """Create a Resume with parsed_json field."""
        resume = Resume(
            id="res-2",
            user_id="user-1",
            content="Resume content",
            parsed_json='{"skills": ["Python", "FastAPI"]}',
        )
        db.add(resume)
        await db.commit()

        result = await db.execute(select(Resume).where(Resume.id == "res-2"))
        row = result.scalar_one()
        assert row.parsed_json == '{"skills": ["Python", "FastAPI"]}'

    async def test_resume_updated_at(self, db: AsyncSession) -> None:
        """Resume has updated_at timestamp."""
        resume = Resume(id="res-3", user_id="user-1", content="content")
        db.add(resume)
        await db.commit()

        result = await db.execute(select(Resume).where(Resume.id == "res-3"))
        row = result.scalar_one()
        assert row.updated_at is not None


class TestSessionResumeId:
    """Test Session.resume_id field."""

    async def test_session_with_resume_id(self, db: AsyncSession) -> None:
        """Create Session with resume_id."""
        session = Session(
            id="sess-1",
            user_id="user-1",
            profile_id="interviewer",
            resume_id="res-1",
        )
        db.add(session)
        await db.commit()

        result = await db.execute(select(Session).where(Session.id == "sess-1"))
        row = result.scalar_one()
        assert row.resume_id == "res-1"

    async def test_session_without_resume_id(self, db: AsyncSession) -> None:
        """Session without resume_id defaults to None."""
        session = Session(
            id="sess-2",
            user_id="user-1",
            profile_id="interviewer",
        )
        db.add(session)
        await db.commit()

        result = await db.execute(select(Session).where(Session.id == "sess-2"))
        row = result.scalar_one()
        assert row.resume_id is None


class TestInitDb:
    """Test that init_db creates all tables including new ones."""

    async def test_init_db_creates_all_tables(self) -> None:
        """init_db creates repo_analyses, resumes, and sessions tables."""
        engine = create_async_engine("sqlite+aiosqlite://", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with engine.connect() as conn:
            table_names = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

        assert "repo_analyses" in table_names
        assert "resumes" in table_names
        assert "sessions" in table_names

        await engine.dispose()
