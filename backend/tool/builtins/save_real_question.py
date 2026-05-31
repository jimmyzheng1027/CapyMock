"""save_real_question tool — save a real interview question to REAL_QUES.md."""

from __future__ import annotations

from pydantic import BaseModel

from tool.base import ToolContext, ToolResult, tool


class SaveRealQuestionArgs(BaseModel):
    """Arguments for save_real_question tool."""

    question: str
    company: str = ""
    source: str = "candidate"


@tool
async def save_real_question(args: SaveRealQuestionArgs, ctx: ToolContext) -> ToolResult:
    """Save a real interview question mentioned by the candidate to memory.

    Use this when the candidate shares a real interview question they encountered.
    The question is appended to the REAL_QUES.md file for this user and resume.
    """
    if not ctx.user_id or not ctx.resume_id:
        return ToolResult.err(
            code="missing_context",
            message="user_id and resume_id are required to save real questions",
            summary="Missing context",
        )

    try:
        from storage.memory.store import MemoryStore

        store = MemoryStore(root_dir=ctx.memory_root or "storage/memory")
        existing = store.read_real_ques(ctx.user_id, ctx.resume_id)

        # Format new entry
        entry = f"\n- {args.question}"
        if args.company:
            entry = f"\n- [{args.company}] {args.question}"

        # Append to existing content
        content = existing + entry if existing else f"# 真实面试题\n{entry.lstrip(chr(10))}"

        store.write_real_ques(ctx.user_id, ctx.resume_id, content)

        return ToolResult.ok(
            data={"question": args.question, "company": args.company},
            summary=f"Saved real question: {args.question[:50]}...",
        )
    except Exception as e:
        return ToolResult.err(
            code="error",
            message=f"Failed to save real question: {e}",
            summary="Failed to save",
        )
