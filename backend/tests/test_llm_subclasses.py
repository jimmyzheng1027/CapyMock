"""Regression tests for LLM provider subclass-specific behaviors.

Tests for DeepSeek-R1 reasoning_content and DashScope enable_thinking.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.llm.events import (
    Done,
    TextDelta,
    ThinkingDelta,
    Usage,
)
from agent.llm.providers.dashscope_compat import DashScopeCompatLLM
from agent.llm.providers.deepseek import DeepSeekLLM
from tests.test_openai_compatible import MockAsyncIterator, make_mock_chunk


class TestDeepSeekLLM:
    """Test DeepSeek-specific behaviors."""

    @pytest.fixture
    def llm(self) -> DeepSeekLLM:
        """Create a DeepSeekLLM instance with a mock client."""
        llm = DeepSeekLLM(api_key="test-key", model="deepseek-reasoner")
        return llm

    @pytest.mark.asyncio
    async def test_reasoning_content(self, llm: DeepSeekLLM) -> None:
        """Test: DeepSeek-R1 reasoning_content is mapped to ThinkingDelta."""
        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        chunks = [
            make_mock_chunk(reasoning_content="Let me reason step by step..."),
            make_mock_chunk(reasoning_content="Therefore, the answer is"),
            make_mock_chunk(content="42"),
            make_mock_chunk(content="", finish_reason="stop", usage=usage_mock),
        ]

        llm.client.chat.completions.create = AsyncMock(return_value=MockAsyncIterator(chunks))

        events = []
        async for event in llm.stream([{"role": "user", "content": "What is 6x7?"}]):
            events.append(event)

        assert len(events) == 5
        assert isinstance(events[0], ThinkingDelta) and events[0].delta == "Let me reason step by step..."
        assert isinstance(events[1], ThinkingDelta) and events[1].delta == "Therefore, the answer is"
        assert isinstance(events[2], TextDelta) and events[2].delta == "42"
        assert isinstance(events[3], Usage)
        assert isinstance(events[4], Done)

    def test_model_name(self, llm: DeepSeekLLM) -> None:
        """Test: get_model_name returns the configured model."""
        assert llm.get_model_name() == "deepseek-reasoner"

    def test_base_url(self, llm: DeepSeekLLM) -> None:
        """Test: base_url is set to DeepSeek API."""
        assert str(llm.client.base_url).rstrip("/") == "https://api.deepseek.com"


class TestDashScopeCompatLLM:
    """Test DashScope-specific behaviors."""

    @pytest.fixture
    def llm(self) -> DashScopeCompatLLM:
        """Create a DashScopeCompatLLM instance with a mock client."""
        llm = DashScopeCompatLLM(api_key="test-key", model="qwen-max")
        return llm

    @pytest.fixture
    def llm_with_thinking(self) -> DashScopeCompatLLM:
        """Create a DashScopeCompatLLM instance with enable_thinking."""
        llm = DashScopeCompatLLM(
            api_key="test-key",
            model="qwen-max",
            enable_thinking=True,
        )
        return llm

    @pytest.mark.asyncio
    async def test_thinking_model(self, llm_with_thinking: DashScopeCompatLLM) -> None:
        """Test: DashScope thinking models map reasoning_content to ThinkingDelta."""
        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        chunks = [
            make_mock_chunk(reasoning_content="Analyzing the question..."),
            make_mock_chunk(content="The answer is 42"),
            make_mock_chunk(content="", finish_reason="stop", usage=usage_mock),
        ]

        llm_with_thinking.client.chat.completions.create = AsyncMock(
            return_value=MockAsyncIterator(chunks)
        )

        events = []
        async for event in llm_with_thinking.stream([{"role": "user", "content": "Test"}]):
            events.append(event)

        assert len(events) == 4
        assert isinstance(events[0], ThinkingDelta)
        assert isinstance(events[1], TextDelta)

    def test_model_name(self, llm: DashScopeCompatLLM) -> None:
        """Test: get_model_name returns the configured model."""
        assert llm.get_model_name() == "qwen-max"

    def test_base_url(self, llm: DashScopeCompatLLM) -> None:
        """Test: base_url is set to DashScope compatible API."""
        assert str(llm.client.base_url).rstrip("/") == "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def test_extra_params_no_thinking(self, llm: DashScopeCompatLLM) -> None:
        """Test: no extra params when enable_thinking is False."""
        params = llm._extra_request_params()
        assert params == {}

    def test_extra_params_with_thinking(self, llm_with_thinking: DashScopeCompatLLM) -> None:
        """Test: extra params include enable_thinking when enabled."""
        params = llm_with_thinking._extra_request_params()
        assert params == {"extra_body": {"enable_thinking": True}}
