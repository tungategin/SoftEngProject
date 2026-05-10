from typing import Any, Dict

from fastapi import FastAPI

from app import services
from app.schemas.auth import InstructorLoginRequest, StudentChangePasswordRequest, StudentLoginRequest
from app.schemas.course import (
    CourseRequest,
    CreateActivityRequest,
    ExportScoresRequest,
    GetActivityRequest,
    ResetActivityRequest,
    StartEndActivityRequest,
    UpdateActivityRequest,
)
from app.schemas.scoring import LogScoreRequest
from app.schemas.tutoring import StudentTutoringRequest

app = FastAPI(title="InClass Platform")


def _normalize_service_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """Keep endpoint JSON contract consistent."""
    if not isinstance(result, dict):
        return {"ok": False, "error": "invalid_service_response"}

    if result.get("ok") is True:
        data = {}
        for key, value in result.items():
            if key != "ok":
                data[key] = value
        return {"ok": True, "data": data}

    return {"ok": False, "error": result.get("error", "operation_failed")}


@app.post("/student/login")
def student_login(payload: StudentLoginRequest) -> Dict[str, Any]:
    result = services.studentLogin(payload.email, payload.password)
    return _normalize_service_response(result)



@app.post("/student/change-password")
def change_student_password(payload: StudentChangePasswordRequest) -> Dict[str, Any]:
    result = services.changeStudentPassword(
        payload.email,
        payload.password,
        payload.new_password,
        payload.old_password,
    )
    return _normalize_service_response(result)


@app.post("/student/get-activity")
def get_activity(payload: GetActivityRequest) -> Dict[str, Any]:
    result = services.getActivity(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_no,
    )
    return _normalize_service_response(result)


@app.post("/student/log-score")
def log_score(payload: LogScoreRequest) -> Dict[str, Any]:
    result = services.logScore(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_no,
        payload.score,
        payload.meta,
    )
    return _normalize_service_response(result)


@app.post("/student/tutor-chat")
def tutor_chat(payload: StudentTutoringRequest) -> Dict[str, Any]:
    result = services.tutoringChat(
        email=payload.email,
        password=payload.password,
        course_id=payload.course_id,
        activity_no=payload.activity_no,
        message=payload.message,
        progress_context=payload.progress_context,
    )
    return _normalize_service_response(result)


@app.post("/instructor/login")
def instructor_login(payload: InstructorLoginRequest) -> Dict[str, Any]:
    result = services.instructorLogin(payload.email, payload.password)
    return _normalize_service_response(result)


@app.post("/instructor/list-courses")
@app.post("/instructor/list-my-courses")
def list_courses(payload: CourseRequest) -> Dict[str, Any]:
    result = services.listMyCourses(payload.email, payload.password)
    return _normalize_service_response(result)


@app.post("/instructor/list-activities")
def list_activities(payload: CourseRequest) -> Dict[str, Any]:
    result = services.listActivities(payload.email, payload.password, payload.course_id)
    return _normalize_service_response(result)


@app.post("/instructor/create-activity")
def create_activity(payload: CreateActivityRequest) -> Dict[str, Any]:
    result = services.createActivity(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_text,
        payload.learning_objectives,
        payload.activity_no_optional,
    )
    return _normalize_service_response(result)


@app.post("/instructor/update-activity")
def update_activity(payload: UpdateActivityRequest) -> Dict[str, Any]:
    result = services.updateActivity(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_no,
        payload.patch,
    )
    return _normalize_service_response(result)


@app.post("/instructor/start-activity")
def start_activity(payload: StartEndActivityRequest) -> Dict[str, Any]:
    result = services.startActivity(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_no,
    )
    return _normalize_service_response(result)


@app.post("/instructor/end-activity")
def end_activity(payload: StartEndActivityRequest) -> Dict[str, Any]:
    result = services.endActivity(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_no,
    )
    return _normalize_service_response(result)


@app.post("/instructor/export-scores")
def export_scores(payload: ExportScoresRequest) -> Dict[str, Any]:
    result = services.exportScores(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_no,
    )
    return _normalize_service_response(result)


@app.post("/instructor/reset-activity")
def reset_activity(payload: ResetActivityRequest) -> Dict[str, Any]:
    result = services.resetActivity(
        payload.email,
        payload.password,
        payload.course_id,
        payload.activity_no,
    )
    return _normalize_service_response(result)
