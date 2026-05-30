"""Tests for ReActAgent: using FakeLLM to test event sequences."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
from pydantic import BaseModel

from agent.context.builder import ContextBuilder
from agent.context.compactor import ContextCompactor
from agent.context.skill_loader import SkillLoader
from agent.llm.base import BaseLLM
from agent.llm.events import (
    Done,
    LLMEvent,
    ProviderError,
    TextDelta,
    ToolCallEnd,
    ToolCallStart,
    Usage,
)
from agent.loop import CancelToken, ReActAgent
from agent.profile import AgentProfile, ContextConfig, LLMConfig, PolicyConfig
from api.schemas import EventType
from storage.session.store import SessionStore
from tool.base import ToolContext, ToolResult, tool
from tool.executor import ToolExecutor
from tool.registry import ToolRegistry


class TestArgs(BaseModel):
    input: str = ""


@tool
async def sample_tool(args: TestArgs, ctx: ToolContext) -> ToolResult:
    """A test tool."""
    return ToolResult.ok(data={"result": f"Processed: {args.input}"})


class FakeLLM(BaseLLM):
    """Fake LLM that yields scripted events."""

    def __init__(self, events: list[LLMEvent]) -> None:
        self.events = events
        self.call_count = 0

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncIterator[LLMEvent]:
        self.call_count += 1
        for event in self.events:
            yield event
            await asyncio.sleep(0)  # Allow other tasks to run

    def get_model_name(self) -> str:
        return "fake-model"


class TestReActAgent:
    """Test ReActAgent behavior."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directories."""
        return tmp_path

    @pytest.fixture
    def profile(self) -> AgentProfile:
        """Create a test profile."""
        return AgentProfile(
            id="test-agent",
            prompt_template="nonexistent.md",
            llm=LLMConfig(provider="test", model="test"),
            tools=["sample_tool"],
            skills=[],
            context=ContextConfig(max_history_tokens=8000, compact_threshold=6000),
            policy=PolicyConfig(max_steps=5, parallel_tools=3, tool_timeout=30.0),
        )

    @pytest.fixture
    def session_store(self, temp_dir) -> SessionStore:
        """Create a test session store."""
        return SessionStore(root_dir=str(temp_dir / "sessions"))

    @pytest.fixture
    def skill_loader(self, temp_dir) -> SkillLoader:
        """Create a test skill loader."""
        return SkillLoader(str(temp_dir / "skills"))

    @pytest.mark.asyncio
    async def test_text_only_response(
        self, profile, session_store, skill_loader
    ) -> None:
        """Test: agent responds with text only, no tool calls."""
        # Setup
        fake_llm = FakeLLM([
            TextDelta(delta="Hello! "),
            TextDelta(delta="How can I help?"),
            Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            Done(stop_reason="end_turn"),
        ])

        context_builder = ContextBuilder(skill_loader)
        compactor = ContextCompactor(fake_llm)
        tool_executor = ToolExecutor()
        registry = ToolRegistry(tools=[sample_tool])
        tools = {meta.name: meta for meta in registry.all()}

        # Create session
        session_store.create("user1", "session1", "profile1")

        agent = ReActAgent(
            profile=profile,
            llm=fake_llm,
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=session_store,
            user_id="user1",
            session_id="session1",
        )

        # Run agent
        events = []
        async for event in agent.run("Hi"):
            events.append(event)

        # Verify events
        event_types = [e.type for e in events]
        assert EventType.STATE_CHANGED in event_types  # thinking
        assert EventType.ASSISTANT_TEXT_DELTA in event_types
        assert EventType.ASSISTANT_TEXT_DONE in event_types
        assert EventType.TURN_DONE in event_types

        # Verify text content
        text_events = [e for e in events if e.type == EventType.ASSISTANT_TEXT_DELTA]
        assert len(text_events) == 2
        assert text_events[0].payload["delta"] == "Hello! "
        assert text_events[1].payload["delta"] == "How can I help?"

    @pytest.mark.asyncio
    async def test_tool_use_appends_assistant_message(
        self, profile, session_store, skill_loader
    ) -> None:
        """Test: multi-turn tool loop includes assistant tool_calls before tool results."""
        round_events = [
            [
                ToolCallStart(tool_call_id="call_1", tool_name="sample_tool"),
                ToolCallEnd(
                    tool_call_id="call_1",
                    tool_name="sample_tool",
                    args={"input": "test"},
                ),
                Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                Done(stop_reason="tool_use"),
            ],
            [
                TextDelta(delta="Done"),
                Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                Done(stop_reason="end_turn"),
            ],
        ]

        class TwoRoundLLM(BaseLLM):
            def __init__(self) -> None:
                self.round = 0
                self.messages_seen: list[list[dict]] = []

            async def stream(
                self, messages: list[dict], tools: list[dict] | None = None
            ) -> AsyncIterator[LLMEvent]:
                self.messages_seen.append(list(messages))
                events = round_events[self.round]
                self.round += 1
                for event in events:
                    yield event
                    await asyncio.sleep(0)

            def get_model_name(self) -> str:
                return "two-round-fake"

        llm = TwoRoundLLM()
        context_builder = ContextBuilder(skill_loader)
        compactor = ContextCompactor(llm)
        tool_executor = ToolExecutor()
        registry = ToolRegistry(tools=[sample_tool])
        tools = {meta.name: meta for meta in registry.all()}

        session_store.create("user1", "session1", "profile1")

        agent = ReActAgent(
            profile=profile,
            llm=llm,
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=session_store,
            user_id="user1",
            session_id="session1",
        )

        async for _ in agent.run("Use tool"):
            pass

        assert llm.round == 2
        second_turn = llm.messages_seen[1]
        assistant_msgs = [m for m in second_turn if m.get("role") == "assistant"]
        tool_msgs = [m for m in second_turn if m.get("role") == "tool"]
        assert len(assistant_msgs) == 1
        assert assistant_msgs[0].get("tool_calls")
        assert assistant_msgs[0]["tool_calls"][0]["function"]["name"] == "sample_tool"
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["tool_call_id"] == "call_1"

    @pytest.mark.asyncio
    async def sample_tool_call(
        self, profile, session_store, skill_loader
    ) -> None:
        """Test: agent calls a tool and continues."""
        fake_llm = FakeLLM([
            # First call: tool use
            ToolCallStart(tool_call_id="call_1", tool_name="sample_tool"),
            ToolCallEnd(
                tool_call_id="call_1",
                tool_name="sample_tool",
                args={"input": "test"},
            ),
            Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            Done(stop_reason="tool_use"),
            # Second call: text response
            TextDelta(delta="Tool result received"),
            Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            Done(stop_reason="end_turn"),
        ])

        context_builder = ContextBuilder(skill_loader)
        compactor = ContextCompactor(fake_llm)
        tool_executor = ToolExecutor()
        registry = ToolRegistry(tools=[sample_tool])
        tools = {meta.name: meta for meta in registry.all()}

        session_store.create("user1", "session1", "profile1")

        agent = ReActAgent(
            profile=profile,
            llm=fake_llm,
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=session_store,
            user_id="user1",
            session_id="session1",
        )

        events = []
        async for event in agent.run("Use tool"):
            events.append(event)

        event_types = [e.type for e in events]
        assert EventType.TOOL_CALL_START in event_types
        assert EventType.TOOL_CALL_END in event_types
        assert EventType.TOOL_RESULT in event_types
        assert EventType.ASSISTANT_TEXT_DONE in event_types

    @pytest.mark.asyncio
    async def test_interrupt(
        self, profile, session_store, skill_loader
    ) -> None:
        """Test: agent can be interrupted mid-stream."""
        # Create a slow LLM that yields events with delays
        class SlowFakeLLM(BaseLLM):
            async def stream(
                self, messages, tools=None
            ) -> AsyncIterator[LLMEvent]:
                yield TextDelta(delta="Part 1")
                await asyncio.sleep(10)  # Long delay
                yield TextDelta(delta="Part 2")
                yield Done(stop_reason="end_turn")

            def get_model_name(self):
                return "slow-fake"

        context_builder = ContextBuilder(skill_loader)
        compactor = ContextCompactor(SlowFakeLLM())
        tool_executor = ToolExecutor()
        registry = ToolRegistry(tools=[sample_tool])
        tools = {meta.name: meta for meta in registry.all()}

        session_store.create("user1", "session1", "profile1")

        cancel_token = CancelToken()
        agent = ReActAgent(
            profile=profile,
            llm=SlowFakeLLM(),
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=session_store,
            user_id="user1",
            session_id="session1",
            cancel_token=cancel_token,
        )

        # Start agent and interrupt
        events = []
        async for event in agent.run("Start"):
            events.append(event)
            if event.type == EventType.ASSISTANT_TEXT_DELTA:
                cancel_token.cancel()

        # Should have partial text
        text_done = [e for e in events if e.type == EventType.ASSISTANT_TEXT_DONE]
        assert len(text_done) == 1
        assert text_done[0].payload["partial"] is True

    @pytest.mark.asyncio
    async def test_max_steps(
        self, profile, session_store, skill_loader
    ) -> None:
        """Test: agent stops at max_steps."""
        # Create LLM that always requests tool use
        class AlwaysToolLLM(BaseLLM):
            call_count = 0

            async def stream(
                self, messages, tools=None
            ) -> AsyncIterator[LLMEvent]:
                AlwaysToolLLM.call_count += 1
                yield ToolCallStart(
                    tool_call_id=f"call_{AlwaysToolLLM.call_count}",
                    tool_name="sample_tool",
                )
                yield ToolCallEnd(
                    tool_call_id=f"call_{AlwaysToolLLM.call_count}",
                    tool_name="sample_tool",
                    args={"input": "test"},
                )
                yield Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                yield Done(stop_reason="tool_use")

            def get_model_name(self):
                return "always-tool"

        # Reset call count
        AlwaysToolLLM.call_count = 0

        context_builder = ContextBuilder(skill_loader)
        compactor = ContextCompactor(AlwaysToolLLM())
        tool_executor = ToolExecutor()
        registry = ToolRegistry(tools=[sample_tool])
        tools = {meta.name: meta for meta in registry.all()}

        session_store.create("user1", "session1", "profile1")

        agent = ReActAgent(
            profile=profile,
            llm=AlwaysToolLLM(),
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=session_store,
            user_id="user1",
            session_id="session1",
        )

        events = []
        async for event in agent.run("Keep going"):
            events.append(event)

        # Should have max_steps_exceeded error
        error_events = [e for e in events if e.type == EventType.ERROR]
        assert len(error_events) > 0
        assert error_events[0].payload["code"] == "max_steps_exceeded"

    @pytest.mark.asyncio
    async def test_provider_error(
        self, profile, session_store, skill_loader
    ) -> None:
        """Test: agent handles provider errors."""
        fake_llm = FakeLLM([
            ProviderError(message="Rate limited", code="429", retryable=False),
            Done(stop_reason="error"),
        ])

        context_builder = ContextBuilder(skill_loader)
        compactor = ContextCompactor(fake_llm)
        tool_executor = ToolExecutor()
        registry = ToolRegistry(tools=[sample_tool])
        tools = {meta.name: meta for meta in registry.all()}

        session_store.create("user1", "session1", "profile1")

        agent = ReActAgent(
            profile=profile,
            llm=fake_llm,
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=session_store,
            user_id="user1",
            session_id="session1",
        )

        events = []
        async for event in agent.run("Test error"):
            events.append(event)

        error_events = [e for e in events if e.type == EventType.ERROR]
        assert len(error_events) > 0
        assert error_events[0].payload["code"] == "429"
