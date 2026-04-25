"""Authentication and authorization helpers.

The service layer should call these helpers instead of duplicating auth checks.
"""

from typing import Any, Dict, Optional

from app.repositories import course_repo, user_repo
from shared.constants.activity_status import ACTIVE, ENDED, NOT_STARTED
from shared.constants.roles import INSTRUCTOR


class SecurityError(Exception):
    """Base class for all security-related failures."""


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""


def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Return user dict when credentials are valid, otherwise None."""
    user = user_repo.get_user_by_email(email)
    if user is None:
        return None
    if not user_repo.verify_password(user, password):
        return None

    return user


def require_role(user: Dict[str, Any], role: str) -> None:
    """Ensure user has the expected role."""
    user_role = str(user.get("role", "")).strip().lower()
    expected_role = role.strip().lower()
    if user_role != expected_role:
        raise AuthorizationError(
            f"Role '{role}' is required. Current role: '{user.get('role')}'.",
        )


def require_course_access(user: Dict[str, Any], course_id: str) -> None:
    """Ensure user is assigned to the given course."""
    user_id = _user_id(user)
    if user_id is None:
        raise AuthorizationError("User id is missing.")

    authorized = course_repo.is_user_in_course(
        user_id=user_id,
        course_id=course_id,
    )
    if not authorized:
        raise AuthorizationError(
            f"User is not authorized for course '{course_id}'.",
        )


def require_active_activity(activity: Dict[str, Any]) -> None:
    """Allow only ACTIVE activities."""
    status = str(activity.get("status", "")).strip().upper()
    if status != ACTIVE:
        if status == NOT_STARTED:
            raise AuthorizationError("Activity has not started yet.")
        if status == ENDED:
            raise AuthorizationError("Activity has already ended.")
        raise AuthorizationError(f"Activity is not active (status={status!r}).")


def require_instructor_of_course(user: Dict[str, Any], course_id: str) -> None:
    """Require instructor role and course assignment together."""
    require_role(user, INSTRUCTOR)
    require_course_access(user, course_id)


def _user_id(user: Dict[str, Any]) -> Optional[str]:
    value = user.get("id")
    if value is None:
        return None
    return str(value)
