"""Tests for ToolExecutor: concurrency, timeout, isolation, cancel_token."""

from __future__ import annotations

import asyncio

import pytest
from pydantic import BaseModel

from tool.base import ToolContext, ToolResult, tool
from tool.executor import ToolCall, ToolExecutor
from tool.registry import ToolRegistry


class SlowArgs(BaseModel):
    delay: float = 0.1


class FailArgs(BaseModel):
    message: str = "fail"


class SuccessArgs(BaseModel):
    value: str = "ok"


@tool
async def slow_tool(args: SlowArgs, ctx: ToolContext) -> ToolResult:
    """A slow tool that takes some time."""
    await asyncio.sleep(args.delay)
    return ToolResult.ok(summary="slow done")


@tool
async def fail_tool(args: FailArgs, ctx: ToolContext) -> ToolResult:
    """A tool that always fails."""
    raise ValueError(args.message)


@tool
async def success_tool(args: SuccessArgs, ctx: ToolContext) -> ToolResult:
    """A tool that succeeds."""
    return ToolResult.ok(data={"value": args.value}, summary="success")


class TestToolExecutor:
    """Test ToolExecutor behavior."""

    @pytest.fixture
    def executor(self) -> ToolExecutor:
        """Create a ToolExecutor with short timeout for testing."""
        return ToolExecutor(default_timeout=1.0)

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        """Create a ToolRegistry with test tools."""
        return ToolRegistry(tools=[slow_tool, fail_tool, success_tool])

    @pytest.mark.asyncio
    async def test_concurrent_execution(
        self, executor: ToolExecutor, registry: ToolRegistry
    ) -> None:
        """Test: multiple tools execute concurrently."""
        calls = [
            ToolCall(tool_call_id="1", tool_name="slow_tool", args={"delay": 0.1}),
            ToolCall(tool_call_id="2", tool_name="slow_tool", args={"delay": 0.1}),
            ToolCall(tool_call_id="3", tool_name="slow_tool", args={"delay": 0.1}),
        ]

        def ctx_factory(call: ToolCall) -> ToolContext:
            return ToolContext()

        tools = {meta.name: meta for meta in registry.all()}
        start = asyncio.get_event_loop().time()
        results = await executor.run_parallel(calls, ctx_factory, tools, parallel_limit=3)
        elapsed = asyncio.get_event_loop().time() - start

        assert len(results) == 3
        assert all(r.status == "ok" for r in results)
        # Should take ~0.1s (concurrent), not ~0.3s (sequential)
        assert elapsed < 0.2

    @pytest.mark.asyncio
    async def test_timeout(self, executor: ToolExecutor, registry: ToolRegistry) -> None:
        """Test: tool execution times out."""
        calls = [
            ToolCall(tool_call_id="1", tool_name="slow_tool", args={"delay": 5.0}),
        ]

        def ctx_factory(call: ToolCall) -> ToolContext:
            return ToolContext()

        tools = {meta.name: meta for meta in registry.all()}
        results = await executor.run_parallel(calls, ctx_factory, tools)

        assert len(results) == 1
        assert results[0].status == "err"
        assert results[0].error["code"] == "timeout"

    @pytest.mark.asyncio
    async def test_failure_isolation(
        self, executor: ToolExecutor, registry: ToolRegistry
    ) -> None:
        """Test: one tool failure doesn't affect others."""
        calls = [
            ToolCall(tool_call_id="1", tool_name="success_tool", args={"value": "a"}),
            ToolCall(tool_call_id="2", tool_name="fail_tool", args={"message": "oops"}),
            ToolCall(tool_call_id="3", tool_name="success_tool", args={"value": "b"}),
        ]

        def ctx_factory(call: ToolCall) -> ToolContext:
            return ToolContext()

        tools = {meta.name: meta for meta in registry.all()}
        results = await executor.run_parallel(calls, ctx_factory, tools, parallel_limit=3)

        assert len(results) == 3
        assert results[0].status == "ok"
        assert results[1].status == "err"
        assert results[1].error["code"] == "error"
        assert results[2].status == "ok"

    @pytest.mark.asyncio
    async def test_cancel_token(self, executor: ToolExecutor, registry: ToolRegistry) -> None:
        """Test: cancel_token stops execution."""
        cancel_token = asyncio.Event()
        cancel_token.set()  # Pre-cancel

        calls = [
            ToolCall(tool_call_id="1", tool_name="success_tool", args={}),
        ]

        def ctx_factory(call: ToolCall) -> ToolContext:
            return ToolContext(cancel_token=cancel_token)

        tools = {meta.name: meta for meta in registry.all()}
        results = await executor.run_parallel(
            calls, ctx_factory, tools, cancel_token=cancel_token
        )

        assert len(results) == 1
        assert results[0].status == "err"
        assert results[0].error["code"] == "cancelled"

    @pytest.mark.asyncio
    async def test_tool_not_found(
        self, executor: ToolExecutor, registry: ToolRegistry
    ) -> None:
        """Test: calling a non-existent tool returns error."""
        calls = [
            ToolCall(tool_call_id="1", tool_name="nonexistent", args={}),
        ]

        def ctx_factory(call: ToolCall) -> ToolContext:
            return ToolContext()

        tools = {meta.name: meta for meta in registry.all()}
        results = await executor.run_parallel(calls, ctx_factory, tools)

        assert len(results) == 1
        assert results[0].status == "err"
        assert results[0].error["code"] == "tool_not_found"

    @pytest.mark.asyncio
    async def test_empty_calls(self, executor: ToolExecutor) -> None:
        """Test: empty calls list returns empty results."""
        results = await executor.run_parallel(
            [], lambda c: ToolContext(), {}, parallel_limit=3
        )
        assert results == []
