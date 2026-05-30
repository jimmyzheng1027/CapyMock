"""Tests for memory tools: remember."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tool.base import ToolContext, ToolResult


class TestRemember:
    """Test remember tool."""

    @pytest.fixture
    def ctx(self) -> ToolContext:
        """ToolContext with a mock session."""
        ctx = ToolContext(user_id="test-user")
        ctx.session = MagicMock(spec=[])
        ctx.session.notes = []
        return ctx

    async def test_remember_buffers_to_session(self, ctx: ToolContext) -> None:
        """remember appends fact to session notes, does not write to file."""
        from tool.builtins.remember import remember, RememberArgs

        args = RememberArgs(fact="字节问了限流设计", category="real_question")
        result = await remember(args, ctx)

        assert result.status == "ok"
        assert len(ctx.session.notes) == 1
        assert ctx.session.notes[0]["note"] == "字节问了限流设计"
        assert ctx.session.notes[0]["category"] == "real_question"

    async def test_remember_no_session(self) -> None:
        """remember without session returns error."""
        from tool.builtins.remember import remember, RememberArgs

        ctx = ToolContext(user_id="test-user")
        ctx.session = None

        args = RememberArgs(fact="test")
        result = await remember(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "no_session"

    async def test_remember_multiple_facts(self, ctx: ToolContext) -> None:
        """Multiple remember calls accumulate in session notes."""
        from tool.builtins.remember import remember, RememberArgs

        await remember(RememberArgs(fact="fact1"), ctx)
        await remember(RememberArgs(fact="fact2", category="strength"), ctx)

        assert len(ctx.session.notes) == 2
        assert ctx.session.notes[0]["note"] == "fact1"
        assert ctx.session.notes[1]["note"] == "fact2"
