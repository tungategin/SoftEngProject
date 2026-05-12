"""Score repository (DB-only operations)."""

import json
from typing import Any, Dict, List, Optional

from app.db.session import get_supabase_client

SCORE_LOGS_TABLE = "score_logs"
ACTIVITIES_TABLE = "activities"
OBJECTIVES_TABLE = "activity_objectives"
USERS_TABLE = "users"
STUDENT_PROGRESS_TABLE = "student_progress"
MANUAL_GRADE_EVENTS_TABLE = "manual_grade_events"

SCORE_SOURCE_TUTORING_FLOW = "TUTORING_FLOW"
SCORE_SOURCE_MANUAL_GRADE = "MANUAL_GRADE"
SCORE_SOURCE_RESET_ADJUSTMENT = "RESET_ADJUSTMENT"


def log_score(
    course_id: str,
    activity_no: int,
    student_id: str,
    student_email: str,
    score: float,
    meta: Optional[str] = None,
    source: str = SCORE_SOURCE_TUTORING_FLOW,
    actor_user_id: Optional[str] = None,
    objective_id: Optional[str] = None,
) -> Dict:
    """Insert and return one score log row."""
    client = get_supabase_client()
    activity = _get_activity_row(client, course_id, activity_no)
    if activity is None:
        raise RuntimeError("Activity not found for score insert.")
    activity_id = activity["id"]

    score_delta = int(round(float(score)))
    if score_delta == 0:
        raise RuntimeError("Score delta must not be zero.")

    score_before = _get_current_score(client, student_id, activity_id)
    score_after = score_before + score_delta

    resolved_objective_id = objective_id
    if resolved_objective_id is None:
        resolved_objective_id = _resolve_objective_id(client, activity_id, meta)

    meta_payload = _build_meta_payload(meta, activity_no, student_email)

    payload = {
        "student_id": student_id,
        "course_id": course_id,
        "activity_id": activity_id,
        "objective_id": resolved_objective_id,
        "score_before": score_before,
        "score_delta": score_delta,
        "score_after": score_after,
        "meta": meta_payload,
        "source": source,
    }
    if actor_user_id:
        payload["actor_user_id"] = actor_user_id

    print("[DEBUG][REPO][score_repo.log_score] insert payload:", payload)
    response = client.table(SCORE_LOGS_TABLE).insert(payload).execute()
    rows = response.data or []
    inserted = rows[0] if rows else payload

    inserted_log_id = inserted.get("id") if isinstance(inserted, dict) else None
    _upsert_student_progress(
        client=client,
        student_id=student_id,
        activity_id=activity_id,
        score_after=score_after,
        objective_id=resolved_objective_id,
        score_log_id=str(inserted_log_id) if inserted_log_id else None,
    )
    return inserted


def create_manual_grade_event(
    instructor_id: str,
    student_id: str,
    course_id: str,
    activity_id: str,
    manual_score: int,
    reason: str,
    score_log_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Insert one manual grade event row."""
    client = get_supabase_client()

    payload = {
        "instructor_id": instructor_id,
        "student_id": student_id,
        "course_id": course_id,
        "activity_id": activity_id,
        "manual_score": manual_score,
        "reason": reason,
        "meta": meta if isinstance(meta, dict) else {},
    }
    if score_log_id:
        payload["score_log_id"] = score_log_id

    response = client.table(MANUAL_GRADE_EVENTS_TABLE).insert(payload).execute()
    rows = response.data or []
    return rows[0] if rows else payload


def get_activity_id(course_id: str, activity_no: int) -> Optional[str]:
    """Return activity id for a course+activity number."""
    client = get_supabase_client()
    row = _get_activity_row(client, course_id, activity_no)
    if row is None:
        return None
    value = row.get("id")
    if value is None:
        return None
    return str(value)


def get_completion_state(course_id: str, activity_no: int, student_id: str) -> Dict[str, Any]:
    """Return objective completion state for one student in one activity."""
    client = get_supabase_client()
    activity = _get_activity_row(client, course_id, activity_no)
    if activity is None:
        return {
            "activity_exists": False,
            "activity_id": None,
            "total_objectives": 0,
            "completed_objective_ids": [],
            "completed_count": 0,
            "current_score": 0,
            "is_completed": False,
        }

    activity_id = str(activity["id"])
    total_objectives = _get_objective_count(client, activity_id)
    progress_row = _get_progress_row(client, student_id, activity_id)

    if not progress_row:
        return {
            "activity_exists": True,
            "activity_id": activity_id,
            "total_objectives": total_objectives,
            "completed_objective_ids": [],
            "completed_count": 0,
            "current_score": 0,
            "is_completed": False,
        }

    completed_ids = progress_row.get("completed_objective_ids", [])
    if not isinstance(completed_ids, list):
        completed_ids = []

    normalized_ids = []
    for value in completed_ids:
        if value is None:
            continue
        normalized_ids.append(str(value))

    current_score = progress_row.get("current_score", 0)
    try:
        normalized_score = int(current_score)
    except Exception:
        normalized_score = 0

    is_completed = bool(progress_row.get("is_completed", False))
    if total_objectives > 0 and len(normalized_ids) >= total_objectives:
        is_completed = True

    return {
        "activity_exists": True,
        "activity_id": activity_id,
        "total_objectives": total_objectives,
        "completed_objective_ids": normalized_ids,
        "completed_count": len(normalized_ids),
        "current_score": normalized_score,
        "is_completed": is_completed,
    }


def resolve_objective(
    course_id: str,
    activity_no: int,
    meta: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Resolve objective row from a meta/objective label."""
    client = get_supabase_client()
    activity = _get_activity_row(client, course_id, activity_no)
    if activity is None:
        return None

    activity_id = str(activity["id"])
    rows = _list_objective_rows(client, activity_id)
    if len(rows) == 0:
        return None

    if not isinstance(meta, str) or meta.strip() == "":
        return None

    target = meta.strip().lower()
    target_tokens = _normalize_tokens(target)

    exact_match = None
    for row in rows:
        description = str(row.get("description", "")).strip().lower()
        objective_key = str(row.get("objective_key", "")).strip().lower()
        if target == description or target == objective_key:
            exact_match = row
            break
    if exact_match is not None:
        return exact_match

    contains_match = None
    for row in rows:
        description = str(row.get("description", "")).strip().lower()
        objective_key = str(row.get("objective_key", "")).strip().lower()
        if target in description or description in target:
            contains_match = row
            break
        if target in objective_key or objective_key in target:
            contains_match = row
            break
    if contains_match is not None:
        return contains_match

    best_row = None
    best_score = 0
    for row in rows:
        description = str(row.get("description", "")).strip().lower()
        objective_key = str(row.get("objective_key", "")).strip().lower()
        objective_tokens = _normalize_tokens("{0} {1}".format(description, objective_key))
        if len(objective_tokens) == 0:
            continue

        overlap = 0
        for token in objective_tokens:
            if token in target_tokens:
                overlap += 1

        if overlap > best_score:
            best_score = overlap
            best_row = row

    if best_row is not None and best_score >= 2:
        return best_row
    return None


def pick_next_unscored_objective(
    course_id: str,
    activity_no: int,
    student_id: str,
) -> Optional[Dict[str, Any]]:
    """Pick first objective not yet completed by this student."""
    state = get_completion_state(course_id, activity_no, student_id)
    if not state.get("activity_exists", False):
        return None

    activity_id = state.get("activity_id")
    if not isinstance(activity_id, str):
        return None

    completed = state.get("completed_objective_ids", [])
    if not isinstance(completed, list):
        completed = []
    completed_set = set([str(value) for value in completed])

    client = get_supabase_client()
    rows = _list_objective_rows(client, activity_id)
    for row in rows:
        objective_id = row.get("id")
        if objective_id is None:
            continue
        if str(objective_id) not in completed_set:
            return row
    return None


def is_objective_completed(
    course_id: str,
    activity_no: int,
    student_id: str,
    objective_id: str,
) -> bool:
    """Return True when objective_id is already completed in student_progress."""
    state = get_completion_state(course_id, activity_no, student_id)
    completed = state.get("completed_objective_ids", [])
    if not isinstance(completed, list):
        return False
    target = str(objective_id)
    for value in completed:
        if str(value) == target:
            return True
    return False


def find_existing_score_log(
    course_id: str,
    activity_no: int,
    student_id: str,
    meta: Optional[str] = None,
) -> Optional[Dict]:
    """Return one existing score row for the same student/activity/meta if present."""
    client = get_supabase_client()
    activity = _get_activity_row(client, course_id, activity_no)
    if activity is None:
        return None
    activity_id = activity["id"]

    query = (
        client.table(SCORE_LOGS_TABLE)
        .select("*")
        .eq("course_id", course_id)
        .eq("activity_id", activity_id)
        .eq("student_id", student_id)
        .limit(1)
    )
    if isinstance(meta, str) and meta.strip() != "":
        query = query.contains("meta", {"label": meta.strip()})

    response = query.execute()
    rows = response.data or []
    return rows[0] if rows else None


def list_scores(course_id: str, activity_no: int) -> List[Dict]:
    """Return all score rows for one activity."""
    client = get_supabase_client()
    activity = _get_activity_row(client, course_id, activity_no)
    if activity is None:
        return []
    activity_id = activity["id"]

    response = (
        client.table(SCORE_LOGS_TABLE)
        .select("*")
        .eq("course_id", course_id)
        .eq("activity_id", activity_id)
        .order("created_at")
        .execute()
    )
    raw_rows = response.data or []

    output = []
    for row in raw_rows:
        user_id = row.get("student_id")
        email = _get_user_email(client, user_id) if user_id else ""
        meta_value = row.get("meta")
        if isinstance(meta_value, dict):
            meta_value = meta_value.get("label", json.dumps(meta_value))
        output.append(
            {
                "student_email": email,
                "score": row.get("score_delta", 0),
                "meta": meta_value,
            },
        )
    return output


def delete_scores(course_id: str, activity_no: int) -> int:
    """Delete all score rows for one activity and return deleted count."""
    client = get_supabase_client()
    activity = _get_activity_row(client, course_id, activity_no)
    if activity is None:
        return 0
    activity_id = activity["id"]

    count_response = (
        client.table(SCORE_LOGS_TABLE)
        .select("id", count="exact")
        .eq("course_id", course_id)
        .eq("activity_id", activity_id)
        .execute()
    )
    deleted_count = count_response.count if count_response.count is not None else len(count_response.data or [])

    (
        client.table(SCORE_LOGS_TABLE)
        .delete()
        .eq("course_id", course_id)
        .eq("activity_id", activity_id)
        .execute()
    )
    return int(deleted_count)


def reset_student_progress(course_id: str, activity_no: int) -> int:
    """Reset student_progress state for one activity and return affected row count."""
    client = get_supabase_client()
    activity = _get_activity_row(client, course_id, activity_no)
    if activity is None:
        return 0
    activity_id = activity["id"]

    count_response = (
        client.table(STUDENT_PROGRESS_TABLE)
        .select("id", count="exact")
        .eq("activity_id", activity_id)
        .execute()
    )
    affected = count_response.count if count_response.count is not None else len(count_response.data or [])

    (
        client.table(STUDENT_PROGRESS_TABLE)
        .update(
            {
                "current_score": 0,
                "completed_objective_ids": [],
                "is_completed": False,
                "last_score_log_id": None,
            },
        )
        .eq("activity_id", activity_id)
        .execute()
    )
    return int(affected)


def _get_activity_row(client: Any, course_id: str, activity_no: int) -> Optional[Dict[str, Any]]:
    response = (
        client.table(ACTIVITIES_TABLE)
        .select("id,activity_no")
        .eq("course_id", course_id)
        .eq("activity_no", activity_no)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def _get_current_score(client: Any, student_id: str, activity_id: str) -> int:
    response = (
        client.table(STUDENT_PROGRESS_TABLE)
        .select("current_score")
        .eq("student_id", student_id)
        .eq("activity_id", activity_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return 0
    value = rows[0].get("current_score", 0)
    try:
        return int(value)
    except Exception:
        return 0


def _resolve_objective_id(client: Any, activity_id: str, meta: Optional[str]) -> Optional[str]:
    if not isinstance(meta, str) or meta.strip() == "":
        return None

    rows = _list_objective_rows(client, activity_id)
    target = meta.strip().lower()
    for row in rows:
        description = str(row.get("description", "")).strip().lower()
        objective_key = str(row.get("objective_key", "")).strip().lower()
        if target == description or target == objective_key:
            value = row.get("id")
            if value is not None:
                return str(value)
    return None


def _build_meta_payload(meta: Optional[str], activity_no: int, student_email: str) -> Dict[str, Any]:
    payload = {
        "activity_no": activity_no,
        "student_email": student_email,
    }
    if isinstance(meta, str) and meta.strip() != "":
        payload["label"] = meta.strip()
    else:
        payload["label"] = "objective_detected"
    return payload


def _upsert_student_progress(
    client: Any,
    student_id: str,
    activity_id: str,
    score_after: int,
    objective_id: Optional[str],
    score_log_id: Optional[str],
) -> None:
    total_objective_count = _get_objective_count(client, activity_id)
    response = (
        client.table(STUDENT_PROGRESS_TABLE)
        .select("id,completed_objective_ids")
        .eq("student_id", student_id)
        .eq("activity_id", activity_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []

    completed_ids = []
    if rows:
        existing_ids = rows[0].get("completed_objective_ids", [])
        if isinstance(existing_ids, list):
            for value in existing_ids:
                if value is not None:
                    completed_ids.append(str(value))

    if objective_id and objective_id not in completed_ids:
        completed_ids.append(objective_id)

    is_completed = total_objective_count > 0 and len(completed_ids) >= total_objective_count

    if not rows:
        payload = {
            "student_id": student_id,
            "activity_id": activity_id,
            "current_score": score_after,
            "completed_objective_ids": completed_ids,
            "is_completed": is_completed,
        }
        if score_log_id:
            payload["last_score_log_id"] = score_log_id
        client.table(STUDENT_PROGRESS_TABLE).insert(payload).execute()
        return

    row = rows[0]
    patch = {
        "current_score": score_after,
        "completed_objective_ids": completed_ids,
        "is_completed": is_completed,
    }
    if score_log_id:
        patch["last_score_log_id"] = score_log_id
    client.table(STUDENT_PROGRESS_TABLE).update(patch).eq("id", row["id"]).execute()


def _get_progress_row(client: Any, student_id: str, activity_id: str) -> Optional[Dict[str, Any]]:
    response = (
        client.table(STUDENT_PROGRESS_TABLE)
        .select("current_score,completed_objective_ids,is_completed")
        .eq("student_id", student_id)
        .eq("activity_id", activity_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def _get_objective_count(client: Any, activity_id: str) -> int:
    response = (
        client.table(OBJECTIVES_TABLE)
        .select("id", count="exact")
        .eq("activity_id", activity_id)
        .eq("is_active", True)
        .execute()
    )
    if response.count is not None:
        return int(response.count)
    return len(response.data or [])


def _list_objective_rows(client: Any, activity_id: str) -> List[Dict[str, Any]]:
    response = (
        client.table(OBJECTIVES_TABLE)
        .select("id,objective_key,description,display_order")
        .eq("activity_id", activity_id)
        .eq("is_active", True)
        .order("display_order")
        .execute()
    )
    rows = response.data or []
    return rows


def _normalize_tokens(text: str) -> List[str]:
    lowered = text.lower()
    normalized = []
    current = []
    for ch in lowered:
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            current.append(ch)
        else:
            if current:
                normalized.append("".join(current))
                current = []
    if current:
        normalized.append("".join(current))
    return normalized


def _get_user_email(client: Any, user_id: Any) -> str:
    response = client.table(USERS_TABLE).select("email").eq("id", user_id).limit(1).execute()
    rows = response.data or []
    if not rows:
        return ""
    value = rows[0].get("email")
    if value is None:
        return ""
    return str(value)
