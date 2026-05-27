from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # API Keys
    DASHSCOPE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    MIMO_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Tracer
    TRACER: str = "noop"  # "noop" | "langfuse"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"

    # Storage
    SQLITE_PATH: str = "backend/storage/sessions.db"
    JSONL_ROOT: str = "backend/storage/sessions"

    # Resume storage
    RESUME_ROOT: str = "backend/data/resumes"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
