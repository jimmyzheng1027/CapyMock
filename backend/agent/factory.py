from __future__ import annotations

from agent.context.builder import ContextBuilder
from agent.context.compactor import ContextCompactor
from agent.context.skill_loader import SkillLoader
from agent.llm.base import BaseLLM
from agent.llm.factory import LLMFactory
from agent.loop import ReActAgent
from agent.profile import AgentProfile
from agent.profile_loader import ProfileLoader
from config.settings import settings
from storage.session.store import SessionStore
from tool.base import ToolMeta
from tool.executor import ToolExecutor
from tool.registry import ToolRegistry


class ProfileNotFound(Exception):
    """Raised when a profile ID is not found."""
    pass


class AgentFactory:
    """Factory for creating ReActAgent instances."""

    def __init__(
        self,
        profile_loader: ProfileLoader,
        tool_registry: ToolRegistry,
        session_store: SessionStore,
        skill_loader: SkillLoader,
    ) -> None:
        self.profile_loader = profile_loader
        self.tool_registry = tool_registry
        self.session_store = session_store
        self.skill_loader = skill_loader

    def create(
        self,
        profile_id: str,
        session_id: str,
        mode: str = "text",
        user_id: str = "default",
    ) -> ReActAgent:
        """Create a ReActAgent instance.

        Args:
            profile_id: ID of the agent profile to use
            session_id: ID of the session
            mode: Mode of the agent ("text" or "voice")
            user_id: ID of the user

        Returns:
            Configured ReActAgent instance

        Raises:
            ProfileNotFound: If profile_id doesn't exist
            NotImplementedError: If mode is "voice"
        """
        if mode == "voice":
            raise NotImplementedError("Voice mode is not yet implemented")

        profile = self.profile_loader.get(profile_id)
        if profile is None:
            raise ProfileNotFound(f"Profile not found: {profile_id}")

        llm = self._create_llm(profile)
        tools = self._get_tools(profile)
        context_builder = ContextBuilder(self.skill_loader)
        compactor = ContextCompactor(llm)
        tool_executor = ToolExecutor(default_timeout=profile.policy.tool_timeout)

        return ReActAgent(
            profile=profile,
            llm=llm,
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=self.session_store,
            user_id=user_id,
            session_id=session_id,
        )

    def _create_llm(self, profile: AgentProfile) -> BaseLLM:
        """Create an LLM instance from profile config."""
        api_key = self._get_api_key(profile.llm.provider)
        return LLMFactory.create(
            profile.llm.provider,
            {
                "api_key": api_key,
                "model": profile.llm.model,
                "temperature": profile.llm.temperature,
            },
        )

    def _get_api_key(self, provider: str) -> str:
        return settings.get_api_key(provider)

    def _get_tools(self, profile: AgentProfile) -> dict[str, ToolMeta]:
        """Get tools filtered by profile whitelist."""
        if not profile.tools:
            return {}

        filtered = self.tool_registry.filter(profile.tools)
        return {meta.name: meta for meta in filtered}
