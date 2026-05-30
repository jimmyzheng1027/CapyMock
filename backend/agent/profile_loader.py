from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from agent.profile import AgentProfile


class ProfileValidationError(Exception):
    """Raised when a profile YAML file is invalid."""

    def __init__(self, file_path: str, errors: list) -> None:
        self.file_path = file_path
        self.errors = errors
        super().__init__(f"Profile validation failed for {file_path}: {errors}")


class ProfileLoader:
    """Loads and validates agent profiles from YAML files."""

    def __init__(self, profiles_dir: str = "config/agents") -> None:
        self.profiles_dir = Path(profiles_dir)
        self._profiles: dict[str, AgentProfile] = {}

    def load_all(self) -> dict[str, AgentProfile]:
        """Load all profile YAML files from the profiles directory.

        Raises ProfileValidationError if any file is invalid.
        """
        self._profiles = {}

        if not self.profiles_dir.exists():
            return self._profiles

        for yaml_file in self.profiles_dir.glob("*.yaml"):
            profile = self._load_one(yaml_file)
            self._profiles[profile.id] = profile

        return self._profiles

    def _load_one(self, file_path: Path) -> AgentProfile:
        """Load and validate a single profile YAML file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ProfileValidationError(str(file_path), [f"YAML parse error: {e}"])

        if not isinstance(data, dict):
            raise ProfileValidationError(str(file_path), ["YAML root must be a mapping"])

        try:
            return AgentProfile(**data)
        except ValidationError as e:
            raise ProfileValidationError(str(file_path), e.errors())

    def get(self, profile_id: str) -> AgentProfile | None:
        """Get a profile by ID."""
        return self._profiles.get(profile_id)

    def all(self) -> list[AgentProfile]:
        """Get all loaded profiles."""
        return list(self._profiles.values())
