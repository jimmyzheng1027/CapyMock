"""Langfuse observability helpers (SDK v4, official context-manager pattern)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol

from config.settings import settings

logger = logging.getLogger(__name__)

_client_initialized = False


class SpanHandle(Protocol):
    def update(self, **kwargs: Any) -> Any: ...


class _NoopSpan:
    def update(self, **kwargs: Any) -> _NoopSpan:
        return self


def is_tracing_enabled() -> bool:
    return (
        settings.TRACER == "langfuse"
        and bool(settings.LANGFUSE_PUBLIC_KEY)
        and bool(settings.LANGFUSE_SECRET_KEY)
    )


def init_tracing() -> None:
    """Initialize Langfuse client singleton (no-op when tracing disabled)."""
    global _client_initialized
    if not is_tracing_enabled() or _client_initialized:
        return

    try:
        from langfuse import Langfuse, get_client

        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            base_url=settings.langfuse_base_url,
        )
        if not get_client().auth_check():
            logger.warning("Langfuse auth_check failed; verify keys and LANGFUSE_BASE_URL")
        _client_initialized = True
    except Exception as e:
        logger.warning("Failed to initialize Langfuse tracing: %s", e)


def shutdown_tracing() -> None:
    """Flush pending Langfuse events."""
    if not is_tracing_enabled() or not _client_initialized:
        return
    try:
        from langfuse import get_client

        get_client().flush()
    except Exception as e:
        logger.warning("Failed to flush Langfuse client: %s", e)


@contextmanager
def trace_agent_turn(
    *,
    session_id: str,
    user_id: str,
    user_input: str,
    profile_id: str = "",
) -> Iterator[SpanHandle]:
    """Root span: one user message / agent.run() invocation."""
    if not is_tracing_enabled():
        yield _NoopSpan()
        return

    from langfuse import get_client, propagate_attributes

    metadata: dict[str, str] = {}
    if profile_id:
        metadata["profile_id"] = profile_id

    with propagate_attributes(
        session_id=session_id,
        user_id=user_id,
        metadata=metadata or None,
    ):
        with get_client().start_as_current_observation(
            as_type="span",
            name="agent_turn",
            input={"user_input": user_input},
        ) as turn:
            yield turn


@contextmanager
def trace_react_step(*, step: int) -> Iterator[SpanHandle]:
    """Span for one ReAct loop iteration."""
    if not is_tracing_enabled():
        yield _NoopSpan()
        return

    from langfuse import get_client

    with get_client().start_as_current_observation(
        as_type="span",
        name=f"react_step_{step}",
        metadata={"step": step},
    ) as step_span:
        yield step_span


@contextmanager
def trace_compaction() -> Iterator[SpanHandle]:
    """Span for context compaction."""
    if not is_tracing_enabled():
        yield _NoopSpan()
        return

    from langfuse import get_client

    with get_client().start_as_current_observation(
        as_type="span",
        name="context_compaction",
    ) as span:
        yield span


@contextmanager
def trace_llm_call(*, model: str, messages: list[dict]) -> Iterator[SpanHandle]:
    """Generation span covering the full LLM stream."""
    if not is_tracing_enabled():
        yield _NoopSpan()
        return

    from langfuse import get_client

    with get_client().start_as_current_observation(
        as_type="generation",
        name="llm",
        model=model,
        input=messages,
    ) as generation:
        yield generation


@contextmanager
def trace_tool(*, name: str, args: dict[str, Any]) -> Iterator[SpanHandle]:
    """Tool span for a single tool invocation."""
    if not is_tracing_enabled():
        yield _NoopSpan()
        return

    from langfuse import get_client

    with get_client().start_as_current_observation(
        as_type="tool",
        name=name,
        input=args,
    ) as tool_span:
        yield tool_span


def tool_result_output(result: Any) -> dict[str, Any]:
    """Serialize ToolResult for Langfuse output."""
    status = getattr(result, "status", "unknown")
    payload: dict[str, Any] = {"status": status}
    if status == "ok":
        payload["data"] = getattr(result, "data", None)
    else:
        payload["error"] = getattr(result, "error", None)
        payload["summary"] = getattr(result, "summary", None)
    return payload


def span_level_for_result(result: Any) -> str:
    return "ERROR" if getattr(result, "status", "") != "ok" else "DEFAULT"
