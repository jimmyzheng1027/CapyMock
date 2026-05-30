"""read_file tool — read a file's content with sandbox and truncation."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from tool.base import ToolContext, ToolResult, tool
from tool.sandbox import validate_sandbox_path

DEFAULT_MAX_CHARS = 50_000

# When the model omits path, try common project metadata files (Phase 2b of repo-analyzer).
DEFAULT_READ_CANDIDATES = (
    "README.md",
    "readme.md",
    "README.rst",
    "README",
    "package.json",
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
)


class ReadFileArgs(BaseModel):
    """Arguments for read_file tool."""

    path: str = Field(
        default="",
        description=(
            "(REQUIRED) File path relative to the cloned repository root. "
            'Examples: "README.md", "src/main.py". '
            'Example call: {"path": "README.md"}'
        ),
    )
    max_chars: int = Field(
        default=DEFAULT_MAX_CHARS,
        description="Maximum characters to read. Default 50000.",
    )


def _repo_base(ctx: ToolContext) -> Path:
    if ctx.sandbox_root:
        return Path(ctx.sandbox_root)
    if ctx.current_repo_path:
        return Path(ctx.current_repo_path)
    return Path(".")


def _resolve_read_path(args: ReadFileArgs, ctx: ToolContext) -> tuple[str | None, bool]:
    """Resolve path; auto-pick a default metadata file when omitted."""
    if args.path.strip():
        return args.path.strip(), False

    base = _repo_base(ctx)
    if not ctx.sandbox_root and not ctx.current_repo_path:
        return None, False

    for candidate in DEFAULT_READ_CANDIDATES:
        target = (base / candidate).resolve()
        if target.is_file():
            return candidate, True

    return None, False


@tool
async def read_file(args: ReadFileArgs, ctx: ToolContext) -> ToolResult:
    """Read a file's content from the cloned repository. Long files are truncated.

    Pass path relative to the repo root (e.g. read_file with path \"README.md\").
    """
    path, auto_resolved = _resolve_read_path(args, ctx)
    if not path:
        return ToolResult.err(
            code="missing_arg",
            message=(
                "path is required. Pass a repo-relative file path, e.g. "
                '{"path": "README.md"} or {"path": "src/main.py"}. '
                f"When omitted, tried defaults: {', '.join(DEFAULT_READ_CANDIDATES[:6])}..."
            ),
            summary="Missing path",
        )

    err = validate_sandbox_path(path, ctx)
    if err:
        return err

    base = _repo_base(ctx)
    target = (base / path).resolve()

    if not target.exists():
        return ToolResult.err(
            code="not_found",
            message=f"File not found: {path}",
            summary=f"Not found: {path}",
        )

    if not target.is_file():
        return ToolResult.err(
            code="not_a_file",
            message=f"Not a file: {path}",
            summary=f"Not a file: {path}",
        )

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return ToolResult.err(
            code="read_error",
            message=f"Failed to read {path}: {e}",
            summary=f"Read error: {path}",
        )

    truncated = False
    if len(content) > args.max_chars:
        content = content[: args.max_chars]
        truncated = True

    data: dict = {"content": content, "path": path}
    if truncated:
        data["truncated"] = True
    if auto_resolved:
        data["auto_resolved_path"] = True

    summary = f"Read {path} ({len(content)} chars)"
    if auto_resolved:
        summary += " [path inferred from defaults]"

    return ToolResult.ok(data=data, summary=summary)
