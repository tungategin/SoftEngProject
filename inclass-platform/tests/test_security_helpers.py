import pytest

from app.core import security


def test_verify_user_returns_user_when_credentials_are_valid(monkeypatch):
    monkeypatch.setattr(
        security.user_repo,
        "get_user_by_email",
        lambda email: {
            "id": "u1",
            "email": email,
            "password_hash": "123456",
            "role": "STUDENT",
        },
    )
    monkeypatch.setattr(
        security.user_repo,
        "verify_password",
        lambda user, password: password == "123456",
    )

    result = security.verify_user("student@test.com", "123456")
    assert result is not None
    assert result["email"] == "student@test.com"


def test_verify_user_returns_none_when_user_not_found(monkeypatch):
    monkeypatch.setattr(security.user_repo, "get_user_by_email", lambda email: None)

    result = security.verify_user("missing@test.com", "123456")
    assert result is None


def test_verify_user_returns_none_when_password_mismatch(monkeypatch):
    monkeypatch.setattr(
        security.user_repo,
        "get_user_by_email",
        lambda email: {
            "id": "u1",
            "email": email,
            "password_hash": "123456",
            "role": "STUDENT",
        },
    )
    monkeypatch.setattr(security.user_repo, "verify_password", lambda user, password: False)

    result = security.verify_user("student@test.com", "wrong")
    assert result is None


def test_require_instructor_of_course_ok(monkeypatch):
    monkeypatch.setattr(
        security.course_repo,
        "is_user_in_course",
        lambda user_id, course_id: user_id == "u1" and course_id == "CSE101",
    )

    security.require_instructor_of_course(
        {"id": "u1", "role": "instructor"},
        "CSE101",
    )


def test_require_instructor_of_course_raises_when_not_authorized(monkeypatch):
    monkeypatch.setattr(security.course_repo, "is_user_in_course", lambda user_id, course_id: False)

    with pytest.raises(security.AuthorizationError):
        security.require_instructor_of_course({"id": "u1", "role": "instructor"}, "CSE101")
