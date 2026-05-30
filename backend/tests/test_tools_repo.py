"""Tests for GitHub analysis tools: list_directory, read_file, search_code,
save_repo_analysis, clone_repo, query_github_analysis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from storage.db.models import Base, RepoAnalysis
from tool.base import ToolContext, ToolResult


# --- Fixtures ---


@pytest.fixture
async def db() -> AsyncSession:
    """In-memory SQLite database."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def repo_dir(tmp_path: Path) -> Path:
    """Create a sample repo directory structure."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('hello')")
    (root / "src" / "utils.py").write_text("def helper(): pass")
    (root / "tests").mkdir()
    (root / "tests" / "test_main.py").write_text("def test_hello(): pass")
    (root / "README.md").write_text("# My Project")
    (root / "pyproject.toml").write_text("[project]\nname = 'test'")
    # Directories that should be pruned
    (root / ".git").mkdir()
    (root / "node_modules").mkdir()
    (root / "__pycache__").mkdir()
    (root / "dist").mkdir()
    return root


@pytest.fixture
def ctx(repo_dir: Path) -> ToolContext:
    """ToolContext with sandbox set to repo_dir."""
    return ToolContext(user_id="test-user", sandbox_root=str(repo_dir))


# --- list_directory tests (3.1) ---


class TestListDirectory:
    """Test list_directory tool."""

    async def test_list_root(self, ctx: ToolContext, repo_dir: Path) -> None:
        """List root directory: returns files and folders, skips pruned dirs."""
        from tool.builtins.list_directory import list_directory, ListDirectoryArgs

        args = ListDirectoryArgs(path=".")
        result = await list_directory(args, ctx)

        assert result.status == "ok"
        names = [item["name"] for item in result.data["entries"]]
        assert "src" in names
        assert "tests" in names
        assert "README.md" in names
        assert "pyproject.toml" in names
        # Pruned directories should not appear
        assert ".git" not in names
        assert "node_modules" not in names
        assert "__pycache__" not in names
        assert "dist" not in names

    async def test_list_subdirectory(self, ctx: ToolContext) -> None:
        """List a subdirectory."""
        from tool.builtins.list_directory import list_directory, ListDirectoryArgs

        args = ListDirectoryArgs(path="src")
        result = await list_directory(args, ctx)

        assert result.status == "ok"
        names = [item["name"] for item in result.data["entries"]]
        assert "main.py" in names
        assert "utils.py" in names

    async def test_list_sandbox_violation(self, ctx: ToolContext) -> None:
        """Path outside sandbox is rejected."""
        from tool.builtins.list_directory import list_directory, ListDirectoryArgs

        args = ListDirectoryArgs(path="../../etc")
        result = await list_directory(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "path_forbidden"

    async def test_list_returns_directory_tree(self, ctx: ToolContext) -> None:
        """list_directory returns a directoryTree-compatible structure."""
        from tool.builtins.list_directory import list_directory, ListDirectoryArgs

        args = ListDirectoryArgs(path=".", max_depth=2)
        result = await list_directory(args, ctx)

        assert result.status == "ok"
        assert "directoryTree" in result.data
        tree = result.data["directoryTree"]
        assert tree["type"] == "folder"
        assert "children" in tree

    async def test_list_nonexistent_path(self, ctx: ToolContext) -> None:
        """Non-existent path returns error."""
        from tool.builtins.list_directory import list_directory, ListDirectoryArgs

        args = ListDirectoryArgs(path="nonexistent")
        result = await list_directory(args, ctx)

        assert result.status == "err"


# --- read_file tests (3.3) ---


class TestReadFile:
    """Test read_file tool."""

    async def test_read_normal_file(self, ctx: ToolContext) -> None:
        """Read a normal file returns content."""
        from tool.builtins.read_file import read_file, ReadFileArgs

        args = ReadFileArgs(path="README.md")
        result = await read_file(args, ctx)

        assert result.status == "ok"
        assert result.data["content"] == "# My Project"
        assert result.data["path"] == "README.md"

    async def test_read_truncated(self, ctx: ToolContext, repo_dir: Path) -> None:
        """Long file is truncated."""
        from tool.builtins.read_file import read_file, ReadFileArgs

        long_content = "x" * 100_000
        (repo_dir / "huge.py").write_text(long_content)

        args = ReadFileArgs(path="huge.py")
        result = await read_file(args, ctx)

        assert result.status == "ok"
        assert len(result.data["content"]) <= 50_000  # default max
        assert result.data.get("truncated") is True

    async def test_read_sandbox_violation(self, ctx: ToolContext) -> None:
        """Path outside sandbox is rejected."""
        from tool.builtins.read_file import read_file, ReadFileArgs

        args = ReadFileArgs(path="../../etc/passwd")
        result = await read_file(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "path_forbidden"

    async def test_read_nonexistent(self, ctx: ToolContext) -> None:
        """Non-existent file returns error."""
        from tool.builtins.read_file import read_file, ReadFileArgs

        args = ReadFileArgs(path="nope.txt")
        result = await read_file(args, ctx)

        assert result.status == "err"

    async def test_read_empty_path_defaults_to_readme(self, ctx: ToolContext) -> None:
        """Empty path picks README.md when inside a cloned repo."""
        from tool.builtins.read_file import read_file, ReadFileArgs
        from tool.executor import ToolCall, ToolExecutor

        result = await read_file(ReadFileArgs(), ctx)
        assert result.status == "ok"
        assert result.data["path"] == "README.md"
        assert result.data.get("auto_resolved_path") is True

        meta = read_file._tool_meta
        executor = ToolExecutor()
        batch = await executor.run_parallel(
            [ToolCall(tool_call_id="1", tool_name="read_file", args={})],
            lambda _c: ctx,
            {meta.name: meta},
        )
        assert batch[0].status == "ok"
        assert batch[0].data["path"] == "README.md"


# --- search_code tests (3.5) ---


class TestSearchCode:
    """Test search_code tool."""

    async def test_search_hit(self, ctx: ToolContext) -> None:
        """Search finds matching content."""
        from tool.builtins.search_code import search_code, SearchCodeArgs

        args = SearchCodeArgs(pattern="def helper")
        result = await search_code(args, ctx)

        assert result.status == "ok"
        assert result.data["match_count"] > 0
        matches = result.data["matches"]
        assert any("utils.py" in m["path"] for m in matches)

    async def test_search_no_hit(self, ctx: ToolContext) -> None:
        """Search with no matches returns zero count."""
        from tool.builtins.search_code import search_code, SearchCodeArgs

        args = SearchCodeArgs(pattern="nonexistent_function_xyz")
        result = await search_code(args, ctx)

        assert result.status == "ok"
        assert result.data["match_count"] == 0

    async def test_search_sandbox_violation(self, ctx: ToolContext) -> None:
        """Search outside sandbox is rejected."""
        from tool.builtins.search_code import search_code, SearchCodeArgs

        args = SearchCodeArgs(pattern="root", path="../../etc")
        result = await search_code(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "path_forbidden"

    async def test_search_skips_pruned_dirs(self, ctx: ToolContext, repo_dir: Path) -> None:
        """Search skips .git, node_modules, etc."""
        from tool.builtins.search_code import search_code, SearchCodeArgs

        # Put a match in .git that should be skipped
        (repo_dir / ".git" / "config").write_text("secret_match_123")

        args = SearchCodeArgs(pattern="secret_match_123")
        result = await search_code(args, ctx)

        assert result.status == "ok"
        assert result.data["match_count"] == 0


# --- save_repo_analysis tests (3.7) ---


class TestSaveRepoAnalysis:
    """Test save_repo_analysis tool."""

    async def test_save_sets_result_json(self, db: AsyncSession) -> None:
        """save_repo_analysis writes result_json and sets status=done."""
        from tool.builtins.save_repo_analysis import save_repo_analysis, SaveRepoAnalysisArgs

        # Create the row first
        analysis = RepoAnalysis(
            id="ra-1", url="https://github.com/o/r", owner="o", repo="r", status="running"
        )
        db.add(analysis)
        await db.commit()

        ctx = ToolContext(user_id="test-user")
        ctx.db_session = db

        result_data = {"overview": "test analysis", "highlights": []}
        args = SaveRepoAnalysisArgs(analysis_id="ra-1", result_json=json.dumps(result_data))
        result = await save_repo_analysis(args, ctx)

        assert result.status == "ok"

        # Verify in DB
        row = await db.execute(select(RepoAnalysis).where(RepoAnalysis.id == "ra-1"))
        updated = row.scalar_one()
        assert updated.status == "done"
        assert json.loads(updated.result_json) == result_data
        assert updated.analyzed_at is not None

    async def test_save_nonexistent(self, db: AsyncSession) -> None:
        """Saving to non-existent analysis returns error."""
        from tool.builtins.save_repo_analysis import save_repo_analysis, SaveRepoAnalysisArgs

        ctx = ToolContext(user_id="test-user")
        ctx.db_session = db

        args = SaveRepoAnalysisArgs(analysis_id="nope", result_json="{}")
        result = await save_repo_analysis(args, ctx)

        assert result.status == "err"


# --- query_github_analysis tests (3.11) ---


class TestQueryGithubAnalysis:
    """Test query_github_analysis reads from SQL."""

    async def test_query_hit(self, db: AsyncSession) -> None:
        """Query returns cached result from SQL."""
        from tool.builtins.query_github_analysis import (
            query_github_analysis,
            QueryGithubAnalysisArgs,
        )

        result_data = {"overview": "cached"}
        analysis = RepoAnalysis(
            id="ra-2",
            url="https://github.com/o/r",
            owner="o",
            repo="r",
            status="done",
            result_json=json.dumps(result_data),
        )
        db.add(analysis)
        await db.commit()

        ctx = ToolContext(user_id="test-user")
        ctx.db_session = db

        args = QueryGithubAnalysisArgs(repo_url="https://github.com/o/r")
        result = await query_github_analysis(args, ctx)

        assert result.status == "ok"
        assert result.data["analysis"] == result_data

    async def test_query_miss(self, db: AsyncSession) -> None:
        """Query returns not_found for missing URL."""
        from tool.builtins.query_github_analysis import (
            query_github_analysis,
            QueryGithubAnalysisArgs,
        )

        ctx = ToolContext(user_id="test-user")
        ctx.db_session = db

        args = QueryGithubAnalysisArgs(repo_url="https://github.com/o/missing")
        result = await query_github_analysis(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "not_found"

    async def test_query_pending_returns_not_ready(self, db: AsyncSession) -> None:
        """Query for pending analysis returns not_ready error."""
        from tool.builtins.query_github_analysis import (
            query_github_analysis,
            QueryGithubAnalysisArgs,
        )

        analysis = RepoAnalysis(
            id="ra-3",
            url="https://github.com/o/r",
            owner="o",
            repo="r",
            status="pending",
        )
        db.add(analysis)
        await db.commit()

        ctx = ToolContext(user_id="test-user")
        ctx.db_session = db

        args = QueryGithubAnalysisArgs(repo_url="https://github.com/o/r")
        result = await query_github_analysis(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "not_ready"


# --- clone_repo tests (3.9) ---


@pytest.fixture
def local_git_repo(tmp_path: Path) -> Path:
    """Create a small local git repo for clone testing."""
    repo = tmp_path / "source-repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True, capture_output=True)
    (repo / "main.py").write_text("print('hello')")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(repo),
        check=True,
        capture_output=True,
        env={"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t.com",
             "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t.com"},
    )
    return repo


class TestCloneRepo:
    """Test clone_repo tool."""

    async def test_clone_local_repo(
        self, local_git_repo: Path, tmp_path: Path, db: AsyncSession
    ) -> None:
        """Clone a local git repo to storage/repo/<id>/."""
        from tool.builtins.clone_repo import clone_repo, CloneRepoArgs

        # Create the analysis row
        analysis = RepoAnalysis(
            id="ra-clone-1",
            url=str(local_git_repo),
            owner="test",
            repo="source-repo",
            status="pending",
        )
        db.add(analysis)
        await db.commit()

        ctx = ToolContext(user_id="test-user")
        ctx.db_session = db
        ctx.repo_root = str(tmp_path / "repos")

        args = CloneRepoArgs(analysis_id="ra-clone-1", url=str(local_git_repo))
        result = await clone_repo(args, ctx)

        assert result.status == "ok"
        assert "repo_path" in result.data
        repo_path = Path(result.data["repo_path"])
        assert repo_path.exists()
        assert (repo_path / "main.py").exists()

    async def test_clone_invalid_url(self, db: AsyncSession, tmp_path: Path) -> None:
        """Clone with invalid URL returns error."""
        from tool.builtins.clone_repo import clone_repo, CloneRepoArgs

        analysis = RepoAnalysis(
            id="ra-clone-2",
            url="https://github.com/nonexistent/repo-xyz",
            owner="nonexistent",
            repo="repo-xyz",
            status="pending",
        )
        db.add(analysis)
        await db.commit()

        ctx = ToolContext(user_id="test-user")
        ctx.db_session = db
        ctx.repo_root = str(tmp_path / "repos")

        args = CloneRepoArgs(analysis_id="ra-clone-2", url="https://github.com/nonexistent/repo-xyz")
        result = await clone_repo(args, ctx)

        assert result.status == "err"
        assert result.error["code"] == "clone_failed"
