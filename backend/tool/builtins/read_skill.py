"""read_skill tool — load full SKILL.md for progressive skill loading."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from tool.base import ToolContext, ToolResult, tool


class ReadSkillArgs(BaseModel):
    """Arguments for read_skill tool."""

    skill_id: str = Field(
        default="",
        description=(
            '(REQUIRED) Skill identifier to load, e.g. "repo-analyzer". '
            "Must match an entry from Available Skills in the system prompt. "
            'Example: {"skill_id": "repo-analyzer"}'
        ),
    )


def _resolve_skill_id(args: ReadSkillArgs, ctx: ToolContext) -> str | None:
    """Infer skill_id when the model omits it (common with some providers)."""
    if args.skill_id.strip():
        return args.skill_id.strip()

    if not ctx.profile or not getattr(ctx.profile, "skills", None):
        return None

    skills: list[str] = ctx.profile.skills
    if len(skills) == 1:
        return skills[0]
    return None


def _strip_frontmatter(content: str) -> str:
    """Return SKILL.md body without YAML frontmatter."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content


@tool
async def read_skill(args: ReadSkillArgs, ctx: ToolContext) -> ToolResult:
    """Load the full SKILL.md workflow for a skill ID.

    Call this before following a multi-phase skill. Pass skill_id explicitly
    (e.g. read_skill with skill_id \"repo-analyzer\"). Only whitelisted skills
    for the current agent profile can be loaded.
    """
    skill_id = _resolve_skill_id(args, ctx)
    if not skill_id:
        allowed = (
            ", ".join(ctx.profile.skills)
            if ctx.profile and getattr(ctx.profile, "skills", None)
            else "(none)"
        )
        return ToolResult.err(
            code="missing_arg",
            message=(
                "skill_id is required. Pass it explicitly, e.g. "
                '{"skill_id": "repo-analyzer"}. '
                f"Allowed skills for this agent: {allowed}"
            ),
            summary="Missing skill_id",
        )

    if ctx.profile and hasattr(ctx.profile, "skills"):
        if skill_id not in ctx.profile.skills:
            return ToolResult.err(
                code="skill_not_available",
                message=f"Skill not available: {skill_id}",
                summary=f"Skill not available: {skill_id}",
            )

    skill_path = Path("data/skill") / skill_id / "SKILL.md"

    if not skill_path.exists():
        return ToolResult.err(
            code="not_found",
            message=f"Skill not found: {skill_id}",
            summary=f"Skill not found: {skill_id}",
        )

    try:
        raw = skill_path.read_text(encoding="utf-8")
        body = _strip_frontmatter(raw)
        return ToolResult.ok(
            data={"skill_id": skill_id, "content": body},
            summary=f"Read skill {skill_id}",
        )
    except Exception as e:
        return ToolResult.err(
            code="read_error",
            message=f"Failed to read skill: {e!s}",
            summary="Failed to read skill",
        )
