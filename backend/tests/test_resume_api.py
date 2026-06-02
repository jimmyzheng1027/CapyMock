"""Tests for resume management API endpoints."""

from __future__ import annotations

import io
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.app import app
from storage.db.models import Base, Resume
from tests.test_resume_media import make_pdf_bytes


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
def sample_pdf():
    """Create a sample PDF file for upload."""
    content = b"%PDF-1.4 fake pdf content"
    return ("resume.pdf", io.BytesIO(content), "application/pdf")


@pytest.fixture
def sample_png():
    """Create a sample PNG file for upload."""
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    return ("resume.png", io.BytesIO(content), "image/png")


class TestResumeUpload:
    """Tests for POST /api/resumes/upload."""

    @pytest.mark.asyncio
    async def test_upload_pdf(self, mock_db, sample_pdf, tmp_path):
        """Upload a PDF resume successfully."""
        with patch("api.resume_analysis.RESUME_ROOT", tmp_path):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/resumes/upload",
                    files={"file": sample_pdf},
                    data={"user_id": "user-1"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["file_name"] == "resume.pdf"
        assert data["file_type"] == "pdf"

    @pytest.mark.asyncio
    async def test_upload_pdf_stores_extracted_content(
        self, mock_db, db_session, tmp_path
    ):
        """Upload extracts PDF text into resume.content."""
        pdf_bytes = make_pdf_bytes("Jane Doe Fullstack Developer")
        files = {"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        with patch("api.resume_analysis.RESUME_ROOT", tmp_path):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/resumes/upload",
                    files=files,
                    data={"user_id": "user-1"},
                )

        assert resp.status_code == 200
        resume_id = resp.json()["id"]

        from sqlalchemy import select

        result = await db_session.execute(select(Resume).where(Resume.id == resume_id))
        row = result.scalar_one()
        assert "Jane Doe" in row.content
        assert "Fullstack Developer" in row.content

    @pytest.mark.asyncio
    async def test_upload_png(self, mock_db, sample_png, tmp_path):
        """Upload a PNG resume successfully."""
        with patch("api.resume_analysis.RESUME_ROOT", tmp_path):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/resumes/upload",
                    files={"file": sample_png},
                    data={"user_id": "user-1"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["file_type"] == "png"

    @pytest.mark.asyncio
    async def test_upload_unsupported_format(self, mock_db):
        """Upload unsupported format returns 400."""
        content = b"not a resume"
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/resumes/upload",
                files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
                data={"user_id": "user-1"},
            )

        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, mock_db):
        """Upload file over 10MB returns 413."""
        content = b"\x00" * (10 * 1024 * 1024 + 1)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/resumes/upload",
                files={"file": ("resume.pdf", io.BytesIO(content), "application/pdf")},
                data={"user_id": "user-1"},
            )

        assert resp.status_code == 413


class TestResumeList:
    """Tests for GET /api/resumes."""

    @pytest.mark.asyncio
    async def test_list_resumes(self, mock_db, db_session):
        """List resumes for a user."""
        r1 = Resume(id="r1", user_id="user-1", file_name="a.pdf", file_type="pdf", content="")
        r2 = Resume(id="r2", user_id="user-1", file_name="b.png", file_type="png", content="")
        r3 = Resume(id="r3", user_id="user-2", file_name="c.pdf", file_type="pdf", content="")
        db_session.add_all([r1, r2, r3])
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/resumes", params={"user_id": "user-1"})

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_resumes_empty(self, mock_db):
        """Empty list when no resumes."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/resumes", params={"user_id": "nobody"})

        assert resp.status_code == 200
        assert resp.json() == []


class TestResumeDetail:
    """Tests for GET /api/resumes/{resume_id}."""

    @pytest.mark.asyncio
    async def test_get_resume(self, mock_db, db_session):
        """Get resume detail with analysis result."""
        r = Resume(
            id="r1",
            user_id="user-1",
            file_name="a.pdf",
            file_type="pdf",
            content="",
            analysis_result='{"strengths": []}',
        )
        db_session.add(r)
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/resumes/r1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "r1"
        assert data["analysis_result"] == {"strengths": []}

    @pytest.mark.asyncio
    async def test_get_resume_not_found(self, mock_db):
        """404 for non-existent resume."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/resumes/nonexistent")

        assert resp.status_code == 404


class TestResumeDelete:
    """Tests for DELETE /api/resumes/{resume_id}."""

    @pytest.mark.asyncio
    async def test_delete_resume(self, mock_db, db_session, tmp_path):
        """Delete resume removes file and DB record."""
        # Create a temp file to be deleted
        file_path = tmp_path / "r1.pdf"
        file_path.write_bytes(b"fake pdf")

        r = Resume(
            id="r1", user_id="user-1", file_name="a.pdf", file_type="pdf",
            content="", file_path=str(file_path),
        )
        db_session.add(r)
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.delete("/api/resumes/r1")

        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_resume_not_found(self, mock_db):
        """404 for non-existent resume."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.delete("/api/resumes/nonexistent")

        assert resp.status_code == 404
