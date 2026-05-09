"""Score repository (DB-only operations)."""

from typing import Any, Dict, List, Optional

from app.db.session import get_supabase_client

SCORE_LOGS_TABLE = "score_logs"


def log_score(
    course_id: str,
    activity_no: int,
    student_id: str,
    student_email: str,
    score: float,
    meta: Optional[str] = None,
) -> Dict:
    """Insert and return one score log row."""
    client = get_supabase_client()
    payload = {
        "course_id": course_id,
        "activity_no": activity_no,
        "student_id": student_id,
        "student_email": student_email,
        "score": score,
        "meta": meta,
    }
    response = client.table(SCORE_LOGS_TABLE).insert(payload).execute()
    rows = response.data or []
    return rows[0] if rows else payload


def list_scores(course_id: str, activity_no: int) -> List[Dict]:
    """Return all score rows for one activity."""
    client = get_supabase_client()
    response = (
        client.table(SCORE_LOGS_TABLE)
        .select("*")
        .eq("course_id", course_id)
        .eq("activity_no", activity_no)
        .order("student_email")
        .execute()
    )
    return response.data or []


def delete_scores(course_id: str, activity_no: int) -> int:
    """Delete all score rows for one activity and return deleted count."""
    client = get_supabase_client()
    existing = list_scores(course_id=course_id, activity_no=activity_no)
    (
        client.table(SCORE_LOGS_TABLE)
        .delete()
        .eq("course_id", course_id)
        .eq("activity_no", activity_no)
        .execute()
    )
    return len(existing)
