import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv, find_dotenv


# Load .env from project root (or current working tree) before reading settings.
load_dotenv(find_dotenv(usecwd=True), override=False)


@dataclass(frozen=True)
class Settings:
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_service_role_key: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    database_url: Optional[str] = os.getenv("DATABASE_URL")

settings = Settings()
