"""Controlled tool dispatcher for LLM-requested actions."""

from typing import Any, Dict, List, Optional

from app import services

_ALLOWED_ACTIONS = set([
    "getActivity",
    "logScore",
    "changeStudentPassword",
    "setStudentPassword",
])


class ToolDispatcher:
    """Dispatches whitelisted action requests to service layer functions."""

    def dispatch(self, action: Optional[str], params: Dict[str, Any]) -> Dict[str, Any]:
        if not action:
            return {
                "ok": False,
                "error": "missing_action",
                "data": {},
            }

        if action not in _ALLOWED_ACTIONS:
            return {
                "ok": False,
                "error": "unsupported_action",
                "data": {},
            }

        if action == "getActivity":
            required = ["email", "password", "course_id", "activity_no"]
            missing = _missing_params(params, required)
            if missing:
                return _missing_params_result(missing)
            return services.getActivity(
                str(params["email"]),
                str(params["password"]),
                str(params["course_id"]),
                int(params["activity_no"]),
            )

        if action == "logScore":
            required = ["email", "password", "course_id", "activity_no", "score"]
            missing = _missing_params(params, required)
            if missing:
                return _missing_params_result(missing)
            meta = params.get("meta")
            if meta is not None:
                meta = str(meta)
            return services.logScore(
                str(params["email"]),
                str(params["password"]),
                str(params["course_id"]),
                int(params["activity_no"]),
                float(params["score"]),
                meta,
            )

        if action == "changeStudentPassword":
            required = ["email", "password", "new_password", "old_password"]
            missing = _missing_params(params, required)
            if missing:
                return _missing_params_result(missing)
            return services.changeStudentPassword(
                str(params["email"]),
                str(params["password"]),
                str(params["new_password"]),
                str(params["old_password"]),
            )

        if action == "setStudentPassword":
            required = ["email", "password"]
            missing = _missing_params(params, required)
            if missing:
                return _missing_params_result(missing)
            return services.setStudentPassword(
                str(params["email"]),
                str(params["password"]),
            )

        return {
            "ok": False,
            "error": "unsupported_action",
            "data": {},
        }


def _missing_params(params: Dict[str, Any], required: List[str]) -> List[str]:
    missing = []
    for key in required:
        if key not in params:
            missing.append(key)
    return missing


def _missing_params_result(missing: List[str]) -> Dict[str, Any]:
    return {
        "ok": False,
        "error": "missing_params",
        "missing": missing,
        "data": {},
    }
