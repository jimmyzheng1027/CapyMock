from __future__ import annotations

from enum import Enum


class AgentState(str, Enum):
    """Agent state machine states."""

    IDLE = "idle"
    THINKING = "thinking"
    STREAMING_TEXT = "streaming_text"
    EXECUTING_TOOLS = "executing_tools"
    AGGREGATING = "aggregating"
    INTERRUPTED = "interrupted"
    COMPACTING = "compacting"


# Valid state transitions
VALID_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.IDLE: {AgentState.THINKING},
    AgentState.THINKING: {
        AgentState.STREAMING_TEXT,
        AgentState.EXECUTING_TOOLS,
        AgentState.IDLE,
        AgentState.INTERRUPTED,
    },
    AgentState.STREAMING_TEXT: {
        AgentState.THINKING,
        AgentState.EXECUTING_TOOLS,
        AgentState.AGGREGATING,
        AgentState.IDLE,
        AgentState.INTERRUPTED,
    },
    AgentState.EXECUTING_TOOLS: {
        AgentState.AGGREGATING,
        AgentState.THINKING,
        AgentState.IDLE,
        AgentState.INTERRUPTED,
    },
    AgentState.AGGREGATING: {
        AgentState.THINKING,
        AgentState.IDLE,
    },
    AgentState.INTERRUPTED: {AgentState.IDLE},
    AgentState.COMPACTING: {AgentState.THINKING},
}


def can_transition(current: AgentState, next_state: AgentState) -> bool:
    """Check if a state transition is valid."""
    return next_state in VALID_TRANSITIONS.get(current, set())


def transition(current: AgentState, next_state: AgentState) -> AgentState:
    """Perform a state transition, raising ValueError if invalid."""
    if not can_transition(current, next_state):
        raise ValueError(
            f"Invalid state transition: {current.value} -> {next_state.value}"
        )
    return next_state
