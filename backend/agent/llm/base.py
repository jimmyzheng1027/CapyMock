from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from agent.llm.events import LLMEvent, TextDelta, ToolCallEnd, Usage


@dataclass
class CompletionResult:
    """Result of a non-streaming LLM call."""

    text: str
    tool_calls: list[dict]
    usage: Usage | None = None


class BaseLLM(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncIterator[LLMEvent]:
        """Stream LLM events for a conversation."""
        ...

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> CompletionResult:
        """Non-streaming chat. Default implementation collects from stream()."""
        text_parts: list[str] = []
        tool_calls: list[dict] = []
        usage: Usage | None = None

        async for event in self.stream(messages, tools):
            if isinstance(event, TextDelta):
                text_parts.append(event.delta)
            elif isinstance(event, ToolCallEnd):
                tool_calls.append({
                    "id": event.tool_call_id,
                    "name": event.tool_name,
                    "args": event.args,
                })
            elif isinstance(event, Usage):
                usage = event

        return CompletionResult(
            text="".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
        )

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name."""
        ...


class BaseRealtimeLLM(BaseLLM):
    """Abstract base for Realtime LLM providers (future use)."""

    @abstractmethod
    async def realtime_connect(self, **opts) -> None:
        """Establish a realtime connection. Not implemented in this change."""
        ...
