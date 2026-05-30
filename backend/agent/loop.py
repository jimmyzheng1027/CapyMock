from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable

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
from trace import (
    span_level_for_result,
    tool_result_output,
    trace_agent_turn,
    trace_compaction,
    trace_llm_call,
    trace_react_step,
    trace_tool,
)
from agent.profile import AgentProfile
from agent.state import AgentState, can_transition
from api.schemas import EventType, FrontendEvent
from storage.session.store import SessionStore
from tool.base import ToolContext, ToolMeta, ToolResult
from tool.executor import ToolCall, ToolExecutor


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
        self.state = AgentState.IDLE
        self._text_buffer: list[str] = []
        self._current_tool_calls: list[ToolCall] = []
        self._session_obj: object | None = None
        self._repo_url: str = ""
        self._sandbox_root: str = ""
        self._current_repo_path: str = ""
        self._db_session: object | None = None
        self._repo_root: str = ""

    async def run(self, user_input: str) -> AsyncIterator[FrontendEvent]:
        """Run the ReAct loop for a user input.

        Yields FrontendEvents to be sent to the frontend.
        """
        with trace_agent_turn(
            session_id=self.session_id,
            user_id=self.user_id,
            user_input=user_input,
            profile_id=self.profile.id,
        ) as turn:
            turn_output: dict[str, object] = {"stop_reason": "completed", "steps": 0}

            # Transition to thinking
            self._set_state(AgentState.THINKING)
            yield self._make_state_event(AgentState.THINKING)

            # Get session events for context
            events = self.session_store.read_events(self.user_id, self.session_id)

            # Build messages
            messages = self.context_builder.build_messages(
                self.profile, events, user_input
            )

            # Check if compaction is needed
            if self.compactor.should_compact(self.profile, messages):
                yield self._make_state_event(AgentState.COMPACTING)
                with trace_compaction() as compaction:
                    summary, messages = await self.compactor.compact(
                        self.profile, messages
                    )
                    compaction.update(
                        output={"summary": summary} if summary else {"summary": None}
                    )
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
                    turn_output["stop_reason"] = "interrupted"
                    break

                steps += 1
                with trace_react_step(step=steps) as step_span:
                    yield self._make_state_event(AgentState.STREAMING_TEXT)

                    self._react_should_continue = False
                    self._text_buffer = []
                    self._current_tool_calls = []
                    if hasattr(self.llm, "begin_stream_turn"):
                        self.llm.begin_stream_turn()
                    async for fe in self._process_llm_events(
                        messages, self._stream_llm(messages)
                    ):
                        yield fe

                    step_span.update(
                        output={
                            "continued": self._react_should_continue,
                            "tool_calls": len(self._current_tool_calls),
                        }
                    )

                if self._react_should_continue:
                    continue
                done = True

            # Check if max steps exceeded
            if steps >= self.profile.policy.max_steps and not done:
                yield FrontendEvent(
                    type=EventType.ERROR,
                    payload={
                        "code": "max_steps_exceeded",
                        "message": (
                            f"Maximum steps ({self.profile.policy.max_steps}) exceeded"
                        ),
                    },
                )
                yield FrontendEvent(
                    type=EventType.TURN_DONE,
                    payload={"stop_reason": "max_steps"},
                )
                turn_output["stop_reason"] = "max_steps"

            turn_output["steps"] = steps
            if self._text_buffer:
                turn_output["assistant_text"] = "".join(self._text_buffer)
            turn.update(output=turn_output)

            # Return to idle
            self._set_state(AgentState.IDLE)
            yield self._make_state_event(AgentState.IDLE)

    async def _process_llm_events(
        self, messages: list[dict], event_stream: AsyncIterator[LLMEvent]
    ) -> AsyncIterator[FrontendEvent]:
        """Process LLM events, executing tools if needed.

        Sets self._react_should_continue = True when tools were executed
        and the ReAct loop should call the LLM again.
        """
        async for event in event_stream:
            if self.cancel_token.is_set():
                yield self._make_interrupt_event()
                return

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
                for tc in self._current_tool_calls:
                    if tc.tool_call_id == event.tool_call_id:
                        tc.args = event.args
                        break
            elif isinstance(event, Done):
                if event.stop_reason == "tool_use":
                    yield self._make_state_event(AgentState.EXECUTING_TOOLS)
                    messages.append(self._build_assistant_tool_use_message())
                    async for msg in self._execute_tools_sequential():
                        if isinstance(msg, FrontendEvent):
                            yield msg
                        else:
                            messages.append(msg)
                    yield self._make_state_event(AgentState.AGGREGATING)
                    self._react_should_continue = True
                else:
                    full_text = "".join(self._text_buffer)
                    yield FrontendEvent(
                        type=EventType.ASSISTANT_TEXT_DONE,
                        payload={"text": full_text, "partial": False},
                    )
                    yield FrontendEvent(
                        type=EventType.TURN_DONE,
                        payload={"stop_reason": event.stop_reason},
                    )
                return
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
                    fallback_llm = self._create_fallback_llm()
                    if fallback_llm:
                        async for fe in self._process_llm_events(
                            messages, fallback_llm.stream(messages, self._get_tool_schemas())
                        ):
                            yield fe
                        return
                yield FrontendEvent(
                    type=EventType.TURN_DONE,
                    payload={"stop_reason": "error"},
                )
                return

    async def _stream_llm(self, messages: list[dict]) -> AsyncIterator[LLMEvent]:
        """Stream events from the LLM."""
        tool_schemas = self._get_tool_schemas()
        model = self.llm.get_model_name()
        prompt_tokens = 0
        completion_tokens = 0

        with trace_llm_call(model=model, messages=messages) as generation:
            async for event in self.llm.stream(messages, tool_schemas):
                if isinstance(event, Usage):
                    prompt_tokens = event.prompt_tokens
                    completion_tokens = event.completion_tokens
                yield event

            generation.update(
                output="".join(self._text_buffer),
                usage_details={
                    "input": prompt_tokens,
                    "output": completion_tokens,
                    "total": prompt_tokens + completion_tokens,
                },
            )

    async def _execute_tools(self) -> list[FrontendEvent]:
        """Execute tool calls and return result events."""
        def ctx_factory(call: ToolCall) -> ToolContext:
            return ToolContext(
                session=self._session_obj,
                session_id=self.session_id,
                user_id=self.user_id,
                profile=self.profile,
                cancel_token=self.cancel_token,
                sandbox_root=self._sandbox_root,
                current_repo_path=self._current_repo_path,
                db_session=self._db_session,
                repo_root=self._repo_root,
                repo_url=self._repo_url,
            )

        async def execute_one(call: ToolCall) -> ToolResult:
            with trace_tool(name=call.tool_name, args=call.args) as tool_span:
                batch = await self.tool_executor.run_parallel(
                    [call],
                    ctx_factory,
                    self.tools,
                    parallel_limit=1,
                    cancel_token=self.cancel_token,
                )
                result = batch[0]
                tool_span.update(
                    output=tool_result_output(result),
                    level=span_level_for_result(result),
                )
                return result

        results = await asyncio.gather(
            *[execute_one(call) for call in self._current_tool_calls]
        )

        events = []
        for call, result in zip(self._current_tool_calls, results):
            # Track repo_path from clone_repo results
            if (
                call.tool_name == "clone_repo"
                and result.status == "ok"
                and result.data
            ):
                repo_path = result.data.get("repo_path")
                if repo_path:
                    self._current_repo_path = repo_path

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

    async def _execute_tools_sequential(
        self,
    ) -> AsyncIterator[FrontendEvent | dict]:
        """Execute tool calls one by one, yielding events and tool messages.

        Yields FrontendEvent for frontend display, and dict messages for the
        LLM context. This ensures each tool result is visible before the next
        tool call, so the agent can react to failures.
        """
        for call in self._current_tool_calls:
            with trace_tool(name=call.tool_name, args=call.args) as tool_span:
                batch = await self.tool_executor.run_parallel(
                    [call],
                    self._make_ctx_factory(),
                    self.tools,
                    parallel_limit=1,
                    cancel_token=self.cancel_token,
                )
                result = batch[0]
                tool_span.update(
                    output=tool_result_output(result),
                    level=span_level_for_result(result),
                )

            # Track repo_path from clone_repo results
            if (
                call.tool_name == "clone_repo"
                and result.status == "ok"
                and result.data
            ):
                repo_path = result.data.get("repo_path")
                if repo_path:
                    self._current_repo_path = repo_path

            yield FrontendEvent(
                type=EventType.TOOL_CALL_END,
                payload={
                    "tool_call_id": call.tool_call_id,
                    "tool_name": call.tool_name,
                },
            )
            yield FrontendEvent(
                type=EventType.TOOL_RESULT,
                payload={
                    "tool_call_id": call.tool_call_id,
                    "tool_name": call.tool_name,
                    "status": result.status,
                    "data": result.data,
                    "error": result.error,
                    "summary": result.summary,
                },
            )
            yield {
                "role": "tool",
                "tool_call_id": call.tool_call_id,
                "content": json.dumps(
                    result.data if result.status == "ok" else result.error
                ),
            }

    def _build_assistant_tool_use_message(self) -> dict:
        """Build assistant message with tool_calls for the next LLM turn."""
        text = "".join(self._text_buffer).strip()
        tool_calls_payload = [
            {
                "id": call.tool_call_id,
                "type": "function",
                "function": {
                    "name": call.tool_name,
                    "arguments": json.dumps(call.args, ensure_ascii=False),
                },
            }
            for call in self._current_tool_calls
        ]
        msg: dict = {
            "role": "assistant",
            "content": text if text else None,
            "tool_calls": tool_calls_payload,
        }
        if hasattr(self.llm, "consume_reasoning_for_message"):
            reasoning = self.llm.consume_reasoning_for_message()
            if reasoning:
                msg["reasoning_content"] = reasoning
        return msg

    def _make_ctx_factory(self) -> Callable[[ToolCall], ToolContext]:
        """Create a context factory for tool execution."""

        def ctx_factory(_call: ToolCall) -> ToolContext:
            return ToolContext(
                session=self._session_obj,
                session_id=self.session_id,
                user_id=self.user_id,
                profile=self.profile,
                cancel_token=self.cancel_token,
                sandbox_root=self._sandbox_root,
                current_repo_path=self._current_repo_path,
                db_session=self._db_session,
                repo_root=self._repo_root,
                repo_url=self._repo_url,
            )

        return ctx_factory

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
        from config.settings import settings

        return settings.get_api_key(provider)

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
