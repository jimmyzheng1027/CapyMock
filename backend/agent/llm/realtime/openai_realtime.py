"""OpenAI Realtime LLM adapter."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI
from openai.types.realtime import (
    ConversationItemInputAudioTranscriptionCompletedEvent,
    InputAudioBufferCommittedEvent,
    InputAudioBufferSpeechStartedEvent,
    InputAudioBufferSpeechStoppedEvent,
    RateLimitsUpdatedEvent,
    RealtimeErrorEvent,
    RealtimeServerEvent,
    ResponseAudioDeltaEvent,
    ResponseAudioDoneEvent,
    ResponseAudioTranscriptDeltaEvent,
    ResponseAudioTranscriptDoneEvent,
    ResponseDoneEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    SessionCreatedEvent,
    SessionUpdatedEvent,
)

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


class OpenAIRealtimeLLM(BaseRealtimeLLM):
    """OpenAI Realtime LLM provider using the official SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-realtime-preview",
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
        """Create an OpenAI Realtime session."""
        client = AsyncOpenAI(api_key=self._api_key)

        session_config: dict[str, Any] = {
            "instructions": instructions,
            "voice": voice,
            "turn_detection": vad,
            "input_audio_transcription": transcription,
            "modalities": ["text", "audio"],
        }
        if tools:
            session_config["tools"] = tools

        conn_manager = client.realtime.connect(model=self._model)
        conn = await conn_manager.__aenter__()

        # Send session.update to configure
        await conn.send({
            "type": "session.update",
            "session": session_config,
        })

        return OpenAIRealtimeSession(conn, client)


class OpenAIRealtimeSession(RealtimeSession):
    """OpenAI Realtime session wrapping AsyncRealtimeConnection."""

    def __init__(self, conn: Any, client: AsyncOpenAI) -> None:
        self._conn = conn
        self._client = client
        self._closed = False

    def __aiter__(self) -> AsyncIterator[RealtimeUpstreamEvent]:
        return self._event_stream()

    async def _event_stream(self) -> AsyncIterator[RealtimeUpstreamEvent]:
        """Iterate over upstream events, mapping to internal dataclasses."""
        while not self._closed:
            try:
                event: RealtimeServerEvent = await self._conn.recv()
            except Exception:
                if not self._closed:
                    logger.debug("Connection closed or error receiving event")
                return

            mapped = self._map_event(event)
            if mapped is not None:
                yield mapped

    def _map_event(self, event: RealtimeServerEvent) -> RealtimeUpstreamEvent | None:
        """Map an OpenAI typed event to our internal dataclass."""
        if isinstance(event, SessionCreatedEvent):
            sid = event.session.id if hasattr(event.session, "id") else ""
            return SessionCreated(session_id=sid)

        if isinstance(event, SessionUpdatedEvent):
            return SessionUpdated()

        if isinstance(event, InputAudioBufferSpeechStartedEvent):
            return InputAudioBufferSpeechStarted(item_id=event.item_id or "")

        if isinstance(event, InputAudioBufferSpeechStoppedEvent):
            return InputAudioBufferSpeechStopped(item_id=event.item_id or "")

        if isinstance(event, InputAudioBufferCommittedEvent):
            return InputAudioBufferCommitted(item_id=event.item_id or "")

        if isinstance(event, ResponseAudioDeltaEvent):
            return ResponseAudioDelta(item_id=event.item_id, delta_b64=event.delta)

        if isinstance(event, ResponseAudioDoneEvent):
            return ResponseAudioDone(item_id=event.item_id)

        if isinstance(event, ResponseAudioTranscriptDeltaEvent):
            return ResponseAudioTranscriptDelta(item_id=event.item_id, delta=event.delta or "")

        if isinstance(event, ResponseAudioTranscriptDoneEvent):
            return ResponseAudioTranscriptDone(
                item_id=event.item_id, text=event.transcript or ""
            )

        if isinstance(event, ResponseFunctionCallArgumentsDoneEvent):
            return ResponseFunctionCallArgumentsDone(
                call_id=event.call_id,
                name=event.name,
                arguments=event.arguments,
            )

        if isinstance(event, ConversationItemInputAudioTranscriptionCompletedEvent):
            return ConversationItemInputAudioTranscriptionCompleted(
                item_id=event.item_id, transcript=event.transcript
            )

        if isinstance(event, ResponseDoneEvent):
            usage = {}
            if event.response and event.response.usage:
                u = event.response.usage
                usage = {
                    "input_tokens": getattr(u, "input_tokens", 0) or 0,
                    "output_tokens": getattr(u, "output_tokens", 0) or 0,
                    "total_tokens": getattr(u, "total_tokens", 0) or 0,
                }
                # Extract audio-specific tokens if available
                if hasattr(u, "input_token_details"):
                    details = u.input_token_details
                    usage["audio_in_tokens"] = getattr(details, "audio_tokens", 0) or 0
                    usage["cached_tokens"] = getattr(details, "cached_tokens", 0) or 0
                if hasattr(u, "output_token_details"):
                    details = u.output_token_details
                    usage["audio_out_tokens"] = getattr(details, "audio_tokens", 0) or 0
            return ResponseDone(
                response_id=event.response.id if event.response else "",
                usage=usage,
            )

        if isinstance(event, RateLimitsUpdatedEvent):
            if event.rate_limits:
                rl = event.rate_limits[0] if event.rate_limits else None
                if rl:
                    return RateLimit(
                        name=getattr(rl, "name", ""),
                        remaining=getattr(rl, "remaining", 0) or 0,
                        reset_ms=getattr(rl, "reset_ms", 0) or 0,
                    )
            return RateLimit()

        if isinstance(event, RealtimeErrorEvent):
            return RealtimeError(
                code=event.error.type if event.error else "",
                message=event.error.message if event.error else str(event),
            )

        # Unknown event type - log and skip
        logger.debug("Unmapped OpenAI realtime event type: %s", type(event).__name__)
        return None

    async def send_audio(self, pcm16_b64: str) -> None:
        await self._conn.send({
            "type": "input_audio_buffer.append",
            "audio": pcm16_b64,
        })

    async def commit_audio(self) -> None:
        await self._conn.send({"type": "input_audio_buffer.commit"})

    async def create_response(self) -> None:
        await self._conn.send({"type": "response.create"})

    async def cancel_response(self) -> None:
        await self._conn.send({"type": "response.cancel"})

    async def inject_summary(self, text: str) -> None:
        await self._conn.send({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "system",
                "content": [{"type": "input_text", "text": text}],
            },
        })

    async def inject_message(self, role: str, text: str) -> None:
        await self._conn.send({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": role,
                "content": [{"type": "input_text", "text": text}],
            },
        })

    async def update_session(self, **fields: object) -> None:
        await self._conn.send({
            "type": "session.update",
            "session": fields,
        })

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            try:
                await self._conn.close()
            except Exception:
                pass
