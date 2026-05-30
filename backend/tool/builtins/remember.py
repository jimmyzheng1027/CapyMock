"""remember tool — buffer facts to session during interview (no file writes)."""

from __future__ import annotations

from pydantic import BaseModel

from tool.base import ToolContext, ToolResult, tool


class RememberArgs(BaseModel):
    """Arguments for remember tool."""

    fact: str
    category: str = "general"


@tool
async def remember(args: RememberArgs, ctx: ToolContext) -> ToolResult:
    """Remember a fact during the interview. Facts are buffered to the session, not written to files."""
    if ctx.session is None:
        return ToolResult.err(
            code="no_session",
            message="No session in context",
            summary="No session",
        )

    try:
        if not hasattr(ctx.session, "notes"):
            ctx.session.notes = []

        ctx.session.notes.append({
            "note": args.fact,
            "category": args.category,
        })

        return ToolResult.ok(
            data={"fact": args.fact, "category": args.category},
            summary=f"Remembered: {args.fact[:50]}...",
        )
    except Exception as e:
        return ToolResult.err(
            code="error",
            message=f"Failed to remember: {e}",
            summary="Failed to remember",
        )
