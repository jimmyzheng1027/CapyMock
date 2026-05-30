"""GitHub analysis API — async pipeline with caching and result storage."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import EventType
from service.task_service import task_service
from storage.db.engine import async_session_factory
from storage.db.models import RepoAnalysis

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request to start GitHub analysis."""
    repo_url: str
    session_id: str | None = None


class AnalysisResponse(BaseModel):
    """Response for analysis submission."""
    task_id: str
    status: str


# --- JSON parsing helpers ---


def parse_analysis_json(raw: str) -> dict | None:
    """Parse analysis JSON with fence stripping and retry.

    Handles:
    - Clean JSON
    - JSON wrapped in ```json fences
    - JSON surrounded by extra text
    """
    # Try direct parse first
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strip ```json ... ``` fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    # Try to find JSON object in the text
    brace_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except (json.JSONDecodeError, TypeError):
            pass

    return None


# --- Database helpers ---


async def check_analysis_cache(db: AsyncSession, url: str) -> dict | None:
    """Check if a completed analysis exists for this URL. Returns result_json or None."""
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.url == url, RepoAnalysis.status == "done")
    )
    analysis = result.scalar_one_or_none()
    if analysis and analysis.result_json:
        try:
            return json.loads(analysis.result_json)
        except json.JSONDecodeError:
            return None
    return None


async def create_analysis_record(
    db: AsyncSession, url: str, owner: str, repo: str
) -> str:
    """Create a pending analysis record. Returns the analysis ID.

    If a record with the same URL already exists, return its ID.
    """
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.url == url)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing.id

    analysis_id = str(uuid.uuid4())
    analysis = RepoAnalysis(
        id=analysis_id,
        url=url,
        owner=owner,
        repo=repo,
        status="pending",
    )
    db.add(analysis)
    await db.commit()
    return analysis_id


async def complete_analysis(
    db: AsyncSession, analysis_id: str, result_data: dict
) -> None:
    """Mark analysis as done with result JSON."""
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if analysis:
        analysis.status = "done"
        analysis.result_json = json.dumps(result_data)
        analysis.analyzed_at = datetime.now(timezone.utc)
        await db.commit()


async def fail_analysis(db: AsyncSession, analysis_id: str, error: str) -> None:
    """Mark analysis as failed with error message."""
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if analysis:
        analysis.status = "failed"
        analysis.error = error
        await db.commit()


async def get_analysis_result(db: AsyncSession, analysis_id: str) -> dict | None:
    """Get analysis result for frontend. Returns parsed JSON or None."""
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if analysis and analysis.status == "done" and analysis.result_json:
        try:
            return json.loads(analysis.result_json)
        except json.JSONDecodeError:
            return None
    return None


async def get_analysis_record(db: AsyncSession, analysis_id: str) -> RepoAnalysis | None:
    """Get full analysis record by ID."""
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.id == analysis_id)
    )
    return result.scalar_one_or_none()


async def get_saved_analysis_result(
    db: AsyncSession, analysis_id: str
) -> dict | None:
    """Return parsed result if save_repo_analysis already persisted it."""
    analysis = await get_analysis_record(db, analysis_id)
    if analysis and analysis.status == "done" and analysis.result_json:
        return parse_analysis_json(analysis.result_json)
    return None


async def finalize_analysis_run(
    db: AsyncSession, task_id: str, final_text: str
) -> None:
    """Finalize analysis after agent loop — prefer tool-saved result over final text."""
    result_data = parse_analysis_json(final_text) if final_text else None
    if result_data:
        await complete_analysis(db, task_id, result_data)
        await task_service.complete_task(task_id, result_data)
        return

    saved = await get_saved_analysis_result(db, task_id)
    if saved:
        await task_service.complete_task(task_id, saved)
        return

    error_msg = (
        "Agent produced unparseable output"
        if final_text
        else "Agent produced no output"
    )
    await fail_analysis(db, task_id, error_msg)
    await task_service.fail_task(task_id, error_msg)


def merge_analysis(analysis: RepoAnalysis, result: dict) -> dict:
    """Merge DB record with agent-generated result_json into frontend format."""
    return {
        "id": analysis.id,
        "fullName": f"{analysis.owner}/{analysis.repo}",
        "owner": analysis.owner,
        "repoName": analysis.repo,
        "description": result.get("description", ""),
        "url": analysis.url,
        "status": analysis.status,
        "analyzedAt": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
        "techTags": result.get("techTags", []),
        "score": result.get("score"),
        "directoryTree": result.get("directoryTree"),
        "highlights": result.get("highlights", []),
        "suggestions": result.get("suggestions", []),
        "questions": result.get("questions", []),
        "sections": result.get("sections", []),
        "codeSnippets": result.get("codeSnippets", []),
    }


async def get_analysis_by_url(db: AsyncSession, url: str) -> RepoAnalysis | None:
    """Get analysis record by URL."""
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.url == url)
    )
    return result.scalar_one_or_none()


# --- API endpoints ---


@router.post("/analysis", response_model=AnalysisResponse)
async def submit_analysis(request: AnalysisRequest):
    """Submit a GitHub repository analysis task."""
    async with async_session_factory() as db:
        # Check cache
        cached = await check_analysis_cache(db, request.repo_url)
        if cached:
            # Return existing analysis ID
            existing = await get_analysis_by_url(db, request.repo_url)
            return AnalysisResponse(task_id=existing.id, status="done")

        # Parse URL to extract owner/repo
        url = request.repo_url.rstrip("/")
        parts = url.split("/")
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid repository URL")
        owner, repo = parts[-2], parts[-1]
        repo = repo.removesuffix(".git")

        # Create pending record
        analysis_id = await create_analysis_record(db, url, owner, repo)

    # Register with TaskService so SSE endpoint can stream progress
    task_service.create_task(task_id=analysis_id)

    # Run analysis in background

    asyncio.create_task(
        _run_analysis(task_id=analysis_id, repo_url=request.repo_url)
    )

    return AnalysisResponse(task_id=analysis_id, status="pending")


@router.get("/analysis")
async def list_analyses():
    """List all completed and failed analyses."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(RepoAnalysis)
            .where(RepoAnalysis.status.in_(["done", "failed"]))
            .order_by(RepoAnalysis.analyzed_at.desc())
        )
        analyses = result.scalars().all()

    items = []
    for analysis in analyses:
        if analysis.status == "done" and analysis.result_json:
            parsed = parse_analysis_json(analysis.result_json)
            if parsed:
                items.append(merge_analysis(analysis, parsed))
        elif analysis.status == "failed":
            items.append({
                "id": analysis.id,
                "fullName": f"{analysis.owner}/{analysis.repo}",
                "owner": analysis.owner,
                "repoName": analysis.repo,
                "url": analysis.url,
                "status": "failed",
                "analyzedAt": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
                "error": analysis.error,
            })
    return items


@router.get("/analysis/{analysis_id}")
async def read_analysis(analysis_id: str):
    """Read analysis result by ID (supports both done and failed)."""
    async with async_session_factory() as db:
        analysis = await get_analysis_record(db, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status == "failed":
        return {
            "id": analysis.id,
            "fullName": f"{analysis.owner}/{analysis.repo}",
            "owner": analysis.owner,
            "repoName": analysis.repo,
            "url": analysis.url,
            "status": "failed",
            "analyzedAt": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            "error": analysis.error,
        }

    if analysis.status != "done" or not analysis.result_json:
        raise HTTPException(status_code=404, detail="Analysis not ready")
    parsed = parse_analysis_json(analysis.result_json)
    if parsed is None:
        raise HTTPException(status_code=500, detail="Failed to parse analysis result")
    return merge_analysis(analysis, parsed)


async def _run_analysis(task_id: str, repo_url: str):
    """Run GitHub analysis using the ReAct agent with TaskService progress."""
    from agent.loop import CancelToken
    from api.app import app
    from config.settings import settings

    agent_factory = app.state.agent_factory
    session_store = app.state.session_store

    # Create a synthetic session for the agent
    # Clear existing history to avoid stale context from previous runs
    session_id = f"analysis-{task_id}"
    session_store.create("system", session_id, "repo-analyzer", clear_existing=True)

    # Create cancel token and bridge to TaskService
    cancel_token = CancelToken()
    asyncio.create_task(_bridge_cancel(task_id, cancel_token))

    await task_service.update_progress(task_id, 0.05, "正在初始化分析...")

    async with async_session_factory() as db:
        try:
            agent = agent_factory.create(
                profile_id="repo-analyzer",
                session_id=session_id,
                mode="text",
                user_id="system",
                db_session=db,
            )
            agent.cancel_token = cancel_token
            agent._repo_root = settings.REPO_ROOT
            agent._repo_url = repo_url

            user_input = (
                f"Analyze repository {repo_url}. "
                f"Use analysis_id={task_id}. "
                f"First call read_skill(skill_id=\"repo-analyzer\"), then follow that workflow. "
                f"Cache was already checked by the API; proceed with clone and analysis."
            )

            tool_count = 0
            final_text = ""

            async for event in agent.run(user_input):
                if event.type == EventType.TOOL_CALL_START:
                    tool_count += 1
                    tool_name = event.payload.get("tool_name", "")
                    progress = min(0.90, 0.05 + tool_count * 0.04)
                    await task_service.update_progress(
                        task_id, progress, _progress_message(tool_name),
                        data={"tool_name": tool_name},
                    )
                elif event.type == EventType.ASSISTANT_TEXT_DONE:
                    final_text = event.payload.get("text", "")
                    await task_service.update_progress(
                        task_id, 0.95, "正在生成分析报告..."
                    )
                elif event.type == EventType.ERROR:
                    error_msg = event.payload.get("message", "Unknown error")
                    await task_service.fail_task(task_id, error_msg)
                    await fail_analysis(db, task_id, error_msg)
                    return

            await finalize_analysis_run(db, task_id, final_text)

        except Exception as e:
            logger.error(f"Analysis failed for {task_id}: {e}")
            await fail_analysis(db, task_id, str(e))
            await task_service.fail_task(task_id, str(e))


async def _bridge_cancel(task_id: str, cancel_token) -> None:
    """Bridge TaskService cancel event to agent CancelToken."""
    event = task_service.get_cancel_token(task_id)
    await event.wait()
    cancel_token.cancel()


def _progress_message(tool_name: str) -> str:
    """Map tool name to a human-readable progress message."""
    messages = {
        "read_skill": "正在加载分析流程...",
        "clone_repo": "正在克隆仓库...",
        "list_directory": "正在扫描目录结构...",
        "read_file": "正在分析源代码...",
        "search_code": "正在搜索代码模式...",
        "save_repo_analysis": "正在保存分析结果...",
    }
    return messages.get(tool_name, "正在分析...")
