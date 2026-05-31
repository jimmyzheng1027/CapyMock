"""Resume management and analysis API endpoints."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select

from agent.llm.factory import LLMFactory
from agent.llm.providers.openai_compatible import build_multimodal_message
from agent.profile_loader import ProfileLoader
from config.settings import settings
from service.resume_media import extract_resume_text, prepare_resume_images
from storage.db.engine import async_session_factory
from storage.db.models import Resume

router = APIRouter(tags=["resumes"])

# Supported file types
ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}
TYPE_EXTENSIONS = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
}
MIME_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Resume file storage root
RESUME_ROOT = Path("storage/resumes")


class ResumeResponse(BaseModel):
    """Response for resume metadata."""
    id: str
    file_name: str | None = None
    file_type: str | None = None
    has_analysis: bool = False
    created_at: str | None = None


class ResumeDetailResponse(BaseModel):
    """Response for resume detail."""
    id: str
    file_name: str | None = None
    file_type: str | None = None
    has_analysis: bool = False
    analysis_result: dict | None = None
    created_at: str | None = None


@router.post("/resumes/upload")
async def upload_resume(file: UploadFile, user_id: str = "default"):
    """Upload a resume file (PDF, PNG, JPG)."""
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, PNG, JPG",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size cannot exceed 10MB")

    # Generate ID and paths
    resume_id = str(uuid.uuid4())
    ext = TYPE_EXTENSIONS[file.content_type]
    user_dir = RESUME_ROOT / user_id
    os.makedirs(user_dir, exist_ok=True)
    file_path = user_dir / f"{resume_id}.{ext}"

    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        text_content = extract_resume_text(content, ext)
    except Exception:
        text_content = ""

    # Save metadata to DB
    async with async_session_factory() as db:
        resume = Resume(
            id=resume_id,
            user_id=user_id,
            file_name=file.filename,
            file_path=str(file_path),
            file_type=ext,
            content=text_content,
        )
        db.add(resume)
        await db.commit()

    return {
        "id": resume_id,
        "file_name": file.filename,
        "file_type": ext,
        "has_analysis": False,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
    }


@router.get("/resumes")
async def list_resumes(user_id: str = "default"):
    """List all resumes for a user."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )
        resumes = result.scalars().all()

    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "has_analysis": r.analysis_result is not None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in resumes
    ]


@router.get("/resumes/{resume_id}")
async def get_resume(resume_id: str):
    """Get resume detail with analysis result if available."""
    async with async_session_factory() as db:
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    analysis = None
    if resume.analysis_result:
        try:
            analysis = json.loads(resume.analysis_result)
        except json.JSONDecodeError:
            pass

    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "has_analysis": resume.analysis_result is not None,
        "analysis_result": analysis,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
    }


@router.delete("/resumes/{resume_id}", status_code=204)
async def delete_resume(resume_id: str):
    """Delete a resume file and its DB record."""
    async with async_session_factory() as db:
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Delete file from disk
        if resume.file_path and os.path.exists(resume.file_path):
            os.remove(resume.file_path)

        # Delete DB record
        await db.delete(resume)
        await db.commit()


@router.post("/resumes/{resume_id}/analyze")
async def analyze_resume(resume_id: str, force: bool = False):
    """Analyze a resume using multimodal LLM. Returns cached result unless force=true."""
    async with async_session_factory() as db:
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Return cached result if available and not forcing
        if resume.analysis_result and not force:
            try:
                return json.loads(resume.analysis_result)
            except json.JSONDecodeError:
                pass  # re-analyze if cache is corrupt

    # Load profile and prompt
    profile_loader = ProfileLoader("config/agents")
    profile_loader.load_all()
    profile = profile_loader.get("resume-analyzer")

    if not profile:
        raise HTTPException(500, "resume-analyzer profile not found")

    with open(profile.prompt_template, encoding="utf-8") as f:
        prompt = f.read()

    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(500, "Resume file not found on disk")

    try:
        images = prepare_resume_images(resume.file_path, resume.file_type or "pdf")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Failed to prepare resume images: {exc}") from exc

    page_hint = ""
    if resume.file_type == "pdf" and len(images) > 1:
        page_hint = f"（共 {len(images)} 页）"

    # Create LLM
    llm = LLMFactory.create(
        profile.llm.provider,
        {
            "api_key": settings.get_api_key(profile.llm.provider),
            "model": profile.llm.model,
            "temperature": profile.llm.temperature,
        },
    )

    user_msg = build_multimodal_message(f"请分析这份简历{page_hint}", images=images)
    messages = [
        {"role": "system", "content": prompt},
        user_msg,
    ]

    llm_result = await llm.chat(messages)

    if llm_result.error:
        raise HTTPException(502, f"LLM error: {llm_result.error}")

    if not llm_result.text:
        raise HTTPException(502, "LLM returned empty response")

    # Parse JSON
    try:
        data = json.loads(llm_result.text)
    except json.JSONDecodeError:
        raise HTTPException(500, f"LLM returned invalid JSON: {llm_result.text[:200]}")

    # Cache result
    async with async_session_factory() as db:
        result = await db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        if resume:
            resume.analysis_result = json.dumps(data, ensure_ascii=False)
            if not (resume.content or "").strip() and resume.file_path:
                try:
                    with open(resume.file_path, "rb") as handle:
                        resume.content = extract_resume_text(
                            handle.read(), resume.file_type or "pdf"
                        )
                except Exception:
                    pass
            await db.commit()

    return data
