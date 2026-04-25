"""Course repository (DB-only operations)."""

from typing import Dict, List

from app.db.session import get_supabase_client

COURSES_TABLE = "courses"
COURSE_AUTHORIZATIONS_TABLE = "course_authorizations"


def get_courses_for_user(user_id: str) -> List[Dict]:
    """Return courses assigned to a user via course_authorizations + courses."""
    client = get_supabase_client()

    # Preferred relational query (join-like in Supabase)
    auth_response = (
        client.table(COURSE_AUTHORIZATIONS_TABLE)
        .select("course_id, courses(*)")
        .eq("user_id", user_id)
        .execute()
    )
    auth_rows = auth_response.data or []

    courses = []
    course_ids = []
    for row in auth_rows:
        nested_course = row.get("courses")
        if isinstance(nested_course, dict):
            courses.append(nested_course)
        course_id = row.get("course_id")
        if isinstance(course_id, str):
            course_ids.append(course_id)

    if courses:
        return courses
    if not course_ids:
        return []

    # Fallback: second query if nested relation is not configured in Supabase.
    courses_response = (
        client.table(COURSES_TABLE)
        .select("*")
        .in_("id", course_ids)
        .execute()
    )
    return courses_response.data or []


def is_user_in_course(user_id: str, course_id: str) -> bool:
    """Return True when user has authorization for the course."""
    client = get_supabase_client()
    response = (
        client.table(COURSE_AUTHORIZATIONS_TABLE)
        .select("course_id", count="exact")
        .eq("user_id", user_id)
        .eq("course_id", course_id)
        .limit(1)
        .execute()
    )

    if response.count is not None:
        return response.count > 0
    return bool(response.data)
