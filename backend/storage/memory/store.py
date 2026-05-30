"""Memory store — layered Markdown file read/write with user_id + resume_id."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Awaitable
from pathlib import Path

DEFAULT_MAX_CHARS = 15_000


class MemoryStore:
    """Read/write layered Markdown memory files.

    Layout:
        <root>/<user_id>/user.md              — user-level (shared across resumes)
        <root>/<user_id>/<resume_id>/CAPY_NOTE.md — resume-level
        <root>/<user_id>/<resume_id>/REAL_QUES.md — resume-level
    """

    def __init__(self, root_dir: str = "storage/memory") -> None:
        self.root = Path(root_dir)

    # --- Read ---

    def read_user(self, user_id: str) -> str:
        path = self._user_path(user_id)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def read_capy_note(self, user_id: str, resume_id: str) -> str:
        path = self._capy_note_path(user_id, resume_id)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def read_real_ques(self, user_id: str, resume_id: str) -> str:
        path = self._real_ques_path(user_id, resume_id)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    # --- Write ---

    def write_user(self, user_id: str, content: str, max_chars: int = DEFAULT_MAX_CHARS) -> None:
        path = self._user_path(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content[:max_chars], encoding="utf-8")

    def write_capy_note(
        self, user_id: str, resume_id: str, content: str, max_chars: int = DEFAULT_MAX_CHARS
    ) -> None:
        path = self._capy_note_path(user_id, resume_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content[:max_chars], encoding="utf-8")

    def write_real_ques(
        self, user_id: str, resume_id: str, content: str, max_chars: int = DEFAULT_MAX_CHARS
    ) -> None:
        path = self._real_ques_path(user_id, resume_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content[:max_chars], encoding="utf-8")

    # --- Merge ---

    async def merge_capy_note(
        self,
        user_id: str,
        resume_id: str,
        old_content: str,
        new_facts: list[str],
        llm_merge_fn: Callable[[str, list[str]], str | Awaitable[str]],
        max_chars: int = DEFAULT_MAX_CHARS,
    ) -> str:
        """Merge old CAPY_NOTE with new facts using the provided merge function.

        The merge function receives (old_content, new_facts) and returns merged text.
        If the merge function is async, it will be awaited.
        """
        result = llm_merge_fn(old_content, new_facts)
        if asyncio.iscoroutine(result):
            result = await result

        merged = result[:max_chars]
        self.write_capy_note(user_id, resume_id, merged, max_chars=max_chars)
        return merged

    # --- Path helpers ---

    def _user_path(self, user_id: str) -> Path:
        return self.root / user_id / "user.md"

    def _capy_note_path(self, user_id: str, resume_id: str) -> Path:
        return self.root / user_id / resume_id / "CAPY_NOTE.md"

    def _real_ques_path(self, user_id: str, resume_id: str) -> Path:
        return self.root / user_id / resume_id / "REAL_QUES.md"
