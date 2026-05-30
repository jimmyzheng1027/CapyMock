"""Sandbox path validation for file tools."""

from __future__ import annotations

from pathlib import Path

from tool.base import ToolContext, ToolResult


def validate_sandbox_path(path: str, ctx: ToolContext) -> ToolResult | None:
    """Validate that a path is within the sandbox root.

    Returns None if the path is allowed, or a ToolResult.err if forbidden.
    """
    if not ctx.sandbox_root:
        return None

    sandbox = Path(ctx.sandbox_root).resolve()
    resolved = (sandbox / path).resolve()

    if not resolved.is_relative_to(sandbox):
        return ToolResult.err(
            code="path_forbidden",
            message=f"Path '{path}' is outside the sandbox root",
            summary="Access denied: path outside sandbox",
        )

    return None
