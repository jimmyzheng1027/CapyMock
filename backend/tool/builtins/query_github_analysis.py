from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from tool.base import ToolContext, ToolResult, tool


class QueryGithubAnalysisArgs(BaseModel):
    """Arguments for query_github_analysis tool."""

    repo_id: str


@tool
async def query_github_analysis(args: QueryGithubAnalysisArgs, ctx: ToolContext) -> ToolResult:
    """Query existing GitHub repository analysis results.

    Only reads pre-existing analysis; does not trigger new analysis.
    """
    # For MVP, we look for analysis results in a standard location
    analysis_path = Path("backend/data/github_analysis") / f"{args.repo_id}.json"

    if not analysis_path.exists():
        return ToolResult.err(
            code="not_found",
            message=f"GitHub analysis not found for repo: {args.repo_id}",
            summary=f"No analysis for {args.repo_id}",
        )

    try:
        import json

        content = analysis_path.read_text(encoding="utf-8")
        analysis = json.loads(content)
        return ToolResult.ok(
            data={"repo_id": args.repo_id, "analysis": analysis},
            summary=f"Loaded analysis for {args.repo_id}",
        )
    except Exception as e:
        return ToolResult.err(
            code="read_error",
            message=f"Failed to read analysis: {str(e)}",
            summary="Failed to read analysis",
        )
