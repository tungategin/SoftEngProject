import pytest

from app import services
from app.core.security import AuthorizationError


def test_change_student_password_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "role": "student", "password_hash": "old"},
    )
    monkeypatch.setattr(services.user_repo, "verify_password", lambda user, raw: raw == "old")

    updated = {}

    def _update_password(user_id, new_password):
        updated["user_id"] = user_id
        updated["new_password"] = new_password

    monkeypatch.setattr(services.user_repo, "update_password", _update_password)

    result = services.changeStudentPassword(
        "student@test.com",
        "old",
        "new",
        "old",
    )

    assert result["ok"] is True
    assert updated == {"user_id": "s1", "new_password": "new"}


def test_set_student_password_first_run_success(monkeypatch):
    monkeypatch.setattr(
        services.user_repo,
        "get_user_by_email",
        lambda email: {"id": "s1", "role": "student", "password_hash": None},
    )
    calls = {}
    monkeypatch.setattr(
        services.user_repo,
        "update_password",
        lambda user_id, value: calls.update({"user_id": user_id, "value": value}),
    )

    result = services.setStudentPassword("student@test.com", "newpass")

    assert result["ok"] is True
    assert calls["user_id"] == "s1"
    assert calls["value"] == "newpass"


def test_instructor_login_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "INSTRUCTOR"},
    )
    result = services.instructorLogin("inst@test.com", "x")
    assert result == {"ok": True}


def test_list_my_courses_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(
        services.course_repo,
        "get_courses_for_user",
        lambda user_id: [{"id": "CSE101"}, {"id": "CSE102"}],
    )
    result = services.listMyCourses("inst@test.com", "x")
    assert result["ok"] is True
    assert len(result["courses"]) == 2


def test_list_activities_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "list_activities",
        lambda course_id: [{"activity_no": 1}],
    )
    result = services.listActivities("inst@test.com", "x", "CSE101")
    assert result["ok"] is True
    assert result["activities"][0]["activity_no"] == 1


def test_get_activity_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(services.course_repo, "is_user_in_course", lambda user_id, course_id: True)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {
            "course_id": course_id,
            "activity_no": activity_no,
            "text": "Solve this",
            "learning_objectives": ["Obj1"],
            "status": "ACTIVE",
        },
    )
    monkeypatch.setattr(services, "require_active_activity", lambda activity: None)

    result = services.getActivity("student@test.com", "x", "CSE101", 1)

    assert result["ok"] is True
    assert result["activity"]["activity_no"] == 1


def test_get_activity_normalizes_learning_objectives_string(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(services.course_repo, "is_user_in_course", lambda user_id, course_id: True)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {
            "course_id": course_id,
            "activity_no": activity_no,
            "text": "Solve this",
            "learning_objectives": "Message types; Message format; Message flow",
            "status": "ACTIVE",
        },
    )
    monkeypatch.setattr(services, "require_active_activity", lambda activity: None)

    result = services.getActivity("student@test.com", "x", "CSE101", 1)

    assert result["ok"] is True
    assert result["activity"]["learning_objectives"] == [
        "Message types",
        "Message format",
        "Message flow",
    ]


def test_log_score_returns_safe_error_when_repo_insert_fails(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(services.course_repo, "is_user_in_course", lambda user_id, course_id: True)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {
            "course_id": course_id,
            "activity_no": activity_no,
            "status": "ACTIVE",
        },
    )
    monkeypatch.setattr(services, "require_active_activity", lambda activity: None)
    monkeypatch.setattr(
        services.score_repo,
        "get_completion_state",
        lambda course_id, activity_no, student_id: {
            "is_completed": False,
            "current_score": 0,
            "completed_count": 0,
            "total_objectives": 3,
        },
    )
    monkeypatch.setattr(
        services.score_repo,
        "resolve_objective",
        lambda course_id, activity_no, meta: {"id": "obj1", "description": "Objective 1"},
    )
    monkeypatch.setattr(
        services.score_repo,
        "is_objective_completed",
        lambda course_id, activity_no, student_id, objective_id: False,
    )
    monkeypatch.setattr(
        services.score_repo,
        "log_score",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("db_insert_failed")),
    )

    result = services.logScore("student@test.com", "pw", "CSE101", 1, 1.0, "meta")
    assert result == {"ok": False, "error": "score_log_insert_failed"}


def test_log_score_duplicate_objective_does_not_insert(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(services.course_repo, "is_user_in_course", lambda user_id, course_id: True)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"course_id": course_id, "activity_no": activity_no, "status": "ACTIVE"},
    )
    monkeypatch.setattr(services, "require_active_activity", lambda activity: None)
    monkeypatch.setattr(
        services.score_repo,
        "get_completion_state",
        lambda course_id, activity_no, student_id: {
            "is_completed": False,
            "current_score": 2,
            "completed_count": 1,
            "total_objectives": 3,
        },
    )
    monkeypatch.setattr(
        services.score_repo,
        "resolve_objective",
        lambda course_id, activity_no, meta: {"id": "obj1", "description": "Message types"},
    )
    monkeypatch.setattr(
        services.score_repo,
        "is_objective_completed",
        lambda course_id, activity_no, student_id, objective_id: True,
    )

    called = {"count": 0}
    monkeypatch.setattr(
        services.score_repo,
        "log_score",
        lambda **kwargs: called.update({"count": called["count"] + 1}),
    )

    result = services.logScore("student@test.com", "pw", "CSE101", 1, 1.0, "Message types")
    assert result["ok"] is True
    assert result["duplicate_objective"] is True
    assert result["score_added"] == 0
    assert called["count"] == 0


def test_log_score_blocks_when_activity_already_completed(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(services.course_repo, "is_user_in_course", lambda user_id, course_id: True)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"course_id": course_id, "activity_no": activity_no, "status": "ACTIVE"},
    )
    monkeypatch.setattr(services, "require_active_activity", lambda activity: None)
    monkeypatch.setattr(
        services.score_repo,
        "get_completion_state",
        lambda course_id, activity_no, student_id: {
            "is_completed": True,
            "current_score": 3,
            "completed_count": 3,
            "total_objectives": 3,
        },
    )

    result = services.logScore("student@test.com", "pw", "CSE101", 1, 1.0, "Any objective")
    assert result == {"ok": False, "error": "activity_completed"}


def test_create_activity_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(services.activity_repo, "get_next_activity_no", lambda course_id: 3)
    monkeypatch.setattr(services.activity_repo, "get_activity", lambda course_id, activity_no: None)
    monkeypatch.setattr(
        services.activity_repo,
        "create_activity",
        lambda course_id, activity_no, text, learning_objectives: {
            "course_id": course_id,
            "activity_no": activity_no,
            "text": text,
            "learning_objectives": learning_objectives,
            "status": "NOT_STARTED",
        },
    )

    result = services.createActivity(
        "inst@test.com",
        "x",
        "CSE101",
        "Prompt",
        ["A", "B"],
        None,
    )

    assert result["ok"] is True
    assert result["activity"]["activity_no"] == 3


def test_update_activity_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"course_id": course_id, "activity_no": activity_no},
    )
    monkeypatch.setattr(
        services.activity_repo,
        "update_activity",
        lambda course_id, activity_no, patch: {
            "course_id": course_id,
            "activity_no": activity_no,
            "text": patch.get("text"),
        },
    )

    result = services.updateActivity(
        "inst@test.com",
        "x",
        "CSE101",
        2,
        {"text": "new text"},
    )

    assert result["ok"] is True
    assert result["activity"]["text"] == "new text"


def test_start_and_end_activity_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"course_id": course_id, "activity_no": activity_no, "status": "NOT_STARTED"},
    )
    monkeypatch.setattr(
        services.activity_repo,
        "set_activity_status",
        lambda course_id, activity_no, status: {"course_id": course_id, "activity_no": activity_no, "status": status},
    )

    start_result = services.startActivity("inst@test.com", "x", "CSE101", 1)
    end_result = services.endActivity("inst@test.com", "x", "CSE101", 1)

    assert start_result["ok"] is True
    assert start_result["activity"]["status"] == "ACTIVE"
    assert end_result["ok"] is True
    assert end_result["activity"]["status"] == "ENDED"


def test_export_scores_returns_csv(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.score_repo,
        "list_scores",
        lambda course_id, activity_no: [
            {"student_email": "s1@test.com", "score": 8.5, "meta": "good"},
        ],
    )

    result = services.exportScores("inst@test.com", "x", "CSE101", 1)
    assert result["ok"] is True
    assert "student_email,score,meta" in result["csv"]
    assert "s1@test.com" in result["csv"]


def test_reset_activity_deletes_scores(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"id": "a1", "activity_no": activity_no, "status": "ACTIVE"},
    )
    monkeypatch.setattr(services.score_repo, "delete_scores", lambda course_id, activity_no: 4)
    monkeypatch.setattr(services.score_repo, "reset_student_progress", lambda course_id, activity_no: 2)
    monkeypatch.setattr(
        services.activity_repo,
        "mark_activity_reset",
        lambda course_id, activity_no: {"id": "a1", "activity_no": activity_no, "status": "ENDED"},
    )

    result = services.resetActivity("inst@test.com", "x", "CSE101", 5)
    assert result["ok"] is True
    assert result["deleted_count"] == 4
    assert result["progress_reset_count"] == 2
    assert result["activity"]["status"] == "ENDED"


def test_manual_grade_student_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "email": email, "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.user_repo,
        "get_user_by_email",
        lambda email: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(services.course_repo, "is_user_in_course", lambda user_id, course_id: True)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"id": "a1", "course_id": course_id, "activity_no": activity_no},
    )
    monkeypatch.setattr(
        services.score_repo,
        "log_score",
        lambda **kwargs: {"id": "score1"},
    )
    monkeypatch.setattr(
        services.score_repo,
        "create_manual_grade_event",
        lambda **kwargs: {"id": "event1"},
    )
    monkeypatch.setattr(
        services.score_repo,
        "get_completion_state",
        lambda course_id, activity_no, student_id: {"current_score": 5, "is_completed": False},
    )

    result = services.manualGradeStudent(
        email="inst@test.com",
        password="pw",
        course_id="CSE101",
        activity_no=1,
        student_email="student@test.com",
        manual_score=2,
        reason="exception_case",
        meta={"type": "manual"},
    )
    assert result["ok"] is True
    assert result["score_log"]["id"] == "score1"
    assert result["manual_grade_event"]["id"] == "event1"


def test_manual_grade_student_denied_for_unauthorized_course(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )

    def _deny(user, course_id):
        raise AuthorizationError("denied")

    monkeypatch.setattr(services, "require_instructor_of_course", _deny)
    result = services.manualGradeStudent(
        email="inst@test.com",
        password="pw",
        course_id="CSE101",
        activity_no=1,
        student_email="student@test.com",
        manual_score=1,
        reason="x",
    )
    assert result == {"ok": False, "error": "course_access_denied"}


def test_reset_student_password_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.user_repo,
        "get_user_by_email",
        lambda email: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(services.course_repo, "is_user_in_course", lambda user_id, course_id: True)

    updates = {}
    monkeypatch.setattr(
        services.user_repo,
        "update_password",
        lambda user_id, new_password: updates.update({"user_id": user_id, "new_password": new_password}),
    )

    result = services.resetStudentPassword(
        "inst@test.com",
        "x",
        "CSE101",
        "student@test.com",
        "reset123",
    )

    assert result["ok"] is True
    assert updates["user_id"] == "s1"
    assert updates["new_password"] == "reset123"


def test_tutoring_chat_stops_when_activity_completion_reached(monkeypatch):
    monkeypatch.setattr(
        services,
        "getActivity",
        lambda email, password, course_id, activity_no: {
            "ok": True,
            "activity": {
                "course_id": course_id,
                "activity_no": activity_no,
                "text": "Activity text",
                "learning_objectives": ["Obj1"],
                "status": "ACTIVE",
            },
        },
    )
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "email": email, "role": "student"},
    )
    monkeypatch.setattr(
        services.score_repo,
        "get_completion_state",
        lambda course_id, activity_no, student_id: {
            "current_score": 1,
            "completed_count": 1,
            "total_objectives": 1,
            "is_completed": True,
        },
    )

    result = services.tutoringChat(
        email="student@test.com",
        password="pw",
        course_id="CSE101",
        activity_no=1,
        message="hello",
    )
    assert result["ok"] is True
    assert result["apicall"] == ""
    assert "complete" in result["response"].lower()


def test_list_activities_denied_when_not_authorized(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )

    def _deny(user, course_id):
        raise AuthorizationError("denied")

    monkeypatch.setattr(services, "require_instructor_of_course", _deny)
    result = services.listActivities("inst@test.com", "x", "CSE101")
    assert result["ok"] is False
