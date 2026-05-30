from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from tool.base import ToolContext, ToolMeta, ToolResult


@dataclass
class ToolCall:
    """A tool call request from the LLM."""

    tool_call_id: str
    tool_name: str
    args: dict


class ToolExecutor:
    """Executes tools with concurrency, timeout, and failure isolation."""

    def __init__(self, default_timeout: float = 30.0) -> None:
        self.default_timeout = default_timeout

    async def run_parallel(
        self,
        calls: list[ToolCall],
        ctx_factory: Callable[[ToolCall], ToolContext],
        tools: dict[str, ToolMeta],
        parallel_limit: int = 3,
        cancel_token: Any = None,
    ) -> list[ToolResult]:
        """Execute multiple tool calls in parallel with concurrency limit.

        Args:
            calls: List of tool calls to execute
            ctx_factory: Factory function to create ToolContext for each call
            tools: Dictionary of tool name -> ToolMeta
            parallel_limit: Maximum number of concurrent tool executions
            cancel_token: Token to signal cancellation

        Returns:
            List of ToolResult in the same order as calls
        """
        if not calls:
            return []

        # Create semaphore for concurrency limiting
        semaphore = asyncio.Semaphore(parallel_limit)

        async def execute_one(call: ToolCall) -> ToolResult:
            """Execute a single tool call with timeout and error isolation."""
            if cancel_token and cancel_token.is_set():
                return ToolResult.err(
                    code="cancelled",
                    message="Tool execution cancelled",
                    summary="Cancelled",
                )

            meta = tools.get(call.tool_name)
            if meta is None:
                return ToolResult.err(
                    code="tool_not_found",
                    message=f"Tool not found: {call.tool_name}",
                    summary=f"Tool not found: {call.tool_name}",
                )

            ctx = ctx_factory(call)

            async with semaphore:
                try:
                    # Create args model instance
                    args = meta.args_model(**call.args)

                    # Execute with timeout
                    result = await asyncio.wait_for(
                        meta.fn(args, ctx),
                        timeout=self.default_timeout,
                    )
                    return result

                except TimeoutError:
                    return ToolResult.err(
                        code="timeout",
                        message=f"Tool {call.tool_name} timed out after {self.default_timeout}s",
                        summary=f"Timeout: {call.tool_name}",
                    )
                except asyncio.CancelledError:
                    return ToolResult.err(
                        code="cancelled",
                        message=f"Tool {call.tool_name} was cancelled",
                        summary=f"Cancelled: {call.tool_name}",
                    )
                except ValidationError as e:
                    # LLM passed invalid/empty args — return full schema as hint
                    schema = meta.args_model.model_json_schema()
                    props = schema.get("properties", {})
                    required = schema.get("required", [])
                    fields_desc = []
                    example_args = {}
                    for name, info in props.items():
                        req = "REQUIRED" if name in required else "optional"
                        desc = info.get("description", "")
                        default = info.get("default", "no default")
                        fields_desc.append(f"  - {name} ({req}): {desc} [default: {default}]")
                        if name in required:
                            example_args[name] = f"<{name}>"
                    schema_str = "\n".join(fields_desc)
                    example_str = json.dumps(example_args)
                    return ToolResult.err(
                        code="invalid_args",
                        message=(
                            f"Tool {call.tool_name} was called with invalid arguments: {call.args}\n"
                            f"Required fields: {', '.join(required)}\n"
                            f"Schema:\n{schema_str}\n"
                            f"Correct example: {call.tool_name}({example_str})"
                        ),
                        summary=f"Missing args for {call.tool_name}",
                    )
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    return ToolResult.err(
                        code="error",
                        message=f"Tool {call.tool_name} error: {type(e).__name__}: {str(e) or repr(e)}\n{tb}",
                        summary=f"Error: {call.tool_name}",
                    )

        # Execute all calls concurrently
        tasks = [execute_one(call) for call in calls]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return list(results)
