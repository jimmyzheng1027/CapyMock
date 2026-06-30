from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass
class ToolResult:
    """Result of a tool execution."""

    status: str  # "ok" or "err"
    data: dict | None = None
    error: dict | None = None
    summary: str = ""

    @classmethod
    def ok(cls, data: dict | None = None, summary: str = "") -> ToolResult:
        """Create a success result."""
        return cls(status="ok", data=data, summary=summary)

    @classmethod
    def err(cls, code: str, message: str, summary: str = "") -> ToolResult:
        """Create an error result."""
        return cls(status="err", error={"code": code, "message": message}, summary=summary)


class ToolError(Exception):
    """Base exception for tool errors."""
    pass


@dataclass
class ToolContext:
    """Context injected into tool execution."""

    session: Any = None
    session_id: str = ""
    user_id: str = ""
    profile: Any = None
    cancel_token: Any = None
    permissions: dict = field(default_factory=dict)
    sandbox_root: str = ""  # root directory for file tool sandboxing
    current_repo_path: str = ""  # path to the currently cloned repo (set after clone_repo)
    db_session: Any = None  # SQLAlchemy AsyncSession
    repo_root: str = "storage/repo"  # root directory for cloned repos
    repo_url: str = ""  # current repo URL (for analysis context)
    resume_id: str = ""  # resume ID for memory file operations
    memory_root: str = "storage/memory"  # root directory for memory files


@dataclass
class ToolMeta:
    """Metadata for a registered tool."""

    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable
    timeout: float | None = None  # per-tool timeout in seconds; None = use executor default
    max_retries: int = 1  # max execution attempts (1 = no retry)
    read_only: bool = False  # True for read-only tools (can run in parallel)


def tool(
    fn: Callable | None = None,
    *,
    timeout: float | None = None,
    max_retries: int = 1,
    read_only: bool = False,
) -> Callable:
    """Decorator to mark a function as a tool.

    The function must have the signature:
        async def fn(args: ArgsModel, ctx: ToolContext) -> ToolResult

    The ArgsModel type hint is used to derive the JSON schema.
    The function docstring is used as the tool description.

    Args:
        timeout: Per-tool timeout in seconds. None = use executor default.
        max_retries: Max execution attempts (1 = no retry). Retries on timeout/network errors only.
        read_only: True for read-only tools (can run in parallel with other read-only tools).

    Usage:
        @tool
        async def my_tool(args, ctx): ...

        @tool(timeout=5.0, max_retries=2, read_only=True)
        async def my_tool(args, ctx): ...
    """

    def _register(tool_fn: Callable) -> Callable:
        import inspect
        import typing

        sig = inspect.signature(tool_fn)
        params = list(sig.parameters.values())

        # Get the args model type from the first parameter
        if len(params) < 2:
            raise ToolError(
                f"Tool function {tool_fn.__name__} must have at least 2 parameters (args, ctx)"
            )

        args_param = params[0]
        if args_param.annotation is inspect.Parameter.empty:
            raise ToolError(
                f"Tool function {tool_fn.__name__} must have type annotation for args parameter"
            )

        # Handle string annotations (from __future__ import annotations)
        args_model = args_param.annotation
        if isinstance(args_model, str):
            # Resolve string annotation to actual type
            hints = typing.get_type_hints(tool_fn)
            args_model = hints.get(args_param.name, args_param.annotation)

        if not (isinstance(args_model, type) and issubclass(args_model, BaseModel)):
            raise ToolError(
                f"Tool function {tool_fn.__name__} args parameter must be a Pydantic BaseModel"
            )

        # Get description from docstring
        description = tool_fn.__doc__ or tool_fn.__name__

        # Attach metadata to the function
        tool_fn._tool_meta = ToolMeta(
            name=tool_fn.__name__,
            description=description,
            args_model=args_model,
            fn=tool_fn,
            timeout=timeout,
            max_retries=max_retries,
            read_only=read_only,
        )

        @functools.wraps(tool_fn)
        async def wrapper(args: BaseModel, ctx: ToolContext) -> ToolResult:
            return await tool_fn(args, ctx)

        wrapper._tool_meta = tool_fn._tool_meta

        return wrapper

    if fn is not None:
        # @tool without parentheses
        return _register(fn)
    else:
        # @tool(...) with parameters
        return _register
