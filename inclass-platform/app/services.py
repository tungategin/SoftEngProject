import csv
import io
import json
from typing import Any, Dict, List, Optional

from app.core.security import (
    AuthorizationError,
    require_active_activity,
    require_instructor_of_course,
    verify_user,
)
from app.repositories import activity_repo, course_repo, score_repo, user_repo
from shared.constants.activity_status import ACTIVE, ENDED
from shared.constants.roles import INSTRUCTOR, STUDENT

"""
IMPORTANT:
Instructor tests will import and call these functions directly.

Keep the function names and parameter order exactly as below.
Implement real logic later; this scaffold preserves contract compatibility.
"""

def studentLogin(email: str, password: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False}

    if _normalize_role(user.get("role")) != STUDENT:
        return {"ok": False}

    return {"ok": True}

def changeStudentPassword(email: str, password: str, new_password: str, old_password: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}

    if _normalize_role(user.get("role")) != STUDENT:
        return {"ok": False, "error": "forbidden_role"}
    if not user_repo.verify_password(user, old_password):
        return {"ok": False, "error": "old_password_mismatch"}

    user_id = _user_id(user)
    if user_id is None:
        return {"ok": False, "error": "user_id_missing"}

    user_repo.update_password(user_id, new_password)
    return {"ok": True}

def setStudentPassword(email: str, password: str) -> Dict[str, Any]:
    user = user_repo.get_user_by_email(email)
    if user is None:
        return {"ok": False, "error": "user_not_found"}
    if _normalize_role(user.get("role")) != STUDENT:
        return {"ok": False, "error": "forbidden_role"}

    existing = user.get("password_hash")
    if isinstance(existing, str) and existing != "":
        return {"ok": False, "error": "password_already_set"}

    user_id = _user_id(user)
    if user_id is None:
        return {"ok": False, "error": "user_id_missing"}

    user_repo.update_password(user_id, password)
    return {"ok": True}

def getActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    if _normalize_role(user.get("role")) != STUDENT:
        return {"ok": False, "error": "forbidden_role"}

    user_id = _user_id(user)
    if user_id is None:
        return {"ok": False, "error": "user_id_missing"}
    if not course_repo.is_user_in_course(user_id, course_id):
        return {"ok": False, "error": "course_access_denied"}

    activity = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not activity:
        return {"ok": False, "error": "activity_not_found"}
    try:
        require_active_activity(activity)
    except AuthorizationError:
        return {"ok": False, "error": "activity_not_active"}

    return {
        "ok": True,
        "activity": {
            "course_id": course_id,
            "activity_no": activity.get("activity_no"),
            "text": activity.get("text"),
            "learning_objectives": _normalize_learning_objectives(
                activity.get("learning_objectives", []),
            ),
            "status": activity.get("status"),
        },
    }

def logScore(
    email: str,
    password: str,
    course_id: str,
    activity_no: int,
    score: float,
    meta: Optional[str] = None
) -> Dict[str, Any]:
    print(
        "[DEBUG][SERVICE][logScore] called email={0} course_id={1} activity_no={2} score={3} meta={4}".format(
            email,
            course_id,
            activity_no,
            score,
            meta,
        ),
    )
    user = verify_user(email, password)
    if not user:
        print("[DEBUG][SERVICE][logScore] verify_user failed")
        return {"ok": False, "error": "invalid_credentials"}
    if _normalize_role(user.get("role")) != STUDENT:
        print("[DEBUG][SERVICE][logScore] forbidden_role:", user.get("role"))
        return {"ok": False, "error": "forbidden_role"}

    user_id = _user_id(user)
    user_email = _user_email(user)
    if user_id is None or user_email is None:
        print(
            "[DEBUG][SERVICE][logScore] user_identity_missing user_id={0} user_email={1}".format(
                user_id,
                user_email,
            ),
        )
        return {"ok": False, "error": "user_identity_missing"}
    if not course_repo.is_user_in_course(user_id, course_id):
        print("[DEBUG][SERVICE][logScore] course_access_denied user_id={0} course_id={1}".format(user_id, course_id))
        return {"ok": False, "error": "course_access_denied"}

    activity = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not activity:
        print("[DEBUG][SERVICE][logScore] activity_not_found")
        return {"ok": False, "error": "activity_not_found"}
    print("[DEBUG][SERVICE][logScore] activity status={0}".format(activity.get("status")))
    try:
        require_active_activity(activity)
    except AuthorizationError:
        print("[DEBUG][SERVICE][logScore] activity_not_active")
        return {"ok": False, "error": "activity_not_active"}

    if float(score) <= 0:
        return {"ok": False, "error": "invalid_score"}

    completion_before = score_repo.get_completion_state(course_id, activity_no, user_id)
    if completion_before.get("is_completed", False):
        return {"ok": False, "error": "activity_completed"}

    objective_row = score_repo.resolve_objective(course_id, activity_no, meta)
    if objective_row is None:
        objective_row = score_repo.pick_next_unscored_objective(
            course_id=course_id,
            activity_no=activity_no,
            student_id=user_id,
        )

    if objective_row is None:
        return {"ok": False, "error": "objective_not_found"}

    objective_id = objective_row.get("id")
    if objective_id is None:
        return {"ok": False, "error": "objective_not_found"}
    objective_id = str(objective_id)

    objective_label = objective_row.get("description")
    if not isinstance(objective_label, str) or objective_label.strip() == "":
        objective_label = meta if isinstance(meta, str) and meta.strip() != "" else "objective_detected"

    if score_repo.is_objective_completed(
        course_id=course_id,
        activity_no=activity_no,
        student_id=user_id,
        objective_id=objective_id,
    ):
        return {
            "ok": True,
            "score_log": None,
            "score_added": 0,
            "duplicate_objective": True,
            "objective": objective_label,
            "current_score": completion_before.get("current_score", 0),
            "activity_completed": completion_before.get("is_completed", False),
            "completed_objectives": completion_before.get("completed_count", 0),
            "total_objectives": completion_before.get("total_objectives", 0),
        }

    print("[DEBUG][SERVICE][logScore] calling score_repo.log_score")
    try:
        score_row = score_repo.log_score(
            course_id=course_id,
            activity_no=activity_no,
            student_id=user_id,
            student_email=user_email,
            score=1,
            meta=objective_label,
            objective_id=objective_id,
            source=score_repo.SCORE_SOURCE_TUTORING_FLOW,
        )
    except Exception as exc:
        print("[DEBUG][SERVICE][logScore] repo error:", repr(exc))
        return {"ok": False, "error": "score_log_insert_failed"}

    completion_after = score_repo.get_completion_state(course_id, activity_no, user_id)
    print("[DEBUG][SERVICE][logScore] score_repo result={0}".format(score_row))
    return {
        "ok": True,
        "score_log": score_row,
        "score_added": 1,
        "duplicate_objective": False,
        "objective": objective_label,
        "current_score": completion_after.get("current_score", 0),
        "activity_completed": completion_after.get("is_completed", False),
        "completed_objectives": completion_after.get("completed_count", 0),
        "total_objectives": completion_after.get("total_objectives", 0),
    }

def instructorLogin(email: str, password: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False}

    if _normalize_role(user.get("role")) != INSTRUCTOR:
        return {"ok": False}

    return {"ok": True}

def changeInstructorPassword(email: str, password: str, old_password: str, new_password: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    if _normalize_role(user.get("role")) != INSTRUCTOR:
        return {"ok": False, "error": "forbidden_role"}
    if not user_repo.verify_password(user, old_password):
        return {"ok": False, "error": "old_password_mismatch"}

    user_id = _user_id(user)
    if user_id is None:
        return {"ok": False, "error": "user_id_missing"}
    user_repo.update_password(user_id, new_password)
    return {"ok": True}

def setInstructorPassword(email: str, password: Optional[str] = None) -> Dict[str, Any]:
    if password is None:
        return {"ok": False, "error": "password_required"}

    user = user_repo.get_user_by_email(email)
    if user is None:
        return {"ok": False, "error": "user_not_found"}
    if _normalize_role(user.get("role")) != INSTRUCTOR:
        return {"ok": False, "error": "forbidden_role"}

    existing = user.get("password_hash")
    if isinstance(existing, str) and existing != "":
        return {"ok": False, "error": "password_already_set"}

    user_id = _user_id(user)
    if user_id is None:
        return {"ok": False, "error": "user_id_missing"}

    user_repo.update_password(user_id, password)
    return {"ok": True}

def listMyCourses(email: str, password: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    if _normalize_role(user.get("role")) != INSTRUCTOR:
        return {"ok": False, "error": "forbidden_role"}

    user_id = _user_id(user)
    if user_id is None:
        return {"ok": False, "error": "user_id_missing"}

    courses = course_repo.get_courses_for_user(user_id)
    return {"ok": True, "courses": courses}

def listActivities(email: str, password: str, course_id: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    activities = activity_repo.list_activities(course_id)
    return {"ok": True, "activities": activities}

def createActivity(
    email: str,
    password: str,
    course_id: str,
    activity_text: str,
    learning_objectives: List[str],
    activity_no_optional: Optional[int] = None
) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    activity_no = activity_no_optional
    if activity_no is None:
        activity_no = activity_repo.get_next_activity_no(course_id)

    existing = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if existing:
        return {"ok": False, "error": "activity_already_exists"}

    created = activity_repo.create_activity(
        course_id=course_id,
        activity_no=activity_no,
        text=activity_text,
        learning_objectives=learning_objectives,
    )
    return {"ok": True, "activity": created}

def updateActivity(email: str, password: str, course_id: str, activity_no: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    existing = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not existing:
        return {"ok": False, "error": "activity_not_found"}

    allowed_keys = {"text", "learning_objectives", "status"}
    filtered_patch = {}
    for key, value in patch.items():
        if key in allowed_keys:
            filtered_patch[key] = value
    if not filtered_patch:
        return {"ok": False, "error": "empty_patch"}

    updated = activity_repo.update_activity(course_id, activity_no, filtered_patch)
    if not updated:
        return {"ok": False, "error": "update_failed"}
    return {"ok": True, "activity": updated}

def startActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    activity = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not activity:
        return {"ok": False, "error": "activity_not_found"}
    if str(activity.get("status", "")).upper() == ACTIVE:
        return {"ok": False, "error": "activity_already_active"}

    updated = activity_repo.set_activity_status(course_id, activity_no, ACTIVE)
    if not updated:
        return {"ok": False, "error": "update_failed"}
    return {"ok": True, "activity": updated}

def endActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    activity = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not activity:
        return {"ok": False, "error": "activity_not_found"}
    if str(activity.get("status", "")).upper() == ENDED:
        return {"ok": False, "error": "activity_already_ended"}

    updated = activity_repo.set_activity_status(course_id, activity_no, ENDED)
    if not updated:
        return {"ok": False, "error": "update_failed"}
    return {"ok": True, "activity": updated}

def exportScores(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    rows = score_repo.list_scores(course_id=course_id, activity_no=activity_no)
    csv_content = _scores_to_csv(rows)
    return {"ok": True, "csv": csv_content, "rows": rows}


def manualGradeStudent(
    email: str,
    password: str,
    course_id: str,
    activity_no: int,
    student_email: str,
    manual_score: int,
    reason: str,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    instructor_id = _user_id(user)
    if instructor_id is None:
        return {"ok": False, "error": "instructor_id_missing"}

    student = user_repo.get_user_by_email(student_email)
    if not student:
        return {"ok": False, "error": "student_not_found"}
    if _normalize_role(student.get("role")) != STUDENT:
        return {"ok": False, "error": "target_not_student"}

    student_id = _user_id(student)
    if student_id is None:
        return {"ok": False, "error": "student_id_missing"}
    if not course_repo.is_user_in_course(student_id, course_id):
        return {"ok": False, "error": "student_not_in_course"}

    activity = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not activity:
        return {"ok": False, "error": "activity_not_found"}

    try:
        normalized_score = int(manual_score)
    except Exception:
        return {"ok": False, "error": "invalid_manual_score"}
    if normalized_score == 0:
        return {"ok": False, "error": "invalid_manual_score"}

    activity_id = activity.get("id")
    if activity_id is None:
        activity_id = score_repo.get_activity_id(course_id, activity_no)
    if activity_id is None:
        return {"ok": False, "error": "activity_not_found"}
    activity_id = str(activity_id)

    reason_text = str(reason).strip()
    if reason_text == "":
        reason_text = "manual_grade"

    try:
        score_row = score_repo.log_score(
            course_id=course_id,
            activity_no=activity_no,
            student_id=student_id,
            student_email=student_email,
            score=normalized_score,
            meta=reason_text,
            source=score_repo.SCORE_SOURCE_MANUAL_GRADE,
            actor_user_id=instructor_id,
        )
    except Exception:
        return {"ok": False, "error": "score_log_insert_failed"}

    try:
        manual_event = score_repo.create_manual_grade_event(
            instructor_id=instructor_id,
            student_id=student_id,
            course_id=course_id,
            activity_id=activity_id,
            manual_score=normalized_score,
            reason=reason_text,
            score_log_id=str(score_row.get("id")) if isinstance(score_row, dict) and score_row.get("id") else None,
            meta=meta,
        )
    except Exception:
        return {"ok": False, "error": "manual_grade_event_insert_failed"}

    completion = score_repo.get_completion_state(course_id, activity_no, student_id)
    return {
        "ok": True,
        "score_log": score_row,
        "manual_grade_event": manual_event,
        "current_score": completion.get("current_score", 0),
        "activity_completed": completion.get("is_completed", False),
    }


def resetActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    activity = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not activity:
        return {"ok": False, "error": "activity_not_found"}

    deleted_count = score_repo.delete_scores(course_id=course_id, activity_no=activity_no)
    progress_reset_count = score_repo.reset_student_progress(course_id=course_id, activity_no=activity_no)
    updated_activity = activity_repo.mark_activity_reset(course_id=course_id, activity_no=activity_no)
    if not updated_activity:
        return {"ok": False, "error": "activity_reset_failed"}

    return {
        "ok": True,
        "deleted_count": deleted_count,
        "progress_reset_count": progress_reset_count,
        "activity": updated_activity,
    }

def resetStudentPassword(email: str, password: str, course_id: str, student_email: str, new_password: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    student = user_repo.get_user_by_email(student_email)
    if not student:
        return {"ok": False, "error": "student_not_found"}
    if _normalize_role(student.get("role")) != STUDENT:
        return {"ok": False, "error": "target_not_student"}

    student_id = _user_id(student)
    if student_id is None:
        return {"ok": False, "error": "student_id_missing"}
    if not course_repo.is_user_in_course(student_id, course_id):
        return {"ok": False, "error": "student_not_in_course"}

    user_repo.update_password(student_id, new_password)
    return {"ok": True}


def tutoringChat(
    email: str,
    password: str,
    course_id: str,
    activity_no: int,
    message: str,
    progress_context: Optional[Dict[str, Any]] = None,
    provider: Optional[Any] = None,
) -> Dict[str, Any]:
    """Thin service wrapper to run tutoring orchestration."""
    activity_result = getActivity(
        email=email,
        password=password,
        course_id=course_id,
        activity_no=activity_no,
    )
    if not activity_result.get("ok", False):
        return activity_result

    if progress_context is None:
        progress_context = {}

    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    user_id = _user_id(user)
    if user_id is None:
        return {"ok": False, "error": "user_id_missing"}

    completion_state = score_repo.get_completion_state(
        course_id=course_id,
        activity_no=activity_no,
        student_id=user_id,
    )

    merged_progress_context = dict(progress_context)
    merged_progress_context.update(
        {
            "current_score": completion_state.get("current_score", 0),
            "completed_count": completion_state.get("completed_count", 0),
            "total_objectives": completion_state.get("total_objectives", 0),
            "is_completed": completion_state.get("is_completed", False),
        },
    )

    if completion_state.get("is_completed", False):
        return {
            "ok": True,
            "response": _activity_completed_response(),
            "apicall": "",
            "data": {
                "completed": True,
                "progress": merged_progress_context,
            },
            "error": None,
        }

    # Local import avoids circular dependency:
    # services -> orchestrator -> dispatcher -> services
    from app.llm.orchestrator import TutorOrchestrator

    orchestrator = TutorOrchestrator(provider=provider)
    return orchestrator.run(
        email=email,
        password=password,
        course_id=course_id,
        activity_no=activity_no,
        student_message=message,
        activity_context=activity_result.get("activity", {}),
        progress_context=merged_progress_context,
    )


def _activity_completed_response() -> str:
    return (
        "Congratulations. You have covered all learning objectives for this activity. "
        "This activity is now complete."
    )


def _normalize_role(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _user_id(user: Dict[str, Any]) -> Optional[str]:
    value = user.get("id")
    if value is None:
        return None
    return str(value)


def _user_email(user: Dict[str, Any]) -> Optional[str]:
    value = user.get("email")
    if not isinstance(value, str) or value == "":
        return None
    return value


def _scores_to_csv(rows: List[Dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["student_email", "score", "meta"])
    for row in rows:
        writer.writerow(
            [
                row.get("student_email", ""),
                row.get("score", ""),
                row.get("meta", ""),
            ],
        )
    return buffer.getvalue()


def _normalize_learning_objectives(raw_value: Any) -> List[str]:
    if isinstance(raw_value, list):
        out = []
        for item in raw_value:
            text = str(item).strip()
            if text != "":
                out.append(text)
        return out

    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if stripped == "":
            return []

        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                loaded = json.loads(stripped)
            except Exception:
                loaded = None
            if isinstance(loaded, list):
                out = []
                for item in loaded:
                    text = str(item).strip()
                    if text != "":
                        out.append(text)
                if out:
                    return out

        if ";" in stripped:
            parts = stripped.split(";")
        elif "\n" in stripped:
            parts = stripped.splitlines()
        elif "," in stripped:
            parts = stripped.split(",")
        else:
            parts = [stripped]

        out = []
        for item in parts:
            text = str(item).strip()
            if text != "":
                out.append(text)
        return out

    return []
