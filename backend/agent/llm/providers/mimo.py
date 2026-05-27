from __future__ import annotations

from agent.llm.providers.openai_compatible import OpenAICompatibleLLM


class MiMoLLM(OpenAICompatibleLLM):
    """MiMo LLM provider (Xiaomi) using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "mimo-v2.5-pro",
        temperature: float = 1.0,
        top_p: float = 0.95,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url="https://api.xiaomimimo.com/v1",
            model=model,
            temperature=temperature,
        )
        self.top_p = top_p

    def _extra_request_params(self) -> dict:
        return {"top_p": self.top_p}
