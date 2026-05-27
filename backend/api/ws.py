from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from agent.factory import AgentFactory
from agent.loop import CancelToken
from api.schemas import EventType, FrontendEvent
from storage.session.store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter()


class WSMessage(BaseModel):
    """WebSocket message from client."""
    type: str
    payload: dict[str, Any] = {}


@router.websocket("/ws/voice/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for voice mode (future use).

    This endpoint is reserved for Realtime voice mode.
    For text mode, use SSE endpoints:
    - POST /api/sessions/{id}/messages
    - GET /api/sessions/{id}/stream
    - POST /api/sessions/{id}/interrupt

    Protocol (voice mode):
    - Client sends: audio chunks, control messages
    - Server sends: audio chunks, FrontendEvent JSON frames
    """
    await websocket.accept()

    # Get dependencies from app state
    agent_factory: AgentFactory = websocket.app.state.agent_factory
    session_store: SessionStore = websocket.app.state.session_store
    tracer = websocket.app.state.tracer

    # Get profile and user_id from query params or defaults
    profile_id = websocket.query_params.get("profile", "interviewer-technical")
    user_id = websocket.query_params.get("user_id", "default")
    mode = websocket.query_params.get("mode", "text")

    # Create cancel token for this connection
    cancel_token = CancelToken()
    agent = None

    try:
        # Check if session exists and replay events
        existing_events = session_store.read_events(user_id, session_id)
        if existing_events:
            # Replay existing events to client
            for event in existing_events:
                await websocket.send_text(event.model_dump_json())

        # Create agent
        try:
            agent = agent_factory.create(
                profile_id=profile_id,
                session_id=session_id,
                mode=mode,
                user_id=user_id,
            )
            agent.cancel_token = cancel_token
            agent.tracer = tracer
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
                # Receive message from client
                data = await websocket.receive_text()

                # Parse message
                try:
                    msg = WSMessage.model_validate_json(data)
                except ValidationError:
                    # Unknown message format, ignore
                    logger.warning(f"Invalid message format: {data}")
                    continue

                # Handle different message types
                if msg.type == "user.text":
                    # User text input
                    user_text = msg.payload.get("text", "")
                    if not user_text:
                        continue

                    # Record user event
                    user_event = FrontendEvent(
                        type=EventType.USER_TEXT,
                        payload={"text": user_text},
                    )
                    await websocket.send_text(user_event.model_dump_json())

                    # Append to session
                    session_store.append_event(user_id, session_id, user_event)

                    # Run agent and stream events
                    async for event in agent.run(user_text):
                        await websocket.send_text(event.model_dump_json())

                        # Persist events that should be saved
                        if session_store._should_persist(event):
                            session_store.append_event(user_id, session_id, event)

                elif msg.type == "control.interrupt":
                    # Interrupt agent
                    if agent:
                        agent.interrupt()

                else:
                    # Unknown message type, ignore
                    logger.info(f"Unknown message type: {msg.type}")

            except WebSocketDisconnect:
                # Client disconnected
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
        # Cleanup
        if cancel_token:
            cancel_token.cancel()

        # Note: We don't pause the session immediately on disconnect
        # The session stays active for potential reconnection
