import pytest

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


class TestLLMEventTypes:
    """Tests for LLMEvent dataclass types."""

    def test_text_delta(self) -> None:
        event = TextDelta(delta="hello")
        assert event.delta == "hello"
        assert isinstance(event, LLMEvent)

    def test_thinking_delta(self) -> None:
        event = ThinkingDelta(delta="reasoning...")
        assert event.delta == "reasoning..."
        assert isinstance(event, LLMEvent)

    def test_tool_call_start(self) -> None:
        event = ToolCallStart(tool_call_id="call_1", tool_name="read_resume")
        assert event.tool_call_id == "call_1"
        assert event.tool_name == "read_resume"
        assert isinstance(event, LLMEvent)

    def test_tool_call_args_delta(self) -> None:
        event = ToolCallArgsDelta(tool_call_id="call_1", delta='{"key":')
        assert event.tool_call_id == "call_1"
        assert event.delta == '{"key":'
        assert isinstance(event, LLMEvent)

    def test_tool_call_end(self) -> None:
        event = ToolCallEnd(
            tool_call_id="call_1",
            tool_name="read_resume",
            args={"resume_id": "r1"},
        )
        assert event.tool_call_id == "call_1"
        assert event.tool_name == "read_resume"
        assert event.args == {"resume_id": "r1"}
        assert isinstance(event, LLMEvent)

    def test_usage(self) -> None:
        event = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        assert event.prompt_tokens == 100
        assert event.completion_tokens == 50
        assert event.total_tokens == 150
        assert isinstance(event, LLMEvent)

    def test_done_end_turn(self) -> None:
        event = Done(stop_reason="end_turn")
        assert event.stop_reason == "end_turn"
        assert isinstance(event, LLMEvent)

    def test_done_tool_use(self) -> None:
        event = Done(stop_reason="tool_use")
        assert event.stop_reason == "tool_use"

    def test_done_max_tokens(self) -> None:
        event = Done(stop_reason="max_tokens")
        assert event.stop_reason == "max_tokens"

    def test_done_stop_sequence(self) -> None:
        event = Done(stop_reason="stop_sequence")
        assert event.stop_reason == "stop_sequence"

    def test_done_error(self) -> None:
        event = Done(stop_reason="error")
        assert event.stop_reason == "error"

    def test_provider_error(self) -> None:
        event = ProviderError(message="Rate limited", code="429", retryable=True)
        assert event.message == "Rate limited"
        assert event.code == "429"
        assert event.retryable is True
        assert isinstance(event, LLMEvent)

    def test_provider_error_not_retryable(self) -> None:
        event = ProviderError(message="Unauthorized", code="401", retryable=False)
        assert event.retryable is False

    def test_events_are_frozen(self) -> None:
        event = TextDelta(delta="hello")
        with pytest.raises(AttributeError):
            event.delta = "world"  # type: ignore[misc]

    def test_done_stop_reason_literal_constraint(self) -> None:
        """Verify that Done accepts only valid stop_reason values."""
        valid_reasons = ["end_turn", "tool_use", "max_tokens", "stop_sequence", "error"]
        for reason in valid_reasons:
            event = Done(stop_reason=reason)
            assert event.stop_reason == reason
