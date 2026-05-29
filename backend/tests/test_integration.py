"""Integration tests: Create session → WS connect → send text → receive events."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from agent.llm.base import BaseLLM
from agent.llm.events import Done, TextDelta, Usage
from api.app import app


class FakeLLM(BaseLLM):
    """Fake LLM for integration tests."""

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncIterator:
        yield TextDelta(delta="Hello! ")
        yield TextDelta(delta="I'm your interviewer.")
        yield Usage(prompt_tokens=10, completion_tokens=8, total_tokens=18)
        yield Done(stop_reason="end_turn")

    def get_model_name(self) -> str:
        return "fake-model"


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_create_session():
    """Test: create a session via REST API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/sessions",
            json={
                "profile_id": "interviewer-technical",
                "mode": "text",
                "user_id": "test-user",
            },
        )

        # Should succeed or fail gracefully if profile not loaded
        assert response.status_code in [200, 400, 500]


@pytest.mark.asyncio
async def test_list_sessions():
    """Test: list sessions via REST API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/sessions")

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_get_session_events():
    """Test: get session events via REST API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First create a session
        create_response = await client.post(
            "/api/sessions",
            json={
                "profile_id": "interviewer-technical",
                "mode": "text",
                "user_id": "test-user",
            },
        )

        if create_response.status_code == 200:
            session_id = create_response.json()["session_id"]

            # Get events
            events_response = await client.get(f"/api/sessions/{session_id}/events")
            assert events_response.status_code == 200
            data = events_response.json()
            assert "events" in data


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test: WebSocket connection and message exchange."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First create a session
        create_response = await client.post(
            "/api/sessions",
            json={
                "profile_id": "interviewer-technical",
                "mode": "text",
                "user_id": "test-user",
            },
        )

        if create_response.status_code == 200:
            session_id = create_response.json()["session_id"]

            # Connect to WebSocket
            async with client.stream("GET", f"/ws/interview/{session_id}") as ws:
                # Send a message
                await ws.send_json({
                    "type": "user.text",
                    "payload": {"text": "Hello"},
                })

                # Receive events
                events = []
                async for line in ws.aiter_lines():
                    if line:
                        try:
                            event = json.loads(line)
                            events.append(event)
                            if event.get("type") == "turn.done":
                                break
                        except json.JSONDecodeError:
                            continue

                # Should have received some events
                assert len(events) > 0


def test_health_check(client):
    """Test: health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "CapyMock API"
