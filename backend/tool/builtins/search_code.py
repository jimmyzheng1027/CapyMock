"""search_code tool — search for a pattern in files (pure Python, zero deps)."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from tool.base import ToolContext, ToolResult, tool
from tool.sandbox import validate_sandbox_path

# Directories to skip during search
PRUNED_DIRS = {".git", "node_modules", "dist", "build", "vendor", "__pycache__", ".venv"}

# File extensions to skip (binary / generated)
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo", ".class", ".o",
    ".lock",
}

MAX_MATCHES = 50
MAX_FILE_SIZE = 500_000  # 500KB


class SearchCodeArgs(BaseModel):
    """Arguments for search_code tool."""

    pattern: str = Field(
        description="(REQUIRED) Regex pattern to search for in source files. You MUST provide this parameter.",
    )
    path: str = Field(
        default=".",
        description=(
            "Directory or file path relative to the cloned repository root. "
            "Use '.' for repo-wide search or a subfolder like 'src'."
        ),
    )
    glob: str = Field(
        default="",
        description="Glob filter for file types (e.g. '*.py', '*.ts'). Empty means all files.",
    )


def _should_skip(path: Path) -> bool:
    """Check if a file should be skipped."""
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return True
    except OSError:
        return True
    return False


def _search_file(file_path: Path, pattern: re.Pattern[str]) -> list[dict]:
    """Search a single file for pattern matches."""
    matches = []
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return matches

    for i, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            matches.append({
                "path": str(file_path),
                "line": i,
                "text": line.rstrip(),
            })
    return matches


@tool
async def search_code(args: SearchCodeArgs, ctx: ToolContext) -> ToolResult:
    """Search for a pattern in source files. Skips binary/generated files."""
    err = validate_sandbox_path(args.path, ctx)
    if err:
        return err

    if ctx.sandbox_root:
        base = Path(ctx.sandbox_root)
    elif ctx.current_repo_path:
        base = Path(ctx.current_repo_path)
    else:
        base = Path(".")
    target = (base / args.path).resolve()

    if not target.exists():
        return ToolResult.err(
            code="not_found",
            message=f"Path not found: {args.path}",
            summary=f"Not found: {args.path}",
        )

    try:
        pattern = re.compile(args.pattern)
    except re.error as e:
        return ToolResult.err(
            code="invalid_pattern",
            message=f"Invalid regex pattern: {e}",
            summary="Invalid regex",
        )

    all_matches: list[dict] = []

    if target.is_file():
        all_matches.extend(_search_file(target, pattern))
    else:
        for file_path in target.rglob("*"):
            if not file_path.is_file():
                continue
            # Skip pruned directories
            parts = file_path.relative_to(base).parts
            if any(p in PRUNED_DIRS for p in parts):
                continue
            if _should_skip(file_path):
                continue
            all_matches.extend(_search_file(file_path, pattern))
            if len(all_matches) >= MAX_MATCHES:
                break

    return ToolResult.ok(
        data={
            "matches": all_matches[:MAX_MATCHES],
            "match_count": len(all_matches),
            "pattern": args.pattern,
        },
        summary=f"Found {len(all_matches)} matches for '{args.pattern}'",
    )
