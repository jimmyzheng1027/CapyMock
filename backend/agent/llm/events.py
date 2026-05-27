from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LLMEvent:
    """Base class for all LLM stream events."""

    pass


@dataclass(frozen=True)
class TextDelta(LLMEvent):
    """Incremental text content from the LLM."""

    delta: str


@dataclass(frozen=True)
class ThinkingDelta(LLMEvent):
    """Incremental thinking/reasoning content."""

    delta: str


@dataclass(frozen=True)
class ToolCallStart(LLMEvent):
    """Signals the start of a tool call."""

    tool_call_id: str
    tool_name: str


@dataclass(frozen=True)
class ToolCallArgsDelta(LLMEvent):
    """Incremental tool call arguments (JSON string fragment)."""

    tool_call_id: str
    delta: str


@dataclass(frozen=True)
class ToolCallEnd(LLMEvent):
    """Signals the end of a tool call with fully parsed arguments."""

    tool_call_id: str
    tool_name: str
    args: dict


@dataclass(frozen=True)
class Usage(LLMEvent):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class Done(LLMEvent):
    """Signals the end of an LLM stream."""

    stop_reason: Literal["end_turn", "tool_use", "max_tokens", "stop_sequence", "error"]


@dataclass(frozen=True)
class ProviderError(LLMEvent):
    """An error from the LLM provider."""

    message: str
    code: str = ""
    retryable: bool = False
