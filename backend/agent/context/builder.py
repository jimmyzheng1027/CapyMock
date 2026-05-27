from __future__ import annotations

from pathlib import Path

from agent.context.skill_loader import SkillLoader
from agent.profile import AgentProfile
from api.schemas import EventType, FrontendEvent


class ContextBuilder:
    """Builds LLM context from session events and profile."""

    def __init__(self, skill_loader: SkillLoader) -> None:
        self.skill_loader = skill_loader

    def build_messages(
        self,
        profile: AgentProfile,
        events: list[FrontendEvent],
        current_input: str | None = None,
    ) -> list[dict]:
        """Build messages list for LLM from profile and session events.

        Args:
            profile: Agent profile with prompt template and skills
            events: List of session events
            current_input: Current user input (if any)

        Returns:
            List of message dicts for LLM API
        """
        messages = []

        # 1. System prompt
        system_prompt = self._build_system_prompt(profile)
        messages.append({"role": "system", "content": system_prompt})

        # 2. Build conversation history from events
        history = self._build_history(events)
        messages.extend(history)

        # 3. Add current user input
        if current_input:
            messages.append({"role": "user", "content": current_input})

        return messages

    def _build_system_prompt(self, profile: AgentProfile) -> str:
        """Build the system prompt from profile and skills."""
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

        return base_prompt

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
                # Add tool result as user message (tool role)
                tool_name = event.payload.get("tool_name", "unknown")
                result = event.payload.get("result", {})
                messages.append({
                    "role": "user",
                    "content": f"Tool result from {tool_name}: {result}",
                })
            elif event.type == EventType.SESSION_COMPACTED:
                # Replace history with summary
                summary = event.payload.get("summary_text", "")
                if summary:
                    messages = [
                        {"role": "system", "content": f"Previous conversation summary:\n{summary}"}
                    ]

        return messages
