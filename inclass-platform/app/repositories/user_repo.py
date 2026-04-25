"""User repository helpers."""

from __future__ import annotations

from typing import Any

from app.db.session import get_supabase_client

USERS_TABLE = "users"


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Fetch a user by email from the users table.

    Returns:
        A user dict when found, otherwise None.
    """
    client = get_supabase_client()
    response = (
        client.table(USERS_TABLE)
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None
