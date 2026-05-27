"""Tests for Tracer: NoopTracer and a collecting fake tracer."""

from __future__ import annotations

from typing import Any

from tracer.base import SpanContext, Tracer
from tracer.noop import NoopTracer


class CollectingTracer(Tracer):
    """Fake tracer that collects all calls for verification."""

    def __init__(self) -> None:
        self.spans: list[dict] = []
        self.llm_calls: list[dict] = []
        self.tool_calls: list[dict] = []
        self.ended_spans: list[str] = []

    def span(self, name: str, **attrs: Any) -> SpanContext:
        """Create a span and record it."""
        span = SpanContext(
            span_id=f"span-{len(self.spans)}",
            trace_id="trace-1",
            attributes=attrs,
        )
        self.spans.append({"name": name, "span_id": span.span_id, **attrs})
        return span

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
        self.llm_calls.append({
            "span_id": span.span_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
        })

    def record_tool_call(
        self,
        span: SpanContext,
        tool_name: str,
        duration_ms: float,
        success: bool,
        **extra: Any,
    ) -> None:
        """Record a tool call."""
        self.tool_calls.append({
            "span_id": span.span_id,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
        })

    def end_span(self, span: SpanContext) -> None:
        """End a span."""
        self.ended_spans.append(span.span_id)


class TestNoopTracer:
    """Test NoopTracer behavior."""

    def test_span(self) -> None:
        """Test: NoopTracer creates a span context."""
        tracer = NoopTracer()
        span = tracer.span("test")

        assert span.span_id != ""
        assert span.trace_id != ""

    def test_record_llm_call(self) -> None:
        """Test: NoopTracer.record_llm_call does nothing."""
        tracer = NoopTracer()
        span = tracer.span("test")

        # Should not raise
        tracer.record_llm_call(
            span=span,
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            latency_ms=100.0,
        )

    def test_record_tool_call(self) -> None:
        """Test: NoopTracer.record_tool_call does nothing."""
        tracer = NoopTracer()
        span = tracer.span("test")

        # Should not raise
        tracer.record_tool_call(
            span=span,
            tool_name="test_tool",
            duration_ms=50.0,
            success=True,
        )

    def test_end_span(self) -> None:
        """Test: NoopTracer.end_span does nothing."""
        tracer = NoopTracer()
        span = tracer.span("test")

        # Should not raise
        tracer.end_span(span)


class TestCollectingTracer:
    """Test CollectingTracer behavior."""

    def test_span_creation(self) -> None:
        """Test: span is created and recorded."""
        tracer = CollectingTracer()
        span = tracer.span("test_span", key="value")

        assert len(tracer.spans) == 1
        assert tracer.spans[0]["name"] == "test_span"
        assert tracer.spans[0]["key"] == "value"

    def test_record_llm_call(self) -> None:
        """Test: LLM call is recorded."""
        tracer = CollectingTracer()
        span = tracer.span("llm_call")

        tracer.record_llm_call(
            span=span,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=200.0,
        )

        assert len(tracer.llm_calls) == 1
        assert tracer.llm_calls[0]["model"] == "gpt-4"
        assert tracer.llm_calls[0]["total_tokens"] == 150

    def test_record_tool_call(self) -> None:
        """Test: tool call is recorded."""
        tracer = CollectingTracer()
        span = tracer.span("tool_execution")

        tracer.record_tool_call(
            span=span,
            tool_name="read_resume",
            duration_ms=100.0,
            success=True,
        )

        assert len(tracer.tool_calls) == 1
        assert tracer.tool_calls[0]["tool_name"] == "read_resume"
        assert tracer.tool_calls[0]["success"] is True

    def test_end_span(self) -> None:
        """Test: span is ended."""
        tracer = CollectingTracer()
        span = tracer.span("test")

        tracer.end_span(span)

        assert len(tracer.ended_spans) == 1
        assert tracer.ended_spans[0] == span.span_id

    def test_multiple_spans(self) -> None:
        """Test: multiple spans are tracked separately."""
        tracer = CollectingTracer()

        span1 = tracer.span("span1")
        span2 = tracer.span("span2")

        tracer.record_llm_call(
            span=span1,
            model="model1",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            latency_ms=100.0,
        )

        tracer.record_tool_call(
            span=span2,
            tool_name="tool1",
            duration_ms=50.0,
            success=True,
        )

        assert len(tracer.llm_calls) == 1
        assert tracer.llm_calls[0]["span_id"] == span1.span_id

        assert len(tracer.tool_calls) == 1
        assert tracer.tool_calls[0]["span_id"] == span2.span_id
