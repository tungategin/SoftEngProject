"""Supabase client lifecycle helpers.

This module keeps Supabase client creation centralized so the rest of the code
does not duplicate connection bootstrap logic.
"""

from supabase import Client, create_client
from typing import Optional

from app.core.config import settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return a singleton Supabase client.

    Raises:
        RuntimeError: If required Supabase environment variables are missing.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not settings.supabase_url:
        raise RuntimeError("Missing required environment variable: SUPABASE_URL")
    if not settings.supabase_service_role_key:
        raise RuntimeError(
            "Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY",
        )

    try:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to initialize Supabase client. "
            "Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY values. "
            "For supabase-py, use a valid JWT-style anon/service_role key.",
        ) from exc
    return _supabase_client
