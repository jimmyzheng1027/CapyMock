"""save_repo_analysis tool — write analysis result to SQL."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import select

from storage.db.models import RepoAnalysis
from tool.base import ToolContext, ToolResult, tool


class SaveRepoAnalysisArgs(BaseModel):
    """Arguments for save_repo_analysis tool."""

    analysis_id: str = ""
    result_json: str = ""


@tool
async def save_repo_analysis(args: SaveRepoAnalysisArgs, ctx: ToolContext) -> ToolResult:
    """Save repo analysis result to the database."""
    analysis_id = args.analysis_id
    if not analysis_id and ctx.session_id:
        analysis_id = ctx.session_id.removeprefix("analysis-")
    result_json = args.result_json
    if not analysis_id:
        return ToolResult.err(
            code="missing_arg",
            message="analysis_id is required",
            summary="Missing analysis_id",
        )
    if not result_json:
        return ToolResult.err(
            code="missing_arg",
            message="result_json is required",
            summary="Missing result_json",
        )

    if ctx.db_session is None:
        return ToolResult.err(
            code="no_db_session",
            message="No database session in context",
            summary="No DB session",
        )
    db = ctx.db_session

    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if analysis is None:
        return ToolResult.err(
            code="not_found",
            message=f"Analysis not found: {analysis_id}",
            summary=f"Not found: {analysis_id}",
        )

    analysis.result_json = result_json
    analysis.status = "done"
    analysis.analyzed_at = datetime.now(timezone.utc)
    await db.commit()

    return ToolResult.ok(
        data={"analysis_id": analysis_id, "status": "done"},
        summary=f"Saved analysis {analysis_id}",
    )
