from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator

from agent.context.builder import ContextBuilder
from agent.context.compactor import ContextCompactor
from agent.llm.base import BaseLLM
from agent.llm.events import (
    Done,
    LLMEvent,
    ProviderError,
    TextDelta,
    ThinkingDelta,
    ToolCallEnd,
    ToolCallStart,
    Usage,
)
from agent.profile import AgentProfile
from agent.state import AgentState, can_transition
from api.schemas import EventType, FrontendEvent
from storage.session.store import SessionStore
from tool.base import ToolContext, ToolMeta
from tool.executor import ToolCall, ToolExecutor
from tracer.base import Tracer


class CancelToken:
    """Token for signaling cancellation."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_set(self) -> bool:
        return self._cancelled


class ReActAgent:
    """ReAct Agent Loop: Reason -> Act -> Observe."""

    def __init__(
        self,
        profile: AgentProfile,
        llm: BaseLLM,
        context_builder: ContextBuilder,
        compactor: ContextCompactor,
        tool_executor: ToolExecutor,
        tools: dict[str, ToolMeta],
        session_store: SessionStore,
        user_id: str,
        session_id: str,
        cancel_token: CancelToken | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.profile = profile
        self.llm = llm
        self.context_builder = context_builder
        self.compactor = compactor
        self.tool_executor = tool_executor
        self.tools = tools
        self.session_store = session_store
        self.user_id = user_id
        self.session_id = session_id
        self.cancel_token = cancel_token or CancelToken()
        self.tracer = tracer
        self.state = AgentState.IDLE
        self._text_buffer: list[str] = []
        self._current_tool_calls: list[ToolCall] = []

    async def run(self, user_input: str) -> AsyncIterator[FrontendEvent]:
        """Run the ReAct loop for a user input.

        Yields FrontendEvents to be sent to the frontend.
        """
        # Transition to thinking
        self._set_state(AgentState.THINKING)
        yield self._make_state_event(AgentState.THINKING)

        # Get session events for context
        events = self.session_store.read_events(self.user_id, self.session_id)

        # Build messages
        messages = self.context_builder.build_messages(self.profile, events, user_input)

        # Check if compaction is needed
        if self.compactor.should_compact(self.profile, messages):
            yield self._make_state_event(AgentState.COMPACTING)
            summary, messages = await self.compactor.compact(self.profile, messages)
            if summary:
                yield FrontendEvent(
                    type=EventType.SESSION_COMPACTED,
                    payload={"summary_text": summary},
                )

        # ReAct loop
        steps = 0
        done = False
        while steps < self.profile.policy.max_steps and not done:
            if self.cancel_token.is_set():
                yield self._make_interrupt_event()
                break

            steps += 1

            # Stream LLM response
            yield self._make_state_event(AgentState.STREAMING_TEXT)
            self._text_buffer = []
            self._current_tool_calls = []
            should_continue = False

            async for event in self._stream_llm(messages):
                if self.cancel_token.is_set():
                    yield self._make_interrupt_event()
                    done = True
                    break

                if isinstance(event, TextDelta):
                    self._text_buffer.append(event.delta)
                    yield FrontendEvent(
                        type=EventType.ASSISTANT_TEXT_DELTA,
                        payload={"delta": event.delta},
                    )
                elif isinstance(event, ThinkingDelta):
                    yield FrontendEvent(
                        type=EventType.ASSISTANT_THINKING_DELTA,
                        payload={"delta": event.delta},
                    )
                elif isinstance(event, ToolCallStart):
                    self._current_tool_calls.append(
                        ToolCall(
                            tool_call_id=event.tool_call_id,
                            tool_name=event.tool_name,
                            args={},
                        )
                    )
                    yield FrontendEvent(
                        type=EventType.TOOL_CALL_START,
                        payload={
                            "tool_call_id": event.tool_call_id,
                            "tool_name": event.tool_name,
                        },
                    )
                elif isinstance(event, ToolCallEnd):
                    # Update tool call args
                    for tc in self._current_tool_calls:
                        if tc.tool_call_id == event.tool_call_id:
                            tc.args = event.args
                            break
                elif isinstance(event, Done):
                    if event.stop_reason == "tool_use":
                        # Execute tools
                        yield self._make_state_event(AgentState.EXECUTING_TOOLS)
                        tool_results = await self._execute_tools()

                        # Yield tool results
                        for result_event in tool_results:
                            yield result_event

                        # Add tool results to messages
                        messages.extend(self._build_tool_messages(tool_results))

                        yield self._make_state_event(AgentState.AGGREGATING)

                        # Continue loop for next LLM call
                        should_continue = True
                        break
                    else:
                        # End turn
                        full_text = "".join(self._text_buffer)
                        yield FrontendEvent(
                            type=EventType.ASSISTANT_TEXT_DONE,
                            payload={"text": full_text, "partial": False},
                        )
                        yield FrontendEvent(
                            type=EventType.TURN_DONE,
                            payload={"stop_reason": event.stop_reason},
                        )
                        done = True
                        break
                elif isinstance(event, ProviderError):
                    yield FrontendEvent(
                        type=EventType.ERROR,
                        payload={
                            "code": event.code,
                            "message": event.message,
                            "retryable": event.retryable,
                        },
                    )
                    if event.retryable and self.profile.llm.fallback:
                        # Try fallback provider
                        fallback_llm = self._create_fallback_llm()
                        if fallback_llm:
                            # Retry with fallback
                            async for fallback_event in fallback_llm.stream(
                                messages, self._get_tool_schemas()
                            ):
                                if isinstance(fallback_event, TextDelta):
                                    self._text_buffer.append(fallback_event.delta)
                                    yield FrontendEvent(
                                        type=EventType.ASSISTANT_TEXT_DELTA,
                                        payload={"delta": fallback_event.delta},
                                    )
                                elif isinstance(fallback_event, Done):
                                    if fallback_event.stop_reason == "tool_use":
                                        # Handle tool use from fallback
                                        pass
                                    else:
                                        full_text = "".join(self._text_buffer)
                                        yield FrontendEvent(
                                            type=EventType.ASSISTANT_TEXT_DONE,
                                            payload={"text": full_text, "partial": False},
                                        )
                                        yield FrontendEvent(
                                            type=EventType.TURN_DONE,
                                            payload={"stop_reason": fallback_event.stop_reason},
                                        )
                                    break
                            break
                    yield FrontendEvent(
                        type=EventType.TURN_DONE,
                        payload={"stop_reason": "error"},
                    )
                    done = True
                    break

            # Check if we should continue to next iteration
            if should_continue:
                continue

        # Check if max steps exceeded
        if steps >= self.profile.policy.max_steps:
            yield FrontendEvent(
                type=EventType.ERROR,
                payload={
                    "code": "max_steps_exceeded",
                    "message": f"Maximum steps ({self.profile.policy.max_steps}) exceeded",
                },
            )
            yield FrontendEvent(
                type=EventType.TURN_DONE,
                payload={"stop_reason": "max_steps"},
            )

        # Return to idle
        self._set_state(AgentState.IDLE)
        yield self._make_state_event(AgentState.IDLE)

    async def _stream_llm(self, messages: list[dict]) -> AsyncIterator[LLMEvent]:
        """Stream events from the LLM."""
        tool_schemas = self._get_tool_schemas()
        start_time = time.time()

        # Create tracer span
        span = None
        if self.tracer:
            span = self.tracer.span(
                "llm_call",
                model=self.llm.get_model_name(),
                session_id=self.session_id,
            )

        prompt_tokens = 0
        completion_tokens = 0

        try:
            async for event in self.llm.stream(messages, tool_schemas):
                # Track usage
                if isinstance(event, Usage):
                    prompt_tokens = event.prompt_tokens
                    completion_tokens = event.completion_tokens

                yield event
        finally:
            # Record LLM call
            if self.tracer and span:
                latency_ms = (time.time() - start_time) * 1000
                self.tracer.record_llm_call(
                    span=span,
                    model=self.llm.get_model_name(),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    latency_ms=latency_ms,
                )
                self.tracer.end_span(span)

    async def _execute_tools(self) -> list[FrontendEvent]:
        """Execute tool calls and return result events."""
        def ctx_factory(call: ToolCall) -> ToolContext:
            return ToolContext(
                session=None,  # Will be populated by session service
                user_id=self.user_id,
                profile=self.profile,
                cancel_token=self.cancel_token,
            )

        start_time = time.time()

        # Create tracer span for tool execution
        span = None
        if self.tracer:
            span = self.tracer.span(
                "tool_execution",
                tool_count=len(self._current_tool_calls),
                session_id=self.session_id,
            )

        results = await self.tool_executor.run_parallel(
            self._current_tool_calls,
            ctx_factory,
            self.tools,
            parallel_limit=self.profile.policy.parallel_tools,
            cancel_token=self.cancel_token,
        )

        # Record tool calls
        if self.tracer and span:
            duration_ms = (time.time() - start_time) * 1000
            for call, result in zip(self._current_tool_calls, results):
                self.tracer.record_tool_call(
                    span=span,
                    tool_name=call.tool_name,
                    duration_ms=duration_ms / len(self._current_tool_calls),
                    success=result.status == "ok",
                )
            self.tracer.end_span(span)

        events = []
        for call, result in zip(self._current_tool_calls, results):
            # Tool call end event
            events.append(FrontendEvent(
                type=EventType.TOOL_CALL_END,
                payload={
                    "tool_call_id": call.tool_call_id,
                    "tool_name": call.tool_name,
                },
            ))

            # Tool result event
            events.append(FrontendEvent(
                type=EventType.TOOL_RESULT,
                payload={
                    "tool_call_id": call.tool_call_id,
                    "tool_name": call.tool_name,
                    "status": result.status,
                    "data": result.data,
                    "error": result.error,
                    "summary": result.summary,
                },
            ))

        return events

    def _build_tool_messages(self, result_events: list[FrontendEvent]) -> list[dict]:
        """Build tool result messages for the next LLM call."""
        messages = []
        for event in result_events:
            if event.type == EventType.TOOL_RESULT:
                messages.append({
                    "role": "tool",
                    "tool_call_id": event.payload["tool_call_id"],
                    "content": json.dumps(event.payload.get("data") or event.payload.get("error")),
                })
        return messages

    def _get_tool_schemas(self) -> list[dict]:
        """Get tool schemas for the LLM."""
        tool_metas = list(self.tools.values())
        schemas = []
        for meta in tool_metas:
            schemas.append({
                "type": "function",
                "function": {
                    "name": meta.name,
                    "description": meta.description,
                    "parameters": meta.args_model.model_json_schema(),
                },
            })
        return schemas

    def _create_fallback_llm(self) -> BaseLLM | None:
        """Create a fallback LLM instance from profile config."""
        from agent.llm.factory import LLMFactory

        if not self.profile.llm.fallback:
            return None

        fallback_config = self.profile.llm.fallback
        try:
            return LLMFactory.create(
                fallback_config.provider,
                {
                    "api_key": self._get_api_key(fallback_config.provider),
                    "model": fallback_config.model,
                    "temperature": fallback_config.temperature,
                },
            )
        except Exception:
            return None

    def _get_api_key(self, provider: str) -> str:
        """Get API key for a provider from settings."""
        from config.settings import settings

        if provider == "dashscope":
            return settings.DASHSCOPE_API_KEY
        elif provider == "deepseek":
            return settings.DEEPSEEK_API_KEY
        elif provider == "openai":
            return settings.OPENAI_API_KEY
        return ""

    def _set_state(self, new_state: AgentState) -> None:
        """Set agent state with validation."""
        if can_transition(self.state, new_state):
            self.state = new_state
        else:
            # Force transition on interrupt
            if new_state == AgentState.INTERRUPTED:
                self.state = new_state

    def _make_state_event(self, state: AgentState) -> FrontendEvent:
        """Create a state.changed event."""
        return FrontendEvent(
            type=EventType.STATE_CHANGED,
            payload={"state": state.value},
        )

    def _make_interrupt_event(self) -> FrontendEvent:
        """Create interrupt event and partial commit."""
        self._set_state(AgentState.INTERRUPTED)

        # Partial commit - combine buffered text
        full_text = "".join(self._text_buffer)
        if full_text:
            return FrontendEvent(
                type=EventType.ASSISTANT_TEXT_DONE,
                payload={"text": full_text, "partial": True},
            )

        return FrontendEvent(
            type=EventType.STATE_CHANGED,
            payload={"state": AgentState.INTERRUPTED.value},
        )

    def interrupt(self) -> None:
        """Signal interruption."""
        self.cancel_token.cancel()
