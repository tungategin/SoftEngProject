from app import services

def test_student_login_success(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "u1", "role": "STUDENT"},
    )
    res = services.studentLogin("student@test.com", "123456")
    assert res["ok"] is True

def test_student_login_fail(monkeypatch):
    monkeypatch.setattr(services, "verify_user", lambda email, password: None)
    res = services.studentLogin("student@test.com", "wrong")
    assert res["ok"] is False

def test_student_login_fail_when_role_is_not_student(monkeypatch):
    monkeypatch.setattr(
        services,
        "verify_user",
        lambda email, password: {"id": "u1", "role": "INSTRUCTOR"},
    )
    res = services.studentLogin("instructor@test.com", "123456")
    assert res["ok"] is False
