"""Tests for sandbox path validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from tool.base import ToolContext


class TestSandboxValidation:
    """Test sandbox_root path constraint enforcement."""

    @pytest.fixture
    def sandbox_root(self, tmp_path: Path) -> Path:
        """Create a sandbox root directory."""
        return tmp_path / "repo"

    @pytest.fixture
    def ctx(self, sandbox_root: Path) -> ToolContext:
        """Create a ToolContext with sandbox_root set."""
        ctx = ToolContext(user_id="test-user")
        ctx.sandbox_root = str(sandbox_root)
        return ctx

    def test_sandbox_root_field_exists(self, ctx: ToolContext) -> None:
        """ToolContext has sandbox_root attribute."""
        assert hasattr(ctx, "sandbox_root")
        assert ctx.sandbox_root is not None

    def test_path_within_sandbox(self, sandbox_root: Path, ctx: ToolContext) -> None:
        """Path inside sandbox is allowed."""
        from tool.sandbox import validate_sandbox_path

        sandbox_root.mkdir(parents=True, exist_ok=True)
        (sandbox_root / "src").mkdir()

        result = validate_sandbox_path("src/main.py", ctx)
        assert result is None  # None means allowed

    def test_path_with_dot_traversal_blocked(self, sandbox_root: Path, ctx: ToolContext) -> None:
        """Path with .. traversal is rejected."""
        from tool.sandbox import validate_sandbox_path

        sandbox_root.mkdir(parents=True, exist_ok=True)

        result = validate_sandbox_path("../../etc/passwd", ctx)
        assert result is not None
        assert result.status == "err"
        assert result.error["code"] == "path_forbidden"

    def test_absolute_path_outside_sandbox_blocked(
        self, sandbox_root: Path, ctx: ToolContext
    ) -> None:
        """Absolute path outside sandbox is rejected."""
        from tool.sandbox import validate_sandbox_path

        sandbox_root.mkdir(parents=True, exist_ok=True)

        result = validate_sandbox_path("/etc/passwd", ctx)
        assert result is not None
        assert result.status == "err"
        assert result.error["code"] == "path_forbidden"

    def test_no_sandbox_allows_any_path(self) -> None:
        """When sandbox_root is not set, any path is allowed."""
        from tool.sandbox import validate_sandbox_path

        ctx = ToolContext(user_id="test-user")
        # sandbox_root not set

        result = validate_sandbox_path("/any/path", ctx)
        assert result is None

    def test_root_path_itself(self, sandbox_root: Path, ctx: ToolContext) -> None:
        """The sandbox root itself is allowed."""
        from tool.sandbox import validate_sandbox_path

        sandbox_root.mkdir(parents=True, exist_ok=True)

        result = validate_sandbox_path(".", ctx)
        assert result is None

    def test_subdirectory_traversal_still_in_sandbox(
        self, sandbox_root: Path, ctx: ToolContext
    ) -> None:
        """Path with .. that stays within sandbox is allowed."""
        from tool.sandbox import validate_sandbox_path

        sandbox_root.mkdir(parents=True, exist_ok=True)
        (sandbox_root / "src").mkdir()

        result = validate_sandbox_path("src/../src/main.py", ctx)
        assert result is None
