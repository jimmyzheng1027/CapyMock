"""Tests for ToolExecutor: concurrency, timeout, isolation, cancel_token, retry, per-tool timeout."""

from __future__ import annotations

import asyncio

import pytest
from pydantic import BaseModel

from tool.base import ToolContext, ToolMeta, ToolResult, tool
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


# --- Tools with per-tool timeout and retry for testing ---


@tool(timeout=0.5)
async def short_timeout_tool(args: SlowArgs, ctx: ToolContext) -> ToolResult:
    """A tool with a short per-tool timeout."""
    await asyncio.sleep(args.delay)
    return ToolResult.ok(summary="done")


_retry_attempts: dict[str, int] = {}


@tool(max_retries=3)
async def flaky_tool(args: SuccessArgs, ctx: ToolContext) -> ToolResult:
    """A tool that fails the first 2 times, then succeeds."""
    key = args.value
    _retry_attempts.setdefault(key, 0)
    _retry_attempts[key] += 1
    if _retry_attempts[key] < 3:
        raise TimeoutError("simulated timeout")
    return ToolResult.ok(data={"value": args.value, "attempts": _retry_attempts[key]}, summary="ok after retries")


@tool(max_retries=2)
async def always_timeout_tool(args: SlowArgs, ctx: ToolContext) -> ToolResult:
    """A tool that always times out."""
    await asyncio.sleep(args.delay)
    return ToolResult.ok(summary="done")


@tool(read_only=True, timeout=5.0)
async def readonly_tool(args: SuccessArgs, ctx: ToolContext) -> ToolResult:
    """A read-only tool."""
    return ToolResult.ok(data={"value": args.value}, summary="readonly ok")


@tool(read_only=False, timeout=5.0)
async def write_tool(args: SuccessArgs, ctx: ToolContext) -> ToolResult:
    """A write tool."""
    return ToolResult.ok(data={"value": args.value}, summary="write ok")


class RequiredFieldArgs(BaseModel):
    """Args with a required field (no default)."""
    required_field: str  # No default → {} will trigger ValidationError


_call_count = 0


@tool(max_retries=3)
async def required_field_tool(args: RequiredFieldArgs, ctx: ToolContext) -> ToolResult:
    """A tool that requires a field with no default."""
    global _call_count
    _call_count += 1
    return ToolResult.ok(summary="ok")


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


class TestPerToolTimeout:
    """Test per-tool timeout configuration."""

    @pytest.mark.asyncio
    async def test_per_tool_timeout_overrides_default(self) -> None:
        """Test: tool-level timeout (0.5s) overrides executor default (10s)."""
        executor = ToolExecutor(default_timeout=10.0)
        reg = ToolRegistry(tools=[short_timeout_tool])
        tools = {meta.name: meta for meta in reg.all()}

        calls = [ToolCall(tool_call_id="1", tool_name="short_timeout_tool", args={"delay": 2.0})]
        results = await executor.run_parallel(calls, lambda c: ToolContext(), tools)

        assert len(results) == 1
        assert results[0].status == "err"
        assert results[0].error["code"] == "timeout"
        assert "0.5s" in results[0].error["message"]

    @pytest.mark.asyncio
    async def test_default_timeout_when_no_per_tool(self) -> None:
        """Test: tools without per-tool timeout use executor default."""
        executor = ToolExecutor(default_timeout=0.5)
        reg = ToolRegistry(tools=[slow_tool])
        tools = {meta.name: meta for meta in reg.all()}

        calls = [ToolCall(tool_call_id="1", tool_name="slow_tool", args={"delay": 2.0})]
        results = await executor.run_parallel(calls, lambda c: ToolContext(), tools)

        assert len(results) == 1
        assert results[0].status == "err"
        assert results[0].error["code"] == "timeout"


class TestToolRetry:
    """Test tool retry on timeout/network errors."""

    @pytest.mark.asyncio
    async def test_retry_on_timeout_succeeds(self) -> None:
        """Test: tool that fails twice with timeout then succeeds on 3rd attempt."""
        global _retry_attempts
        _retry_attempts = {}  # Reset

        executor = ToolExecutor(default_timeout=10.0)
        reg = ToolRegistry(tools=[flaky_tool])
        tools = {meta.name: meta for meta in reg.all()}

        calls = [ToolCall(tool_call_id="1", tool_name="flaky_tool", args={"value": "test_retry"})]
        results = await executor.run_parallel(calls, lambda c: ToolContext(), tools)

        assert len(results) == 1
        assert results[0].status == "ok"
        assert results[0].data["attempts"] == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        """Test: tool that always times out returns error after all retries."""
        executor = ToolExecutor(default_timeout=0.3)
        reg = ToolRegistry(tools=[always_timeout_tool])
        tools = {meta.name: meta for meta in reg.all()}

        calls = [ToolCall(tool_call_id="1", tool_name="always_timeout_tool", args={"delay": 5.0})]
        results = await executor.run_parallel(calls, lambda c: ToolContext(), tools)

        assert len(results) == 1
        assert results[0].status == "err"
        assert results[0].error["code"] == "timeout"
        assert "2/2" in results[0].error["message"]

    @pytest.mark.asyncio
    async def test_no_retry_on_validation_error(self) -> None:
        """Test: ValidationError is not retried even with max_retries > 1."""
        global _call_count
        _call_count = 0

        executor = ToolExecutor(default_timeout=10.0)
        reg = ToolRegistry(tools=[required_field_tool])
        tools = {meta.name: meta for meta in reg.all()}

        # Pass empty args to trigger ValidationError (required_field missing)
        calls = [ToolCall(tool_call_id="1", tool_name="required_field_tool", args={})]
        results = await executor.run_parallel(calls, lambda c: ToolContext(), tools)

        assert len(results) == 1
        assert results[0].status == "err"
        assert results[0].error["code"] == "invalid_args"
        assert _call_count == 0  # Tool function should never be called


class TestReadOnlyFlag:
    """Test read_only flag on ToolMeta."""

    def test_read_only_default_false(self) -> None:
        """Test: tools without read_only flag default to False."""
        reg = ToolRegistry(tools=[success_tool])
        meta = reg.get("success_tool")
        assert meta is not None
        assert meta.read_only is False

    def test_read_only_set_true(self) -> None:
        """Test: read_only=True is correctly stored."""
        reg = ToolRegistry(tools=[readonly_tool])
        meta = reg.get("readonly_tool")
        assert meta is not None
        assert meta.read_only is True

    def test_read_only_set_false(self) -> None:
        """Test: read_only=False is correctly stored."""
        reg = ToolRegistry(tools=[write_tool])
        meta = reg.get("write_tool")
        assert meta is not None
        assert meta.read_only is False
