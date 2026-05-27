from __future__ import annotations

from pathlib import Path

import yaml


class SkillLoader:
    """Loads and parses skill definitions from SKILL.md files."""

    def __init__(self, skills_dir: str = "backend/data/skill") -> None:
        self.skills_dir = Path(skills_dir)
        self._skills: dict[str, dict] = {}

    def load_all(self) -> dict[str, dict]:
        """Load all skills from the skills directory."""
        self._skills = {}

        if not self.skills_dir.exists():
            return self._skills

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    skill = self._parse_skill(skill_dir.name, skill_md)
                    if skill:
                        self._skills[skill_dir.name] = skill

        return self._skills

    def _parse_skill(self, skill_id: str, path: Path) -> dict | None:
        """Parse a SKILL.md file with YAML frontmatter."""
        try:
            content = path.read_text(encoding="utf-8")

            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()

                    return {
                        "id": skill_id,
                        "name": frontmatter.get("name", skill_id),
                        "description": frontmatter.get("description", ""),
                        "content": body,
                        **{k: v for k, v in frontmatter.items() if k not in ("name", "description")},
                    }

            # No frontmatter, return as-is
            return {
                "id": skill_id,
                "name": skill_id,
                "description": "",
                "content": content,
            }

        except Exception:
            return None

    def get_skill(self, skill_id: str) -> dict | None:
        """Get a skill by ID."""
        return self._skills.get(skill_id)

    def all(self) -> list[dict]:
        """Get all loaded skills."""
        return list(self._skills.values())
