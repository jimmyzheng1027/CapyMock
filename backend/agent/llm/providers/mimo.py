from __future__ import annotations

from agent.llm.providers.openai_compatible import OpenAICompatibleLLM

# Models that use MiMo thinking mode (reasoning_content + tool_calls).
THINKING_MODELS = frozenset({
    "mimo-v2.5-pro",
    "mimo-v2.5",
    "mimo-v2-pro",
})


class MiMoLLM(OpenAICompatibleLLM):
    """MiMo LLM provider (Xiaomi) using OpenAI-compatible API.

    Tool streaming uses OpenAICompatibleLLM (index-based argument merge).
    MiMo-specific: thinking extra_body, temperature, reasoning_content buffer.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "mimo-v2.5-pro",
        temperature: float = 1.0,
        top_p: float = 0.95,
        enable_thinking: bool | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url="https://token-plan-cn.xiaomimimo.com/v1",
            model=model,
            temperature=temperature,
        )
        self.top_p = top_p
        self.enable_thinking = (
            enable_thinking if enable_thinking is not None else model in THINKING_MODELS
        )
        self._reasoning_buffer: str = ""

    def begin_stream_turn(self) -> None:
        """Reset per-turn state before a new LLM stream (called from ReAct loop)."""
        self._reasoning_buffer = ""

    def consume_reasoning_for_message(self) -> str:
        """Return accumulated reasoning_content for the assistant message, then clear."""
        reasoning = self._reasoning_buffer
        self._reasoning_buffer = ""
        return reasoning

    def _on_thinking_delta(self, delta: str) -> None:
        self._reasoning_buffer += delta

    def _extra_request_params(self) -> dict:
        params: dict = {"top_p": self.top_p}
        if self.enable_thinking:
            # OpenAI SDK rejects unknown top-level fields; MiMo reads thinking from body.
            params["extra_body"] = {"thinking": {"type": "enabled"}}
            # MiMo docs: thinking mode does not support custom temperature on pro models.
            params["temperature"] = 1.0
        return params
