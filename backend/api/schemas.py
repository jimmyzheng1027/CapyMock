from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Frontend event types with dot notation."""

    # Session events
    SESSION_STARTED = "session.started"
    SESSION_COMPACTED = "session.compacted"

    # Assistant events
    ASSISTANT_TEXT_DELTA = "assistant.text.delta"
    ASSISTANT_TEXT_DONE = "assistant.text.done"
    ASSISTANT_THINKING_DELTA = "assistant.thinking.delta"

    # Tool events
    TOOL_CALL_START = "tool.call.start"
    TOOL_CALL_END = "tool.call.end"
    TOOL_RESULT = "tool.result"

    # User events
    USER_TEXT = "user.text"
    USER_TRANSCRIPT = "user.transcript"

    # State events
    STATE_CHANGED = "state.changed"

    # Control events
    TURN_DONE = "turn.done"
    ERROR = "error"
    CONTROL_INTERRUPT = "control.interrupt"


class FrontendEvent(BaseModel):
    """Event sent to the frontend via WebSocket or stored in JSONL."""

    type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    ts: float | None = None

    class Config:
        use_enum_values = True


# Request/Response schemas for REST API

class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    profile_id: str
    mode: str = "text"
    resume_id: str | None = None
    github_repo_ids: list[str] = Field(default_factory=list)
    user_id: str = "default"


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session_id: str
    profile_id: str
    created_at: str


class SessionMetadata(BaseModel):
    """Session metadata for list/detail endpoints."""

    id: str
    user_id: str
    profile_id: str
    status: str  # active, paused, completed, abandoned
    mode: str
    created_at: str
    updated_at: str
    last_event_ts: str | None = None
    event_count: int = 0
    turn_count: int = 0
    summary: dict | None = None


class SessionListResponse(BaseModel):
    """Response for session list endpoint."""

    sessions: list[SessionMetadata]
    total: int


class FinalizeRequest(BaseModel):
    """Request to finalize a session."""
    pass


class FinalizeResponse(BaseModel):
    """Response after finalizing a session."""

    session_id: str
    summary: dict
