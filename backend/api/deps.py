from __future__ import annotations

from fastapi import Request

from agent.factory import AgentFactory
from storage.session.store import SessionStore
from tracer.base import Tracer


def get_agent_factory(request: Request) -> AgentFactory:
    """Get agent factory from app state."""
    return request.app.state.agent_factory


def get_session_store(request: Request) -> SessionStore:
    """Get session store from app state."""
    return request.app.state.session_store


def get_tracer(request: Request) -> Tracer:
    """Get tracer from app state."""
    return request.app.state.tracer
