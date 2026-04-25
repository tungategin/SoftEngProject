"""Activity repository (DB-only operations)."""

from typing import Dict, List, Optional

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
