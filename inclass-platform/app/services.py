import csv
import io
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
            "learning_objectives": activity.get("learning_objectives", []),
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
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    if _normalize_role(user.get("role")) != STUDENT:
        return {"ok": False, "error": "forbidden_role"}

    user_id = _user_id(user)
    user_email = _user_email(user)
    if user_id is None or user_email is None:
        return {"ok": False, "error": "user_identity_missing"}
    if not course_repo.is_user_in_course(user_id, course_id):
        return {"ok": False, "error": "course_access_denied"}

    activity = activity_repo.get_activity(course_id=course_id, activity_no=activity_no)
    if not activity:
        return {"ok": False, "error": "activity_not_found"}
    try:
        require_active_activity(activity)
    except AuthorizationError:
        return {"ok": False, "error": "activity_not_active"}

    score_row = score_repo.log_score(
        course_id=course_id,
        activity_no=activity_no,
        student_id=user_id,
        student_email=user_email,
        score=score,
        meta=meta,
    )
    return {"ok": True, "score_log": score_row}

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

def resetActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False, "error": "invalid_credentials"}
    try:
        require_instructor_of_course(user, course_id)
    except AuthorizationError:
        return {"ok": False, "error": "course_access_denied"}

    deleted_count = score_repo.delete_scores(course_id=course_id, activity_no=activity_no)
    return {"ok": True, "deleted_count": deleted_count}

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
