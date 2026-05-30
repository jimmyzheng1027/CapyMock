"""read_resume tool — read resume content from SQL."""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import select

from storage.db.models import Resume
from tool.base import ToolContext, ToolResult, tool


class ReadResumeArgs(BaseModel):
    """Arguments for read_resume tool."""

    resume_id: str


@tool
async def read_resume(args: ReadResumeArgs, ctx: ToolContext) -> ToolResult:
    """Read a user's resume by ID from the database."""
    user_id = ctx.user_id
    if not user_id:
        return ToolResult.err(
            code="no_user_id",
            message="No user ID in context",
            summary="No user ID",
        )

    if ctx.db_session is None:
        return ToolResult.err(
            code="no_db_session",
            message="No database session in context",
            summary="No DB session",
        )
    db = ctx.db_session

    result = await db.execute(
        select(Resume).where(Resume.id == args.resume_id, Resume.user_id == user_id)
    )
    resume = result.scalar_one_or_none()

    if resume is None:
        return ToolResult.err(
            code="not_found",
            message=f"Resume not found: {args.resume_id}",
            summary=f"Resume not found: {args.resume_id}",
        )

    return ToolResult.ok(
        data={"content": resume.content, "resume_id": args.resume_id},
        summary=f"Read resume {args.resume_id}",
    )
