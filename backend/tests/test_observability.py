"""Tests for trace.observability helpers."""

from __future__ import annotations

import trace.observability as observability
from trace import (
    is_tracing_enabled,
    trace_agent_turn,
    trace_llm_call,
    trace_react_step,
    trace_tool,
)

from config.settings import Settings


def _patch_settings(monkeypatch, **kwargs: str) -> None:
    monkeypatch.setattr(
        observability,
        "settings",
        Settings(**kwargs),
    )


class TestTracingEnabled:
    def test_disabled_when_tracer_noop(self, monkeypatch) -> None:
        _patch_settings(monkeypatch, TRACER="noop")
        assert is_tracing_enabled() is False

    def test_enabled_with_langfuse_and_keys(self, monkeypatch) -> None:
        _patch_settings(
            monkeypatch,
            TRACER="langfuse",
            LANGFUSE_PUBLIC_KEY="pk-test",
            LANGFUSE_SECRET_KEY="sk-test",
        )
        assert is_tracing_enabled() is True

    def test_langfuse_without_keys_is_disabled(self, monkeypatch) -> None:
        _patch_settings(
            monkeypatch,
            TRACER="langfuse",
            LANGFUSE_PUBLIC_KEY="",
            LANGFUSE_SECRET_KEY="",
        )
        assert is_tracing_enabled() is False


class TestNoopContextManagers:
    def test_trace_agent_turn_noop(self, monkeypatch) -> None:
        _patch_settings(monkeypatch, TRACER="noop")
        with trace_agent_turn(
            session_id="s1",
            user_id="u1",
            user_input="hello",
        ) as turn:
            turn.update(output={"ok": True})

    def test_trace_react_step_noop(self, monkeypatch) -> None:
        _patch_settings(monkeypatch, TRACER="noop")
        with trace_react_step(step=1) as step:
            step.update(output={"continued": False})

    def test_trace_llm_call_noop(self, monkeypatch) -> None:
        _patch_settings(monkeypatch, TRACER="noop")
        with trace_llm_call(model="fake", messages=[{"role": "user", "content": "hi"}]) as gen:
            gen.update(output="hello", usage_details={"input": 1, "output": 2, "total": 3})

    def test_trace_tool_noop(self, monkeypatch) -> None:
        _patch_settings(monkeypatch, TRACER="noop")
        with trace_tool(name="sample", args={"x": 1}) as tool:
            tool.update(output={"status": "ok"})
