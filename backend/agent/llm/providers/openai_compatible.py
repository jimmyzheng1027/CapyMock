from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI

from agent.llm.base import BaseLLM
from agent.llm.events import (
    Done,
    LLMEvent,
    ProviderError,
    TextDelta,
    ThinkingDelta,
    ToolCallArgsDelta,
    ToolCallEnd,
    ToolCallStart,
    Usage,
)


@dataclass
class _StreamToolCall:
    """Accumulates one streamed tool call keyed by OpenAI chunk index."""

    index: int
    tool_call_id: str = ""
    name: str = ""
    arguments: str = ""
    started: bool = False


class OpenAICompatibleLLM(BaseLLM):
    """Base class for OpenAI-compatible LLM providers (Template Method pattern)."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.7,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def _on_thinking_delta(self, delta: str) -> None:
        """Hook when reasoning/thinking content arrives. Override to accumulate per turn."""
        return None

    def _emit_tool_call_start(self, slot: _StreamToolCall) -> ToolCallStart | None:
        if slot.started or not slot.tool_call_id or not slot.name:
            return None
        slot.started = True
        return ToolCallStart(tool_call_id=slot.tool_call_id, tool_name=slot.name)

    def _update_tool_slot(
        self, tc: object, pending: dict[int, _StreamToolCall]
    ) -> list[LLMEvent]:
        """Apply one streamed tool_calls delta; return events to yield."""
        events: list[LLMEvent] = []
        index = getattr(tc, "index", None)
        if index is None:
            index = 0

        if index not in pending:
            pending[index] = _StreamToolCall(index=index)
        slot = pending[index]

        if getattr(tc, "id", None):
            slot.tool_call_id = tc.id

        fn = getattr(tc, "function", None)
        if fn is None:
            return events

        if getattr(fn, "name", None):
            slot.name = fn.name
        start = self._emit_tool_call_start(slot)
        if start:
            events.append(start)

        arg_delta = getattr(fn, "arguments", None)
        if arg_delta:
            slot.arguments += arg_delta
            if slot.tool_call_id:
                events.append(
                    ToolCallArgsDelta(tool_call_id=slot.tool_call_id, delta=arg_delta)
                )

        return events

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncIterator[LLMEvent]:
        """Stream LLM events from an OpenAI-compatible provider."""
        pending: dict[int, _StreamToolCall] = {}

        try:
            params = self._build_request_params(messages, tools)
            response = await self.client.chat.completions.create(**params)

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

                thinking = self._extract_thinking(delta)
                if thinking:
                    self._on_thinking_delta(thinking)
                    yield ThinkingDelta(delta=thinking)

                if delta and delta.content:
                    yield TextDelta(delta=delta.content)

                if delta and delta.tool_calls:
                    for tc in delta.tool_calls:
                        for event in self._update_tool_slot(tc, pending):
                            yield event

                if finish_reason:
                    for slot in pending.values():
                        if not slot.tool_call_id:
                            continue
                        try:
                            args = json.loads(slot.arguments) if slot.arguments else {}
                        except json.JSONDecodeError:
                            args = {}
                        yield ToolCallEnd(
                            tool_call_id=slot.tool_call_id,
                            tool_name=slot.name,
                            args=args,
                        )

                    if chunk.usage:
                        yield Usage(
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens,
                        )

                    stop_reason = self._map_finish_reason(finish_reason)
                    yield Done(stop_reason=stop_reason)

        except Exception as e:
            retryable = self._is_retryable_error(e)
            yield ProviderError(
                message=str(e),
                code=getattr(e, "status_code", ""),
                retryable=retryable,
            )
            yield Done(stop_reason="error")

    def _build_request_params(self, messages: list[dict], tools: list[dict] | None) -> dict:
        """Build the request parameters for the API call."""
        params: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True,
        }

        if tools:
            params["tools"] = self._normalize_tool_schema(tools)

        params.update(self._extra_request_params())

        return params

    def _extract_thinking(self, delta: object) -> str | None:
        """Extract thinking/reasoning content from a chunk. Override for provider-specific behavior."""
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            return delta.reasoning_content
        return None

    def _extra_request_params(self) -> dict:
        """Return extra parameters for the API request. Override for provider-specific params."""
        return {}

    def _normalize_tool_schema(self, tools: list[dict]) -> list[dict]:
        """Normalize tool schema to OpenAI format. Override if provider has different format."""
        return tools

    def _map_finish_reason(self, finish_reason: str) -> str:
        """Map OpenAI finish_reason to our stop_reason."""
        mapping = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
            "content_filter": "error",
        }
        return mapping.get(finish_reason, "end_turn")

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable."""
        # Server errors (5xx) are retryable
        status_code = getattr(error, "status_code", None)
        if status_code and 500 <= status_code < 600:
            return True
        # Rate limit errors are retryable
        if status_code == 429:
            return True
        return False

    def get_model_name(self) -> str:
        return self.model
