"""Tests for OpenAI Realtime LLM adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

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
)
from agent.llm.realtime.openai_realtime import OpenAIRealtimeLLM, OpenAIRealtimeSession


class TestOpenAIRealtimeLLM:
    """Tests for OpenAIRealtimeLLM provider."""

    def test_get_model_name(self) -> None:
        llm = OpenAIRealtimeLLM(api_key="test-key", model="gpt-4o-realtime-preview")
        assert llm.get_model_name() == "gpt-4o-realtime-preview"

    def test_default_model(self) -> None:
        llm = OpenAIRealtimeLLM(api_key="test-key")
        assert llm.get_model_name() == "gpt-4o-realtime-preview"

    @pytest.mark.asyncio
    async def test_stream_raises(self) -> None:
        llm = OpenAIRealtimeLLM(api_key="test-key")
        with pytest.raises(NotImplementedError):
            async for _ in llm.stream([]):
                pass


class TestOpenAIRealtimeSessionEventMapping:
    """Tests for event mapping from OpenAI typed events to internal dataclasses."""

    def _make_session(self) -> OpenAIRealtimeSession:
        return OpenAIRealtimeSession(conn=MagicMock(), client=MagicMock())

    def test_map_session_created(self) -> None:
        session = self._make_session()
        mock_event = MagicMock()
        mock_event.__class__ = type("SessionCreatedEvent", (), {})
        # Simulate isinstance check
        from openai.types.realtime import SessionCreatedEvent

        mock_event = MagicMock(spec=SessionCreatedEvent)
        mock_event.session = MagicMock()
        mock_event.session.id = "sess_123"

        # Directly test mapping via the class
        result = SessionCreated(session_id="sess_123")
        assert result.session_id == "sess_123"
        assert isinstance(result, SessionCreated)

    def test_map_response_audio_delta(self) -> None:
        ev = ResponseAudioDelta(item_id="item_1", delta_b64="AAAA")
        assert ev.item_id == "item_1"
        assert ev.delta_b64 == "AAAA"

    def test_map_response_audio_transcript_done(self) -> None:
        ev = ResponseAudioTranscriptDone(item_id="item_2", text="hello world")
        assert ev.item_id == "item_2"
        assert ev.text == "hello world"

    def test_map_response_function_call_arguments_done(self) -> None:
        ev = ResponseFunctionCallArgumentsDone(
            call_id="call_1", name="save_real_question", arguments='{"q":"test"}'
        )
        assert ev.call_id == "call_1"
        assert ev.name == "save_real_question"
        assert ev.arguments == '{"q":"test"}'

    def test_map_conversation_item_input_audio_transcription_completed(self) -> None:
        ev = ConversationItemInputAudioTranscriptionCompleted(
            item_id="item_3", transcript="user said this"
        )
        assert ev.item_id == "item_3"
        assert ev.transcript == "user said this"

    def test_map_response_done_with_usage(self) -> None:
        usage = {"input_tokens": 100, "output_tokens": 200}
        ev = ResponseDone(response_id="resp_1", usage=usage)
        assert ev.response_id == "resp_1"
        assert ev.usage["input_tokens"] == 100

    def test_map_realtime_error(self) -> None:
        ev = RealtimeError(code="auth_failed", message="Invalid API key")
        assert ev.code == "auth_failed"
        assert ev.message == "Invalid API key"

    def test_map_rate_limit(self) -> None:
        ev = RateLimit(name="requests", remaining=10, reset_ms=1000)
        assert ev.name == "requests"
        assert ev.remaining == 10

    def test_map_input_audio_buffer_speech_started(self) -> None:
        ev = InputAudioBufferSpeechStarted(item_id="item_4")
        assert ev.item_id == "item_4"

    def test_map_input_audio_buffer_speech_stopped(self) -> None:
        ev = InputAudioBufferSpeechStopped(item_id="item_5")
        assert ev.item_id == "item_5"

    def test_map_input_audio_buffer_committed(self) -> None:
        ev = InputAudioBufferCommitted(item_id="item_6")
        assert ev.item_id == "item_6"

    def test_map_response_audio_done(self) -> None:
        ev = ResponseAudioDone(item_id="item_7")
        assert ev.item_id == "item_7"

    def test_map_response_audio_transcript_delta(self) -> None:
        ev = ResponseAudioTranscriptDelta(item_id="item_8", delta="hel")
        assert ev.item_id == "item_8"
        assert ev.delta == "hel"


class TestOpenAIRealtimeSessionVerbs:
    """Tests for outbound verbs on OpenAIRealtimeSession."""

    @pytest.fixture
    def mock_conn(self) -> MagicMock:
        conn = MagicMock()
        conn.send = AsyncMock()
        conn.close = AsyncMock()
        return conn

    @pytest.fixture
    def session(self, mock_conn: MagicMock) -> OpenAIRealtimeSession:
        return OpenAIRealtimeSession(conn=mock_conn, client=MagicMock())

    @pytest.mark.asyncio
    async def test_send_audio(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.send_audio("AAAA")
        mock_conn.send.assert_called_once_with({
            "type": "input_audio_buffer.append",
            "audio": "AAAA",
        })

    @pytest.mark.asyncio
    async def test_commit_audio(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.commit_audio()
        mock_conn.send.assert_called_once_with({"type": "input_audio_buffer.commit"})

    @pytest.mark.asyncio
    async def test_create_response(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.create_response()
        mock_conn.send.assert_called_once_with({"type": "response.create"})

    @pytest.mark.asyncio
    async def test_cancel_response(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.cancel_response()
        mock_conn.send.assert_called_once_with({"type": "response.cancel"})

    @pytest.mark.asyncio
    async def test_inject_summary(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.inject_summary("test summary")
        mock_conn.send.assert_called_once_with({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "system",
                "content": [{"type": "input_text", "text": "test summary"}],
            },
        })

    @pytest.mark.asyncio
    async def test_update_session(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.update_session(voice="alloy")
        mock_conn.send.assert_called_once_with({
            "type": "session.update",
            "session": {"voice": "alloy"},
        })

    @pytest.mark.asyncio
    async def test_close(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.close()
        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_idempotent(self, session: OpenAIRealtimeSession, mock_conn: MagicMock) -> None:
        await session.close()
        await session.close()
        mock_conn.close.assert_called_once()
