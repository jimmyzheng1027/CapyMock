"""Tests for ContextBuilder and ContextCompactor."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.context.builder import ContextBuilder
from agent.context.compactor import ContextCompactor
from agent.context.skill_loader import SkillLoader
from agent.profile import AgentProfile, ContextConfig, LLMConfig
from api.schemas import EventType, FrontendEvent


class TestSkillLoader:
    """Test SkillLoader behavior."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory with test skills."""
        skill_dir = tmp_path / "skill" / "test-skill"
        skill_dir.mkdir(parents=True)

        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("""---
name: Test Skill
description: A test skill for unit tests
---

# Test Skill

This is a test skill.
""")

        return tmp_path / "skill"

    def test_load_skills(self, temp_dir: Path) -> None:
        """Test: loading skills from directory."""
        loader = SkillLoader(str(temp_dir))
        skills = loader.load_all()

        assert len(skills) == 1
        assert "test-skill" in skills
        assert skills["test-skill"]["name"] == "Test Skill"
        assert skills["test-skill"]["description"] == "A test skill for unit tests"

    def test_get_skill(self, temp_dir: Path) -> None:
        """Test: getting a skill by ID."""
        loader = SkillLoader(str(temp_dir))
        loader.load_all()

        skill = loader.get_skill("test-skill")
        assert skill is not None
        assert skill["name"] == "Test Skill"

    def test_get_nonexistent_skill(self, temp_dir: Path) -> None:
        """Test: getting a non-existent skill returns None."""
        loader = SkillLoader(str(temp_dir))
        loader.load_all()

        skill = loader.get_skill("nonexistent")
        assert skill is None


class TestContextBuilder:
    """Test ContextBuilder behavior."""

    @pytest.fixture
    def skill_loader(self, tmp_path: Path) -> SkillLoader:
        """Create a SkillLoader with test skills."""
        skill_dir = tmp_path / "skill" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: Test Skill
description: A test skill
---

Skill content here.
""")

        return SkillLoader(str(tmp_path / "skill"))

    @pytest.fixture
    def profile(self) -> AgentProfile:
        """Create a test profile."""
        return AgentProfile(
            id="test-agent",
            prompt_template="nonexistent.md",
            llm=LLMConfig(provider="test", model="test"),
            tools=["read_resume"],
            skills=["test-skill"],
        )

    @pytest.fixture
    def builder(self, skill_loader: SkillLoader) -> ContextBuilder:
        """Create a ContextBuilder."""
        return ContextBuilder(skill_loader)

    def test_build_messages_basic(
        self, builder: ContextBuilder, profile: AgentProfile
    ) -> None:
        """Test: building messages with no history."""
        events = []
        messages = builder.build_messages(profile, events, "Hello")

        # Should have system + user message
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_build_messages_with_history(
        self, builder: ContextBuilder, profile: AgentProfile
    ) -> None:
        """Test: building messages with conversation history."""
        events = [
            FrontendEvent(type=EventType.USER_TEXT, payload={"text": "Hi"}),
            FrontendEvent(type=EventType.ASSISTANT_TEXT_DONE, payload={"text": "Hello!"}),
            FrontendEvent(type=EventType.USER_TEXT, payload={"text": "How are you?"}),
        ]

        messages = builder.build_messages(profile, events, "Fine, thanks")

        # Should have system + 3 history messages + current user
        assert len(messages) == 5
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hi"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Hello!"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "How are you?"
        assert messages[4]["role"] == "user"
        assert messages[4]["content"] == "Fine, thanks"

    def test_build_messages_with_compaction(
        self, builder: ContextBuilder, profile: AgentProfile
    ) -> None:
        """Test: building messages with compaction event."""
        events = [
            FrontendEvent(
                type=EventType.SESSION_COMPACTED,
                payload={"summary_text": "Previous conversation about React."},
            ),
            FrontendEvent(type=EventType.USER_TEXT, payload={"text": "Continue"}),
        ]

        messages = builder.build_messages(profile, events, "Next topic")

        # Should have system + summary + continue + current
        assert len(messages) == 4
        assert "summary" in messages[1]["content"].lower()


class TestContextCompactor:
    """Test ContextCompactor behavior."""

    def test_estimate_tokens(self) -> None:
        """Test: token estimation."""
        from unittest.mock import MagicMock

        llm = MagicMock()
        compactor = ContextCompactor(llm)

        messages = [
            {"role": "user", "content": "Hello world"},  # 4 + 11 = 15 chars
            {"role": "assistant", "content": "Hi there"},  # 9 + 8 = 17 chars
        ]

        # 32 chars / 4 = 8 tokens (rough estimate)
        tokens = compactor.estimate_tokens(messages)
        assert tokens == 8

    def test_should_compact(self) -> None:
        """Test: should_compact threshold check."""
        from unittest.mock import MagicMock

        llm = MagicMock()
        compactor = ContextCompactor(llm)

        profile = AgentProfile(
            id="test",
            prompt_template="test.md",
            llm=LLMConfig(provider="test", model="test"),
            context=ContextConfig(compact_threshold=100),
        )

        # Short messages - should not compact
        short_messages = [
            {"role": "user", "content": "Hello"},
        ]
        assert compactor.should_compact(profile, short_messages) is False

        # Long messages - should compact
        long_messages = [
            {"role": "user", "content": "A" * 500},  # 500 chars = 125 tokens
        ]
        assert compactor.should_compact(profile, long_messages) is True
