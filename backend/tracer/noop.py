from __future__ import annotations

import uuid
from typing import Any

from tracer.base import SpanContext, Tracer


class NoopTracer(Tracer):
    """No-op tracer that does nothing. Used for testing."""

    def span(self, name: str, **attrs: Any) -> SpanContext:
        """Create a span context (no-op)."""
        return SpanContext(
            span_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            attributes=attrs,
        )

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
        """Record an LLM call (no-op)."""
        pass

    def record_tool_call(
        self,
        span: SpanContext,
        tool_name: str,
        duration_ms: float,
        success: bool,
        **extra: Any,
    ) -> None:
        """Record a tool call (no-op)."""
        pass

    def end_span(self, span: SpanContext) -> None:
        """End a span (no-op)."""
        pass
