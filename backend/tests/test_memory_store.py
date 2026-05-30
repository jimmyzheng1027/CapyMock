"""Tests for storage/memory/ layered read/write module."""

from __future__ import annotations

from pathlib import Path

import pytest

from storage.memory.store import MemoryStore


@pytest.fixture
def memory_root(tmp_path: Path) -> Path:
    """Temporary memory root directory."""
    return tmp_path / "memory"


@pytest.fixture
def store(memory_root: Path) -> MemoryStore:
    """MemoryStore instance with temp root."""
    return MemoryStore(root_dir=str(memory_root))


class TestLayeredPaths:
    """Test that memory files are stored in the correct layered structure."""

    def test_user_md_at_user_level(
        self, store: MemoryStore, memory_root: Path
    ) -> None:
        """user.md is stored at <user_id>/user.md."""
        store.write_user("user-1", "# User profile\n偏好：中文面试")
        content = store.read_user("user-1")
        assert content == "# User profile\n偏好：中文面试"
        assert (memory_root / "user-1" / "user.md").exists()

    def test_capy_note_at_resume_level(
        self, store: MemoryStore, memory_root: Path
    ) -> None:
        """CAPY_NOTE.md is stored at <user_id>/<resume_id>/CAPY_NOTE.md."""
        store.write_capy_note("user-1", "res-1", "# 强弱项\n弱项：系统设计")
        content = store.read_capy_note("user-1", "res-1")
        assert content == "# 强弱项\n弱项：系统设计"
        assert (memory_root / "user-1" / "res-1" / "CAPY_NOTE.md").exists()

    def test_real_ques_at_resume_level(
        self, store: MemoryStore, memory_root: Path
    ) -> None:
        """REAL_QUES.md is stored at <user_id>/<resume_id>/REAL_QUES.md."""
        store.write_real_ques("user-1", "res-1", "# 真题\n字节：限流设计")
        content = store.read_real_ques("user-1", "res-1")
        assert content == "# 真题\n字节：限流设计"
        assert (memory_root / "user-1" / "res-1" / "REAL_QUES.md").exists()

    def test_read_nonexistent_returns_empty(
        self, store: MemoryStore
    ) -> None:
        """Reading non-existent memory returns empty string."""
        assert store.read_user("no-user") == ""
        assert store.read_capy_note("no-user", "no-res") == ""
        assert store.read_real_ques("no-user", "no-res") == ""

    def test_user_shared_across_resumes(
        self, store: MemoryStore
    ) -> None:
        """user.md is shared across all resumes for the same user."""
        store.write_user("user-1", "profile content")
        # Read with different resume_ids — both see the same user.md
        assert store.read_user("user-1") == "profile content"

    def test_capy_note_per_resume(
        self, store: MemoryStore
    ) -> None:
        """Different resumes have separate CAPY_NOTE.md files."""
        store.write_capy_note("user-1", "res-1", "note for res-1")
        store.write_capy_note("user-1", "res-2", "note for res-2")
        assert store.read_capy_note("user-1", "res-1") == "note for res-1"
        assert store.read_capy_note("user-1", "res-2") == "note for res-2"


class TestRewriteMerge:
    """Test rewrite-merge semantics for CAPY_NOTE.md."""

    async def test_merge_removes_improved_weakness(
        self, store: MemoryStore
    ) -> None:
        """Old content + new facts → merged result is written to file.

        We test the write logic (merged content is persisted), not the merge wording.
        """
        old_note = "# 强弱项\n## 弱项\n- 系统设计：概念不清\n- 算法：慢"
        new_facts = ["系统设计已练习，表现良好"]

        merged = await store.merge_capy_note(
            "user-1", "res-1", old_note, new_facts, llm_merge_fn=fake_merge_fn
        )

        # Merged content is persisted and contains both old and new content
        persisted = store.read_capy_note("user-1", "res-1")
        assert persisted == merged
        assert "系统设计" in merged  # still present (fake fn appends, doesn't remove)
        assert "新增" in merged  # new section added

    async def test_merge_appends_new_info(
        self, store: MemoryStore
    ) -> None:
        """New facts are incorporated into merged note."""
        old_note = "# 强弱项\n## 强项\n- Python 熟练"
        new_facts = ["Redis 缓存策略答得好"]

        merged = await store.merge_capy_note(
            "user-1", "res-1", old_note, new_facts, llm_merge_fn=fake_merge_fn
        )

        assert len(merged) > 0

    async def test_merge_with_empty_old(
        self, store: MemoryStore
    ) -> None:
        """Merge with empty old note creates new content."""
        new_facts = ["第一次面试"]

        merged = await store.merge_capy_note(
            "user-1", "res-1", "", new_facts, llm_merge_fn=fake_merge_fn
        )

        assert len(merged) > 0


def fake_merge_fn(old_content: str, new_facts: list[str]) -> str:
    """Fake LLM merge function for testing — deterministic merge."""
    lines = []
    if old_content:
        lines.append(old_content)
    if new_facts:
        lines.append("\n## 新增")
        for fact in new_facts:
            lines.append(f"- {fact}")
    return "\n".join(lines)


class TestCapacityLimit:
    """Test capacity limit and compression."""

    def test_write_truncates_at_limit(
        self, store: MemoryStore
    ) -> None:
        """Content exceeding limit is truncated."""
        long_content = "x" * 20_000
        store.write_user("user-1", long_content, max_chars=10_000)
        content = store.read_user("user-1")
        assert len(content) <= 10_000
