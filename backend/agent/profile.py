from __future__ import annotations

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration for an agent profile."""

    provider: str
    model: str
    temperature: float = 0.7
    fallback: LLMConfig | None = None


class ContextConfig(BaseModel):
    """Context configuration for an agent profile."""

    max_history_tokens: int = 8000
    compact_threshold: int = 6000


class PolicyConfig(BaseModel):
    """Policy configuration for an agent profile."""

    max_steps: int = 10
    parallel_tools: int = 3
    tool_timeout: float = 30.0


class RealtimeTranscriptionConfig(BaseModel):
    """Transcription config for realtime voice mode."""

    enabled: bool = True
    model: str = "whisper"


class RealtimeMidSummaryConfig(BaseModel):
    """MidSummary config for realtime voice mode."""

    enabled: bool = True
    interval_minutes: int = 8
    subagent_profile: str = "mid-summary-injector"
    timeout_seconds: int = 5


class RealtimeConfig(BaseModel):
    """Realtime voice mode configuration."""

    provider: str
    model: str
    voice: str = "alloy"
    vad_mode: str = "semantic"  # semantic / server / none
    vad_threshold: float = 0.5
    transcription: RealtimeTranscriptionConfig = Field(default_factory=RealtimeTranscriptionConfig)
    max_session_minutes: int = 15
    midsummary: RealtimeMidSummaryConfig = Field(default_factory=RealtimeMidSummaryConfig)


class AgentProfile(BaseModel):
    """Agent profile loaded from YAML configuration."""

    id: str
    prompt_template: str
    llm: LLMConfig
    tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    context: ContextConfig = Field(default_factory=ContextConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    realtime: RealtimeConfig | None = None
