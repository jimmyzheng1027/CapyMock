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
    user_id: str = ""
    profile: Any = None
    cancel_token: Any = None
    permissions: dict = field(default_factory=dict)


@dataclass
class ToolMeta:
    """Metadata for a registered tool."""

    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable


def tool(fn: Callable) -> Callable:
    """Decorator to mark a function as a tool.

    The function must have the signature:
        async def fn(args: ArgsModel, ctx: ToolContext) -> ToolResult

    The ArgsModel type hint is used to derive the JSON schema.
    The function docstring is used as the tool description.
    """
    import inspect
    import typing

    sig = inspect.signature(fn)
    params = list(sig.parameters.values())

    # Get the args model type from the first parameter
    if len(params) < 2:
        raise ToolError(f"Tool function {fn.__name__} must have at least 2 parameters (args, ctx)")

    args_param = params[0]
    if args_param.annotation is inspect.Parameter.empty:
        raise ToolError(f"Tool function {fn.__name__} must have type annotation for args parameter")

    # Handle string annotations (from __future__ import annotations)
    args_model = args_param.annotation
    if isinstance(args_model, str):
        # Resolve string annotation to actual type
        hints = typing.get_type_hints(fn)
        args_model = hints.get(args_param.name, args_param.annotation)

    if not (isinstance(args_model, type) and issubclass(args_model, BaseModel)):
        raise ToolError(f"Tool function {fn.__name__} args parameter must be a Pydantic BaseModel")

    # Get description from docstring
    description = fn.__doc__ or fn.__name__

    # Attach metadata to the function
    fn._tool_meta = ToolMeta(
        name=fn.__name__,
        description=description,
        args_model=args_model,
        fn=fn,
    )

    @functools.wraps(fn)
    async def wrapper(args: BaseModel, ctx: ToolContext) -> ToolResult:
        return await fn(args, ctx)

    wrapper._tool_meta = fn._tool_meta

    return wrapper
