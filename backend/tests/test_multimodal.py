"""Tests for chat() method and multimodal message construction."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.llm.events import TextDelta, Usage
from agent.llm.providers.openai_compatible import OpenAICompatibleLLM, build_multimodal_message


def make_mock_chunk(
    content: str | None = None,
    finish_reason: str | None = None,
    usage: object | None = None,
) -> MagicMock:
    chunk = MagicMock()
    delta = MagicMock()
    delta.content = content
    delta.tool_calls = None
    delta.reasoning_content = None
    chunk.choices = [MagicMock(delta=delta, finish_reason=finish_reason)]
    chunk.usage = usage
    return chunk


class MockAsyncIterator:
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


class TestChatMethod:
    """Tests for BaseLLM.chat() which collects from stream()."""

    @pytest.fixture
    def llm(self) -> OpenAICompatibleLLM:
        return OpenAICompatibleLLM(
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )

    @pytest.mark.asyncio
    async def test_chat_collects_text(self, llm: OpenAICompatibleLLM) -> None:
        """chat() should collect all TextDelta into a single string."""
        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        chunks = [
            make_mock_chunk(content="Hello"),
            make_mock_chunk(content=" world"),
            make_mock_chunk(content="", finish_reason="stop", usage=usage_mock),
        ]
        llm.client.chat.completions.create = AsyncMock(return_value=MockAsyncIterator(chunks))

        result = await llm.chat([{"role": "user", "content": "Hi"}])

        assert result.text == "Hello world"
        assert result.usage.total_tokens == 15

    @pytest.mark.asyncio
    async def test_chat_returns_empty_on_no_text(self, llm: OpenAICompatibleLLM) -> None:
        """chat() should return empty text if no TextDelta events."""
        usage_mock = MagicMock(prompt_tokens=10, completion_tokens=0, total_tokens=10)
        chunks = [
            make_mock_chunk(content="", finish_reason="stop", usage=usage_mock),
        ]
        llm.client.chat.completions.create = AsyncMock(return_value=MockAsyncIterator(chunks))

        result = await llm.chat([{"role": "user", "content": "Test"}])

        assert result.text == ""

    @pytest.mark.asyncio
    async def test_chat_handles_error_gracefully(self, llm: OpenAICompatibleLLM) -> None:
        """chat() should still return a result when stream() encounters an error."""
        error = Exception("API error")
        error.status_code = 500
        llm.client.chat.completions.create = AsyncMock(side_effect=error)

        result = await llm.chat([{"role": "user", "content": "Test"}])

        # stream() catches the error and yields ProviderError, so chat() returns normally
        assert result.text == ""
        assert result.tool_calls == []


class TestBuildMultimodalMessage:
    """Tests for build_multimodal_message() helper."""

    def test_plain_text_unchanged(self) -> None:
        """Plain text messages should not be modified."""
        msg = build_multimodal_message("分析这份简历", text_only=True)
        assert msg == {"role": "user", "content": "分析这份简历"}

    def test_image_multimodal(self) -> None:
        """Image files should produce image_url content part."""
        msg = build_multimodal_message(
            "分析这份简历",
            file_b64="iVBORw0KGgo=",
            mime_type="image/png",
        )
        assert msg["role"] == "user"
        assert isinstance(msg["content"], list)
        assert len(msg["content"]) == 2
        assert msg["content"][0] == {"type": "text", "text": "分析这份简历"}
        assert msg["content"][1]["type"] == "image_url"
        assert msg["content"][1]["image_url"]["url"] == "data:image/png;base64,iVBORw0KGgo="

    def test_pdf_multimodal(self) -> None:
        """Multiple images should produce multiple image_url content parts."""
        msg = build_multimodal_message(
            "分析这份简历",
            images=[("JVBERi0xLjQ=", "image/png"), ("abc=", "image/png")],
        )
        assert msg["content"][0] == {"type": "text", "text": "分析这份简历"}
        assert len(msg["content"]) == 3
        assert msg["content"][1]["image_url"]["url"] == "data:image/png;base64,JVBERi0xLjQ="
        assert msg["content"][2]["image_url"]["url"] == "data:image/png;base64,abc="

    def test_jpg_multimodal(self) -> None:
        """JPG files should produce image_url content part."""
        msg = build_multimodal_message(
            "分析这份简历",
            file_b64="/9j/4AAQ=",
            mime_type="image/jpeg",
        )
        assert msg["content"][1]["image_url"]["url"] == "data:image/jpeg;base64,/9j/4AAQ="
