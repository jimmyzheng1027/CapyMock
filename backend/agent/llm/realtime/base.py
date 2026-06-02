"""Abstract base for Realtime LLM sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from types import TracebackType

from agent.llm.realtime.events import RealtimeUpstreamEvent


class RealtimeSession(ABC):
    """Abstract async context manager for a realtime LLM session.

    Supports async iteration over upstream events and outbound verbs.
    """

    async def __aenter__(self) -> RealtimeSession:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[RealtimeUpstreamEvent]:
        """Iterate over upstream events."""
        ...

    @abstractmethod
    async def send_audio(self, pcm16_b64: str) -> None:
        """Send a base64-encoded PCM16 audio chunk to the provider."""
        ...

    @abstractmethod
    async def commit_audio(self) -> None:
        """Commit the current audio buffer (manual VAD mode only)."""
        ...

    @abstractmethod
    async def create_response(self) -> None:
        """Request the provider to generate a response (manual VAD mode)."""
        ...

    @abstractmethod
    async def cancel_response(self) -> None:
        """Cancel the current in-progress response (barge-in)."""
        ...

    @abstractmethod
    async def inject_summary(self, text: str) -> None:
        """Inject a system text item into the conversation (MidSummary)."""
        ...

    @abstractmethod
    async def inject_message(self, role: str, text: str) -> None:
        """Inject a user/assistant text message into the conversation history."""
        ...

    @abstractmethod
    async def update_session(self, **fields: object) -> None:
        """Update session configuration on the provider side."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the connection to the provider."""
        ...
