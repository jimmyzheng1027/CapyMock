from typing import ClassVar

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # API Keys
    DASHSCOPE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    MIMO_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    _PROVIDER_KEY_MAP: ClassVar[dict[str, str]] = {
        "dashscope": "DASHSCOPE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "mimo": "MIMO_API_KEY",
        "openai": "OPENAI_API_KEY",
    }

    def get_api_key(self, provider: str) -> str:
        attr = self._PROVIDER_KEY_MAP.get(provider, "")
        return getattr(self, attr, "") if attr else ""

    # Tracer
    TRACER: str = "noop"  # "noop" | "langfuse"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_BASE_URL: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"  # legacy alias for LANGFUSE_BASE_URL

    @property
    def langfuse_base_url(self) -> str:
        return self.LANGFUSE_BASE_URL or self.LANGFUSE_HOST

    # Storage
    SQLITE_PATH: str = "storage/db/app.db"
    JSONL_ROOT: str = "storage/sessions"

    # Resume storage
    RESUME_ROOT: str = "data/resumes"

    # Repo analysis & memory
    REPO_ROOT: str = "storage/repo"
    MEMORY_ROOT: str = "storage/memory"
    CLONE_TIMEOUT: int = 120
    MAX_REPO_FILES: int = 10000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
