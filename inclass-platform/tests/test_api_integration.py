import pytest

from app import services

fastapi_testclient = pytest.importorskip("fastapi.testclient")
TestClient = fastapi_testclient.TestClient

from app.main import app

client = TestClient(app)


def test_student_login_success_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "role": "student"},
    )
    response = client.post(
        "/student/login",
        json={"email": "student@test.com", "password": "123456"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "data" in response.json()


def test_student_login_fail_endpoint(monkeypatch):
    monkeypatch.setattr(services, "verify_user", lambda email, password: None)
    response = client.post(
        "/student/login",
        json={"email": "student@test.com", "password": "wrong"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "operation_failed"}


def test_instructor_login_success_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    response = client.post(
        "/instructor/login",
        json={"email": "inst@test.com", "password": "123456"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_unauthorized_role_access_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "s1", "role": "student"},
    )
    response = client.post(
        "/instructor/list-courses",
        json={
            "email": "student@test.com",
            "password": "123456",
            "course_id": "CSE101",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "forbidden_role"}


def test_list_my_courses_success_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(
        services.course_repo,
        "get_courses_for_user",
        lambda user_id: [{"id": "CSE101", "name": "SE"}],
    )
    response = client.post(
        "/instructor/list-courses",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["courses"][0]["id"] == "CSE101"


def test_list_activities_success_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "list_activities",
        lambda course_id: [{"activity_no": 1, "status": "ACTIVE"}],
    )

    response = client.post(
        "/instructor/list-activities",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["activities"][0]["activity_no"] == 1


def test_get_activity_success_endpoint(monkeypatch):
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
            "activity_no": activity_no,
            "text": "Solve this",
            "learning_objectives": ["Obj1"],
            "status": "ACTIVE",
        },
    )

    response = client.post(
        "/student/get-activity",
        json={
            "email": "student@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_no": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["activity"]["activity_no"] == 1


def test_get_activity_inactive_fail_endpoint(monkeypatch):
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
            "activity_no": activity_no,
            "text": "Solve this",
            "learning_objectives": ["Obj1"],
            "status": "NOT_STARTED",
        },
    )

    response = client.post(
        "/student/get-activity",
        json={
            "email": "student@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_no": 1,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "activity_not_active"}


def test_create_activity_success_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(services.activity_repo, "get_next_activity_no", lambda course_id: 2)
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

    response = client.post(
        "/instructor/create-activity",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_text": "Activity body",
            "learning_objectives": ["Obj1", "Obj2"],
            "activity_no_optional": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["activity"]["activity_no"] == 2


def test_start_activity_success_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"status": "NOT_STARTED"},
    )
    monkeypatch.setattr(
        services.activity_repo,
        "set_activity_status",
        lambda course_id, activity_no, status: {"activity_no": activity_no, "status": status},
    )

    response = client.post(
        "/instructor/start-activity",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_no": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["activity"]["status"] == "ACTIVE"


def test_end_activity_success_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"status": "ACTIVE"},
    )
    monkeypatch.setattr(
        services.activity_repo,
        "set_activity_status",
        lambda course_id, activity_no, status: {"activity_no": activity_no, "status": status},
    )

    response = client.post(
        "/instructor/end-activity",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_no": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["activity"]["status"] == "ENDED"


def test_export_scores_success_endpoint(monkeypatch):
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
            {"student_email": "s1@test.com", "score": 9.0, "meta": "great"},
        ],
    )

    response = client.post(
        "/instructor/export-scores",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_no": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "student_email,score,meta" in body["data"]["csv"]


def test_manual_grade_success_endpoint(monkeypatch):
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
        lambda course_id, activity_no: {"id": "a1", "activity_no": activity_no},
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
        lambda course_id, activity_no, student_id: {"current_score": 7, "is_completed": False},
    )

    response = client.post(
        "/instructor/manual-grade",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_no": 1,
            "student_email": "student@test.com",
            "manual_score": 2,
            "reason": "exceptional_case",
            "meta": {"channel": "in_class"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["manual_grade_event"]["id"] == "event1"


def test_reset_activity_sets_ended_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "i1", "role": "instructor"},
    )
    monkeypatch.setattr(services, "require_instructor_of_course", lambda user, course_id: None)
    monkeypatch.setattr(
        services.activity_repo,
        "get_activity",
        lambda course_id, activity_no: {"id": "a1", "status": "ACTIVE"},
    )
    monkeypatch.setattr(services.score_repo, "delete_scores", lambda course_id, activity_no: 5)
    monkeypatch.setattr(services.score_repo, "reset_student_progress", lambda course_id, activity_no: 3)
    monkeypatch.setattr(
        services.activity_repo,
        "mark_activity_reset",
        lambda course_id, activity_no: {"id": "a1", "activity_no": activity_no, "status": "ENDED"},
    )

    response = client.post(
        "/instructor/reset-activity",
        json={
            "email": "inst@test.com",
            "password": "123456",
            "course_id": "CSE101",
            "activity_no": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["deleted_count"] == 5
    assert body["data"]["activity"]["status"] == "ENDED"
