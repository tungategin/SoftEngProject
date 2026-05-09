"""Activity repository (DB-only operations)."""

from typing import Any, Dict, List, Optional

from app.db.session import get_supabase_client

ACTIVITIES_TABLE = "activities"


def get_activity(course_id: str, activity_no: int) -> Optional[Dict]:
    """Return one activity row by course_id + activity_no."""
    client = get_supabase_client()
    response = (
        client.table(ACTIVITIES_TABLE)
        .select("*")
        .eq("course_id", course_id)
        .eq("activity_no", activity_no)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def list_activities(course_id: str) -> List[Dict]:
    """Return all activities for a course."""
    client = get_supabase_client()
    response = (
        client.table(ACTIVITIES_TABLE)
        .select("*")
        .eq("course_id", course_id)
        .order("activity_no")
        .execute()
    )
    return response.data or []


def create_activity(
    course_id: str,
    activity_no: int,
    text: str,
    learning_objectives: List[str],
) -> Dict:
    """Insert and return a new activity."""
    client = get_supabase_client()
    payload = {
        "course_id": course_id,
        "activity_no": activity_no,
        "text": text,
        "learning_objectives": learning_objectives,
        "status": "NOT_STARTED",
    }
    response = client.table(ACTIVITIES_TABLE).insert(payload).execute()
    rows = response.data or []
    return rows[0] if rows else payload


def update_activity(
    course_id: str,
    activity_no: int,
    patch: Dict[str, Any],
) -> Optional[Dict]:
    """Patch an activity and return the updated row."""
    client = get_supabase_client()
    response = (
        client.table(ACTIVITIES_TABLE)
        .update(patch)
        .eq("course_id", course_id)
        .eq("activity_no", activity_no)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def set_activity_status(
    course_id: str,
    activity_no: int,
    status: str,
) -> Optional[Dict]:
    """Update status for one activity."""
    return update_activity(
        course_id=course_id,
        activity_no=activity_no,
        patch={"status": status},
    )


def get_next_activity_no(course_id: str) -> int:
    """Return next activity number for a course."""
    client = get_supabase_client()
    response = (
        client.table(ACTIVITIES_TABLE)
        .select("activity_no")
        .eq("course_id", course_id)
        .order("activity_no", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return 1
    current = rows[0].get("activity_no")
    if isinstance(current, int):
        return current + 1
    return 1
