"""Tests for MiMoLLM-specific behavior (thinking params, reasoning buffer)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.llm.events import ThinkingDelta
from agent.llm.providers.mimo import MiMoLLM
from tests.test_openai_compatible import MockAsyncIterator, make_mock_chunk


class TestMiMoLLM:
    @pytest.fixture
    def llm(self) -> MiMoLLM:
        return MiMoLLM(api_key="test-key", model="mimo-v2.5-pro", enable_thinking=True)

    def test_extra_params_thinking_mode(self, llm: MiMoLLM) -> None:
        params = llm._extra_request_params()
        assert params["extra_body"]["thinking"] == {"type": "enabled"}
        assert params["temperature"] == 1.0
        assert params["top_p"] == 0.95

    @pytest.mark.asyncio
    async def test_reasoning_buffer_for_messages(self, llm: MiMoLLM) -> None:
        usage_mock = MagicMock(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        chunks = [
            make_mock_chunk(reasoning_content="plan: read skill"),
            make_mock_chunk(content="ok", finish_reason="stop", usage=usage_mock),
        ]
        llm.client.chat.completions.create = AsyncMock(
            return_value=MockAsyncIterator(chunks)
        )
        llm.begin_stream_turn()

        events = []
        async for event in llm.stream([{"role": "user", "content": "Hi"}]):
            events.append(event)

        assert any(isinstance(e, ThinkingDelta) for e in events)
        assert llm.consume_reasoning_for_message() == "plan: read skill"
        assert llm.consume_reasoning_for_message() == ""
