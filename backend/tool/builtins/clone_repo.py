"""clone_repo tool — shallow clone a git repo with limits."""

from __future__ import annotations

import asyncio
import os
import shutil
import stat
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy import select

from storage.db.models import RepoAnalysis
from tool.base import ToolContext, ToolResult, tool

CLONE_TIMEOUT = 120  # seconds
MAX_FILE_COUNT = 10_000


def _rmtree_onexc(func, path, exc):
    """Handle Windows read-only files during rmtree."""
    if isinstance(exc, PermissionError) and os.name == "nt":
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except OSError:
            pass  # File locked by git process, skip
    else:
        raise exc


class CloneRepoArgs(BaseModel):
    """Arguments for clone_repo tool."""

    analysis_id: str = Field(
        default="",
        description="The analysis ID (UUID). Use the analysis_id from the current task context.",
    )
    url: str = Field(
        default="",
        description="The GitHub repository URL to clone (e.g. https://github.com/owner/repo).",
    )


@tool
async def clone_repo(args: CloneRepoArgs, ctx: ToolContext) -> ToolResult:
    """Shallow clone a git repository to storage/repo/<id>/."""
    import traceback
    try:
        return await _clone_repo_impl(args, ctx)
    except Exception as e:
        tb = traceback.format_exc()
        return ToolResult.err(
            code="clone_error",
            message=f"clone_repo failed: {type(e).__name__}: {str(e) or repr(e)}\n{tb}",
            summary=f"Clone error: {type(e).__name__}",
        )


async def _clone_repo_impl(args: CloneRepoArgs, ctx: ToolContext) -> ToolResult:
    url = args.url or ctx.repo_url
    analysis_id = args.analysis_id
    if not analysis_id and ctx.session_id:
        analysis_id = ctx.session_id.removeprefix("analysis-")
    if not url:
        return ToolResult.err(
            code="missing_arg",
            message="url is required",
            summary="Missing repo URL",
        )
    if not analysis_id:
        return ToolResult.err(
            code="missing_arg",
            message="analysis_id is required",
            summary="Missing analysis_id",
        )

    if ctx.db_session is None:
        return ToolResult.err(
            code="no_db_session",
            message="No database session in context",
            summary="No DB session",
        )
    db = ctx.db_session

    # Check git is available
    if not shutil.which("git"):
        return ToolResult.err(
            code="git_not_available",
            message="git is not installed or not in PATH",
            summary="git not available",
        )

    # Resolve clone destination
    dest = Path(ctx.repo_root) / analysis_id

    # Skip clone if already cloned (retry / resume scenario)
    if dest.exists() and dest.is_dir():
        existing_files = sum(1 for _ in dest.rglob("*") if _.is_file())
        if existing_files > 0:
            # Update DB status
            result = await db.execute(
                select(RepoAnalysis).where(RepoAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            if analysis and analysis.status != "done":
                analysis.status = "running"
                await db.commit()

            return ToolResult.ok(
                data={
                    "repo_path": str(dest),
                    "analysis_id": analysis_id,
                    "file_count": existing_files,
                },
                summary=f"Reusing existing clone ({existing_files} files)",
            )

    if dest.exists():
        shutil.rmtree(dest, onexc=_rmtree_onexc)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Update status to running
    result = await db.execute(
        select(RepoAnalysis).where(RepoAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if analysis:
        analysis.status = "running"
        await db.commit()

    # Shallow clone (subprocess.run in executor for Windows compat)
    try:
        loop = asyncio.get_running_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["git", "clone", "--depth", "1", url, str(dest)],
                    capture_output=True,
                    timeout=CLONE_TIMEOUT,
                ),
            ),
            timeout=CLONE_TIMEOUT + 5,
        )
    except (TimeoutError, subprocess.TimeoutExpired):
        if dest.exists():
            shutil.rmtree(dest, onexc=_rmtree_onexc)
        return ToolResult.err(
            code="clone_timeout",
            message=f"Clone timed out after {CLONE_TIMEOUT}s",
            summary="Clone timeout",
        )

    if result.returncode != 0:
        error_msg = result.stderr.decode("utf-8", errors="replace").strip()

        # Clone succeeded but checkout failed — try to recover
        if "Clone succeeded, but checkout failed" in error_msg:
            recover = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ["git", "restore", "--source=HEAD", ":/"],
                        cwd=str(dest),
                        capture_output=True,
                        timeout=30,
                    ),
                ),
                timeout=35,
            )
            if recover.returncode == 0:
                # Recovery succeeded — fall through to file count check
                pass
            else:
                if dest.exists():
                    shutil.rmtree(dest, onexc=_rmtree_onexc)
                return ToolResult.err(
                    code="clone_failed",
                    message=f"Clone succeeded but checkout failed, recovery also failed: {recover.stderr.decode('utf-8', errors='replace').strip()}",
                    summary="Clone checkout failed",
                )
        else:
            if dest.exists():
                shutil.rmtree(dest, onexc=_rmtree_onexc)
            return ToolResult.err(
                code="clone_failed",
                message=f"git clone failed: {error_msg}",
                summary="Clone failed",
            )

    # Check file count
    file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
    if file_count > MAX_FILE_COUNT:
        return ToolResult.err(
            code="repo_too_large",
            message=f"Repository has {file_count} files (max {MAX_FILE_COUNT})",
            summary="Repository too large",
        )

    return ToolResult.ok(
        data={
            "repo_path": str(dest),
            "analysis_id": analysis_id,
            "file_count": file_count,
        },
        summary=f"Cloned {url} ({file_count} files)",
    )
