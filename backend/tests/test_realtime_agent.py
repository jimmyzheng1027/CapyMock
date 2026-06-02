"""Tests for RealtimeAgent."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.llm.realtime.base import RealtimeSession
from agent.llm.realtime.events import (
    ConversationItemInputAudioTranscriptionCompleted,
    InputAudioBufferSpeechStarted,
    RealtimeError,
    RealtimeUpstreamEvent,
    ResponseAudioDelta,
    ResponseAudioDone,
    ResponseAudioTranscriptDone,
    ResponseDone,
)
from agent.profile import (
    AgentProfile,
    LLMConfig,
    RealtimeConfig,
    RealtimeMidSummaryConfig,
    RealtimeTranscriptionConfig,
)
from agent.realtime_agent import (
    RealtimeAgent,
    RealtimeAgentState,
    _build_voice_handoff_summary,
)
from api.schemas import EventType, FrontendEvent
from tool.base import ToolMeta


class FakeRealtimeSession(RealtimeSession):
    """Fake realtime session for testing."""

    def __init__(self, events: list[RealtimeUpstreamEvent] | None = None) -> None:
        self.events = events or []
        self.sent: list[dict] = []
        self.injected: list[str] = []
        self._closed = False
        self._index = 0

    def __aiter__(self) -> AsyncIterator[RealtimeUpstreamEvent]:
        return self._iter()

    async def _iter(self) -> AsyncIterator[RealtimeUpstreamEvent]:
        for event in self.events:
            yield event
            self._index += 1

    async def send_audio(self, pcm16_b64: str) -> None:
        self.sent.append({"type": "send_audio", "audio": pcm16_b64})

    async def commit_audio(self) -> None:
        self.sent.append({"type": "commit_audio"})

    async def create_response(self) -> None:
        self.sent.append({"type": "create_response"})

    async def cancel_response(self) -> None:
        self.sent.append({"type": "cancel_response"})

    async def inject_summary(self, text: str) -> None:
        self.injected.append(text)
        self.sent.append({"type": "inject_summary", "text": text})

    async def inject_message(self, role: str, text: str) -> None:
        self.injected.append(f"{role}:{text}")
        self.sent.append({"type": "inject_message", "role": role, "text": text})

    async def update_session(self, **fields: object) -> None:
        self.sent.append({"type": "update_session", **fields})

    async def close(self) -> None:
        self._closed = True


class FakeClientWS:
    """Fake client WebSocket for testing."""

    def __init__(self, messages: list[str] | None = None) -> None:
        self.messages = messages or []
        self.sent: list[str] = []
        self._index = 0
        self._closed = False

    async def receive_text(self) -> str:
        if self._index >= len(self.messages):
            # Simulate disconnect
            await asyncio.sleep(100)  # Will be cancelled
        msg = self.messages[self._index]
        self._index += 1
        return msg

    async def send_text(self, data: str) -> None:
        self.sent.append(data)

    def sent_events(self) -> list[FrontendEvent]:
        events = []
        for raw in self.sent:
            try:
                events.append(FrontendEvent.model_validate_json(raw))
            except Exception:
                pass
        return events


def make_test_profile(
    vad_mode: str = "semantic",
    max_session_minutes: int = 15,
    midsummary_enabled: bool = False,
) -> AgentProfile:
    """Create a test AgentProfile with realtime config."""
    return AgentProfile(
        id="test-interviewer",
        prompt_template="test.md",
        llm=LLMConfig(provider="mimo", model="test"),
        tools=["save_real_question"],
        realtime=RealtimeConfig(
            provider="openai_realtime",
            model="gpt-4o-realtime-preview",
            voice="alloy",
            vad_mode=vad_mode,
            max_session_minutes=max_session_minutes,
            midsummary=RealtimeMidSummaryConfig(
                enabled=midsummary_enabled,
                interval_minutes=8,
                subagent_profile="mid-summary-injector",
                timeout_seconds=5,
            ),
            transcription=RealtimeTranscriptionConfig(enabled=True, model="whisper"),
        ),
    )


def make_test_tools() -> dict[str, ToolMeta]:
    """Create minimal test tools."""
    from pydantic import BaseModel

    class SaveRealQuestionArgs(BaseModel):
        question: str

    return {
        "save_real_question": ToolMeta(
            name="save_real_question",
            description="Save a real interview question",
            args_model=SaveRealQuestionArgs,
            fn=AsyncMock(return_value="saved"),
        ),
    }


class TestRealtimeAgentState:
    """Tests for RealtimeAgentState enum."""

    def test_states_exist(self) -> None:
        assert RealtimeAgentState.IDLE == "idle"
        assert RealtimeAgentState.LISTENING == "listening"
        assert RealtimeAgentState.AI_SPEAKING == "ai_speaking"
        assert RealtimeAgentState.THINKING == "thinking"
        assert RealtimeAgentState.CLOSED == "closed"


class TestRealtimeAgentInit:
    """Tests for RealtimeAgent initialization."""

    def test_basic_init(self) -> None:
        profile = make_test_profile()
        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=MagicMock(),
            tools=make_test_tools(),
            instructions="test instructions",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )
        assert agent._state == RealtimeAgentState.IDLE
        assert agent._closed is False
        assert agent._audio_seconds_used == 0.0

    def test_custom_max_session_minutes(self) -> None:
        profile = make_test_profile(max_session_minutes=30)
        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=MagicMock(),
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
            max_session_minutes=30,
        )
        assert agent._max_seconds == 30 * 60


class TestRealtimeAgentBargeIn:
    """Tests for barge-in (interrupt) handling."""

    @pytest.mark.asyncio
    async def test_speech_started_while_ai_speaking_cancels(self) -> None:
        profile = make_test_profile()
        upstream = FakeRealtimeSession(
            events=[
                ResponseAudioDelta(item_id="i1", delta_b64="audio"),
                InputAudioBufferSpeechStarted(item_id="i2"),
            ]
        )
        client = FakeClientWS()

        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=MagicMock(),
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )
        agent._state = RealtimeAgentState.AI_SPEAKING

        # Simulate the upstream pump directly
        await agent._pump_upstream_to_client(upstream, client)

        # Should have sent ai.interrupted
        events = client.sent_events()
        interrupted = [e for e in events if e.type == EventType.AI_INTERRUPTED]
        assert len(interrupted) >= 1
        # Should have called cancel_response
        assert any(s.get("type") == "cancel_response" for s in upstream.sent)


class TestRealtimeAgentFunctionCall:
    """Tests for fire-and-forget function call handling."""

    @pytest.mark.asyncio
    async def test_save_real_question_fire_and_forget(self) -> None:
        profile = make_test_profile()
        mock_store = MagicMock()
        mock_store.read_events.return_value = []
        mock_store.append_event = MagicMock()

        tools = make_test_tools()

        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=mock_store,
            tools=tools,
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )

        # Call _on_function_call
        await agent._on_function_call(
            "call_1", "save_real_question", '{"question":"test q"}'
        )

        # Let the fire-and-forget task run
        await asyncio.sleep(0.1)

        # Tool should have been called
        tools["save_real_question"].fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_tool_ignored(self) -> None:
        profile = make_test_profile()
        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=MagicMock(),
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )

        # Should not raise
        await agent._on_function_call("call_1", "unknown_tool", "{}")


class TestRealtimeAgentCostCap:
    """Tests for L1 cost cap enforcement."""

    @pytest.mark.asyncio
    async def test_cost_cap_triggers_close(self) -> None:
        profile = make_test_profile(max_session_minutes=1)  # 1 minute cap
        mock_store = MagicMock()
        mock_store.append_event = MagicMock()

        upstream = FakeRealtimeSession()
        client = FakeClientWS()

        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=mock_store,
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
            max_session_minutes=1,
        )
        agent._realtime_session = upstream

        # Simulate exceeding the cap
        agent._audio_seconds_used = 70.0  # > 60 seconds

        # Simulate response.done
        event = ResponseDone(response_id="r1", usage={"audio_in_tokens": 100, "audio_out_tokens": 200})
        await agent._on_response_done(event)

        assert agent._closed is True


class TestVoiceHandoffSummary:
    """Tests for text→voice continuation system inject."""

    def test_handoff_when_last_is_assistant_question(self) -> None:
        events = [
            FrontendEvent(type=EventType.USER_TEXT, payload={"text": "my answer"}),
            FrontendEvent(
                type=EventType.ASSISTANT_TEXT_DONE,
                payload={"text": "请详细说明压缩比如何计算？"},
            ),
        ]
        summary = _build_voice_handoff_summary(events)
        assert summary is not None
        assert "语音模式接续" in summary
        assert "压缩比如何计算" in summary
        assert "不要提出新的主问题" in summary

    def test_no_handoff_when_only_assistant_greeting(self) -> None:
        events = [
            FrontendEvent(
                type=EventType.ASSISTANT_TEXT_DONE,
                payload={"text": "你好，欢迎参加面试"},
            ),
        ]
        assert _build_voice_handoff_summary(events) is None

    def test_no_handoff_when_last_is_user(self) -> None:
        events = [
            FrontendEvent(
                type=EventType.ASSISTANT_TEXT_DONE,
                payload={"text": "第一个问题"},
            ),
            FrontendEvent(type=EventType.USER_TEXT, payload={"text": "我的回答"}),
        ]
        assert _build_voice_handoff_summary(events) is None


class TestRealtimeAgentPersistence:
    """Tests for JSONL persistence strategy."""

    @pytest.mark.asyncio
    async def test_transcript_events_persisted(self) -> None:
        profile = make_test_profile()
        mock_store = MagicMock()
        mock_store.read_events.return_value = []
        mock_store.append_event = MagicMock()

        upstream = FakeRealtimeSession(
            events=[
                ResponseAudioTranscriptDone(item_id="i1", text="AI said hello"),
            ]
        )
        client = FakeClientWS()

        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=mock_store,
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )

        await agent._pump_upstream_to_client(upstream, client)

        # Should have persisted ASSISTANT_TRANSCRIPT_DONE
        persisted = [
            c for c in mock_store.append_event.call_args_list
            if c[0][2].type == EventType.ASSISTANT_TRANSCRIPT_DONE
        ]
        assert len(persisted) >= 1

    @pytest.mark.asyncio
    async def test_user_transcript_persisted(self) -> None:
        profile = make_test_profile()
        mock_store = MagicMock()
        mock_store.read_events.return_value = []
        mock_store.append_event = MagicMock()

        upstream = FakeRealtimeSession(
            events=[
                ConversationItemInputAudioTranscriptionCompleted(
                    item_id="u1", transcript="用户说了这些"
                ),
            ]
        )
        client = FakeClientWS()

        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=mock_store,
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )

        await agent._pump_upstream_to_client(upstream, client)

        persisted = [
            c for c in mock_store.append_event.call_args_list
            if c[0][2].type == EventType.USER_TRANSCRIPT
        ]
        assert len(persisted) == 1
        assert persisted[0][0][2].payload["text"] == "用户说了这些"

    @pytest.mark.asyncio
    async def test_audio_delta_not_persisted(self) -> None:
        profile = make_test_profile()
        mock_store = MagicMock()
        mock_store.read_events.return_value = []
        mock_store.append_event = MagicMock()

        upstream = FakeRealtimeSession(
            events=[
                ResponseAudioDelta(item_id="i1", delta_b64="AAAA"),
                ResponseAudioDone(item_id="i1"),
            ]
        )
        client = FakeClientWS()

        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=mock_store,
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )

        await agent._pump_upstream_to_client(upstream, client)

        # Should NOT have persisted audio delta or done
        audio_persisted = [
            c for c in mock_store.append_event.call_args_list
            if c[0][2].type in (EventType.ASSISTANT_AUDIO_DELTA, EventType.ASSISTANT_AUDIO_DONE)
        ]
        assert len(audio_persisted) == 0


class TestRealtimeAgentErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_upstream_error_pushes_to_client(self) -> None:
        profile = make_test_profile()
        mock_store = MagicMock()
        mock_store.read_events.return_value = []

        upstream = FakeRealtimeSession(
            events=[
                RealtimeError(code="auth_failed", message="Invalid API key"),
            ]
        )
        client = FakeClientWS()

        agent = RealtimeAgent(
            profile=profile,
            realtime_llm=MagicMock(),
            session_store=mock_store,
            tools=make_test_tools(),
            instructions="test",
            subagent_provider=MagicMock(),
            user_id="u1",
            session_id="s1",
        )

        await agent._pump_upstream_to_client(upstream, client)

        events = client.sent_events()
        errors = [e for e in events if e.type == EventType.ERROR]
        assert len(errors) >= 1
        assert errors[0].payload.get("code") == "auth_failed"
        assert agent._closed is True
