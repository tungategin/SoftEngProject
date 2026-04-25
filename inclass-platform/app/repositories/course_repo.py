"""Course repository helpers."""

from typing import Optional

from app.db.session import get_supabase_client

COURSE_AUTHORIZATIONS_TABLE = "course_authorizations"


def has_course_authorization(
    *,
    course_id: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
) -> bool:
    """Check whether a user is assigned to a course.

    Supports either `user_id` or `user_email` to stay resilient to minor schema
    differences while keeping one centralized check.
    """
    if not user_id and not user_email:
        return False

    client = get_supabase_client()
    query = (
        client.table(COURSE_AUTHORIZATIONS_TABLE)
        .select("course_id", count="exact")
        .eq("course_id", course_id)
    )

    if user_id:
        query = query.eq("user_id", user_id)
    else:
        query = query.eq("user_email", user_email)

    response = query.limit(1).execute()
    if response.count is not None:
        return response.count > 0
    return bool(response.data)
