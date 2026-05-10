import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv, find_dotenv


# Load .env from project root (or current working tree) before reading settings.
load_dotenv(find_dotenv(usecwd=True), override=False)


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except Exception:
        return default


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_service_role_key: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    openrouter_model: Optional[str] = os.getenv("OPENROUTER_MODEL")
    openrouter_base_url: str = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    )
    openrouter_timeout_seconds: float = _float_env("OPENROUTER_TIMEOUT_SECONDS", 20.0)
    openrouter_max_retries: int = _int_env("OPENROUTER_MAX_RETRIES", 1)
    openrouter_max_completion_tokens: int = _int_env("OPENROUTER_MAX_COMPLETION_TOKENS", 900)
    openrouter_debug: bool = os.getenv("OPENROUTER_DEBUG", "false").lower() == "true"

settings = Settings()
