"""Tests for read_skill tool."""

from __future__ import annotations

import pytest

from agent.profile import AgentProfile, LLMConfig
from tool.base import ToolContext
from tool.builtins.read_skill import (
    ReadSkillArgs,
    _resolve_skill_id,
    _strip_frontmatter,
    read_skill,
)


class TestStripFrontmatter:
    def test_strips_yaml(self) -> None:
        raw = "---\nname: x\ndescription: y\n---\n\n## Workflow\nstep 1"
        assert _strip_frontmatter(raw) == "## Workflow\nstep 1"


class TestResolveSkillId:
    def test_explicit(self) -> None:
        profile = AgentProfile(
            id="repo-analyzer",
            prompt_template="x.md",
            llm=LLMConfig(provider="t", model="t"),
            skills=["repo-analyzer"],
        )
        ctx = ToolContext(profile=profile)
        assert _resolve_skill_id(ReadSkillArgs(skill_id="repo-analyzer"), ctx) == "repo-analyzer"

    def test_empty_single_skill_profile(self) -> None:
        profile = AgentProfile(
            id="repo-analyzer",
            prompt_template="x.md",
            llm=LLMConfig(provider="t", model="t"),
            skills=["repo-analyzer"],
        )
        ctx = ToolContext(profile=profile)
        assert _resolve_skill_id(ReadSkillArgs(), ctx) == "repo-analyzer"

    def test_empty_multi_skill(self) -> None:
        profile = AgentProfile(
            id="interviewer",
            prompt_template="x.md",
            llm=LLMConfig(provider="t", model="t"),
            skills=["a", "b"],
        )
        ctx = ToolContext(profile=profile)
        assert _resolve_skill_id(ReadSkillArgs(), ctx) is None


@pytest.mark.asyncio
async def test_read_skill_accepts_empty_args_for_repo_analyzer() -> None:
    profile = AgentProfile(
        id="repo-analyzer",
        prompt_template="x.md",
        llm=LLMConfig(provider="t", model="t"),
        skills=["repo-analyzer"],
    )
    ctx = ToolContext(profile=profile)
    result = await read_skill(ReadSkillArgs(), ctx)
    assert result.status == "ok"
    assert result.data is not None
    assert result.data["skill_id"] == "repo-analyzer"
    assert "---" not in result.data["content"][:10] or "Workflow" in result.data["content"]
