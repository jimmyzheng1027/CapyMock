"""Regression tests for OpenAI-compatible LLM providers.

These tests use a mock OpenAI client to verify event sequences.
All OpenAI-compatible providers should share this test set.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.llm.events import (
    Done,
    ProviderError,
    TextDelta,
    ThinkingDelta,
    ToolCallArgsDelta,
    ToolCallEnd,
    ToolCallStart,
    Usage,
)
from agent.llm.providers.openai_compatible import OpenAICompatibleLLM


def make_mock_chunk(
    content: str | None = None,
    tool_calls: list | None = None,
    finish_reason: str | None = None,
    reasoning_content: str | None = None,
    usage: object | None = None,
) -> MagicMock:
    """Create a mock chunk for testing."""
    chunk = MagicMock()
    delta = MagicMock()
    delta.content = content
    delta.tool_calls = tool_calls
    delta.reasoning_content = reasoning_content
    chunk.choices = [MagicMock(delta=delta, finish_reason=finish_reason)]
    chunk.usage = usage
    return chunk


def make_tool_delta(
    *,
    index: int = 0,
    tool_id: str | None = None,
    name: str | None = None,
    arguments: str | None = None,
) -> MagicMock:
    """Tool call delta (arguments chunks often omit id; use index)."""
    tc = MagicMock()
    tc.index = index
    tc.id = tool_id
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


class MockAsyncIterator:
    """Helper to create a proper async iterator from a list."""

    def __init__(self, items: list) -> None:
        self._items = items
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        return item


class TestOpenAICompatibleLLM:
    """Test event sequences for OpenAI-compatible providers."""

    @pytest.fixture
    def llm(self) -> OpenAICompatibleLLM:
        """Create an OpenAICompatibleLLM instance with a mock client."""
        llm = OpenAICompatibleLLM(
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )
        return llm

    @pytest.mark.asyncio
    async def test_text_only(self, llm: OpenAICompatibleLLM) -> None:
        """Test: pure text response with no tool calls."""
        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        chunks = [
            make_mock_chunk(content="Hello"),
            make_mock_chunk(content=" world"),
            make_mock_chunk(content="", finish_reason="stop", usage=usage_mock),
        ]

        llm.client.chat.completions.create = AsyncMock(return_value=MockAsyncIterator(chunks))

        events = []
        async for event in llm.stream([{"role": "user", "content": "Hi"}]):
            events.append(event)

        assert len(events) == 4
        assert isinstance(events[0], TextDelta) and events[0].delta == "Hello"
        assert isinstance(events[1], TextDelta) and events[1].delta == " world"
        assert isinstance(events[2], Usage) and events[2].total_tokens == 15
        assert isinstance(events[3], Done) and events[3].stop_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_single_tool_call(self, llm: OpenAICompatibleLLM) -> None:
        """Test: single tool call in response."""
        tool_call = make_tool_delta(
            index=0,
            tool_id="call_1",
            name="read_resume",
            arguments='{"resume_id": "r1"}',
        )

        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        chunks = [
            make_mock_chunk(tool_calls=[tool_call]),
            make_mock_chunk(finish_reason="tool_calls", usage=usage_mock),
        ]

        llm.client.chat.completions.create = AsyncMock(return_value=MockAsyncIterator(chunks))

        events = []
        async for event in llm.stream([{"role": "user", "content": "Read my resume"}]):
            events.append(event)

        # Should have: ToolCallStart, ToolCallArgsDelta, ToolCallEnd, Usage, Done
        assert len(events) == 5
        assert isinstance(events[0], ToolCallStart)
        assert events[0].tool_call_id == "call_1"
        assert events[0].tool_name == "read_resume"
        assert isinstance(events[1], ToolCallArgsDelta)
        assert isinstance(events[2], ToolCallEnd)
        assert events[2].args == {"resume_id": "r1"}
        assert isinstance(events[3], Usage)
        assert isinstance(events[4], Done)
        assert events[4].stop_reason == "tool_use"

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self, llm: OpenAICompatibleLLM) -> None:
        """Test: multiple concurrent tool calls."""
        tc1 = make_tool_delta(
            index=0,
            tool_id="call_1",
            name="read_resume",
            arguments='{"id": "r1"}',
        )
        tc2 = make_tool_delta(
            index=1,
            tool_id="call_2",
            name="take_note",
            arguments='{"note": "test"}',
        )

        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        chunks = [
            make_mock_chunk(tool_calls=[tc1, tc2]),
            make_mock_chunk(finish_reason="tool_calls", usage=usage_mock),
        ]

        llm.client.chat.completions.create = AsyncMock(return_value=MockAsyncIterator(chunks))

        events = []
        async for event in llm.stream([{"role": "user", "content": "Test"}]):
            events.append(event)

        # Should have: ToolCallStart x2, ToolCallArgsDelta x2, ToolCallEnd x2, Usage, Done
        assert len(events) == 8
        assert isinstance(events[0], ToolCallStart) and events[0].tool_call_id == "call_1"
        assert isinstance(events[2], ToolCallStart) and events[2].tool_call_id == "call_2"
        assert isinstance(events[6], Usage)
        assert isinstance(events[7], Done)
        assert events[7].stop_reason == "tool_use"

    @pytest.mark.asyncio
    async def test_fragmented_tool_arguments_by_index(self, llm: OpenAICompatibleLLM) -> None:
        """Arguments split across chunks without id must still parse."""
        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        chunks = [
            make_mock_chunk(
                tool_calls=[
                    make_tool_delta(
                        index=0,
                        tool_id="call_abc",
                        name="read_file",
                        arguments="",
                    )
                ],
            ),
            make_mock_chunk(
                tool_calls=[make_tool_delta(index=0, arguments='{"path":')],
            ),
            make_mock_chunk(
                tool_calls=[make_tool_delta(index=0, arguments=' "README.md"}')],
            ),
            make_mock_chunk(finish_reason="tool_calls", usage=usage_mock),
        ]

        llm.client.chat.completions.create = AsyncMock(
            return_value=MockAsyncIterator(chunks)
        )

        events = []
        async for event in llm.stream([{"role": "user", "content": "Read"}]):
            events.append(event)

        tool_ends = [e for e in events if isinstance(e, ToolCallEnd)]
        assert len(tool_ends) == 1
        assert tool_ends[0].tool_call_id == "call_abc"
        assert tool_ends[0].args == {"path": "README.md"}

    @pytest.mark.asyncio
    async def test_thinking_chain(self, llm: OpenAICompatibleLLM) -> None:
        """Test: thinking/reasoning content followed by text."""
        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        chunks = [
            make_mock_chunk(reasoning_content="Let me think..."),
            make_mock_chunk(reasoning_content="about this"),
            make_mock_chunk(content="The answer is 42"),
            make_mock_chunk(content="", finish_reason="stop", usage=usage_mock),
        ]

        llm.client.chat.completions.create = AsyncMock(return_value=MockAsyncIterator(chunks))

        events = []
        async for event in llm.stream([{"role": "user", "content": "What is 6x7?"}]):
            events.append(event)

        assert len(events) == 5
        assert isinstance(events[0], ThinkingDelta) and events[0].delta == "Let me think..."
        assert isinstance(events[1], ThinkingDelta) and events[1].delta == "about this"
        assert isinstance(events[2], TextDelta) and events[2].delta == "The answer is 42"
        assert isinstance(events[3], Usage)
        assert isinstance(events[4], Done)
        assert events[4].stop_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_error_response(self, llm: OpenAICompatibleLLM) -> None:
        """Test: error from provider."""
        error = Exception("Rate limit exceeded")
        error.status_code = 429

        llm.client.chat.completions.create = AsyncMock(side_effect=error)

        events = []
        async for event in llm.stream([{"role": "user", "content": "Test"}]):
            events.append(event)

        assert len(events) == 2
        assert isinstance(events[0], ProviderError)
        assert events[0].retryable is True
        assert isinstance(events[1], Done)
        assert events[1].stop_reason == "error"

    @pytest.mark.asyncio
    async def test_server_error_retryable(self, llm: OpenAICompatibleLLM) -> None:
        """Test: 5xx error is retryable."""
        error = Exception("Internal Server Error")
        error.status_code = 500

        llm.client.chat.completions.create = AsyncMock(side_effect=error)

        events = []
        async for event in llm.stream([{"role": "user", "content": "Test"}]):
            events.append(event)

        assert isinstance(events[0], ProviderError)
        assert events[0].retryable is True

    @pytest.mark.asyncio
    async def test_auth_error_not_retryable(self, llm: OpenAICompatibleLLM) -> None:
        """Test: 401 error is not retryable."""
        error = Exception("Unauthorized")
        error.status_code = 401

        llm.client.chat.completions.create = AsyncMock(side_effect=error)

        events = []
        async for event in llm.stream([{"role": "user", "content": "Test"}]):
            events.append(event)

        assert isinstance(events[0], ProviderError)
        assert events[0].retryable is False
