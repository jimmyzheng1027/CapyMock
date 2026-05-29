from __future__ import annotations

from agent.llm.providers.openai_compatible import OpenAICompatibleLLM


class DashScopeCompatLLM(OpenAICompatibleLLM):
    """DashScope LLM provider using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen-max",
        temperature: float = 0.7,
        enable_thinking: bool = False,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=model,
            temperature=temperature,
        )
        self.enable_thinking = enable_thinking

    def _extra_request_params(self) -> dict:
        """Inject DashScope-specific parameters."""
        params: dict = {}
        if self.enable_thinking:
            params["extra_body"] = {"enable_thinking": True}
        return params

