"""DashScope Qwen-Omni Realtime LLM adapter."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from agent.llm.base import BaseRealtimeLLM
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

logger = logging.getLogger(__name__)

try:
    from dashscope.audio.qwen_omni.omni_realtime import OmniRealtimeCallback
except ImportError:  # pragma: no cover
    class OmniRealtimeCallback:  # type: ignore[no-redef]
        """Fallback when dashscope is not installed."""

        def on_open(self) -> None:
            pass

        def on_close(self, close_status_code: Any, close_msg: Any) -> None:
            pass

        def on_event(self, message: str) -> None:
            pass


class DashScopeRealtimeLLM(BaseRealtimeLLM):
    """DashScope Qwen-Omni Realtime LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen3.5-omni-plus-realtime",
        temperature: float = 0.7,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._temperature = temperature

    async def stream(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> AsyncIterator[Any]:
        """Not used for realtime providers."""
        raise NotImplementedError("Realtime providers do not support stream()")
        yield  # make it an async generator

    def get_model_name(self) -> str:
        return self._model

    async def realtime_connect(
        self,
        instructions: str,
        tools: list[dict],
        voice: str,
        vad: dict,
        transcription: dict,
    ) -> RealtimeSession:
        """Create a DashScope Qwen-Omni Realtime session."""
        if not self._api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY 未配置，请在 backend/.env 中设置 DASHSCOPE_API_KEY"
            )

        import dashscope
        from dashscope.audio.qwen_omni import OmniRealtimeConversation
        from dashscope.audio.qwen_omni.omni_realtime import MultiModality, OmniRealtimeCallback

        dashscope.api_key = self._api_key

        callback = _DashScopeCallback()
        callback.set_loop(asyncio.get_running_loop())

        conv = OmniRealtimeConversation(
            model=self._model,
            callback=callback,
            api_key=self._api_key,
        )
        await asyncio.to_thread(conv.connect)

        session = DashScopeRealtimeSession(conv, callback)

        # Configure session
        vad_mode = vad.get("type", "server_vad")
        enable_vad = vad_mode != "none"
        vad_type_map = {
            "semantic_vad": "server_vad",
            "semantic": "server_vad",
            "server_vad": "server_vad",
            "server": "server_vad",
        }
        vad_type = vad_type_map.get(vad_mode, "server_vad")

        from dashscope.audio.qwen_omni.omni_realtime import MultiModality

        transcription_model = transcription.get("model") or None
        if transcription_model == "whisper":
            transcription_model = None  # DashScope uses its own built-in model

        await session.update_session(
            output_modalities=[MultiModality.TEXT, MultiModality.AUDIO],
            voice=voice,
            enable_turn_detection=enable_vad,
            turn_detection_type=vad_type,
            turn_detection_threshold=vad.get("threshold", 0.5),
            enable_input_audio_transcription=transcription.get("enabled", True),
            input_audio_transcription_model=transcription_model,
        )

        # Send initial instructions via session.update
        if instructions:
            conv.send_raw(json.dumps({
                "type": "session.update",
                "session": {"instructions": instructions},
            }))

        return session


class _DashScopeCallback(OmniRealtimeCallback):
    """Callback that bridges DashScope's background-thread events to asyncio.Queue."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[dict | None] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def on_event(self, message: Any) -> None:
        if isinstance(message, dict):
            data = message
        elif isinstance(message, str):
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.warning("DashScope callback received non-JSON message: %s", message[:200])
                return
        else:
            logger.warning("DashScope callback received unexpected payload type: %s", type(message).__name__)
            return

        if self._loop is not None:
            self._loop.call_soon_threadsafe(self.queue.put_nowait, data)
        else:
            # Fallback: try to get running loop
            try:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self.queue.put_nowait, data)
            except RuntimeError:
                logger.warning("No event loop available to dispatch DashScope event")

    def on_open(self) -> None:
        logger.debug("DashScope realtime connection opened")

    def on_close(self, close_status_code: Any, close_msg: Any) -> None:
        logger.debug("DashScope realtime connection closed: %s %s", close_status_code, close_msg)
        # Signal end of stream
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self.queue.put_nowait, None)


def _extract_item_id(data: dict) -> str:
    return str(data.get("item_id") or (data.get("item") or {}).get("id") or "")


def _extract_transcript_text(data: dict) -> str:
    """Read user transcript from DashScope event (top-level or nested item)."""
    transcript = data.get("transcript")
    if isinstance(transcript, str) and transcript.strip():
        return transcript.strip()

    item = data.get("item")
    if isinstance(item, dict):
        nested = item.get("transcript")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
        for part in item.get("content") or []:
            if isinstance(part, dict):
                part_text = part.get("transcript") or part.get("text")
                if isinstance(part_text, str) and part_text.strip():
                    return part_text.strip()

    return ""


class DashScopeRealtimeSession(RealtimeSession):
    """DashScope Realtime session wrapping OmniRealtimeConversation."""

    def __init__(self, conv: Any, callback: _DashScopeCallback) -> None:
        self._conv = conv
        self._callback = callback
        self._closed = False
        self._transcription_buffers: dict[str, str] = {}

    async def __aenter__(self) -> DashScopeRealtimeSession:
        self._callback.set_loop(asyncio.get_running_loop())
        return self

    def __aiter__(self) -> AsyncIterator[RealtimeUpstreamEvent]:
        return self._event_stream()

    async def _event_stream(self) -> AsyncIterator[RealtimeUpstreamEvent]:
        """Iterate over upstream events from the callback queue."""
        while not self._closed:
            try:
                data = await asyncio.wait_for(
                    self._callback.queue.get(), timeout=1.0
                )
            except TimeoutError:
                continue

            if data is None:
                # Connection closed signal
                return

            mapped = self._map_event(data)
            if mapped is not None:
                yield mapped

    def _map_event(self, data: dict) -> RealtimeUpstreamEvent | None:
        """Map a DashScope event dict to our internal dataclass."""
        event_type = data.get("type", "")

        if event_type == "session.created":
            session_id = data.get("session", {}).get("id", "")
            return SessionCreated(session_id=session_id)

        if event_type == "session.updated":
            return SessionUpdated()

        if event_type == "input_audio_buffer.speech_started":
            return InputAudioBufferSpeechStarted(
                item_id=data.get("item_id", "")
            )

        if event_type == "input_audio_buffer.speech_stopped":
            return InputAudioBufferSpeechStopped(
                item_id=data.get("item_id", "")
            )

        if event_type == "input_audio_buffer.committed":
            return InputAudioBufferCommitted(
                item_id=data.get("item_id", "")
            )

        if event_type == "response.audio.delta":
            return ResponseAudioDelta(
                item_id=data.get("item_id") or "",
                delta_b64=data.get("delta") or "",
            )

        if event_type == "response.audio.done":
            return ResponseAudioDone(
                item_id=data.get("item_id", ""),
            )

        if event_type == "response.audio_transcript.delta":
            return ResponseAudioTranscriptDelta(
                item_id=data.get("item_id") or "",
                delta=data.get("delta") or "",
            )

        if event_type == "response.audio_transcript.done":
            return ResponseAudioTranscriptDone(
                item_id=data.get("item_id") or "",
                text=data.get("transcript") or "",
            )

        if event_type == "response.function_call_arguments.done":
            return ResponseFunctionCallArgumentsDone(
                call_id=data.get("call_id", ""),
                name=data.get("name", ""),
                arguments=data.get("arguments", ""),
            )

        if event_type in (
            "conversation.item.input_audio_transcription.delta",
            "conversation.item.input_audio_transcription.text",
        ):
            item_id = _extract_item_id(data)
            if item_id:
                confirmed = data.get("text") or ""
                stash = data.get("stash") or data.get("transcript") or ""
                partial = (confirmed + stash).strip()
                if partial:
                    self._transcription_buffers[item_id] = partial
            return None

        if event_type == "conversation.item.input_audio_transcription.completed":
            item_id = _extract_item_id(data)
            transcript = _extract_transcript_text(data)
            if not transcript and item_id:
                transcript = self._transcription_buffers.pop(item_id, "")
            elif item_id:
                self._transcription_buffers.pop(item_id, None)
            if not transcript:
                logger.debug(
                    "DashScope user transcription completed with empty text (item_id=%s)",
                    item_id,
                )
                return None
            return ConversationItemInputAudioTranscriptionCompleted(
                item_id=item_id,
                transcript=transcript,
            )

        if event_type == "response.done":
            response = data.get("response", {})
            usage = response.get("usage", {})
            return ResponseDone(
                response_id=response.get("id", ""),
                usage=usage,
            )

        if event_type == "rate_limits.updated":
            rl_list = data.get("rate_limits", [])
            if rl_list:
                rl = rl_list[0]
                return RateLimit(
                    name=rl.get("name", ""),
                    remaining=rl.get("remaining", 0),
                    reset_ms=rl.get("reset_ms", 0),
                )
            return RateLimit()

        if event_type == "error":
            error = data.get("error", {})
            return RealtimeError(
                code=error.get("type", data.get("type", "")),
                message=error.get("message", str(data)),
            )

        # Unknown event type - log and skip
        logger.debug("Unmapped DashScope realtime event type: %s", event_type)
        return None

    async def send_audio(self, pcm16_b64: str) -> None:
        self._conv.append_audio(pcm16_b64)

    async def commit_audio(self) -> None:
        self._conv.commit()

    async def create_response(self) -> None:
        self._conv.create_response()

    async def cancel_response(self) -> None:
        self._conv.cancel_response()

    async def inject_summary(self, text: str) -> None:
        self._conv.create_item({
            "type": "message",
            "role": "system",
            "content": [{"type": "input_text", "text": text}],
        })

    async def inject_message(self, role: str, text: str) -> None:
        self._conv.create_item({
            "type": "message",
            "role": role,
            "content": [{"type": "input_text", "text": text}],
        })

    async def update_session(self, **fields: object) -> None:
        self._conv.update_session(**fields)

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            try:
                self._conv.close()
            except Exception:
                pass
