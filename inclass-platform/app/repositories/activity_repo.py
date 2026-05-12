"""Activity repository (DB-only operations)."""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db.session import get_supabase_client

ACTIVITIES_TABLE = "activities"
OBJECTIVES_TABLE = "activity_objectives"


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
    if not rows:
        return None
    return _to_contract_activity(client, rows[0])


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
    rows = response.data or []
    result = []
    for row in rows:
        result.append(_to_contract_activity(client, row))
    return result


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
        "activity_text": text,
        "status": "NOT_STARTED",
    }
    response = client.table(ACTIVITIES_TABLE).insert(payload).execute()
    rows = response.data or []
    if not rows:
        return {
            "course_id": course_id,
            "activity_no": activity_no,
            "text": text,
            "learning_objectives": learning_objectives,
            "status": "NOT_STARTED",
        }
    created_row = rows[0]
    activity_id = created_row.get("id")
    if activity_id:
        _replace_objectives(client, str(activity_id), learning_objectives)
    return _to_contract_activity(client, created_row)


def update_activity(
    course_id: str,
    activity_no: int,
    patch: Dict[str, Any],
) -> Optional[Dict]:
    """Patch an activity and return the updated row."""
    client = get_supabase_client()
    db_patch = {}
    if "text" in patch:
        db_patch["activity_text"] = patch["text"]
    if "status" in patch:
        db_patch["status"] = patch["status"]

    row = None
    if db_patch:
        response = (
            client.table(ACTIVITIES_TABLE)
            .update(db_patch)
            .eq("course_id", course_id)
            .eq("activity_no", activity_no)
            .execute()
        )
        rows = response.data or []
        row = rows[0] if rows else None
    else:
        response = (
            client.table(ACTIVITIES_TABLE)
            .select("*")
            .eq("course_id", course_id)
            .eq("activity_no", activity_no)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        row = rows[0] if rows else None

    if row is None:
        return None

    if "learning_objectives" in patch:
        activity_id = row.get("id")
        if activity_id:
            new_objectives = patch.get("learning_objectives", [])
            if isinstance(new_objectives, list):
                _replace_objectives(client, str(activity_id), new_objectives)

    return _to_contract_activity(client, row)


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


def mark_activity_reset(course_id: str, activity_no: int) -> Optional[Dict]:
    """Set activity to ENDED and stamp reset/ended timestamps."""
    client = get_supabase_client()
    timestamp = datetime.now(timezone.utc).isoformat()
    response = (
        client.table(ACTIVITIES_TABLE)
        .update(
            {
                "status": "ENDED",
                "ended_at": timestamp,
                "reset_at": timestamp,
            },
        )
        .eq("course_id", course_id)
        .eq("activity_no", activity_no)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None
    return _to_contract_activity(client, rows[0])


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


def _to_contract_activity(client: Any, row: Dict[str, Any]) -> Dict[str, Any]:
    activity_id = row.get("id")
    objectives = []
    if activity_id is not None:
        objectives = _load_objectives(client, str(activity_id))
    return {
        "id": row.get("id"),
        "course_id": row.get("course_id"),
        "activity_no": row.get("activity_no"),
        "text": row.get("activity_text") if row.get("activity_text") is not None else row.get("text"),
        "learning_objectives": objectives,
        "status": row.get("status"),
    }


def _load_objectives(client: Any, activity_id: str) -> List[str]:
    response = (
        client.table(OBJECTIVES_TABLE)
        .select("description,objective_key,display_order")
        .eq("activity_id", activity_id)
        .eq("is_active", True)
        .order("display_order")
        .execute()
    )
    rows = response.data or []
    objectives = []
    for row in rows:
        description = row.get("description")
        if isinstance(description, str) and description.strip() != "":
            objectives.append(description.strip())
            continue
        objective_key = row.get("objective_key")
        if isinstance(objective_key, str) and objective_key.strip() != "":
            objectives.append(objective_key.strip())
    return objectives


def _replace_objectives(client: Any, activity_id: str, learning_objectives: List[str]) -> None:
    (
        client.table(OBJECTIVES_TABLE)
        .update({"is_active": False})
        .eq("activity_id", activity_id)
        .eq("is_active", True)
        .execute()
    )

    payload_rows = []
    index = 1
    for value in learning_objectives:
        description = str(value).strip()
        if description == "":
            continue
        payload_rows.append(
            {
                "activity_id": activity_id,
                "objective_key": _objective_key(description, index),
                "description": description,
                "display_order": index,
                "is_active": True,
            },
        )
        index += 1

    if payload_rows:
        client.table(OBJECTIVES_TABLE).insert(payload_rows).execute()


def _objective_key(description: str, index: int) -> str:
    lowered = description.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    if cleaned == "":
        cleaned = "objective"
    return "{0}_{1}".format(cleaned, index)
