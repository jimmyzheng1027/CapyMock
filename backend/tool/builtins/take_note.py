from __future__ import annotations

from pydantic import BaseModel

from tool.base import ToolContext, ToolResult, tool


class TakeNoteArgs(BaseModel):
    """Arguments for take_note tool."""

    note: str
    category: str = "general"


@tool
async def take_note(args: TakeNoteArgs, ctx: ToolContext) -> ToolResult:
    """Take a note during the interview. Notes are appended to the current session."""
    if ctx.session is None:
        return ToolResult.err(
            code="no_session",
            message="No session in context",
            summary="No session",
        )

    try:
        # Append note to session's notes list
        if not hasattr(ctx.session, "notes"):
            ctx.session.notes = []

        ctx.session.notes.append({
            "note": args.note,
            "category": args.category,
        })

        return ToolResult.ok(
            data={"note": args.note, "category": args.category},
            summary=f"Noted: {args.note[:50]}...",
        )
    except Exception as e:
        return ToolResult.err(
            code="error",
            message=f"Failed to take note: {str(e)}",
            summary="Failed to take note",
        )
