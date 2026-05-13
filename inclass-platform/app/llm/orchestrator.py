"""Tutoring orchestration layer for the student chat flow."""

import json
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.llm.prompt_loader import PromptLoader
from app.llm.providers.base import LLMProvider
from app.llm.providers.openrouter_provider import OpenRouterProvider
from app.llm.response_parser import (
    get_action_name,
    get_action_params,
    get_response_text,
    parse_llm_response,
)
from app.llm.tool_dispatcher import ToolDispatcher

_FALLBACK_RESPONSE = (
    "Let's continue step by step. "
    "Could you explain your answer with one concrete technical detail?"
)
_DEFAULT_FALLBACK_OBJECTIVE = "objective_detected"


class TutorOrchestrator:
    """Coordinates prompt loading, LLM call, parsing, and tool dispatching."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        prompt_loader: Optional[PromptLoader] = None,
        tool_dispatcher: Optional[ToolDispatcher] = None,
    ) -> None:
        self.provider = provider or OpenRouterProvider()
        self.prompt_loader = prompt_loader or PromptLoader()
        self.tool_dispatcher = tool_dispatcher or ToolDispatcher()

    def run(
        self,
        email: str,
        password: str,
        course_id: str,
        activity_no: int,
        student_message: str,
        activity_context: Optional[Dict[str, Any]] = None,
        progress_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        print("[DEBUG][ORCH] run called course_id={0} activity_no={1}".format(course_id, activity_no))
        activity_context = activity_context or {}
        progress_context = progress_context or {}
        if progress_context.get("is_completed", False):
            return {
                "ok": True,
                "response": self._completion_message(),
                "apicall": "",
                "data": {
                    "parsed": {
                        "ok": True,
                        "apicall": "",
                        "action": None,
                        "params": {},
                        "response": self._completion_message(),
                        "error": None,
                    },
                    "tool_result": None,
                },
                "error": None,
            }

        try:
            tutor_prompt_template = self._load_tutor_prompt()
            system_prompt = self._load_system_prompt()
            objective_detector_prompt = self.prompt_loader.load_prompt("objective_detector_prompt")
        except Exception as exc:
            print("[DEBUG][ORCH] prompt load failed:", repr(exc))
            return self._fallback("prompt_load_failed", str(exc))

        rendered_prompt = self._render_prompt(
            tutor_prompt_template=tutor_prompt_template,
            student_message=student_message,
            course_id=course_id,
            activity_no=activity_no,
            activity_context=activity_context,
            progress_context=progress_context,
            objective_detector_prompt=objective_detector_prompt,
        )

        final_prompt = rendered_prompt

        try:
            raw_output = self._call_llm(
                final_prompt=final_prompt,
                system_prompt=system_prompt,
            )
        except Exception as exc:
            print("[DEBUG][ORCH] llm call failed:", repr(exc))
            return self._fallback("llm_call_failed", str(exc))

        print("[DEBUG][ORCH] raw_output:", raw_output)
        parsed = parse_llm_response(raw_output)
        print("[DEBUG][ORCH] parsed:", parsed)
        action_name = get_action_name(parsed)
        action_params = get_action_params(parsed)
        print("[DEBUG][ORCH] action={0} params={1}".format(action_name, _mask_params(action_params)))
        response_text = get_response_text(parsed)

        if not parsed.get("ok", False):
            return {
                "ok": False,
                "response": response_text,
                "apicall": parsed.get("apicall", ""),
                "data": {},
                "error": parsed.get("error", "parse_failed"),
            }

        dispatch_result = None
        if action_name is not None:
            if action_name == "logScore" and not self._allow_log_score(
                student_message=student_message,
                activity_context=activity_context,
                action_params=action_params,
            ):
                print("[DEBUG][ORCH] blocked off-topic logScore")
                parsed["apicall"] = ""
                parsed["action"] = None
                parsed["params"] = {}
                action_name = None
                action_params = {}
                response_text = (
                    "Let's stay focused on this activity. "
                    "Please answer using the activity scenario and terminology."
                )
            else:
                merged_params = self._merge_identity_params(
                    action_name=action_name,
                    action_params=action_params,
                    email=email,
                    password=password,
                    course_id=course_id,
                    activity_no=activity_no,
                )
                print("[DEBUG][ORCH] dispatching action={0} merged_params={1}".format(action_name, _mask_params(merged_params)))
                dispatch_result = self.tool_dispatcher.dispatch(action_name, merged_params)
                print("[DEBUG][ORCH] dispatch_result:", dispatch_result)
        else:
            # Recovery path: if model avoids APICall, attempt deterministic
            # objective detection from student message and run logScore.
            inferred_objective = self._infer_learned_objective(
                student_message=student_message,
                activity_context=activity_context,
            )
            if inferred_objective is None and _looks_like_conceptual_answer(student_message):
                inferred_objective = _DEFAULT_FALLBACK_OBJECTIVE
                print("[DEBUG][ORCH] conceptual fallback objective:", inferred_objective)
            print("[DEBUG][ORCH] fallback inferred_objective:", inferred_objective)
            if inferred_objective is not None:
                fallback_params = {
                    "score": 1,
                    "meta": inferred_objective,
                }
                if self._allow_log_score(
                    student_message=student_message,
                    activity_context=activity_context,
                    action_params=fallback_params,
                ):
                    merged_params = self._merge_identity_params(
                        action_name="logScore",
                        action_params=fallback_params,
                        email=email,
                        password=password,
                        course_id=course_id,
                        activity_no=activity_no,
                    )
                    print("[DEBUG][ORCH] fallback dispatch logScore params:", _mask_params(merged_params))
                    dispatch_result = self.tool_dispatcher.dispatch("logScore", merged_params)
                    print("[DEBUG][ORCH] fallback dispatch_result:", dispatch_result)
                    if dispatch_result.get("ok") is True:
                        action_name = "logScore"
                        action_params = fallback_params
                        parsed["apicall"] = (
                            'studentApi(action:"logScore", score=1, meta="{0}")'
                        ).format(inferred_objective)
                        parsed["action"] = "logScore"
                        parsed["params"] = fallback_params
                else:
                    print("[DEBUG][ORCH] fallback blocked off-topic logScore")
            else:
                print("[DEBUG][ORCH] fallback did not dispatch logScore")

        data = {
            "parsed": parsed,
            "tool_result": dispatch_result,
        }

        score_added = _to_int(dispatch_result.get("score_added", 0)) if isinstance(dispatch_result, dict) else 0
        if (
            action_name == "logScore"
            and dispatch_result
            and dispatch_result.get("ok") is True
            and score_added > 0
        ):
            current_score = dispatch_result.get("current_score")
            if current_score is not None:
                response_text = "{0}\n\nYour current score is now {1}.".format(response_text, current_score)
            objective_text = action_params.get("meta", "learning objective")
            mini_lesson = self._build_mini_lesson(self._mini_lesson_topic(str(objective_text)))
            response_text = "{0}\n\n{1}".format(response_text, mini_lesson)
            data["mini_lesson"] = mini_lesson
            if dispatch_result.get("activity_completed", False):
                response_text = "{0}\n\n{1}".format(response_text, self._completion_message())
                data["activity_completed"] = True

        response_text = self._stabilize_tutoring_response(
            response_text=response_text,
            student_message=student_message,
            activity_context=activity_context,
            is_completed=bool(data.get("activity_completed", False)),
        )

        return {
            "ok": True,
            "response": response_text,
            "apicall": parsed.get("apicall", ""),
            "data": data,
            "error": None,
        }

    def _call_llm(self, final_prompt: str, system_prompt: str) -> str:
        messages = [{"role": "user", "content": final_prompt}]
        return str(
            self.provider.generate(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=settings.openrouter_max_completion_tokens,
                metadata={"feature": "student_tutoring"},
            ),
        )

    def _render_prompt(
        self,
        tutor_prompt_template: str,
        student_message: str,
        course_id: str,
        activity_no: int,
        activity_context: Dict[str, Any],
        progress_context: Dict[str, Any],
        objective_detector_prompt: str,
    ) -> str:
        activity_text = activity_context.get("text", "")
        learning_objectives = self._extract_objectives(activity_context)
        runtime_context = {
            "course_id": course_id,
            "activity_no": activity_no,
            "activity_text": activity_text,
            "learning_objectives": learning_objectives,
            "progress_context": progress_context,
            "student_message": student_message,
            # topic aliases for prompt compatibility
            "topic_no": activity_no,
            "topic_text": activity_text,
        }
        context_json = json.dumps(runtime_context, ensure_ascii=True)
        return (
            "{0}\n\n"
            "RUNTIME_CONTEXT_JSON:\n{1}\n\n"
            "OBJECTIVE_DETECTOR_HINT:\n{2}\n\n"
            "RUNTIME_POLICY_OVERRIDE:\n"
            "- Identity fields are already collected by backend; do NOT ask for email, password, course_id, or activity_no again.\n"
            "- If an API call is needed, emit APICall directly; backend will inject missing identity fields safely.\n"
            "- If student's latest message clearly matches a learning objective, prioritize APICall logScore immediately.\n\n"
            "- Use only activity_text and learning_objectives from RUNTIME_CONTEXT_JSON. Ignore any hardcoded examples in base prompt text.\n"
            "- Do not restart the activity on every turn; keep conversational continuity.\n"
            "- Score only if the student's latest message is relevant to this activity and objective set.\n"
            "- Do not reveal raw objective sentence in mini-lesson title; use a concise concept name.\n\n"
            "OUTPUT_CONSTRAINT:\n"
            "Return JSON only. Exactly two fields: APICall and response."
        ).format(tutor_prompt_template, context_json, objective_detector_prompt)

    def _merge_identity_params(
        self,
        action_name: str,
        action_params: Dict[str, Any],
        email: str,
        password: str,
        course_id: str,
        activity_no: int,
    ) -> Dict[str, Any]:
        params = dict(action_params)

        # Identity and activity context must come from authenticated backend input,
        # not from model-generated placeholders.
        if action_name in ("getActivity", "logScore"):
            params["email"] = email
            params["password"] = password
            params["course_id"] = course_id
            params["activity_no"] = activity_no
            # Ensure score triggers are reliable if model forgets score.
            if action_name == "logScore":
                self._set_if_missing_or_blank(params, "score", 1)
                self._set_if_missing_or_blank(params, "meta", "objective_detected")

        if action_name in ("changeStudentPassword", "setStudentPassword"):
            params["email"] = email
            params["password"] = password

        return params

    def _set_if_missing_or_blank(self, params: Dict[str, Any], key: str, value: Any) -> None:
        if key not in params:
            params[key] = value
            return

        current = params.get(key)
        if _is_blank_value(current):
            params[key] = value

    def _build_mini_lesson(self, objective_text: str) -> str:
        return (
            "**Mini Lesson: {0}**\n"
            "Focus on the definition, one practical implication, and one concrete example."
        ).format(objective_text)

    def _mini_lesson_topic(self, objective_text: str) -> str:
        topic = objective_text.strip()
        lowered = topic.lower()
        prefixes = [
            "student should understand",
            "student should learn",
            "the student should understand",
            "the student should learn",
        ]
        for prefix in prefixes:
            if lowered.startswith(prefix):
                topic = topic[len(prefix):].strip(" .:-")
                break
        if topic == "":
            topic = "Core Activity Concept"
        return topic

    def _completion_message(self) -> str:
        return (
            "Excellent work. You have covered all learning objectives for this activity. "
            "The activity is now complete."
        )

    def _stabilize_tutoring_response(
        self,
        response_text: str,
        student_message: str,
        activity_context: Dict[str, Any],
        is_completed: bool,
    ) -> str:
        text = str(response_text or "").strip()
        if text == "":
            text = _FALLBACK_RESPONSE

        # First turn must present activity text explicitly.
        start_markers = [
            "ready to start",
            "start the activity",
            "ask the first question",
            "begin the activity",
        ]
        lowered_student_message = student_message.lower()
        is_start_turn = False
        for marker in start_markers:
            if marker in lowered_student_message:
                is_start_turn = True
                break

        activity_text = str(activity_context.get("text", "")).strip()
        if is_start_turn and activity_text != "" and activity_text not in text:
            text = "{0}\n\n{1}".format(activity_text, text)
        if not is_start_turn:
            text = _remove_redundant_activity_restart(text, activity_text)

        if is_completed:
            return text

        return _enforce_single_question(text)

    def _allow_log_score(
        self,
        student_message: str,
        activity_context: Dict[str, Any],
        action_params: Dict[str, Any],
    ) -> bool:
        del action_params
        return _is_message_relevant_to_activity(student_message, activity_context)

    def _infer_learned_objective(
        self,
        student_message: str,
        activity_context: Dict[str, Any],
    ) -> Optional[str]:
        objectives = self._extract_objectives(activity_context)
        if len(objectives) == 0:
            return None

        normalized_message_tokens = _normalize_tokens(student_message)
        if len(normalized_message_tokens) == 0:
            return None

        best_objective = None
        best_score = 0
        for objective in objectives:
            if not isinstance(objective, str) or objective.strip() == "":
                continue
            objective_tokens = _normalize_tokens(objective)
            if len(objective_tokens) == 0:
                continue

            overlap = 0
            for token in objective_tokens:
                if _token_in_map(token, normalized_message_tokens):
                    overlap += 1

            # Light synonym expansion for common networking wording.
            synonym_bonus = 0
            if "format" in objective_tokens and (
                "format" in normalized_message_tokens or "schema" in normalized_message_tokens
            ):
                synonym_bonus += 1
            if "message" in objective_tokens and "message" in normalized_message_tokens:
                synonym_bonus += 1
            if "fields" in objective_tokens and (
                "field" in normalized_message_tokens or "fields" in normalized_message_tokens
            ):
                synonym_bonus += 1
            if "meaning" in objective_tokens and (
                _token_in_map("meaning", normalized_message_tokens)
                or "interpret" in normalized_message_tokens
                or "semantic" in normalized_message_tokens
            ):
                synonym_bonus += 1
            if ("flow" in objective_tokens or "types" in objective_tokens) and (
                "rules" in normalized_message_tokens
                or "process" in normalized_message_tokens
                or "communication" in normalized_message_tokens
                or "order" in normalized_message_tokens
                or "sequence" in normalized_message_tokens
            ):
                synonym_bonus += 1
            if "types" in objective_tokens and _contains_message_type_signals(normalized_message_tokens):
                synonym_bonus += 2

            total = overlap + synonym_bonus
            if total > best_score:
                best_score = total
                best_objective = objective

        # Require meaningful evidence before auto-scoring.
        if best_score >= 2:
            return best_objective
        return None

    def _extract_objectives(self, activity_context: Dict[str, Any]) -> List[str]:
        raw_value = activity_context.get("learning_objectives", [])
        if isinstance(raw_value, list):
            out = []
            for item in raw_value:
                text = str(item).strip()
                if text != "":
                    out.append(text)
            return out

        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if stripped == "":
                return []
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    loaded = json.loads(stripped)
                except Exception:
                    loaded = None
                if isinstance(loaded, list):
                    out = []
                    for item in loaded:
                        text = str(item).strip()
                        if text != "":
                            out.append(text)
                    return out
            if ";" in stripped:
                return [part.strip() for part in stripped.split(";") if part.strip() != ""]
            if "\n" in stripped:
                return [part.strip() for part in stripped.splitlines() if part.strip() != ""]
            if "," in stripped:
                return [part.strip() for part in stripped.split(",") if part.strip() != ""]
            return [stripped]

        return []

    def _fallback(self, error_code: str, error_details: str) -> Dict[str, Any]:
        return {
            "ok": False,
            "response": _FALLBACK_RESPONSE,
            "apicall": "",
            "data": {},
            "error": "{0}: {1}".format(error_code, error_details),
        }

    def _load_tutor_prompt(self) -> str:
        try:
            return self.prompt_loader.load_prompt("student_tutor_prompt")
        except Exception:
            return self.prompt_loader.load_prompt("tutor_prompt")

    def _load_system_prompt(self) -> str:
        try:
            return self.prompt_loader.load_prompt("system_prompt")
        except Exception:
            return ""


def _normalize_tokens(text: str) -> Dict[str, bool]:
    lowered = text.lower()
    parts = re.split(r"[^a-z0-9]+", lowered)
    tokens = {}
    for part in parts:
        if part == "":
            continue
        tokens[part] = True
    return tokens


def _looks_like_conceptual_answer(text: str) -> bool:
    tokens = _normalize_tokens(text)
    if len(tokens) < 6:
        return False

    hits = 0
    signals = [
        "message",
        "format",
        "field",
        "meaning",
        "rule",
        "communication",
        "process",
        "interpret",
        "must",
        "need",
        "should",
    ]
    for signal in signals:
        if signal in tokens:
            hits += 1
    return hits >= 3


def _mask_params(params: Dict[str, Any]) -> Dict[str, Any]:
    masked = {}
    for key, value in params.items():
        if key in ("password", "old_password", "new_password"):
            masked[key] = "***"
        else:
            masked[key] = value
    return masked


def _is_blank_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _enforce_single_question(text: str) -> str:
    if "?" not in text:
        return "{0}\n\nCould you answer this in one concrete technical sentence?".format(text)

    first_q_index = text.find("?")
    prefix = text[: first_q_index + 1]
    suffix = text[first_q_index + 1 :]
    suffix = suffix.replace("?", ".")
    return "{0}{1}".format(prefix, suffix)


def _is_message_relevant_to_activity(student_message: str, activity_context: Dict[str, Any]) -> bool:
    message_tokens = _normalize_tokens(student_message)
    if len(message_tokens) == 0:
        return False

    objective_texts = _extract_objective_texts(activity_context)
    objective_tokens = _normalize_tokens(" ".join(objective_texts))
    if len(objective_tokens) > 0:
        objective_overlap = 0
        for token in message_tokens:
            if _token_in_map(token, objective_tokens):
                objective_overlap += 1
        if objective_overlap >= 1:
            return True
        if "types" in objective_tokens and _contains_message_type_signals(message_tokens):
            return True

    activity_text_tokens = _normalize_tokens(str(activity_context.get("text", "")))
    if len(activity_text_tokens) == 0:
        # If there is no reliable reference context, allow concept-style answers.
        return _looks_like_conceptual_answer(student_message)

    overlap = 0
    for token in message_tokens:
        if token in activity_text_tokens:
            overlap += 1
    if overlap >= 2:
        return True

    return _looks_like_conceptual_answer(student_message)


def _extract_objective_texts(activity_context: Dict[str, Any]) -> List[str]:
    raw = activity_context.get("learning_objectives", [])
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip() != ""]
    if isinstance(raw, str) and raw.strip() != "":
        if ";" in raw:
            return [part.strip() for part in raw.split(";") if part.strip() != ""]
        return [raw.strip()]
    return []


def _remove_redundant_activity_restart(text: str, activity_text: str) -> str:
    lowered = text.lower()
    starters = [
        "great, let's begin",
        "let's begin our activity",
        "great let's begin",
        "here is the scenario",
    ]
    has_restart = False
    for starter in starters:
        if lowered.startswith(starter):
            has_restart = True
            break
    if not has_restart:
        return text

    cleaned = text
    if activity_text and activity_text in cleaned:
        cleaned = cleaned.replace(activity_text, "").strip()

    first_question = cleaned.find("?")
    if first_question != -1:
        prefix_start = cleaned.rfind("\n", 0, first_question)
        if prefix_start != -1:
            return cleaned[prefix_start + 1 :].strip()
    return cleaned


def _contains_message_type_signals(tokens: Dict[str, bool]) -> bool:
    signals = [
        "turn",
        "on",
        "off",
        "status",
        "request",
        "response",
        "command",
        "commands",
        "ack",
        "acknowledgement",
    ]
    hits = 0
    for signal in signals:
        if _token_in_map(signal, tokens):
            hits += 1
    return hits >= 2


def _token_in_map(token: str, token_map: Dict[str, bool]) -> bool:
    if token in token_map:
        return True
    if token.endswith("s") and token[:-1] in token_map:
        return True
    plural = "{0}s".format(token)
    if plural in token_map:
        return True
    return False


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0
