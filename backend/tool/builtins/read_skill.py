from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from tool.base import ToolContext, ToolResult, tool


class ReadSkillArgs(BaseModel):
    """Arguments for read_skill tool."""

    skill_id: str


@tool
async def read_skill(args: ReadSkillArgs, ctx: ToolContext) -> ToolResult:
    """Read a skill definition by ID.

    Only reads skills that are in the profile's skills whitelist.
    """
    # Check if skill is in profile's whitelist
    if ctx.profile and hasattr(ctx.profile, "skills"):
        if args.skill_id not in ctx.profile.skills:
            return ToolResult.err(
                code="skill_not_available",
                message=f"Skill not available: {args.skill_id}",
                summary=f"Skill not available: {args.skill_id}",
            )

    skill_path = Path("backend/data/skill") / args.skill_id / "SKILL.md"

    if not skill_path.exists():
        return ToolResult.err(
            code="not_found",
            message=f"Skill not found: {args.skill_id}",
            summary=f"Skill not found: {args.skill_id}",
        )

    try:
        content = skill_path.read_text(encoding="utf-8")
        return ToolResult.ok(
            data={"skill_id": args.skill_id, "content": content},
            summary=f"Read skill {args.skill_id}",
        )
    except Exception as e:
        return ToolResult.err(
            code="read_error",
            message=f"Failed to read skill: {str(e)}",
            summary="Failed to read skill",
        )
