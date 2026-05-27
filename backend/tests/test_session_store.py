"""Tests for SessionStore: append-only, persistence filter, replay order."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.schemas import EventType, FrontendEvent
from storage.session.store import SessionStore


class TestSessionStore:
    """Test SessionStore behavior."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for test sessions."""
        return tmp_path / "sessions"

    @pytest.fixture
    def store(self, temp_dir: Path) -> SessionStore:
        """Create a SessionStore with a temporary directory."""
        return SessionStore(root_dir=str(temp_dir))

    def test_create_session(self, store: SessionStore, temp_dir: Path) -> None:
        """Test: creating a new session writes session.started event."""
        path = store.create("user1", "session1", "profile1")

        assert path.exists()
        events = store.read_events("user1", "session1")
        assert len(events) == 1
        assert events[0].type == EventType.SESSION_STARTED
        assert events[0].payload["session_id"] == "session1"

    def test_append_event_persisted(self, store: SessionStore) -> None:
        """Test: persisted events are written to JSONL."""
        store.create("user1", "session1", "profile1")

        event = FrontendEvent(
            type=EventType.USER_TEXT,
            payload={"text": "Hello"},
        )
        store.append_event("user1", "session1", event)

        events = store.read_events("user1", "session1")
        assert len(events) == 2
        assert events[1].type == EventType.USER_TEXT

    def test_append_event_filtered(self, store: SessionStore) -> None:
        """Test: high-frequency events are NOT persisted."""
        store.create("user1", "session1", "profile1")

        # These should be filtered out
        delta_event = FrontendEvent(
            type=EventType.ASSISTANT_TEXT_DELTA,
            payload={"delta": "Hello"},
        )
        store.append_event("user1", "session1", delta_event)

        thinking_event = FrontendEvent(
            type=EventType.ASSISTANT_THINKING_DELTA,
            payload={"delta": "thinking..."},
        )
        store.append_event("user1", "session1", thinking_event)

        state_event = FrontendEvent(
            type=EventType.STATE_CHANGED,
            payload={"state": "thinking"},
        )
        store.append_event("user1", "session1", state_event)

        events = store.read_events("user1", "session1")
        # Only session.started should be persisted
        assert len(events) == 1

    def test_read_events_order(self, store: SessionStore) -> None:
        """Test: events are returned in chronological order."""
        store.create("user1", "session1", "profile1")

        # Add multiple events
        for i in range(5):
            event = FrontendEvent(
                type=EventType.USER_TEXT,
                payload={"text": f"Message {i}"},
            )
            store.append_event("user1", "session1", event)

        events = store.read_events("user1", "session1")
        assert len(events) == 6  # 5 user.text + 1 session.started
        for i in range(5):
            assert events[i + 1].payload["text"] == f"Message {i}"

    def test_read_nonexistent_session(self, store: SessionStore) -> None:
        """Test: reading a non-existent session returns empty list."""
        events = store.read_events("user1", "nonexistent")
        assert events == []

    def test_directory_structure(self, store: SessionStore, temp_dir: Path) -> None:
        """Test: sessions are stored in user_id subdirectories."""
        store.create("user1", "session1", "profile1")
        store.create("user2", "session2", "profile2")

        assert (temp_dir / "user1" / "session1.jsonl").exists()
        assert (temp_dir / "user2" / "session2.jsonl").exists()

    def test_multiple_sessions_per_user(self, store: SessionStore) -> None:
        """Test: multiple sessions for the same user are separate files."""
        store.create("user1", "session1", "profile1")
        store.create("user1", "session2", "profile2")

        events1 = store.read_events("user1", "session1")
        events2 = store.read_events("user1", "session2")

        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0].payload["session_id"] == "session1"
        assert events2[0].payload["session_id"] == "session2"

    def test_persistence_filter_all_event_types(self, store: SessionStore) -> None:
        """Test: persistence filter correctly handles all event types."""
        store.create("user1", "session1", "profile1")

        # Events that should be persisted
        persist_types = [
            EventType.SESSION_STARTED,
            EventType.SESSION_COMPACTED,
            EventType.ASSISTANT_TEXT_DONE,
            EventType.TOOL_CALL_START,
            EventType.TOOL_CALL_END,
            EventType.TOOL_RESULT,
            EventType.USER_TEXT,
            EventType.USER_TRANSCRIPT,
            EventType.TURN_DONE,
            EventType.ERROR,
            EventType.CONTROL_INTERRUPT,
        ]

        # Events that should NOT be persisted
        skip_types = [
            EventType.ASSISTANT_TEXT_DELTA,
            EventType.ASSISTANT_THINKING_DELTA,
            EventType.STATE_CHANGED,
        ]

        # Append all persist types
        for event_type in persist_types:
            event = FrontendEvent(type=event_type, payload={})
            store.append_event("user1", "session1", event)

        # Append all skip types
        for event_type in skip_types:
            event = FrontendEvent(type=event_type, payload={})
            store.append_event("user1", "session1", event)

        events = store.read_events("user1", "session1")
        # Should have session.started + persist_types
        assert len(events) == len(persist_types) + 1
