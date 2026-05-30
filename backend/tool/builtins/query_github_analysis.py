"""query_github_analysis tool — query analysis from SQL."""

from __future__ import annotations

import json

from pydantic import BaseModel
from sqlalchemy import select

from storage.db.models import RepoAnalysis
from tool.base import ToolContext, ToolResult, tool


class QueryGithubAnalysisArgs(BaseModel):
    """Arguments for query_github_analysis tool."""

    repo_url: str = ""


@tool
async def query_github_analysis(args: QueryGithubAnalysisArgs, ctx: ToolContext) -> ToolResult:
    """Query existing GitHub repository analysis results from the database."""
    if ctx.db_session is None:
        return ToolResult.err(
            code="no_db_session",
            message="No database session in context",
            summary="No DB session",
        )
    db = ctx.db_session

    repo_url = args.repo_url
    if not repo_url:
        repo_url = ctx.repo_url
    if not repo_url:
        return ToolResult.err(
            code="missing_arg",
            message="repo_url is required",
            summary="Missing repo_url",
        )

    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.url == repo_url)
    )
    analysis = result.scalar_one_or_none()

    if analysis is None:
        return ToolResult.err(
            code="not_found",
            message=f"GitHub analysis not found for: {repo_url}",
            summary=f"No analysis for {repo_url}",
        )

    if analysis.status == "failed":
        return ToolResult.err(
            code="analysis_failed",
            message=f"Analysis failed: {analysis.error or 'unknown error'}",
            summary="Analysis failed — consider retrying",
        )

    if analysis.status != "done":
        return ToolResult.err(
            code="not_ready",
            message=f"Analysis not ready (status={analysis.status})",
            summary=f"Analysis status: {analysis.status}",
        )

    try:
        data = json.loads(analysis.result_json) if analysis.result_json else {}
    except json.JSONDecodeError:
        data = {}

    return ToolResult.ok(
        data={"repo_url": repo_url, "analysis": data, "analysis_id": analysis.id},
        summary=f"Loaded analysis for {repo_url}",
    )
