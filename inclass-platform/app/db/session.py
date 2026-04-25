"""Supabase client lifecycle helpers.

This module keeps Supabase client creation centralized so the rest of the code
does not duplicate connection bootstrap logic.
"""

from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings

_supabase_client: Client | None = None


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

    _supabase_client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
    return _supabase_client
