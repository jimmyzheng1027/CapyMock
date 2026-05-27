from __future__ import annotations

from agent.llm.providers.openai_compatible import OpenAICompatibleLLM


class DeepSeekLLM(OpenAICompatibleLLM):
    """DeepSeek LLM provider using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v4-flash",
        temperature: float = 0.7,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model=model,
            temperature=temperature,
        )

    def _extract_thinking(self, delta: object) -> str | None:
        """Extract reasoning_content from DeepSeek-R1 models."""
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            return delta.reasoning_content
        return None
