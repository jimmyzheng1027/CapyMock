from __future__ import annotations

import logging
import uuid
from typing import Any

from tracer.base import SpanContext, Tracer

logger = logging.getLogger(__name__)


class LangfuseTracer(Tracer):
    """Langfuse tracer implementation."""

    def __init__(
        self,
        public_key: str = "",
        secret_key: str = "",
        host: str = "http://localhost:3000",
    ) -> None:
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = host
        self._client = None

        # Try to initialize Langfuse client
        try:
            from langfuse import Langfuse

            if public_key and secret_key:
                self._client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host,
                )
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse: {e}")

    def span(self, name: str, **attrs: Any) -> SpanContext:
        """Create a new span context."""
        span_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        if self._client:
            try:
                trace = self._client.trace(
                    name=name,
                    id=trace_id,
                    metadata=attrs,
                )
                span = trace.span(
                    name=name,
                    id=span_id,
                )
                return SpanContext(
                    span_id=span_id,
                    trace_id=trace_id,
                    attributes={"langfuse_span": span, **attrs},
                )
            except Exception as e:
                logger.warning(f"Failed to create Langfuse span: {e}")

        return SpanContext(
            span_id=span_id,
            trace_id=trace_id,
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
        """Record an LLM call."""
        if self._client:
            try:
                langfuse_span = span.attributes.get("langfuse_span")
                if langfuse_span:
                    langfuse_span.generation(
                        name="llm_call",
                        model=model,
                        usage={
                            "promptTokens": prompt_tokens,
                            "completionTokens": completion_tokens,
                            "totalTokens": total_tokens,
                        },
                        metadata={
                            "latency_ms": latency_ms,
                            **extra,
                        },
                    )
            except Exception as e:
                logger.warning(f"Failed to record LLM call to Langfuse: {e}")

    def record_tool_call(
        self,
        span: SpanContext,
        tool_name: str,
        duration_ms: float,
        success: bool,
        **extra: Any,
    ) -> None:
        """Record a tool call."""
        if self._client:
            try:
                langfuse_span = span.attributes.get("langfuse_span")
                if langfuse_span:
                    langfuse_span.span(
                        name=f"tool:{tool_name}",
                        metadata={
                            "duration_ms": duration_ms,
                            "success": success,
                            **extra,
                        },
                    )
            except Exception as e:
                logger.warning(f"Failed to record tool call to Langfuse: {e}")

    def end_span(self, span: SpanContext) -> None:
        """End a span."""
        if self._client:
            try:
                langfuse_span = span.attributes.get("langfuse_span")
                if langfuse_span:
                    langfuse_span.end()
            except Exception as e:
                logger.warning(f"Failed to end Langfuse span: {e}")
