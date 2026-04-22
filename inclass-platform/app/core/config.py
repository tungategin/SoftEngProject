import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    database_url: str | None = os.getenv("DATABASE_URL")

settings = Settings()
