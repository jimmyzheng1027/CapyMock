from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, ValidationError

from agent.factory import AgentFactory, RealtimeNotConfigured
from agent.loop import CancelToken
from api.chat import _load_session_context
from api.schemas import EventType, FrontendEvent
from storage.session.store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter()


async def _ws_send_error(websocket: WebSocket, code: str, message: str) -> None:
    """Send an error event and close the websocket."""
    try:
        await websocket.send_text(
            FrontendEvent(
                type=EventType.ERROR,
                payload={"code": code, "message": message},
            ).model_dump_json()
        )
        await websocket.close()
    except Exception:
        pass


class WSMessage(BaseModel):
    """WebSocket message from client."""
    type: str
    payload: dict[str, Any] = {}


@router.websocket("/ws/voice/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for voice mode.

    Query params: profile (default: interviewer-technical), user_id (default: default), mode (default: voice)

    For text mode, use SSE endpoints:
    - POST /api/sessions/{id}/messages
    - GET /api/sessions/{id}/stream
    """
    await websocket.accept()

    agent_factory: AgentFactory = websocket.app.state.agent_factory
    session_store: SessionStore = websocket.app.state.session_store

    profile_id = websocket.query_params.get("profile", "interviewer-technical")
    user_id = websocket.query_params.get("user_id", "default")
    mode = websocket.query_params.get("mode", "voice")

    if mode == "voice":
        await _handle_voice_mode(websocket, agent_factory, session_store, session_id, profile_id, user_id)
    else:
        await _handle_text_mode(websocket, agent_factory, session_store, session_id, profile_id, user_id, mode)


async def _handle_voice_mode(
    websocket: WebSocket,
    agent_factory: AgentFactory,
    session_store: SessionStore,
    session_id: str,
    profile_id: str,
    user_id: str,
) -> None:
    """Handle voice mode WebSocket connection."""
    # Load session context
    try:
        ctx = await _load_session_context(session_id)
    except HTTPException as e:
        await _ws_send_error(websocket, "session_not_found", str(e.detail))
        return

    profile_id = ctx["profile_id"]
    user_id = ctx["user_id"]
    resume_content = ctx.get("resume_content") or ""
    github_repos = ctx.get("github_repos") or []
    resume_id = ctx.get("resume_id") or ""

    capy_note = ""
    if resume_id:
        from config.settings import settings
        from storage.memory.store import MemoryStore

        memory_store = MemoryStore(root_dir=settings.MEMORY_ROOT)
        capy_note = memory_store.read_capy_note(user_id, resume_id) or ""

    # Create realtime agent
    try:
        agent = agent_factory.create_realtime_agent(
            profile_id=profile_id,
            session_id=session_id,
            user_id=user_id,
            resume_content=resume_content,
            github_repos=github_repos,
            resume_id=resume_id or "",
            capy_note=capy_note,
        )
    except RealtimeNotConfigured as e:
        await _ws_send_error(websocket, "realtime_not_configured", str(e))
        return
    except Exception as e:
        await _ws_send_error(websocket, "agent_creation_failed", str(e))
        return

    # Run agent
    try:
        await agent.run(websocket)
    except WebSocketDisconnect:
        logger.info("Voice client disconnected from session %s", session_id)
    except Exception as e:
        logger.error("Voice agent error: %s", e, exc_info=True)
        code = "realtime_not_configured" if isinstance(e, RealtimeNotConfigured) else "agent_error"
        await _ws_send_error(websocket, code, str(e))


async def _handle_text_mode(
    websocket: WebSocket,
    agent_factory: AgentFactory,
    session_store: SessionStore,
    session_id: str,
    profile_id: str,
    user_id: str,
    mode: str,
) -> None:
    """Handle text mode WebSocket connection (backward-compat)."""
    cancel_token = CancelToken()
    agent = None

    try:
        # Replay existing events
        existing_events = session_store.read_events(user_id, session_id)
        for event in existing_events:
            await websocket.send_text(event.model_dump_json())

        # Create text agent
        try:
            agent = agent_factory.create_text_agent(
                profile_id=profile_id,
                session_id=session_id,
                user_id=user_id,
            )
            agent.cancel_token = cancel_token
        except Exception as e:
            await websocket.send_text(
                FrontendEvent(
                    type=EventType.ERROR,
                    payload={"code": "agent_creation_failed", "message": str(e)},
                ).model_dump_json()
            )
            await websocket.close()
            return

        # Main message loop
        while True:
            try:
                data = await websocket.receive_text()
                try:
                    msg = WSMessage.model_validate_json(data)
                except ValidationError:
                    logger.warning(f"Invalid message format: {data}")
                    continue

                if msg.type == "user.text":
                    user_text = msg.payload.get("text", "")
                    if not user_text:
                        continue

                    user_event = FrontendEvent(
                        type=EventType.USER_TEXT,
                        payload={"text": user_text},
                    )
                    await websocket.send_text(user_event.model_dump_json())
                    session_store.append_event(user_id, session_id, user_event)

                    async for event in agent.run(user_text):
                        await websocket.send_text(event.model_dump_json())
                        if session_store._should_persist(event):
                            session_store.append_event(user_id, session_id, event)

                elif msg.type == "control.interrupt":
                    if agent:
                        agent.interrupt()
                else:
                    logger.info(f"Unknown message type: {msg.type}")

            except WebSocketDisconnect:
                logger.info(f"Client disconnected from session {session_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_text(
                    FrontendEvent(
                        type=EventType.ERROR,
                        payload={"code": "processing_error", "message": str(e)},
                    ).model_dump_json()
                )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if cancel_token:
            cancel_token.cancel()
