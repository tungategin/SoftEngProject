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
        print("[DEBUG][DISPATCHER] action={0} params={1}".format(action, _mask_params(params)))
        if not action:
            print("[DEBUG][DISPATCHER] missing_action")
            return {
                "ok": False,
                "error": "missing_action",
                "data": {},
            }

        if action not in _ALLOWED_ACTIONS:
            print("[DEBUG][DISPATCHER] unsupported_action:", action)
            return {
                "ok": False,
                "error": "unsupported_action",
                "data": {},
            }

        if action == "getActivity":
            required = ["email", "password", "course_id", "activity_no"]
            missing = _missing_params(params, required)
            if missing:
                print("[DEBUG][DISPATCHER] getActivity missing params:", missing)
                return _missing_params_result(missing)
            print("[DEBUG][DISPATCHER] calling services.getActivity")
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
                print("[DEBUG][DISPATCHER] logScore missing params:", missing)
                return _missing_params_result(missing)
            meta = params.get("meta")
            if meta is not None:
                meta = str(meta)
            print("[DEBUG][DISPATCHER] calling services.logScore meta={0} score={1}".format(meta, params.get("score")))
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
                print("[DEBUG][DISPATCHER] changeStudentPassword missing params:", missing)
                return _missing_params_result(missing)
            print("[DEBUG][DISPATCHER] calling services.changeStudentPassword")
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
                print("[DEBUG][DISPATCHER] setStudentPassword missing params:", missing)
                return _missing_params_result(missing)
            print("[DEBUG][DISPATCHER] calling services.setStudentPassword")
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


def _mask_params(params: Dict[str, Any]) -> Dict[str, Any]:
    masked = {}
    for key, value in params.items():
        if key in ("password", "old_password", "new_password"):
            masked[key] = "***"
        else:
            masked[key] = value
    return masked
