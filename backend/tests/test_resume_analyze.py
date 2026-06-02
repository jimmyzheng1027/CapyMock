"""Tests for resume analysis API endpoint."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.app import app
from storage.db.models import Base, Resume


@pytest.fixture
async def db_engine():
    """Create an in-memory SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create a DB session."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def mock_db(db_engine):
    """Patch async_session_factory to use test engine."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def mock_factory():
        async with factory() as session:
            yield session

    with patch("api.resume_analysis.async_session_factory", mock_factory):
        yield


@pytest.fixture
def mock_profile():
    """Mock resume-analyzer profile."""
    profile = MagicMock()
    profile.id = "resume-analyzer"
    profile.prompt_template = "data/prompt/resume_analyzer.md"
    profile.llm.provider = "dashscope"
    profile.llm.model = "qwen-vl-max"
    profile.llm.temperature = 0.3
    return profile


@pytest.fixture
def mock_llm_response():
    return {
        "strengths": [
            {"text": "项目经历丰富", "detail": "有3个完整项目"}
        ],
        "weaknesses": [
            {"text": "缺少量化成果", "suggestion": "添加具体数据指标"}
        ],
        "suggestions": [
            "每个项目增加量化指标"
        ],
    }


class TestResumeAnalyze:
    """Tests for POST /api/resumes/{resume_id}/analyze."""

    @pytest.mark.asyncio
    async def test_analyze_success(
        self, mock_db, db_session, mock_profile, mock_llm_response, tmp_path
    ):
        """First analysis returns result and caches it."""
        file_path = tmp_path / "r1.pdf"
        file_path.write_bytes(b"fake pdf content")

        r = Resume(
            id="r1", user_id="user-1", file_name="a.pdf", file_type="pdf",
            content="", file_path=str(file_path),
        )
        db_session.add(r)
        await db_session.commit()

        mock_llm = MagicMock()
        mock_result = MagicMock()
        mock_result.text = json.dumps(mock_llm_response)
        mock_result.error = None
        mock_llm.chat = AsyncMock(return_value=mock_result)

        with (
            patch("api.resume_analysis.ProfileLoader") as MockLoader,
            patch("api.resume_analysis.LLMFactory.create", return_value=mock_llm),
            patch(
                "api.resume_analysis.prepare_resume_images",
                return_value=[("fakepng", "image/png")],
            ),
        ):
            MockLoader.return_value.load_all.return_value = None
            MockLoader.return_value.get.return_value = mock_profile

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/resumes/r1/analyze")

        assert resp.status_code == 200
        data = resp.json()
        assert "strengths" in data
        assert "weaknesses" in data
        assert "suggestions" in data

    @pytest.mark.asyncio
    async def test_analyze_cached(self, mock_db, db_session, tmp_path):
        """Second analysis returns cached result without calling LLM."""
        file_path = tmp_path / "r1.pdf"
        file_path.write_bytes(b"fake pdf content")

        cached_result = json.dumps({
            "strengths": [{"text": "cached", "detail": "cached detail"}],
            "weaknesses": [],
            "suggestions": [],
        })
        r = Resume(
            id="r1", user_id="user-1", file_name="a.pdf", file_type="pdf",
            content="", file_path=str(file_path), analysis_result=cached_result,
        )
        db_session.add(r)
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/resumes/r1/analyze")

        assert resp.status_code == 200
        data = resp.json()
        assert data["strengths"][0]["text"] == "cached"

    @pytest.mark.asyncio
    async def test_analyze_force_reanalysis(
        self, mock_db, db_session, mock_profile, mock_llm_response, tmp_path
    ):
        """force=true ignores cache and re-analyzes."""
        file_path = tmp_path / "r1.pdf"
        file_path.write_bytes(b"fake pdf content")

        r = Resume(
            id="r1", user_id="user-1", file_name="a.pdf", file_type="pdf",
            content="", file_path=str(file_path),
            analysis_result='{"strengths":[],"weaknesses":[],"suggestions":[]}',
        )
        db_session.add(r)
        await db_session.commit()

        mock_llm = MagicMock()
        mock_result = MagicMock()
        mock_result.text = json.dumps(mock_llm_response)
        mock_result.error = None
        mock_llm.chat = AsyncMock(return_value=mock_result)

        with (
            patch("api.resume_analysis.ProfileLoader") as MockLoader,
            patch("api.resume_analysis.LLMFactory.create", return_value=mock_llm),
            patch(
                "api.resume_analysis.prepare_resume_images",
                return_value=[("fakepng", "image/png")],
            ),
        ):
            MockLoader.return_value.load_all.return_value = None
            MockLoader.return_value.get.return_value = mock_profile

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/resumes/r1/analyze?force=true")

        assert resp.status_code == 200
        data = resp.json()
        assert data["strengths"][0]["text"] == "项目经历丰富"

    @pytest.mark.asyncio
    async def test_analyze_not_found(self, mock_db):
        """404 for non-existent resume."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/resumes/nonexistent/analyze")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_analyze_llm_error(self, mock_db, db_session, mock_profile, tmp_path):
        """LLM returning empty response returns 502."""
        file_path = tmp_path / "r1.pdf"
        file_path.write_bytes(b"fake pdf content")

        r = Resume(
            id="r1", user_id="user-1", file_name="a.pdf", file_type="pdf",
            content="", file_path=str(file_path),
        )
        db_session.add(r)
        await db_session.commit()

        mock_llm = MagicMock()
        mock_result = MagicMock()
        mock_result.text = ""
        mock_result.error = "Model not found"
        mock_llm.chat = AsyncMock(return_value=mock_result)

        with (
            patch("api.resume_analysis.ProfileLoader") as MockLoader,
            patch("api.resume_analysis.LLMFactory.create", return_value=mock_llm),
            patch(
                "api.resume_analysis.prepare_resume_images",
                return_value=[("fakepng", "image/png")],
            ),
        ):
            MockLoader.return_value.load_all.return_value = None
            MockLoader.return_value.get.return_value = mock_profile

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/resumes/r1/analyze")

        assert resp.status_code == 502
