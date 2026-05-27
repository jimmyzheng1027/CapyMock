from __future__ import annotations

from agent.llm.base import BaseLLM
from agent.llm.events import TextDelta
from agent.profile import AgentProfile


class ContextCompactor:
    """Compacts conversation history when it exceeds token threshold."""

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    async def compact(
        self,
        profile: AgentProfile,
        messages: list[dict],
        kept_recent_turns: int = 3,
    ) -> tuple[str, list[dict]]:
        """Compact conversation history by summarizing older messages.

        Args:
            profile: Agent profile with context config
            messages: Current message list
            kept_recent_turns: Number of recent turns to keep verbatim

        Returns:
            Tuple of (summary_text, compacted_messages)
        """
        if len(messages) <= kept_recent_turns + 1:  # +1 for system message
            return "", messages

        # Split into old messages (to summarize) and recent messages (to keep)
        system_message = messages[0] if messages[0]["role"] == "system" else None
        non_system_messages = [m for m in messages if m["role"] != "system"]

        if len(non_system_messages) <= kept_recent_turns:
            return "", messages

        old_messages = non_system_messages[:-kept_recent_turns]
        recent_messages = non_system_messages[-kept_recent_turns:]

        # Build summary prompt
        summary_prompt = self._build_summary_prompt(old_messages)

        # Call LLM to generate summary
        summary_text = await self._generate_summary(summary_prompt)

        # Rebuild messages with summary
        compacted = []
        if system_message:
            compacted.append(system_message)
        compacted.append({
            "role": "system",
            "content": f"Previous conversation summary:\n{summary_text}",
        })
        compacted.extend(recent_messages)

        return summary_text, compacted

    def _build_summary_prompt(self, messages: list[dict]) -> str:
        """Build a prompt for summarizing old messages."""
        conversation = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            conversation += f"{role}: {content}\n\n"

        return f"""Please summarize the following conversation concisely, preserving key information:

{conversation}

Summary:"""

    async def _generate_summary(self, prompt: str) -> str:
        """Generate a summary using the LLM."""
        messages = [{"role": "user", "content": prompt}]
        summary_parts = []

        async for event in self.llm.stream(messages):
            if isinstance(event, TextDelta):
                summary_parts.append(event.delta)

        return "".join(summary_parts)

    def estimate_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for messages.

        This is a rough estimation (4 chars ≈ 1 token).
        """
        total_chars = 0
        for msg in messages:
            total_chars += len(msg.get("role", ""))
            total_chars += len(msg.get("content", ""))

        return total_chars // 4

    def should_compact(self, profile: AgentProfile, messages: list[dict]) -> bool:
        """Check if messages exceed the compact threshold."""
        estimated_tokens = self.estimate_tokens(messages)
        return estimated_tokens > profile.context.compact_threshold
