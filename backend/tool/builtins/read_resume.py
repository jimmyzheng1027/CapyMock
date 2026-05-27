from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from config.settings import settings
from tool.base import ToolContext, ToolResult, tool


class ReadResumeArgs(BaseModel):
    """Arguments for read_resume tool."""

    resume_id: str


@tool
async def read_resume(args: ReadResumeArgs, ctx: ToolContext) -> ToolResult:
    """Read a user's resume by ID. Returns the resume content."""
    user_id = ctx.user_id
    if not user_id:
        return ToolResult.err(
            code="no_user_id",
            message="No user ID in context",
            summary="No user ID",
        )

    resume_path = Path(settings.RESUME_ROOT) / user_id / f"{args.resume_id}.md"

    if not resume_path.exists():
        # Try .txt extension
        resume_path = Path(settings.RESUME_ROOT) / user_id / f"{args.resume_id}.txt"

    if not resume_path.exists():
        return ToolResult.err(
            code="not_found",
            message=f"Resume not found: {args.resume_id}",
            summary=f"Resume not found: {args.resume_id}",
        )

    try:
        content = resume_path.read_text(encoding="utf-8")
        return ToolResult.ok(
            data={"content": content, "resume_id": args.resume_id},
            summary=f"Read resume {args.resume_id}",
        )
    except Exception as e:
        return ToolResult.err(
            code="read_error",
            message=f"Failed to read resume: {str(e)}",
            summary="Failed to read resume",
        )
