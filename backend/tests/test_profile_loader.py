"""Tests for ProfileLoader: loading, validation, and error handling."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agent.profile_loader import ProfileLoader, ProfileValidationError


class TestProfileLoader:
    """Test ProfileLoader behavior."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for test profiles."""
        return tmp_path / "agents"

    def test_load_valid_profile(self, temp_dir: Path) -> None:
        """Test: loading a valid profile."""
        temp_dir.mkdir()

        profile_data = {
            "id": "test-agent",
            "prompt_template": "test.md",
            "llm": {
                "provider": "dashscope",
                "model": "qwen-max",
                "temperature": 0.7,
            },
            "tools": ["read_resume", "take_note"],
            "skills": ["skill-1"],
        }

        with open(temp_dir / "test.yaml", "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader(str(temp_dir))
        profiles = loader.load_all()

        assert len(profiles) == 1
        assert "test-agent" in profiles
        assert profiles["test-agent"].id == "test-agent"
        assert profiles["test-agent"].llm.provider == "dashscope"
        assert profiles["test-agent"].tools == ["read_resume", "take_note"]

    def test_load_multiple_profiles(self, temp_dir: Path) -> None:
        """Test: loading multiple profiles."""
        temp_dir.mkdir()

        for i in range(3):
            profile_data = {
                "id": f"agent-{i}",
                "prompt_template": f"test{i}.md",
                "llm": {"provider": "dashscope", "model": "qwen-max"},
            }
            with open(temp_dir / f"agent{i}.yaml", "w") as f:
                yaml.dump(profile_data, f)

        loader = ProfileLoader(str(temp_dir))
        profiles = loader.load_all()

        assert len(profiles) == 3
        for i in range(3):
            assert f"agent-{i}" in profiles

    def test_missing_required_field(self, temp_dir: Path) -> None:
        """Test: fail-fast on missing required field."""
        temp_dir.mkdir()

        # Missing 'llm' field
        profile_data = {
            "id": "bad-agent",
            "prompt_template": "test.md",
        }

        with open(temp_dir / "bad.yaml", "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader(str(temp_dir))

        with pytest.raises(ProfileValidationError) as exc_info:
            loader.load_all()

        assert "bad.yaml" in exc_info.value.file_path

    def test_invalid_yaml_format(self, temp_dir: Path) -> None:
        """Test: fail-fast on invalid YAML."""
        temp_dir.mkdir()

        with open(temp_dir / "bad.yaml", "w") as f:
            f.write("invalid: yaml: content: [")

        loader = ProfileLoader(str(temp_dir))

        with pytest.raises(ProfileValidationError):
            loader.load_all()

    def test_nonexistent_directory(self) -> None:
        """Test: loading from non-existent directory returns empty."""
        loader = ProfileLoader("/nonexistent/path")
        profiles = loader.load_all()

        assert profiles == {}

    def test_get_existing_profile(self, temp_dir: Path) -> None:
        """Test: getting an existing profile by ID."""
        temp_dir.mkdir()

        profile_data = {
            "id": "test-agent",
            "prompt_template": "test.md",
            "llm": {"provider": "dashscope", "model": "qwen-max"},
        }

        with open(temp_dir / "test.yaml", "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader(str(temp_dir))
        loader.load_all()

        profile = loader.get("test-agent")
        assert profile is not None
        assert profile.id == "test-agent"

    def test_get_nonexistent_profile(self, temp_dir: Path) -> None:
        """Test: getting a non-existent profile returns None."""
        temp_dir.mkdir()

        loader = ProfileLoader(str(temp_dir))
        loader.load_all()

        profile = loader.get("nonexistent")
        assert profile is None

    def test_all_profiles(self, temp_dir: Path) -> None:
        """Test: getting all profiles."""
        temp_dir.mkdir()

        for i in range(3):
            profile_data = {
                "id": f"agent-{i}",
                "prompt_template": f"test{i}.md",
                "llm": {"provider": "dashscope", "model": "qwen-max"},
            }
            with open(temp_dir / f"agent{i}.yaml", "w") as f:
                yaml.dump(profile_data, f)

        loader = ProfileLoader(str(temp_dir))
        loader.load_all()

        all_profiles = loader.all()
        assert len(all_profiles) == 3

    def test_default_values(self, temp_dir: Path) -> None:
        """Test: default values are applied correctly."""
        temp_dir.mkdir()

        profile_data = {
            "id": "test-agent",
            "prompt_template": "test.md",
            "llm": {"provider": "dashscope", "model": "qwen-max"},
        }

        with open(temp_dir / "test.yaml", "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader(str(temp_dir))
        profiles = loader.load_all()

        profile = profiles["test-agent"]
        assert profile.tools == []
        assert profile.skills == []
        assert profile.context.max_history_tokens == 8000
        assert profile.context.compact_threshold == 6000
        assert profile.policy.max_steps == 10
        assert profile.policy.parallel_tools == 3
