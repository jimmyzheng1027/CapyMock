"""Tests for DashScope Qwen-Omni Realtime LLM adapter."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest

from agent.llm.realtime.dashscope_realtime import (
    DashScopeRealtimeLLM,
    DashScopeRealtimeSession,
    _DashScopeCallback,
)
from agent.llm.realtime.events import (
    ConversationItemInputAudioTranscriptionCompleted,
    InputAudioBufferCommitted,
    InputAudioBufferSpeechStarted,
    InputAudioBufferSpeechStopped,
    RateLimit,
    RealtimeError,
    ResponseAudioDelta,
    ResponseAudioDone,
    ResponseAudioTranscriptDelta,
    ResponseAudioTranscriptDone,
    ResponseDone,
    ResponseFunctionCallArgumentsDone,
    SessionCreated,
    SessionUpdated,
)


class TestDashScopeRealtimeLLM:
    """Tests for DashScopeRealtimeLLM provider."""

    def test_get_model_name(self) -> None:
        llm = DashScopeRealtimeLLM(api_key="test-key", model="qwen3.5-omni-plus-realtime")
        assert llm.get_model_name() == "qwen3.5-omni-plus-realtime"

    def test_default_model(self) -> None:
        llm = DashScopeRealtimeLLM(api_key="test-key")
        assert llm.get_model_name() == "qwen3.5-omni-plus-realtime"

    @pytest.mark.asyncio
    async def test_stream_raises(self) -> None:
        llm = DashScopeRealtimeLLM(api_key="test-key")
        with pytest.raises(NotImplementedError):
            async for _ in llm.stream([]):
                pass


class TestDashScopeCallback:
    """Tests for _DashScopeCallback asyncio.Queue bridge."""

    @pytest.mark.asyncio
    async def test_on_event_parses_json(self) -> None:
        cb = _DashScopeCallback()
        cb.set_loop(asyncio.get_running_loop())

        data = {"type": "session.created", "session": {"id": "s1"}}
        cb.on_event(json.dumps(data))

        result = await asyncio.wait_for(cb.queue.get(), timeout=1.0)
        assert result == data

    @pytest.mark.asyncio
    async def test_on_event_invalid_json(self) -> None:
        cb = _DashScopeCallback()
        cb.set_loop(asyncio.get_running_loop())

        cb.on_event("not valid json")
        # Should not put anything in the queue
        assert cb.queue.empty()

    @pytest.mark.asyncio
    async def test_on_close_signals_none(self) -> None:
        cb = _DashScopeCallback()
        cb.set_loop(asyncio.get_running_loop())

        cb.on_close(1000, "normal")
        result = await asyncio.wait_for(cb.queue.get(), timeout=1.0)
        assert result is None


class TestDashScopeRealtimeSessionEventMapping:
    """Tests for event mapping from DashScope dicts to internal dataclasses."""

    def _make_session(self) -> DashScopeRealtimeSession:
        return DashScopeRealtimeSession(conv=MagicMock(), callback=MagicMock())

    def test_map_session_created(self) -> None:
        session = self._make_session()
        data = {"type": "session.created", "session": {"id": "sess_1"}}
        result = session._map_event(data)
        assert isinstance(result, SessionCreated)
        assert result.session_id == "sess_1"

    def test_map_session_updated(self) -> None:
        session = self._make_session()
        data = {"type": "session.updated"}
        result = session._map_event(data)
        assert isinstance(result, SessionUpdated)

    def test_map_speech_started(self) -> None:
        session = self._make_session()
        data = {"type": "input_audio_buffer.speech_started", "item_id": "i1"}
        result = session._map_event(data)
        assert isinstance(result, InputAudioBufferSpeechStarted)
        assert result.item_id == "i1"

    def test_map_speech_stopped(self) -> None:
        session = self._make_session()
        data = {"type": "input_audio_buffer.speech_stopped", "item_id": "i2"}
        result = session._map_event(data)
        assert isinstance(result, InputAudioBufferSpeechStopped)
        assert result.item_id == "i2"

    def test_map_committed(self) -> None:
        session = self._make_session()
        data = {"type": "input_audio_buffer.committed", "item_id": "i3"}
        result = session._map_event(data)
        assert isinstance(result, InputAudioBufferCommitted)
        assert result.item_id == "i3"

    def test_map_response_audio_delta(self) -> None:
        session = self._make_session()
        data = {"type": "response.audio.delta", "item_id": "i4", "delta": "AAAA"}
        result = session._map_event(data)
        assert isinstance(result, ResponseAudioDelta)
        assert result.item_id == "i4"
        assert result.delta_b64 == "AAAA"

    def test_map_response_audio_done(self) -> None:
        session = self._make_session()
        data = {"type": "response.audio.done", "item_id": "i5"}
        result = session._map_event(data)
        assert isinstance(result, ResponseAudioDone)
        assert result.item_id == "i5"

    def test_map_response_audio_transcript_delta(self) -> None:
        session = self._make_session()
        data = {"type": "response.audio_transcript.delta", "item_id": "i6", "delta": "hel"}
        result = session._map_event(data)
        assert isinstance(result, ResponseAudioTranscriptDelta)
        assert result.item_id == "i6"
        assert result.delta == "hel"

    def test_map_response_audio_transcript_done(self) -> None:
        session = self._make_session()
        data = {"type": "response.audio_transcript.done", "item_id": "i7", "transcript": "hello"}
        result = session._map_event(data)
        assert isinstance(result, ResponseAudioTranscriptDone)
        assert result.item_id == "i7"
        assert result.text == "hello"

    def test_map_response_function_call_arguments_done(self) -> None:
        session = self._make_session()
        data = {
            "type": "response.function_call_arguments.done",
            "call_id": "c1",
            "name": "save_real_question",
            "arguments": '{"q":"test"}',
        }
        result = session._map_event(data)
        assert isinstance(result, ResponseFunctionCallArgumentsDone)
        assert result.call_id == "c1"
        assert result.name == "save_real_question"

    def test_map_transcription_completed(self) -> None:
        session = self._make_session()
        data = {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "i8",
            "transcript": "user said",
        }
        result = session._map_event(data)
        assert isinstance(result, ConversationItemInputAudioTranscriptionCompleted)
        assert result.item_id == "i8"
        assert result.transcript == "user said"

    def test_map_transcription_completed_nested_item(self) -> None:
        session = self._make_session()
        data = {
            "type": "conversation.item.input_audio_transcription.completed",
            "item": {"id": "i9", "transcript": "nested answer"},
        }
        result = session._map_event(data)
        assert isinstance(result, ConversationItemInputAudioTranscriptionCompleted)
        assert result.item_id == "i9"
        assert result.transcript == "nested answer"

    def test_map_transcription_delta_then_completed(self) -> None:
        session = self._make_session()
        delta = {
            "type": "conversation.item.input_audio_transcription.delta",
            "item_id": "i10",
            "text": "hello ",
            "stash": "world",
        }
        assert session._map_event(delta) is None
        completed = {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "i10",
            "transcript": "",
        }
        result = session._map_event(completed)
        assert isinstance(result, ConversationItemInputAudioTranscriptionCompleted)
        assert result.transcript == "hello world"

    def test_map_transcription_completed_empty_skipped(self) -> None:
        session = self._make_session()
        data = {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "i11",
            "transcript": "",
        }
        assert session._map_event(data) is None

    def test_map_response_done(self) -> None:
        session = self._make_session()
        data = {
            "type": "response.done",
            "response": {"id": "r1", "usage": {"input_tokens": 100}},
        }
        result = session._map_event(data)
        assert isinstance(result, ResponseDone)
        assert result.response_id == "r1"
        assert result.usage["input_tokens"] == 100

    def test_map_rate_limit(self) -> None:
        session = self._make_session()
        data = {
            "type": "rate_limits.updated",
            "rate_limits": [{"name": "req", "remaining": 5, "reset_ms": 1000}],
        }
        result = session._map_event(data)
        assert isinstance(result, RateLimit)
        assert result.name == "req"
        assert result.remaining == 5

    def test_map_error(self) -> None:
        session = self._make_session()
        data = {"type": "error", "error": {"type": "auth_failed", "message": "bad key"}}
        result = session._map_event(data)
        assert isinstance(result, RealtimeError)
        assert result.code == "auth_failed"
        assert result.message == "bad key"

    def test_map_unknown_returns_none(self) -> None:
        session = self._make_session()
        data = {"type": "some.unknown.event"}
        result = session._map_event(data)
        assert result is None


class TestDashScopeRealtimeSessionVerbs:
    """Tests for outbound verbs on DashScopeRealtimeSession."""

    @pytest.fixture
    def mock_conv(self) -> MagicMock:
        conv = MagicMock()
        conv.append_audio = MagicMock()
        conv.commit = MagicMock()
        conv.create_response = MagicMock()
        conv.cancel_response = MagicMock()
        conv.create_item = MagicMock()
        conv.update_session = MagicMock()
        conv.close = MagicMock()
        return conv

    @pytest.fixture
    def session(self, mock_conv: MagicMock) -> DashScopeRealtimeSession:
        return DashScopeRealtimeSession(conv=mock_conv, callback=MagicMock())

    @pytest.mark.asyncio
    async def test_send_audio(self, session: DashScopeRealtimeSession, mock_conv: MagicMock) -> None:
        await session.send_audio("AAAA")
        mock_conv.append_audio.assert_called_once_with("AAAA")

    @pytest.mark.asyncio
    async def test_commit_audio(self, session: DashScopeRealtimeSession, mock_conv: MagicMock) -> None:
        await session.commit_audio()
        mock_conv.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_response(self, session: DashScopeRealtimeSession, mock_conv: MagicMock) -> None:
        await session.create_response()
        mock_conv.create_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_response(self, session: DashScopeRealtimeSession, mock_conv: MagicMock) -> None:
        await session.cancel_response()
        mock_conv.cancel_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_inject_summary(self, session: DashScopeRealtimeSession, mock_conv: MagicMock) -> None:
        await session.inject_summary("test summary")
        mock_conv.create_item.assert_called_once_with({
            "type": "message",
            "role": "system",
            "content": [{"type": "input_text", "text": "test summary"}],
        })

    @pytest.mark.asyncio
    async def test_close(self, session: DashScopeRealtimeSession, mock_conv: MagicMock) -> None:
        await session.close()
        mock_conv.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_idempotent(self, session: DashScopeRealtimeSession, mock_conv: MagicMock) -> None:
        await session.close()
        await session.close()
        mock_conv.close.assert_called_once()
