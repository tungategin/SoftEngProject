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
    "gettopic": "getActivity",
    "getactivity": "getActivity",
    "logscore": "logScore",
    "changestudentpassword": "changeStudentPassword",
    "setstudentpassword": "setStudentPassword",
}

_FALLBACK_TEXT = (
    "I could not process that response safely. "
    "Please answer in one short sentence so we can continue."
)


def parse_llm_response(raw_text: str) -> Dict[str, Any]:
    """Parse raw LLM output into a normalized dict safely."""
    print("[DEBUG][PARSER] raw_text:", raw_text)
    data = _parse_json_object(raw_text)
    if data is None:
        print("[DEBUG][PARSER] invalid_json")
        return _fallback_result("invalid_json")

    if not isinstance(data, dict):
        print("[DEBUG][PARSER] json_not_object")
        return _fallback_result("json_not_object")

    api_call = data.get("APICall", "")
    response_text = data.get("response", "")

    if not isinstance(api_call, str):
        print("[DEBUG][PARSER] apicall_not_string")
        return _fallback_result("apicall_not_string")
    if not isinstance(response_text, str):
        print("[DEBUG][PARSER] response_not_string")
        return _fallback_result("response_not_string")

    action_name, params = _extract_action_and_params(api_call)
    print("[DEBUG][PARSER] extracted action={0} params={1}".format(action_name, params))
    canonical_action = _canonical_action(action_name)
    if canonical_action is not None and canonical_action not in SUPPORTED_ACTIONS:
        print("[DEBUG][PARSER] unsupported_action:", action_name)
        return {
            "ok": False,
            "apicall": api_call,
            "action": action_name,
            "params": {},
            "response": response_text if response_text else _FALLBACK_TEXT,
            "error": "unsupported_action",
        }

    normalized_params = _normalize_param_aliases(params)
    print(
        "[DEBUG][PARSER] canonical action={0} normalized_params={1}".format(
            canonical_action,
            normalized_params,
        ),
    )

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

    candidate = _strip_markdown_fence(raw_text.strip())
    if candidate == "":
        return None

    try:
        loaded = json.loads(candidate)
        if isinstance(loaded, dict):
            return loaded
        return None
    except Exception as exc:
        print("[DEBUG][PARSER] json.loads(candidate) failed:", repr(exc))

    match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if not match:
        return _extract_structured_fields(candidate)

    try:
        loaded = json.loads(match.group(0))
    except Exception as exc:
        print("[DEBUG][PARSER] json.loads(match) failed:", repr(exc))
        return _extract_structured_fields(match.group(0))

    if isinstance(loaded, dict):
        return loaded
    return _extract_structured_fields(candidate)


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
    if action_name in ACTION_ALIASES:
        return ACTION_ALIASES.get(action_name, action_name)
    lowered = action_name.lower()
    if lowered in ACTION_ALIASES:
        return ACTION_ALIASES.get(lowered, action_name)
    return ACTION_ALIASES.get(action_name, action_name)


def _normalize_param_aliases(params: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(params)
    if "topic_no" in normalized and "activity_no" not in normalized:
        normalized["activity_no"] = normalized["topic_no"]
    if "topic_text" in normalized and "activity_text" not in normalized:
        normalized["activity_text"] = normalized["topic_text"]
    return normalized


def _strip_markdown_fence(text: str) -> str:
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return text


def _extract_structured_fields(raw_text: str) -> Optional[Dict[str, Any]]:
    api_call = _extract_json_string_field(raw_text, "APICall")
    response_text = _extract_json_string_field(raw_text, "response")

    if api_call is None:
        api_call = _extract_lenient_field(raw_text, "APICall")
    if response_text is None:
        response_text = _extract_lenient_field(raw_text, "response")

    if api_call is None and response_text is None:
        return None

    if api_call is None:
        api_call = ""
    if response_text is None:
        response_text = ""

    print("[DEBUG][PARSER] using structured fallback parse")
    return {
        "APICall": api_call,
        "response": response_text,
    }


def _extract_json_string_field(raw_text: str, field_name: str) -> Optional[str]:
    pattern = r'"{0}"\s*:\s*"((?:\\.|[^"\\])*)"\s*(?=,|\}})'.format(re.escape(field_name))
    match = re.search(pattern, raw_text, re.DOTALL)
    if not match:
        return None

    encoded = '"' + match.group(1) + '"'
    try:
        value = json.loads(encoded)
        if isinstance(value, str):
            return value
        return str(value)
    except Exception:
        # If escape decoding fails, keep raw capture so caller can continue.
        return match.group(1)


def _extract_lenient_field(raw_text: str, field_name: str) -> Optional[str]:
    field_pattern = r'"{0}"\s*:\s*'.format(re.escape(field_name))
    match = re.search(field_pattern, raw_text)
    if not match:
        return None

    index = match.end()
    length = len(raw_text)
    while index < length and raw_text[index].isspace():
        index += 1
    if index >= length:
        return None

    if raw_text[index] != '"':
        return _extract_unquoted_value(raw_text, index)

    # Parse quoted text and tolerate unescaped inner quotes.
    index += 1
    out_chars = []
    escaped = False
    while index < length:
        ch = raw_text[index]
        if escaped:
            out_chars.append(ch)
            escaped = False
            index += 1
            continue
        if ch == "\\":
            escaped = True
            out_chars.append(ch)
            index += 1
            continue
        if ch == '"':
            tail_index = index + 1
            while tail_index < length and raw_text[tail_index].isspace():
                tail_index += 1
            if tail_index >= length or raw_text[tail_index] in [",", "}"]:
                break
            # Treat as content quote if next token is not a field delimiter.
            out_chars.append(ch)
            index += 1
            continue
        out_chars.append(ch)
        index += 1

    extracted = "".join(out_chars).strip()
    if extracted == "":
        return ""

    try:
        return json.loads('"{0}"'.format(extracted))
    except Exception:
        return extracted


def _extract_unquoted_value(raw_text: str, start_index: int) -> Optional[str]:
    index = start_index
    length = len(raw_text)
    out_chars = []
    while index < length:
        ch = raw_text[index]
        if ch in [",", "}"]:
            break
        out_chars.append(ch)
        index += 1
    value = "".join(out_chars).strip()
    if value == "":
        return None
    return value
