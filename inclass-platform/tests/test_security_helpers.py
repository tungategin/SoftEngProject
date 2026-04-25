import hashlib

import pytest

from app.core import security
from shared.constants.activity_status import ACTIVE, ENDED, NOT_STARTED
from shared.constants.roles import INSTRUCTOR, STUDENT


def test_verify_user_success_plain_password(monkeypatch):
    monkeypatch.setattr(
        security.user_repo,
        "get_user_by_email",
        lambda email: {
            "id": "u1",
            "email": email,
            "role": STUDENT,
            "is_active": True,
            "password": "secret123",
        },
    )

    user = security.verify_user("student@example.com", "secret123")
    assert user["email"] == "student@example.com"


def test_verify_user_success_sha256_password(monkeypatch):
    digest = hashlib.sha256("secret123".encode("utf-8")).hexdigest()
    monkeypatch.setattr(
        security.user_repo,
        "get_user_by_email",
        lambda email: {
            "id": "u1",
            "email": email,
            "role": STUDENT,
            "is_active": True,
            "password_hash": f"sha256${digest}",
        },
    )

    user = security.verify_user("student@example.com", "secret123")
    assert user["email"] == "student@example.com"


def test_verify_user_not_found(monkeypatch):
    monkeypatch.setattr(security.user_repo, "get_user_by_email", lambda email: None)

    with pytest.raises(security.AuthenticationError, match="User not found"):
        security.verify_user("missing@example.com", "x")


def test_verify_user_inactive(monkeypatch):
    monkeypatch.setattr(
        security.user_repo,
        "get_user_by_email",
        lambda email: {
            "id": "u1",
            "email": email,
            "role": STUDENT,
            "status": "inactive",
            "password": "secret123",
        },
    )

    with pytest.raises(security.AuthenticationError, match="inactive"):
        security.verify_user("inactive@example.com", "secret123")


def test_verify_user_password_mismatch(monkeypatch):
    monkeypatch.setattr(
        security.user_repo,
        "get_user_by_email",
        lambda email: {
            "id": "u1",
            "email": email,
            "role": STUDENT,
            "is_active": True,
            "password": "secret123",
        },
    )

    with pytest.raises(security.AuthenticationError, match="Password mismatch"):
        security.verify_user("student@example.com", "wrong-password")


def test_require_role():
    security.require_role({"role": INSTRUCTOR}, INSTRUCTOR)
    with pytest.raises(security.AuthorizationError, match="Role"):
        security.require_role({"role": STUDENT}, INSTRUCTOR)


def test_require_course_access(monkeypatch):
    monkeypatch.setattr(
        security.course_repo,
        "has_course_authorization",
        lambda **kwargs: True,
    )
    security.require_course_access({"id": "u1", "email": "a@b.com"}, "CSE101")

    monkeypatch.setattr(
        security.course_repo,
        "has_course_authorization",
        lambda **kwargs: False,
    )
    with pytest.raises(security.AuthorizationError, match="not authorized"):
        security.require_course_access({"id": "u1", "email": "a@b.com"}, "CSE101")


def test_require_active_activity():
    security.require_active_activity({"status": ACTIVE})

    with pytest.raises(security.AuthorizationError, match="not started"):
        security.require_active_activity({"status": NOT_STARTED})

    with pytest.raises(security.AuthorizationError, match="already ended"):
        security.require_active_activity({"status": ENDED})


def test_require_instructor_of_course(monkeypatch):
    monkeypatch.setattr(
        security.course_repo,
        "has_course_authorization",
        lambda **kwargs: True,
    )
    security.require_instructor_of_course(
        {"id": "u1", "email": "inst@example.com", "role": INSTRUCTOR},
        "CSE101",
    )

    with pytest.raises(security.AuthorizationError, match="Role"):
        security.require_instructor_of_course(
            {"id": "u2", "email": "stu@example.com", "role": STUDENT},
            "CSE101",
        )
