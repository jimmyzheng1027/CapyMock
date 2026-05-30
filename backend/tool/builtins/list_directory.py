"""list_directory tool — list files and subdirectories with pruning."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from tool.base import ToolContext, ToolResult, tool
from tool.sandbox import validate_sandbox_path

# Directories to skip during scanning
PRUNED_DIRS = {".git", "node_modules", "dist", "build", "vendor", "__pycache__", ".venv"}


class ListDirectoryArgs(BaseModel):
    """Arguments for list_directory tool."""

    path: str = Field(
        default=".",
        description=(
            "Path relative to the cloned repository root. "
            "After clone_repo succeeds, use '.' for the whole tree or a subfolder like 'src'. "
            "Do NOT use storage/repo/<id> prefixes."
        ),
    )
    max_depth: int = Field(
        default=5,
        description="Maximum depth for recursive directory tree. Use 2-3 for large repos (>5000 files).",
    )


def _build_tree(root: Path, current: Path, depth: int, max_depth: int) -> dict:
    """Recursively build a directory tree dict."""
    if depth > max_depth:
        return {"name": current.name, "type": "folder", "children": []}

    children = []
    try:
        entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return {"name": current.name, "type": "folder", "children": []}

    for entry in entries:
        if entry.name in PRUNED_DIRS:
            continue
        if entry.is_dir():
            children.append(_build_tree(root, entry, depth + 1, max_depth))
        else:
            ext = entry.suffix.lstrip(".")
            children.append({"name": entry.name, "type": "file", "language": ext or "text"})

    return {"name": current.name, "type": "folder", "children": children}


@tool
async def list_directory(args: ListDirectoryArgs, ctx: ToolContext) -> ToolResult:
    """List files and subdirectories at a path. Skips .git, node_modules, dist, etc."""
    err = validate_sandbox_path(args.path, ctx)
    if err:
        return err

    # Resolve base: sandbox_root > current_repo_path > CWD
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
            message=f"Directory not found: {args.path}",
            summary=f"Not found: {args.path}",
        )

    if not target.is_dir():
        return ToolResult.err(
            code="not_a_directory",
            message=f"Not a directory: {args.path}",
            summary=f"Not a directory: {args.path}",
        )

    entries = []
    try:
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name in PRUNED_DIRS:
                continue
            entries.append({
                "name": item.name,
                "type": "folder" if item.is_dir() else "file",
            })
    except PermissionError:
        return ToolResult.err(
            code="permission_denied",
            message=f"Permission denied: {args.path}",
            summary=f"Permission denied: {args.path}",
        )

    tree = _build_tree(base, target, 0, args.max_depth)
    if args.path == ".":
        tree["name"] = base.name

    return ToolResult.ok(
        data={
            "entries": entries,
            "directoryTree": tree,
            "path": args.path,
        },
        summary=f"Listed {len(entries)} entries in {args.path}",
    )
