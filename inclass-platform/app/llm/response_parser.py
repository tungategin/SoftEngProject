"""Utilities for parsing structured LLM responses."""

import json
import re
from typing import Any, Dict, Optional, Tuple

SUPPORTED_ACTIONS = set([
    "getActivity",
    "getTopic",
    "logScore",
    "changeStudentPassword",
    "setStudentPassword",
])

ACTION_ALIASES = {
    "getTopic": "getActivity",
}

_FALLBACK_TEXT = (
    "I could not process that response safely. "
    "Please answer in one short sentence so we can continue."
)


def parse_llm_response(raw_text: str) -> Dict[str, Any]:
    """Parse raw LLM output into a normalized dict safely."""
    data = _parse_json_object(raw_text)
    if data is None:
        return _fallback_result("invalid_json")

    if not isinstance(data, dict):
        return _fallback_result("json_not_object")

    api_call = data.get("APICall", "")
    response_text = data.get("response", "")

    if not isinstance(api_call, str):
        return _fallback_result("apicall_not_string")
    if not isinstance(response_text, str):
        return _fallback_result("response_not_string")

    action_name, params = _extract_action_and_params(api_call)
    if action_name is not None and action_name not in SUPPORTED_ACTIONS:
        return {
            "ok": False,
            "apicall": api_call,
            "action": action_name,
            "params": {},
            "response": response_text if response_text else _FALLBACK_TEXT,
            "error": "unsupported_action",
        }

    canonical_action = _canonical_action(action_name)
    normalized_params = _normalize_param_aliases(params)

    return {
        "ok": True,
        "apicall": api_call,
        "action": canonical_action,
        "params": normalized_params,
        "response": response_text,
        "error": None,
    }


def get_action_name(parsed: Dict[str, Any]) -> Optional[str]:
    """Extract normalized action name from parsed result."""
    action = parsed.get("action")
    if isinstance(action, str):
        return action
    return None


def get_action_params(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Extract action params map from parsed result."""
    params = parsed.get("params")
    if isinstance(params, dict):
        return params
    return {}


def get_response_text(parsed: Dict[str, Any]) -> str:
    """Extract user-facing response text from parsed result."""
    response = parsed.get("response")
    if isinstance(response, str) and response != "":
        return response
    return _FALLBACK_TEXT


def _parse_json_object(raw_text: str) -> Optional[Dict[str, Any]]:
    if not isinstance(raw_text, str):
        return None

    candidate = raw_text.strip()
    if candidate == "":
        return None

    try:
        loaded = json.loads(candidate)
        if isinstance(loaded, dict):
            return loaded
        return None
    except Exception:
        pass

    match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if not match:
        return None

    try:
        loaded = json.loads(match.group(0))
    except Exception:
        return None

    if isinstance(loaded, dict):
        return loaded
    return None


def _extract_action_and_params(api_call: str) -> Tuple[Optional[str], Dict[str, Any]]:
    stripped = api_call.strip()
    if stripped == "":
        return None, {}

    # Accept direct action names as a compact form.
    if stripped in SUPPORTED_ACTIONS:
        return stripped, {}

    action_name = _extract_action_name_from_call(stripped)
    if action_name is None:
        return None, {}

    return action_name, _parse_params(stripped)


def _parse_params(params_raw: str) -> Dict[str, Any]:
    params = {}

    # Handles values in single/double quotes or raw token values.
    for match in re.finditer(
        r'([A-Za-z0-9_]+)\s*[:=]\s*("[^"]*"|\'[^\']*\'|[A-Za-z0-9_@.\-]+)',
        params_raw,
    ):
        key = match.group(1)
        raw_value = match.group(2).strip()
        value = _coerce_value(raw_value)
        params[key] = value

    return params


def _coerce_value(raw_value: str) -> Any:
    if raw_value.startswith('"') and raw_value.endswith('"'):
        return raw_value[1:-1]
    if raw_value.startswith("'") and raw_value.endswith("'"):
        return raw_value[1:-1]

    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        if "." in raw_value:
            return float(raw_value)
        return int(raw_value)
    except Exception:
        return raw_value


def _fallback_result(error_code: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "apicall": "",
        "action": None,
        "params": {},
        "response": _FALLBACK_TEXT,
        "error": error_code,
    }


def _extract_action_name_from_call(raw_call: str) -> Optional[str]:
    # Supports patterns like:
    # studentApi(action:"logScore", ...)
    # studentApi(action='logScore', ...)
    # studentApi(action=logScore, ...)
    action_match = re.search(
        r'action\s*[:=]\s*(?:"([A-Za-z0-9_]+)"|\'([A-Za-z0-9_]+)\'|([A-Za-z0-9_]+))',
        raw_call,
    )
    if not action_match:
        return None

    for index in (1, 2, 3):
        value = action_match.group(index)
        if value:
            return value
    return None


def _canonical_action(action_name: Optional[str]) -> Optional[str]:
    if action_name is None:
        return None
    return ACTION_ALIASES.get(action_name, action_name)


def _normalize_param_aliases(params: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(params)
    if "topic_no" in normalized and "activity_no" not in normalized:
        normalized["activity_no"] = normalized["topic_no"]
    if "topic_text" in normalized and "activity_text" not in normalized:
        normalized["activity_text"] = normalized["topic_text"]
    return normalized
