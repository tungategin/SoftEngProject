"""Authentication and authorization helpers.

The service layer should call these helpers instead of duplicating auth checks.
"""

import hashlib
import hmac
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


def verify_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticate a user and return the user row.

    Validation steps:
    1) user must exist
    2) user must be active
    3) password must match
    """
    user = user_repo.get_user_by_email(email)
    if user is None:
        raise AuthenticationError("User not found.")

    if not _is_user_active(user):
        raise AuthenticationError("User is inactive.")

    stored_password = _extract_stored_password(user)
    if not stored_password:
        raise AuthenticationError("User password is not set.")

    if not _verify_password(password, stored_password):
        raise AuthenticationError("Password mismatch.")

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
    authorized = course_repo.has_course_authorization(
        course_id=course_id,
        user_id=_user_id(user),
        user_email=_user_email(user),
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


def _is_user_active(user: Dict[str, Any]) -> bool:
    """Normalize active/inactive status checks across common field styles."""
    if "is_active" in user and isinstance(user["is_active"], bool):
        return user["is_active"]
    if "active" in user and isinstance(user["active"], bool):
        return user["active"]

    status = str(user.get("status", "")).strip().lower()
    if not status:
        return True
    return status not in {"inactive", "disabled", "blocked", "deleted"}


def _extract_stored_password(user: Dict[str, Any]) -> Optional[str]:
    """Read password/hash fields from a user row."""
    for field in ("password_hash", "hashed_password", "password"):
        value = user.get(field)
        if isinstance(value, str) and value:
            return value
    return None


def _verify_password(plain_password: str, stored_password: str) -> bool:
    """Compare a plain password to stored password formats.

    Supported stored formats:
    - plain text (legacy / bootstrap)
    - `sha256$<hex_digest>`
    """
    if stored_password.startswith("sha256$"):
        expected_hex = stored_password.split("$", maxsplit=1)[1]
        candidate_hex = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(candidate_hex, expected_hex)

    return hmac.compare_digest(plain_password, stored_password)


def _user_id(user: Dict[str, Any]) -> Optional[str]:
    value = user.get("id")
    if value is None:
        return None
    return str(value)


def _user_email(user: Dict[str, Any]) -> Optional[str]:
    value = user.get("email")
    if isinstance(value, str) and value:
        return value
    return None
