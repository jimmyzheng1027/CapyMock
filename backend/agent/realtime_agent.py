"""RealtimeAgent: event-driven voice interview agent.

Dual-pump architecture that bridges a client WebSocket to a realtime LLM provider.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from enum import Enum

from agent.llm.base import BaseRealtimeLLM
from agent.llm.realtime.base import RealtimeSession
from agent.llm.realtime.events import (
    ConversationItemInputAudioTranscriptionCompleted,
    InputAudioBufferSpeechStarted,
    InputAudioBufferSpeechStopped,
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
from agent.loop import ReActAgent
from agent.profile import AgentProfile
from api.schemas import EventType, FrontendEvent
from storage.session.store import SessionStore
from tool.base import ToolContext, ToolMeta

logger = logging.getLogger(__name__)

# Default constants
DEFAULT_MAX_SESSION_MINUTES = 15
DEFAULT_INACTIVITY_TIMEOUT_SECONDS = 300
DEFAULT_MIDSUMMARY_INTERVAL_MINUTES = 8
DEFAULT_MIDSUMMARY_TIMEOUT_SECONDS = 5
DEFAULT_MIDSUMMARY_INJECT_WINDOW_TIMEOUT = 30.0
_HANDOFF_QUESTION_MAX_CHARS = 600


def _build_voice_handoff_summary(events: list) -> str | None:
    """Build system inject text when resuming a session that has text-mode history."""
    has_user_turn = False
    has_assistant_turn = False
    for ev in events:
        if ev.type in (EventType.USER_TEXT, EventType.USER_TRANSCRIPT):
            if (ev.payload.get("text") or "").strip():
                has_user_turn = True
        elif ev.type in (EventType.ASSISTANT_TEXT_DONE, EventType.ASSISTANT_TRANSCRIPT_DONE):
            if (ev.payload.get("text") or "").strip():
                has_assistant_turn = True

    if not has_user_turn or not has_assistant_turn:
        return None

    last = None
    for ev in reversed(events):
        if ev.type in (
            EventType.USER_TEXT,
            EventType.USER_TRANSCRIPT,
            EventType.ASSISTANT_TEXT_DONE,
            EventType.ASSISTANT_TRANSCRIPT_DONE,
        ):
            text = (ev.payload.get("text") or "").strip()
            if text:
                last = ev
                break

    if last is None or last.type not in (
        EventType.ASSISTANT_TEXT_DONE,
        EventType.ASSISTANT_TRANSCRIPT_DONE,
    ):
        return None

    pending = (last.payload.get("text") or "").strip()
    if len(pending) > _HANDOFF_QUESTION_MAX_CHARS:
        pending = pending[:_HANDOFF_QUESTION_MAX_CHARS] + "…"

    return (
        "[语音模式接续]\n"
        "用户刚从文字模式切换到语音。上方对话历史已完整注入。\n"
        "请勿重新自我介绍，也不要换一道全新的开场题。\n"
        "当前待用户回答的最后一个问题是：\n"
        f"「{pending}」\n"
        "请用一两句口语简短提醒用户继续回答上述问题，然后保持倾听；"
        "在用户回答前不要提出新的主问题。"
    )


class RealtimeAgentState(str, Enum):  # noqa: UP042
    IDLE = "idle"
    LISTENING = "listening"
    AI_SPEAKING = "ai_speaking"
    THINKING = "thinking"
    CLOSED = "closed"


class RealtimeAgent:
    """Event-driven voice interview agent.

    Uses dual pump coroutines to bridge client WebSocket ↔ realtime LLM provider.
    """

    def __init__(
        self,
        profile: AgentProfile,
        realtime_llm: BaseRealtimeLLM,
        session_store: SessionStore,
        tools: dict[str, ToolMeta],
        instructions: str,
        subagent_provider: Callable[[str, str], ReActAgent],
        user_id: str,
        session_id: str,
        resume_id: str = "",
        max_session_minutes: int = DEFAULT_MAX_SESSION_MINUTES,
        inactivity_timeout: int = DEFAULT_INACTIVITY_TIMEOUT_SECONDS,
        midsummary_interval_minutes: int = DEFAULT_MIDSUMMARY_INTERVAL_MINUTES,
        midsummary_timeout_seconds: int = DEFAULT_MIDSUMMARY_TIMEOUT_SECONDS,
    ) -> None:
        self.profile = profile
        self.realtime_llm = realtime_llm
        self.session_store = session_store
        self.tools = tools
        self.instructions = instructions
        self._subagent_provider = subagent_provider
        self.user_id = user_id
        self.session_id = session_id
        self._resume_id = resume_id
        self._max_seconds = max_session_minutes * 60
        self._inactivity_timeout = inactivity_timeout
        self._midsummary_interval = midsummary_interval_minutes * 60
        self._midsummary_timeout = midsummary_timeout_seconds

        self._state = RealtimeAgentState.IDLE
        self._closed = False
        self._audio_seconds_used = 0.0
        self._last_activity_ts: float = 0.0
        self._realtime_session: RealtimeSession | None = None

    async def run(self, client_ws: object) -> None:
        """Run the realtime agent.

        Args:
            client_ws: The client WebSocket connection (FastAPI WebSocket).
        """
        # Restore history from JSONL to upstream
        # (done inside realtime_connect after session is configured)

        midsummary_task: asyncio.Task[None] | None = None

        try:
            # Connect to realtime provider
            vad_config = self._build_vad_config()
            transcription_config = self._build_transcription_config()

            self._realtime_session = await self.realtime_llm.realtime_connect(
                instructions=self.instructions,
                tools=self._get_tool_schemas(),
                voice=self.profile.realtime.voice if self.profile.realtime else "alloy",
                vad=vad_config,
                transcription=transcription_config,
            )

            async with self._realtime_session as upstream:
                # Restore history and inject text→voice handoff guidance when needed
                events = self.session_store.read_events(self.user_id, self.session_id)
                await self._restore_history_to_upstream(upstream, events)
                await self._inject_voice_handoff(upstream, events)

                # Push session.started
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.SESSION_STARTED,
                    payload={
                        "session_id": self.session_id,
                        "mode": "voice",
                        "audio": self._get_audio_config(),
                    },
                ))

                # Start MidSummary timer
                midsummary_task = asyncio.create_task(
                    self._midsummary_loop(upstream, client_ws)
                )

                # Start inactivity watchdog
                inactivity_task = asyncio.create_task(
                    self._inactivity_watchdog(client_ws)
                )

                # Dual pump
                try:
                    await asyncio.gather(
                        self._pump_client_to_upstream(client_ws, upstream),
                        self._pump_upstream_to_client(upstream, client_ws),
                    )
                finally:
                    if midsummary_task:
                        midsummary_task.cancel()
                    inactivity_task.cancel()

        except Exception as e:
            logger.error("RealtimeAgent error: %s", e, exc_info=True)
            await self._push_to_client(client_ws, FrontendEvent(
                type=EventType.ERROR,
                payload={"code": "agent_error", "message": str(e)},
            ))
        finally:
            self._state = RealtimeAgentState.CLOSED
            await self._push_to_client(client_ws, FrontendEvent(
                type=EventType.TURN_DONE,
            ))

    def _build_vad_config(self) -> dict:
        if not self.profile.realtime:
            return {"type": "server_vad"}
        vad_mode = self.profile.realtime.vad_mode
        if vad_mode == "none":
            return {"type": "none"}
        if vad_mode == "server":
            return {"type": "server_vad", "threshold": self.profile.realtime.vad_threshold}
        # Default: semantic_vad
        return {"type": "semantic_vad"}

    def _build_transcription_config(self) -> dict:
        if not self.profile.realtime or not self.profile.realtime.transcription:
            return {"enabled": True}
        return {
            "enabled": self.profile.realtime.transcription.enabled,
            "model": self.profile.realtime.transcription.model,
        }

    def _get_audio_config(self) -> dict:
        provider = (
            self.profile.realtime.provider
            if self.profile.realtime
            else "openai_realtime"
        )
        input_rate = 16000 if provider == "dashscope_realtime" else 24000
        return {
            "format": "pcm16",
            "input_sample_rate": input_rate,
            "output_sample_rate": 24000,
        }

    def _get_tool_schemas(self) -> list[dict]:
        """Get tool schemas for realtime provider."""
        schemas = []
        for tool in self.tools.values():
            schema = tool.args_model.model_json_schema() if hasattr(tool, "args_model") else {}
            schemas.append({
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": schema,
            })
        return schemas

    # ── History Restore ──────────────────────────────────────────────

    async def _restore_history_to_upstream(
        self, upstream: RealtimeSession, events: list | None = None
    ) -> None:
        """Read JSONL events and inject as conversation items into upstream."""
        if events is None:
            events = self.session_store.read_events(self.user_id, self.session_id)
        for ev in events:
            if ev.type in (EventType.USER_TEXT, EventType.USER_TRANSCRIPT):
                text = (ev.payload.get("text") or "").strip()
                if text:
                    await upstream.inject_message("user", text)
            elif ev.type in (EventType.ASSISTANT_TEXT_DONE, EventType.ASSISTANT_TRANSCRIPT_DONE):
                text = (ev.payload.get("text") or "").strip()
                if text:
                    await upstream.inject_message("assistant", text)
            # Other events (state/audio/tool) are not restored

    async def _inject_voice_handoff(
        self, upstream: RealtimeSession, events: list
    ) -> None:
        """After text→voice switch, tell the model to continue the open question."""
        summary = _build_voice_handoff_summary(events)
        if summary:
            await upstream.inject_summary(summary)

    # ── Client → Upstream Pump ───────────────────────────────────────

    async def _pump_client_to_upstream(
        self, client_ws: object, upstream: RealtimeSession
    ) -> None:
        """Parse client frames and forward to upstream provider."""
        import json as json_mod

        while not self._closed:
            try:
                data = await client_ws.receive_text()
            except Exception:
                # Client disconnected
                self._closed = True
                return

            self._last_activity_ts = asyncio.get_event_loop().time()

            try:
                msg = json_mod.loads(data)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from client: %s", data[:200])
                continue

            msg_type = msg.get("type", "")
            payload = msg.get("payload", {})

            if msg_type == "user.audio.chunk":
                audio = payload.get("audio", "")
                if not audio:
                    await self._push_to_client(client_ws, FrontendEvent(
                        type=EventType.ERROR,
                        payload={"code": "invalid_audio_frame", "retryable": True},
                    ))
                    continue
                await upstream.send_audio(audio)

            elif msg_type == "control.commit":
                # Manual VAD: commit audio buffer and trigger response
                await upstream.commit_audio()
                await upstream.create_response()
                self._set_state(RealtimeAgentState.THINKING)

            elif msg_type == "control.interrupt":
                await upstream.cancel_response()
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.AI_INTERRUPTED,
                    payload={},
                ))

            elif msg_type == "user.text":
                text = payload.get("text", "")
                if text:
                    # Inject as user message and trigger response
                    await upstream.inject_summary(
                        json.dumps({"role": "user", "content": text})
                    )
                    await upstream.create_response()
                    self._set_state(RealtimeAgentState.THINKING)

            elif msg_type == "control.switch_mode":
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.ERROR,
                    payload={
                        "code": "unsupported_control_frame",
                        "message": "Switch mode not supported. Close WS and use SSE instead.",
                    },
                ))

            else:
                logger.info("Unknown client message type: %s", msg_type)

    # ── Upstream → Client Pump ───────────────────────────────────────

    async def _pump_upstream_to_client(
        self, upstream: RealtimeSession, client_ws: object
    ) -> None:
        """Forward upstream events to client and handle business logic."""
        async for event in upstream:
            if self._closed:
                return

            self._last_activity_ts = asyncio.get_event_loop().time()

            if isinstance(event, SessionCreated):
                logger.debug("Realtime session created: %s", event.session_id)

            elif isinstance(event, SessionUpdated):
                logger.debug("Realtime session updated")

            elif isinstance(event, InputAudioBufferSpeechStarted):
                # Barge-in: if AI is speaking, cancel and notify client
                if self._state == RealtimeAgentState.AI_SPEAKING:
                    await upstream.cancel_response()
                    await self._push_to_client(client_ws, FrontendEvent(
                        type=EventType.AI_INTERRUPTED,
                        payload={"item_id": event.item_id},
                    ))
                    self._append_event(FrontendEvent(
                        type=EventType.AI_INTERRUPTED,
                        payload={"item_id": event.item_id},
                    ))
                self._set_state(RealtimeAgentState.LISTENING)

            elif isinstance(event, InputAudioBufferSpeechStopped):
                pass  # No action needed

            elif isinstance(event, ResponseAudioDelta):
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.ASSISTANT_AUDIO_DELTA,
                    payload={"audio": event.delta_b64, "item_id": event.item_id},
                ))
                self._set_state(RealtimeAgentState.AI_SPEAKING)

            elif isinstance(event, ResponseAudioDone):
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.ASSISTANT_AUDIO_DONE,
                    payload={"item_id": event.item_id},
                ))

            elif isinstance(event, ResponseAudioTranscriptDelta):
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.ASSISTANT_TRANSCRIPT_DELTA,
                    payload={"item_id": event.item_id, "text": event.delta or ""},
                ))

            elif isinstance(event, ResponseAudioTranscriptDone):
                text = event.text or ""
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.ASSISTANT_TRANSCRIPT_DONE,
                    payload={"item_id": event.item_id, "text": text},
                ))
                self._append_event(FrontendEvent(
                    type=EventType.ASSISTANT_TRANSCRIPT_DONE,
                    payload={"item_id": event.item_id, "text": text},
                ))

            elif isinstance(event, ConversationItemInputAudioTranscriptionCompleted):
                text = (event.transcript or "").strip()
                if not text:
                    continue
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.USER_TRANSCRIPT,
                    payload={"item_id": event.item_id, "text": text},
                ))
                self._append_event(FrontendEvent(
                    type=EventType.USER_TRANSCRIPT,
                    payload={"item_id": event.item_id, "text": text},
                ))

            elif isinstance(event, ResponseFunctionCallArgumentsDone):
                await self._on_function_call(
                    event.call_id, event.name, event.arguments
                )

            elif isinstance(event, ResponseDone):
                await self._on_response_done(event)

            elif isinstance(event, RealtimeError):
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.ERROR,
                    payload={"code": event.code, "message": event.message},
                ))
                self._closed = True
                return

    # ── Function Call Handler ────────────────────────────────────────

    async def _on_function_call(
        self, call_id: str, name: str, args_json: str
    ) -> None:
        """Handle function call from realtime provider (fire-and-forget)."""
        if name != "save_real_question":
            logger.warning("Realtime got unexpected tool: %s", name)
            return

        # Fire-and-forget: execute tool without submit_tool_output
        asyncio.create_task(self._execute_save_real_question(args_json))

    async def _execute_save_real_question(self, args_json: str) -> None:
        """Execute save_real_question tool asynchronously."""
        try:
            raw_args = json.loads(args_json)
            tool = self.tools.get("save_real_question")
            if tool:
                ctx = ToolContext(
                    user_id=self.user_id,
                    resume_id=self._resume_id,
                )
                args = tool.args_model(**raw_args)
                result = await tool.fn(args, ctx)
                logger.info("save_real_question executed: %s", result)
        except Exception as e:
            logger.error("save_real_question failed: %s", e)

    # ── Response Done Handler ────────────────────────────────────────

    async def _on_response_done(self, event: ResponseDone) -> None:
        """Handle response.done: update audio usage, check cost cap."""
        usage = event.usage or {}
        audio_in = usage.get("audio_in_tokens") or 0
        audio_out = usage.get("audio_out_tokens") or 0
        self._audio_seconds_used += (audio_in + audio_out) * 0.03

        self._set_state(RealtimeAgentState.LISTENING)

        # Check cost cap
        if self._audio_seconds_used >= self._max_seconds:
            await self._enforce_session_cap()

    async def _enforce_session_cap(self) -> None:
        """Enforce L1 session cost cap."""
        logger.warning(
            "Session %s hit cost cap: %.0fs / %ds",
            self.session_id, self._audio_seconds_used, self._max_seconds,
        )
        if self._realtime_session:
            await self._realtime_session.cancel_response()

        self._append_event(FrontendEvent(
            type=EventType.COST_LIMIT_REACHED,
            payload={
                "reason": "session_minutes_exceeded",
                "limit_minutes": self._max_seconds // 60,
            },
        ))
        self._closed = True

    # ── AgentState Management ────────────────────────────────────────

    def _set_state(self, new_state: RealtimeAgentState) -> None:
        if self._state != new_state and self._state != RealtimeAgentState.CLOSED:
            self._state = new_state

    # ── MidSummary Timer ─────────────────────────────────────────────

    async def _midsummary_loop(
        self, upstream: RealtimeSession, client_ws: object
    ) -> None:
        """Periodic MidSummary injection loop."""
        while not self._closed:
            await asyncio.sleep(self._midsummary_interval)
            if self._closed:
                return

            # Wait for safe inject window
            try:
                await asyncio.wait_for(
                    self._wait_for_safe_inject_window(),
                    timeout=DEFAULT_MIDSUMMARY_INJECT_WINDOW_TIMEOUT,
                )
            except TimeoutError:
                logger.warning("MidSummary: no safe inject window, skipping")
                continue

            # Run subagent
            try:
                summary = await asyncio.wait_for(
                    self._run_midsummary_subagent(),
                    timeout=self._midsummary_timeout,
                )
            except TimeoutError:
                logger.warning("MidSummary subagent timeout, skipping")
                continue

            if summary:
                await upstream.inject_summary(summary)
                self._append_event(FrontendEvent(
                    type=EventType.SYSTEM_CONTEXT_REFRESHED,
                    payload={"summary": summary},
                ))
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.SYSTEM_CONTEXT_REFRESHED,
                    payload={"summary": summary},
                ))

    async def _wait_for_safe_inject_window(self) -> None:
        """Wait until the agent is in LISTENING state (not AI_SPEAKING)."""
        while self._state in (RealtimeAgentState.AI_SPEAKING, RealtimeAgentState.THINKING):
            await asyncio.sleep(0.5)

    async def _run_midsummary_subagent(self) -> str | None:
        """Run the MidSummary subagent to generate a context summary."""
        try:
            agent = self._subagent_provider(self.session_id, self.user_id)
            result_text = ""
            prompt = (
                "请生成对话至今的中段摘要，涵盖已讨论的话题、"
                "用户已回答的关键事实、以及剩余想深入的方向。"
            )
            async for event in agent.run(prompt):
                if event.type == EventType.ASSISTANT_TEXT_DONE:
                    result_text = event.payload.get("text", "")
            return result_text or None
        except Exception as e:
            logger.error("MidSummary subagent error: %s", e)
            return None

    # ── Inactivity Watchdog ──────────────────────────────────────────

    async def _inactivity_watchdog(self, client_ws: object) -> None:
        """Close connection after inactivity timeout."""
        while not self._closed:
            await asyncio.sleep(30)
            if self._closed:
                return

            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_activity_ts
            if self._last_activity_ts > 0 and elapsed > self._inactivity_timeout:
                logger.warning("Inactivity timeout for session %s", self.session_id)
                await self._push_to_client(client_ws, FrontendEvent(
                    type=EventType.STATE_CHANGED,
                    payload={"state": "inactive_timeout"},
                ))
                self._closed = True
                return

    # ── Helpers ──────────────────────────────────────────────────────

    async def _push_to_client(self, client_ws: object, event: FrontendEvent) -> None:
        """Push a FrontendEvent to the client WebSocket."""
        try:
            await client_ws.send_text(event.model_dump_json())
        except Exception as e:
            logger.debug("Failed to push to client: %s", e)

    def _append_event(self, event: FrontendEvent) -> None:
        """Append an event to the session JSONL store."""
        try:
            self.session_store.append_event(self.user_id, self.session_id, event)
        except Exception as e:
            logger.error("Failed to append event to session store: %s", e)
