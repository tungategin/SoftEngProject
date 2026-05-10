"""Tutoring orchestration layer for the student chat flow."""

import json
import re
from typing import Any, Dict, Optional

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
        activity_context = activity_context or {}
        progress_context = progress_context or {}

        try:
            tutor_prompt_template = self._load_tutor_prompt()
            system_prompt = self._load_system_prompt()
            objective_detector_prompt = self.prompt_loader.load_prompt("objective_detector_prompt")
        except Exception as exc:
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
            return self._fallback("llm_call_failed", str(exc))

        parsed = parse_llm_response(raw_output)
        action_name = get_action_name(parsed)
        action_params = get_action_params(parsed)
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
            merged_params = self._merge_identity_params(
                action_name=action_name,
                action_params=action_params,
                email=email,
                password=password,
                course_id=course_id,
                activity_no=activity_no,
            )
            dispatch_result = self.tool_dispatcher.dispatch(action_name, merged_params)
        else:
            # Recovery path: if model avoids APICall, attempt deterministic
            # objective detection from student message and run logScore.
            inferred_objective = self._infer_learned_objective(
                student_message=student_message,
                activity_context=activity_context,
            )
            if inferred_objective is not None:
                fallback_params = {
                    "score": 1,
                    "meta": inferred_objective,
                }
                merged_params = self._merge_identity_params(
                    action_name="logScore",
                    action_params=fallback_params,
                    email=email,
                    password=password,
                    course_id=course_id,
                    activity_no=activity_no,
                )
                dispatch_result = self.tool_dispatcher.dispatch("logScore", merged_params)
                if dispatch_result.get("ok") is True:
                    action_name = "logScore"
                    action_params = fallback_params
                    parsed["apicall"] = (
                        'studentApi(action:"logScore", score=1, meta="{0}")'
                    ).format(inferred_objective)
                    parsed["action"] = "logScore"
                    parsed["params"] = fallback_params

        data = {
            "parsed": parsed,
            "tool_result": dispatch_result,
        }

        if action_name == "logScore" and dispatch_result and dispatch_result.get("ok") is True:
            objective_text = action_params.get("meta", "learning objective")
            mini_lesson = self._build_mini_lesson(str(objective_text))
            response_text = "{0}\n\n{1}".format(response_text, mini_lesson)
            data["mini_lesson"] = mini_lesson

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
        learning_objectives = activity_context.get("learning_objectives", [])
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

        # Keep client-provided values if they exist; fill required identity values safely.
        if action_name in ("getActivity", "logScore"):
            params.setdefault("email", email)
            params.setdefault("password", password)
            params.setdefault("course_id", course_id)
            params.setdefault("activity_no", activity_no)
            # Ensure score triggers are reliable if model forgets score.
            if action_name == "logScore":
                params.setdefault("score", 1)
                params.setdefault("meta", "objective_detected")

        if action_name in ("changeStudentPassword", "setStudentPassword"):
            params.setdefault("email", email)
            params.setdefault("password", password)

        return params

    def _build_mini_lesson(self, objective_text: str) -> str:
        return (
            "**Mini Lesson: {0}**\n"
            "Focus on the definition, one practical implication, and one concrete example."
        ).format(objective_text)

    def _infer_learned_objective(
        self,
        student_message: str,
        activity_context: Dict[str, Any],
    ) -> Optional[str]:
        objectives = activity_context.get("learning_objectives", [])
        if not isinstance(objectives, list) or len(objectives) == 0:
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
                if token in normalized_message_tokens:
                    overlap += 1

            # Light synonym expansion for common networking wording.
            synonym_bonus = 0
            if "format" in objective_tokens and "format" in normalized_message_tokens:
                synonym_bonus += 1
            if "message" in objective_tokens and "message" in normalized_message_tokens:
                synonym_bonus += 1
            if "fields" in objective_tokens and (
                "field" in normalized_message_tokens or "fields" in normalized_message_tokens
            ):
                synonym_bonus += 1
            if ("flow" in objective_tokens or "types" in objective_tokens) and (
                "rules" in normalized_message_tokens
                or "process" in normalized_message_tokens
                or "communication" in normalized_message_tokens
            ):
                synonym_bonus += 1

            total = overlap + synonym_bonus
            if total > best_score:
                best_score = total
                best_objective = objective

        # Require meaningful evidence before auto-scoring.
        if best_score >= 2:
            return best_objective
        return None

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
