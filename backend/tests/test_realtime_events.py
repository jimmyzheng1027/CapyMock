"""Tests for RealtimeUpstreamEvent dataclass family and RealtimeSession protocol."""

from __future__ import annotations

import inspect

import pytest

from agent.llm.realtime.base import RealtimeSession
from agent.llm.realtime.events import (
    ConversationItemInputAudioTranscriptionCompleted,
    InputAudioBufferCommitted,
    InputAudioBufferSpeechStarted,
    InputAudioBufferSpeechStopped,
    RateLimit,
    RealtimeError,
    RealtimeUpstreamEvent,
    ResponseAudioDelta,
    ResponseAudioDone,
    ResponseAudioTranscriptDelta,
    ResponseAudioTranscriptDone,
    ResponseDone,
    ResponseFunctionCallArgumentsDone,
    SessionCreated,
    SessionUpdated,
)

# All concrete event classes for parametrized tests
ALL_EVENT_CLASSES = [
    SessionCreated,
    SessionUpdated,
    InputAudioBufferSpeechStarted,
    InputAudioBufferSpeechStopped,
    InputAudioBufferCommitted,
    ResponseAudioDelta,
    ResponseAudioDone,
    ResponseAudioTranscriptDelta,
    ResponseAudioTranscriptDone,
    ResponseFunctionCallArgumentsDone,
    ConversationItemInputAudioTranscriptionCompleted,
    ResponseDone,
    RateLimit,
    RealtimeError,
]


class TestRealtimeUpstreamEvents:
    """Tests for RealtimeUpstreamEvent dataclass family."""

    @pytest.mark.parametrize("cls", ALL_EVENT_CLASSES, ids=lambda c: c.__name__)
    def test_is_frozen(self, cls: type) -> None:
        """All event dataclasses must be frozen (immutable)."""
        instance = cls()
        with pytest.raises(AttributeError):
            instance.nonexistent_field = "value"  # type: ignore[attr-defined]

    @pytest.mark.parametrize("cls", ALL_EVENT_CLASSES, ids=lambda c: c.__name__)
    def test_inherits_base(self, cls: type) -> None:
        """All event classes must inherit from RealtimeUpstreamEvent."""
        instance = cls()
        assert isinstance(instance, RealtimeUpstreamEvent)

    def test_session_created_fields(self) -> None:
        ev = SessionCreated(session_id="s1")
        assert ev.session_id == "s1"

    def test_response_audio_delta_fields(self) -> None:
        ev = ResponseAudioDelta(item_id="i1", delta_b64="AAAA")
        assert ev.item_id == "i1"
        assert ev.delta_b64 == "AAAA"

    def test_response_audio_transcript_done_fields(self) -> None:
        ev = ResponseAudioTranscriptDone(item_id="i2", text="hello world")
        assert ev.item_id == "i2"
        assert ev.text == "hello world"

    def test_response_function_call_arguments_done_fields(self) -> None:
        ev = ResponseFunctionCallArgumentsDone(
            call_id="c1", name="save_real_question", arguments='{"q":"test"}'
        )
        assert ev.call_id == "c1"
        assert ev.name == "save_real_question"
        assert ev.arguments == '{"q":"test"}'

    def test_conversation_item_input_audio_transcription_completed_fields(self) -> None:
        ev = ConversationItemInputAudioTranscriptionCompleted(
            item_id="i3", transcript="user said this"
        )
        assert ev.item_id == "i3"
        assert ev.transcript == "user said this"

    def test_response_done_with_usage(self) -> None:
        usage = {"audio_in_tokens": 100, "audio_out_tokens": 200}
        ev = ResponseDone(response_id="r1", usage=usage)
        assert ev.response_id == "r1"
        assert ev.usage == usage

    def test_response_done_default_usage(self) -> None:
        ev = ResponseDone()
        assert ev.usage == {}

    def test_realtime_error_fields(self) -> None:
        ev = RealtimeError(code="auth_failed", message="Invalid API key")
        assert ev.code == "auth_failed"
        assert ev.message == "Invalid API key"

    def test_rate_limit_fields(self) -> None:
        ev = RateLimit(name="requests", remaining=10, reset_ms=1000)
        assert ev.name == "requests"
        assert ev.remaining == 10
        assert ev.reset_ms == 1000

    @pytest.mark.parametrize("cls", ALL_EVENT_CLASSES, ids=lambda c: c.__name__)
    def test_default_constructor(self, cls: type) -> None:
        """All event classes must be constructible with no arguments (defaults)."""
        instance = cls()
        assert isinstance(instance, RealtimeUpstreamEvent)


class TestRealtimeSessionProtocol:
    """Tests for RealtimeSession abstract protocol."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            RealtimeSession()  # type: ignore[abstract]

    def test_has_send_audio(self) -> None:
        assert hasattr(RealtimeSession, "send_audio")
        assert inspect.isfunction(RealtimeSession.send_audio) or inspect.ismethod(RealtimeSession.send_audio)

    def test_has_commit_audio(self) -> None:
        assert hasattr(RealtimeSession, "commit_audio")

    def test_has_create_response(self) -> None:
        assert hasattr(RealtimeSession, "create_response")

    def test_has_cancel_response(self) -> None:
        assert hasattr(RealtimeSession, "cancel_response")

    def test_has_inject_summary(self) -> None:
        assert hasattr(RealtimeSession, "inject_summary")

    def test_has_update_session(self) -> None:
        assert hasattr(RealtimeSession, "update_session")

    def test_has_close(self) -> None:
        assert hasattr(RealtimeSession, "close")

    def test_async_context_manager(self) -> None:
        assert hasattr(RealtimeSession, "__aenter__")
        assert hasattr(RealtimeSession, "__aexit__")

    def test_async_iterable(self) -> None:
        assert hasattr(RealtimeSession, "__aiter__")
