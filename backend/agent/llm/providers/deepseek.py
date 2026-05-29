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

