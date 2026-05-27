from __future__ import annotations

import json
from collections.abc import AsyncIterator

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

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncIterator[LLMEvent]:
        """Stream LLM events from an OpenAI-compatible provider."""
        # Accumulate tool call arguments across chunks
        tool_call_args: dict[str, str] = {}
        tool_call_names: dict[str, str] = {}
        has_text = False
        has_thinking = False

        try:
            params = self._build_request_params(messages, tools)

            response = await self.client.chat.completions.create(**params)

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

                # Handle thinking/reasoning content
                thinking = self._extract_thinking(delta)
                if thinking:
                    has_thinking = True
                    yield ThinkingDelta(delta=thinking)

                # Handle text content
                if delta and delta.content:
                    has_text = True
                    yield TextDelta(delta=delta.content)

                # Handle tool calls
                if delta and delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.id and tc.function and tc.function.name:
                            tool_call_id = tc.id
                            tool_call_names[tool_call_id] = tc.function.name
                            tool_call_args[tool_call_id] = ""
                            yield ToolCallStart(
                                tool_call_id=tool_call_id,
                                tool_name=tc.function.name,
                            )
                        if tc.function and tc.function.arguments:
                            tool_call_id = tc.id or ""
                            tool_call_args[tool_call_id] = (
                                tool_call_args.get(tool_call_id, "") + tc.function.arguments
                            )
                            yield ToolCallArgsDelta(
                                tool_call_id=tool_call_id,
                                delta=tc.function.arguments,
                            )

                # Handle finish reason
                if finish_reason:
                    # Emit ToolCallEnd for each tool call
                    for tool_call_id, args_str in tool_call_args.items():
                        try:
                            args = json.loads(args_str) if args_str else {}
                        except json.JSONDecodeError:
                            args = {}
                        yield ToolCallEnd(
                            tool_call_id=tool_call_id,
                            tool_name=tool_call_names.get(tool_call_id, ""),
                            args=args,
                        )

                    # Emit Usage if available
                    if chunk.usage:
                        yield Usage(
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens,
                        )

                    # Map finish reason to stop reason
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

        # Add provider-specific parameters
        params.update(self._extra_request_params())

        return params

    def _extract_thinking(self, delta: object) -> str | None:
        """Extract thinking/reasoning content from a chunk. Override for provider-specific behavior."""
        # Default: check for reasoning_content (DeepSeek-R1 style)
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
