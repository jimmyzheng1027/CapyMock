"""Tests for analysis pipeline: JSON parsing, caching, state machine."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from storage.db.models import Base, RepoAnalysis


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


# --- 7.1/7.2: JSON fence stripping + retry ---


class TestJsonParsing:
    """Test JSON parsing with fence stripping and retry."""

    def test_parse_clean_json(self) -> None:
        """Clean JSON parses directly."""
        from api.github_analysis import parse_analysis_json

        data = parse_analysis_json('{"overview": "test"}')
        assert data == {"overview": "test"}

    def test_parse_json_with_fences(self) -> None:
        """JSON wrapped in ```json fences is stripped and parsed."""
        from api.github_analysis import parse_analysis_json

        raw = '```json\n{"overview": "test"}\n```'
        data = parse_analysis_json(raw)
        assert data == {"overview": "test"}

    def test_parse_json_with_extra_text(self) -> None:
        """JSON with surrounding text: extract the JSON object."""
        from api.github_analysis import parse_analysis_json

        raw = 'Here is the analysis:\n```json\n{"overview": "test"}\n```\nDone.'
        data = parse_analysis_json(raw)
        assert data is not None
        assert data["overview"] == "test"

    def test_parse_invalid_json_returns_none(self) -> None:
        """Invalid JSON returns None."""
        from api.github_analysis import parse_analysis_json

        data = parse_analysis_json("not json at all")
        assert data is None


# --- 7.3: Caching tests ---


class TestAnalysisCaching:
    """Test that done analyses are cached and not re-run."""

    async def test_cache_hit_returns_immediately(self, db: AsyncSession) -> None:
        """Same URL with status=done → return cached result, no re-analysis."""
        from api.github_analysis import check_analysis_cache

        result_data = {"overview": "cached analysis"}
        analysis = RepoAnalysis(
            id="ra-cache-1",
            url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            status="done",
            result_json=json.dumps(result_data),
        )
        db.add(analysis)
        await db.commit()

        cached = await check_analysis_cache(db, "https://github.com/owner/repo")
        assert cached is not None
        assert cached["overview"] == "cached analysis"

    async def test_cache_miss_returns_none(self, db: AsyncSession) -> None:
        """No existing analysis → returns None."""
        from api.github_analysis import check_analysis_cache

        cached = await check_analysis_cache(db, "https://github.com/owner/missing")
        assert cached is None

    async def test_pending_returns_none(self, db: AsyncSession) -> None:
        """Pending analysis → returns None (not cached yet)."""
        from api.github_analysis import check_analysis_cache

        analysis = RepoAnalysis(
            id="ra-cache-2",
            url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            status="pending",
        )
        db.add(analysis)
        await db.commit()

        cached = await check_analysis_cache(db, "https://github.com/owner/repo")
        assert cached is None


# --- 7.4: State machine test ---


class TestAnalysisStateMachine:
    """Test analysis status transitions."""

    async def test_pending_to_done(self, db: AsyncSession) -> None:
        """Analysis goes from pending → running → done with result."""
        from api.github_analysis import complete_analysis, create_analysis_record

        analysis_id = await create_analysis_record(
            db, "https://github.com/o/r", "o", "r"
        )

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == analysis_id))
        row = result.scalar_one()
        assert row.status == "pending"

        await complete_analysis(db, analysis_id, {"overview": "done"})

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == analysis_id))
        row = result.scalar_one()
        assert row.status == "done"
        assert json.loads(row.result_json) == {"overview": "done"}

    async def test_failed_analysis(self, db: AsyncSession) -> None:
        """Analysis with error → status=failed + error message."""
        from api.github_analysis import create_analysis_record, fail_analysis

        analysis_id = await create_analysis_record(
            db, "https://github.com/o/private", "o", "private"
        )
        await fail_analysis(db, analysis_id, "Repository is private")

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == analysis_id))
        row = result.scalar_one()
        assert row.status == "failed"
        assert row.error == "Repository is private"

    async def test_finalize_prefers_saved_result_over_markdown(self, db: AsyncSession) -> None:
        """When save_repo_analysis already saved JSON, markdown final text must not fail."""
        from api.github_analysis import (
            complete_analysis,
            create_analysis_record,
            finalize_analysis_run,
        )
        from service.task_service import task_service

        analysis_id = await create_analysis_record(
            db, "https://github.com/o/r", "o", "r"
        )
        saved_data = {"description": "saved by tool", "highlights": []}
        await complete_analysis(db, analysis_id, saved_data)

        task_service.create_task(task_id=analysis_id)
        await finalize_analysis_run(
            db,
            analysis_id,
            "# Repo Report\n\nMarkdown summary after save_repo_analysis.",
        )

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == analysis_id))
        row = result.scalar_one()
        assert row.status == "done"
        assert json.loads(row.result_json) == saved_data

        task = task_service.get_task(analysis_id)
        assert task is not None
        assert task.status == "completed"
        assert task.result == saved_data

    async def test_finalize_fails_when_no_json_and_not_saved(self, db: AsyncSession) -> None:
        """Unparseable final text with no prior save → failed."""
        from api.github_analysis import create_analysis_record, finalize_analysis_run
        from service.task_service import task_service

        analysis_id = await create_analysis_record(
            db, "https://github.com/o/r", "o", "r"
        )
        task_service.create_task(task_id=analysis_id)
        await finalize_analysis_run(db, analysis_id, "not json")

        result = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == analysis_id))
        row = result.scalar_one()
        assert row.status == "failed"
        assert row.error == "Agent produced unparseable output"


# --- 7.6: Frontend read endpoint test ---


class TestFrontendReadEndpoint:
    """Test GET /api/analysis/{id} returns result_json."""

    async def test_read_completed_analysis(self, db: AsyncSession) -> None:
        """Read completed analysis returns result_json."""
        from api.github_analysis import get_analysis_result

        result_data = {"overview": "test", "highlights": []}
        analysis = RepoAnalysis(
            id="ra-read-1",
            url="https://github.com/o/r",
            owner="o",
            repo="r",
            status="done",
            result_json=json.dumps(result_data),
        )
        db.add(analysis)
        await db.commit()

        result = await get_analysis_result(db, "ra-read-1")
        assert result is not None
        assert result["overview"] == "test"

    async def test_read_pending_analysis(self, db: AsyncSession) -> None:
        """Read pending analysis returns None (not ready)."""
        from api.github_analysis import get_analysis_result

        analysis = RepoAnalysis(
            id="ra-read-2",
            url="https://github.com/o/r",
            owner="o",
            repo="r",
            status="pending",
        )
        db.add(analysis)
        await db.commit()

        result = await get_analysis_result(db, "ra-read-2")
        assert result is None
