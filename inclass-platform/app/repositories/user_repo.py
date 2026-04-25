"""User repository (DB-only operations)."""

from typing import Dict, Optional

from app.db.session import get_supabase_client

USERS_TABLE = "users"


def get_user_by_email(email: str) -> Optional[Dict]:
    """Return the first user row that matches email, otherwise None."""
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


def update_password(user_id: str, new_password: str) -> None:
    """Update password_hash for a single user."""
    client = get_supabase_client()
    (
        client.table(USERS_TABLE)
        .update({"password_hash": new_password})
        .eq("id", user_id)
        .execute()
    )


def verify_password(user: Dict, password: str) -> bool:
    """Temporary plain comparison; replace with hashing in later phase."""
    stored_password = user.get("password_hash")
    return isinstance(stored_password, str) and stored_password == password
