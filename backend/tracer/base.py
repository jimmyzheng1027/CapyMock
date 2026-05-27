from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpanContext:
    """Context for a tracer span."""

    span_id: str = ""
    trace_id: str = ""
    parent_span_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


class Tracer(ABC):
    """Abstract base class for tracers."""

    @abstractmethod
    def span(self, name: str, **attrs: Any) -> SpanContext:
        """Create a new span context."""
        ...

    @abstractmethod
    def record_llm_call(
        self,
        span: SpanContext,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: float,
        **extra: Any,
    ) -> None:
        """Record an LLM call."""
        ...

    @abstractmethod
    def record_tool_call(
        self,
        span: SpanContext,
        tool_name: str,
        duration_ms: float,
        success: bool,
        **extra: Any,
    ) -> None:
        """Record a tool call."""
        ...

    @abstractmethod
    def end_span(self, span: SpanContext) -> None:
        """End a span."""
        ...
