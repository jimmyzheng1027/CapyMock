"""Realtime upstream event dataclasses.

Naming is 1:1 aligned with the wire protocol used by both OpenAI Realtime API
and DashScope Qwen-Omni Realtime API (DashScope forked the OpenAI protocol).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RealtimeUpstreamEvent:
    """Base class for all realtime upstream events."""

    pass


@dataclass(frozen=True)
class SessionCreated(RealtimeUpstreamEvent):
    session_id: str = ""


@dataclass(frozen=True)
class SessionUpdated(RealtimeUpstreamEvent):
    pass


@dataclass(frozen=True)
class InputAudioBufferSpeechStarted(RealtimeUpstreamEvent):
    item_id: str = ""


@dataclass(frozen=True)
class InputAudioBufferSpeechStopped(RealtimeUpstreamEvent):
    item_id: str = ""


@dataclass(frozen=True)
class InputAudioBufferCommitted(RealtimeUpstreamEvent):
    item_id: str = ""


@dataclass(frozen=True)
class ResponseAudioDelta(RealtimeUpstreamEvent):
    item_id: str = ""
    delta_b64: str = ""


@dataclass(frozen=True)
class ResponseAudioDone(RealtimeUpstreamEvent):
    item_id: str = ""


@dataclass(frozen=True)
class ResponseAudioTranscriptDelta(RealtimeUpstreamEvent):
    item_id: str = ""
    delta: str = ""


@dataclass(frozen=True)
class ResponseAudioTranscriptDone(RealtimeUpstreamEvent):
    item_id: str = ""
    text: str = ""


@dataclass(frozen=True)
class ResponseFunctionCallArgumentsDone(RealtimeUpstreamEvent):
    call_id: str = ""
    name: str = ""
    arguments: str = ""


@dataclass(frozen=True)
class ConversationItemInputAudioTranscriptionCompleted(RealtimeUpstreamEvent):
    item_id: str = ""
    transcript: str = ""


@dataclass(frozen=True)
class ResponseDone(RealtimeUpstreamEvent):
    response_id: str = ""
    usage: dict = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.usage is None:
            object.__setattr__(self, "usage", {})


@dataclass(frozen=True)
class RateLimit(RealtimeUpstreamEvent):
    name: str = ""
    remaining: int = 0
    reset_ms: int = 0


@dataclass(frozen=True)
class RealtimeError(RealtimeUpstreamEvent):
    code: str = ""
    message: str = ""
