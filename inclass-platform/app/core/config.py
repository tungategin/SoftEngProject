import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_service_role_key: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    database_url: Optional[str] = os.getenv("DATABASE_URL")

settings = Settings()
