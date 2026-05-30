from __future__ import annotations

from datetime import datetime
from pathlib import Path

from api.schemas import EventType, FrontendEvent
from config.settings import settings


class SessionStore:
    """JSONL-based session event storage."""

    def __init__(self, root_dir: str | None = None) -> None:
        self.root_dir = Path(root_dir or settings.JSONL_ROOT)

    def _get_session_path(self, user_id: str, session_id: str) -> Path:
        """Get the JSONL file path for a session."""
        return self.root_dir / user_id / f"{session_id}.jsonl"

    def create(self, user_id: str, session_id: str, profile_id: str, clear_existing: bool = False) -> Path:
        """Create a new session and write the session.started event.

        Args:
            clear_existing: If True, delete existing JSONL file before writing.
                           Use this for re-analysis to avoid stale history.
        """
        session_path = self._get_session_path(user_id, session_id)
        session_path.parent.mkdir(parents=True, exist_ok=True)

        if clear_existing and session_path.exists():
            session_path.unlink()

        # Write session.started event
        event = FrontendEvent(
            type=EventType.SESSION_STARTED,
            payload={
                "session_id": session_id,
                "profile_id": profile_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
            },
            ts=datetime.utcnow().timestamp(),
        )

        self._append_event(session_path, event)

        return session_path

    def append_event(self, user_id: str, session_id: str, event: FrontendEvent) -> None:
        """Append an event to the session's JSONL file."""
        session_path = self._get_session_path(user_id, session_id)
        self._append_event(session_path, event)

    def _append_event(self, path: Path, event: FrontendEvent) -> None:
        """Append an event to a JSONL file."""
        # Apply persistence filter
        if not self._should_persist(event):
            return

        with open(path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def read_events(self, user_id: str, session_id: str) -> list[FrontendEvent]:
        """Read all events from a session's JSONL file."""
        session_path = self._get_session_path(user_id, session_id)

        if not session_path.exists():
            return []

        events = []
        with open(session_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = FrontendEvent.model_validate_json(line)
                        events.append(event)
                    except Exception:
                        # Skip malformed lines
                        continue

        return events

    def update_metadata(
        self,
        user_id: str,
        session_id: str,
        last_event_ts: datetime | None = None,
        event_count: int | None = None,
    ) -> None:
        """Update session metadata (to be called by SessionService)."""
        # This is a placeholder - actual implementation will update SQLite
        pass

    def _should_persist(self, event: FrontendEvent) -> bool:
        """Determine if an event should be persisted to JSONL.

        High-frequency events are only pushed, not persisted.
        Turn-level and decision-point events are always persisted.
        """
        # Events that should NOT be persisted (high-frequency)
        skip_types = {
            EventType.ASSISTANT_TEXT_DELTA,
            EventType.ASSISTANT_THINKING_DELTA,
            EventType.STATE_CHANGED,
        }

        if event.type in skip_types:
            return False

        # All other events are persisted
        return True
