"""Tests for save_real_question tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from tool.base import ToolContext
from tool.builtins.save_real_question import SaveRealQuestionArgs, save_real_question


@pytest.fixture
def memory_root(tmp_path: Path) -> Path:
    """Temp memory directory."""
    return tmp_path / "memory"


@pytest.fixture
def ctx(memory_root: Path) -> ToolContext:
    """ToolContext with user_id, resume_id, and memory_root."""
    return ToolContext(
        user_id="test-user",
        resume_id="res-1",
        memory_root=str(memory_root),
    )


class TestSaveRealQuestion:
    """Test save_real_question tool."""

    async def test_save_question_basic(self, ctx: ToolContext, memory_root: Path) -> None:
        """Save a basic real question."""
        args = SaveRealQuestionArgs(question="请设计一个限流系统")
        result = await save_real_question(args, ctx)

        assert result.status == "ok"
        assert "Saved" in result.summary

        # Verify file was written
        from storage.memory.store import MemoryStore
        store = MemoryStore(root_dir=str(memory_root))
        content = store.read_real_ques("test-user", "res-1")
        assert "限流系统" in content

    async def test_save_question_with_company(self, ctx: ToolContext, memory_root: Path) -> None:
        """Save a question with company name."""
        args = SaveRealQuestionArgs(
            question="设计一个分布式锁",
            company="字节跳动",
        )
        result = await save_real_question(args, ctx)

        assert result.status == "ok"

        from storage.memory.store import MemoryStore
        store = MemoryStore(root_dir=str(memory_root))
        content = store.read_real_ques("test-user", "res-1")
        assert "字节跳动" in content
        assert "分布式锁" in content

    async def test_save_multiple_questions(self, ctx: ToolContext, memory_root: Path) -> None:
        """Multiple saves append to the same file."""
        await save_real_question(
            SaveRealQuestionArgs(question="问题1", company="字节"),
            ctx,
        )
        await save_real_question(
            SaveRealQuestionArgs(question="问题2", company="腾讯"),
            ctx,
        )

        from storage.memory.store import MemoryStore
        store = MemoryStore(root_dir=str(memory_root))
        content = store.read_real_ques("test-user", "res-1")
        assert "问题1" in content
        assert "问题2" in content
        assert "字节" in content
        assert "腾讯" in content

    async def test_save_missing_context(self) -> None:
        """Save without user_id or resume_id returns error."""
        ctx = ToolContext(user_id="", resume_id="")
        args = SaveRealQuestionArgs(question="test")
        result = await save_real_question(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "missing_context"
