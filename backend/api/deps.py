from __future__ import annotations

from fastapi import Request

from agent.factory import AgentFactory
from storage.session.store import SessionStore


def get_agent_factory(request: Request) -> AgentFactory:
    """Get agent factory from app state."""
    return request.app.state.agent_factory


def get_session_store(request: Request) -> SessionStore:
    """Get session store from app state."""
    return request.app.state.session_store
