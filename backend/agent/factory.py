from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from agent.context.builder import ContextBuilder
from agent.context.compactor import ContextCompactor
from agent.context.skill_loader import SkillLoader
from agent.llm.base import BaseLLM, BaseRealtimeLLM
from agent.llm.factory import LLMFactory
from agent.loop import ReActAgent
from agent.profile import AgentProfile
from agent.profile_loader import ProfileLoader
from config.settings import settings
from storage.session.store import SessionStore
from tool.base import ToolMeta
from tool.executor import ToolExecutor
from tool.registry import ToolRegistry

if TYPE_CHECKING:
    from agent.realtime_agent import RealtimeAgent


class ProfileNotFound(Exception):  # noqa: N818
    """Raised when a profile ID is not found."""
    pass


class RealtimeNotConfigured(Exception):  # noqa: N818
    """Raised when a profile does not have a realtime configuration."""
    pass


class AgentFactory:
    """Factory for creating agent instances (text and voice)."""

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

    # ── Backward-compat dispatch ─────────────────────────────────────

    def create(
        self,
        profile_id: str,
        session_id: str,
        mode: str = "text",
        user_id: str = "default",
        db_session: object | None = None,
        resume_content: str = "",
        github_repos: list[str] | None = None,
        resume_id: str = "",
        capy_note: str = "",
    ) -> ReActAgent:
        """Create an agent instance (backward-compat dispatch).

        mode="voice" → create_realtime_agent()
        mode="text" (default) → create_text_agent()
        """
        if mode == "voice":
            return self.create_realtime_agent(
                profile_id, session_id,
                user_id=user_id,
                resume_content=resume_content,
                github_repos=github_repos,
                resume_id=resume_id,
                capy_note=capy_note,
            )
        return self.create_text_agent(
            profile_id, session_id,
            user_id=user_id,
            db_session=db_session,
            resume_content=resume_content,
            github_repos=github_repos,
            resume_id=resume_id,
        )

    # ── Text agent ───────────────────────────────────────────────────

    def create_text_agent(
        self,
        profile_id: str,
        session_id: str,
        *,
        user_id: str = "default",
        db_session: object | None = None,
        resume_content: str = "",
        github_repos: list[str] | None = None,
        resume_id: str = "",
    ) -> ReActAgent:
        """Create a text-mode ReActAgent."""
        profile = self._get_profile(profile_id)
        llm = self._create_llm(profile)
        tools = self._get_tools(profile)
        context_builder = ContextBuilder(self.skill_loader)
        compactor = ContextCompactor(llm)
        tool_executor = ToolExecutor(default_timeout=profile.policy.tool_timeout)

        agent = ReActAgent(
            profile=profile,
            llm=llm,
            context_builder=context_builder,
            compactor=compactor,
            tool_executor=tool_executor,
            tools=tools,
            session_store=self.session_store,
            user_id=user_id,
            session_id=session_id,
            resume_content=resume_content,
            github_repos=github_repos or [],
            resume_id=resume_id,
        )
        agent._db_session = db_session
        return agent

    # ── Realtime agent ───────────────────────────────────────────────

    def create_realtime_agent(
        self,
        profile_id: str,
        session_id: str,
        *,
        user_id: str = "default",
        resume_content: str = "",
        github_repos: list[str] | None = None,
        resume_id: str = "",
        capy_note: str = "",
    ) -> RealtimeAgent:  # noqa: F821
        """Create a voice-mode RealtimeAgent."""
        from agent.realtime_agent import RealtimeAgent  # noqa: F811

        profile = self._get_profile(profile_id)
        if profile.realtime is None:
            raise RealtimeNotConfigured(
                f"Profile '{profile_id}' does not have realtime configuration"
            )

        realtime_llm = self._create_realtime_llm(profile)
        tools = self._get_tools(profile, allow_list={"save_real_question"})
        instructions = self._build_realtime_instructions(
            profile, resume_content, github_repos or [], capy_note
        )

        return RealtimeAgent(
            profile=profile,
            realtime_llm=realtime_llm,
            session_store=self.session_store,
            tools=tools,
            instructions=instructions,
            subagent_provider=lambda sid, uid: self.create_text_agent(
                profile_id=profile.realtime.midsummary.subagent_profile,
                session_id=sid,
                user_id=uid,
            ),
            user_id=user_id,
            session_id=session_id,
            resume_id=resume_id,
            max_session_minutes=profile.realtime.max_session_minutes,
        )

    # ── Internal helpers ─────────────────────────────────────────────

    def _get_profile(self, profile_id: str) -> AgentProfile:
        profile = self.profile_loader.get(profile_id)
        if profile is None:
            raise ProfileNotFound(f"Profile not found: {profile_id}")
        return profile

    def _create_llm(self, profile: AgentProfile) -> BaseLLM:
        api_key = self._get_api_key(profile.llm.provider)
        return LLMFactory.create(
            profile.llm.provider,
            {
                "api_key": api_key,
                "model": profile.llm.model,
                "temperature": profile.llm.temperature,
            },
        )

    def _create_realtime_llm(self, profile: AgentProfile) -> BaseRealtimeLLM:
        provider = profile.realtime.provider
        api_key = self._get_api_key(provider)
        if not api_key:
            env_name = settings._PROVIDER_KEY_MAP.get(provider, "API_KEY")
            raise RealtimeNotConfigured(
                f"语音面试需要配置 {env_name}，请在 backend/.env 中设置"
            )
        llm = LLMFactory.create(
            provider,
            {
                "api_key": api_key,
                "model": profile.realtime.model,
            },
        )
        if not isinstance(llm, BaseRealtimeLLM):
            raise RealtimeNotConfigured(
                f"Provider '{provider}' does not implement BaseRealtimeLLM"
            )
        return llm

    def _build_realtime_instructions(
        self,
        profile: AgentProfile,
        resume_content: str,
        github_repos: list,
        capy_note: str,
    ) -> str:
        """Build instructions for the realtime agent."""
        parts = []

        # Load prompt template
        try:
            prompt_path = Path(profile.prompt_template)
            if prompt_path.exists():
                parts.append(prompt_path.read_text(encoding="utf-8"))
        except Exception:
            pass

        if resume_content:
            parts.append(f"[简历]\n{resume_content}")

        if github_repos:
            repo_texts = []
            for repo in github_repos:
                if isinstance(repo, str):
                    repo_texts.append(repo)
                else:
                    repo_texts.append(json.dumps(repo, ensure_ascii=False))
            parts.append(f"[GitHub 仓库分析]\n{chr(10).join(repo_texts)}")

        if capy_note:
            parts.append(f"[用户历史画像]\n{capy_note}")

        parts.append(
            "[行为规则]\n"
            "- 你只能调用 save_real_question 工具记录用户提到的真实面试题\n"
            "- 不要询问用户的简历内容，简历已在上方\n"
            "- 用自然口语提问，像真人面试官一样\n"
            "- 可以随时打断用户（barge-in），但要有礼貌\n"
            "- 若对话历史中已有文字模式往来（用户从文字切到语音），不要重新自我介绍或换全新开场题；"
            "接续最后一个尚未被用户充分回答的追问，简短提醒后等待用户语音作答，在用户回答前不要提出新的主问题"
        )

        return "\n\n".join(parts)

    def _get_api_key(self, provider: str) -> str:
        return settings.get_api_key(provider)

    def _get_tools(
        self, profile: AgentProfile, allow_list: set[str] | None = None
    ) -> dict[str, ToolMeta]:
        """Get tools filtered by profile whitelist and optional allow_list."""
        if not profile.tools:
            return {}

        tool_names = set(profile.tools)
        if allow_list is not None:
            tool_names = tool_names & allow_list

        filtered = self.tool_registry.filter(list(tool_names))
        return {meta.name: meta for meta in filtered}
