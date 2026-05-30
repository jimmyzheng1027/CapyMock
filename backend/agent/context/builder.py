from __future__ import annotations

import json
from pathlib import Path

from agent.context.skill_loader import SkillLoader
from agent.profile import AgentProfile
from api.schemas import EventType, FrontendEvent


class ContextBuilder:
    """Builds LLM context from session events and profile."""

    def __init__(self, skill_loader: SkillLoader) -> None:
        self.skill_loader = skill_loader
        self._memory_root: str = "storage/memory"

    def build_messages(
        self,
        profile: AgentProfile,
        events: list[FrontendEvent],
        current_input: str | None = None,
        resume_content: str | None = None,
        user_id: str | None = None,
        resume_id: str | None = None,
    ) -> list[dict]:
        """Build messages list for LLM from profile and session events.

        Args:
            profile: Agent profile with prompt template and skills
            events: List of session events
            current_input: Current user input (if any)
            resume_content: Resume content to inject into system prompt
            user_id: User ID for memory lookup
            resume_id: Resume ID for memory lookup

        Returns:
            List of message dicts for LLM API
        """
        messages = []

        # 1. System prompt (with resume + memory injection)
        system_prompt = self._build_system_prompt(
            profile, resume_content=resume_content,
            user_id=user_id, resume_id=resume_id,
        )
        messages.append({"role": "system", "content": system_prompt})

        # 2. Build conversation history from events
        history = self._build_history(events)
        messages.extend(history)

        # 3. Add current user input
        if current_input:
            messages.append({"role": "user", "content": current_input})

        return messages

    def _build_system_prompt(
        self,
        profile: AgentProfile,
        resume_content: str | None = None,
        user_id: str | None = None,
        resume_id: str | None = None,
    ) -> str:
        """Build the system prompt from profile, skills, resume, and memory."""
        # Read prompt template
        prompt_path = Path(profile.prompt_template)
        if prompt_path.exists():
            base_prompt = prompt_path.read_text(encoding="utf-8")
        else:
            base_prompt = f"You are {profile.id}, an AI interviewer."

        # Add skill summaries
        skill_summaries = self._get_skill_summaries(profile)
        if skill_summaries:
            base_prompt += "\n\n## Available Skills\n"
            for skill_id, summary in skill_summaries:
                base_prompt += f"- **{skill_id}**: {summary}\n"

        # Inject resume content
        if resume_content:
            base_prompt += f"\n\n## 用户简历\n{resume_content}\n"

        # Inject memory files
        if user_id and resume_id:
            memory = self._load_memory(user_id, resume_id)
            if memory:
                base_prompt += memory

        return base_prompt

    def _load_memory(self, user_id: str, resume_id: str) -> str:
        """Load and format memory files for injection."""
        from storage.memory.store import MemoryStore

        store = MemoryStore(root_dir=self._memory_root)
        parts = []

        user_md = store.read_user(user_id)
        if user_md:
            parts.append(f"\n\n## 用户记忆\n{user_md}")

        capy_note = store.read_capy_note(user_id, resume_id)
        if capy_note:
            parts.append(f"\n\n## 面试官记忆\n{capy_note}")

        real_ques = store.read_real_ques(user_id, resume_id)
        if real_ques:
            parts.append(f"\n\n## 真实面试题\n{real_ques}")

        return "".join(parts)

    def _get_skill_summaries(self, profile: AgentProfile) -> list[tuple[str, str]]:
        """Get skill summaries for the profile's skill whitelist."""
        summaries = []
        for skill_id in profile.skills:
            skill = self.skill_loader.get_skill(skill_id)
            if skill:
                summaries.append((skill_id, skill.get("description", "")))
        return summaries

    def _build_history(self, events: list[FrontendEvent]) -> list[dict]:
        """Build conversation history from session events."""
        messages = []
        current_assistant_text = ""

        for event in events:
            if event.type == EventType.USER_TEXT:
                # Add user message
                messages.append({
                    "role": "user",
                    "content": event.payload.get("text", ""),
                })
            elif event.type == EventType.ASSISTANT_TEXT_DONE:
                # Add assistant message (complete text)
                text = event.payload.get("text", "")
                if event.payload.get("partial", False):
                    # Partial message - add as-is with note
                    text += "\n[Response was interrupted]"
                messages.append({
                    "role": "assistant",
                    "content": text,
                })
            elif event.type == EventType.TOOL_RESULT:
                # Add tool result with proper tool role
                payload = event.payload
                content = json.dumps(payload.get("data") or payload.get("error", {}))
                messages.append({
                    "role": "tool",
                    "tool_call_id": payload.get("tool_call_id", ""),
                    "content": content,
                })
            elif event.type == EventType.SESSION_COMPACTED:
                # Replace history with summary
                summary = event.payload.get("summary_text", "")
                if summary:
                    messages = [
                        {"role": "system", "content": f"Previous conversation summary:\n{summary}"}
                    ]

        return messages
