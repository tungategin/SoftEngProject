# ReadMeAI

Last updated: May 10, 2026 (OpenRouter content-null fix + tutoring reliability)

## Current Project State
- Backend runs with layered architecture (`main -> services -> repositories`).
- Core Phase 1 service logic remains intact.
- New LLM orchestration layer is integrated in isolation under `app/llm/`.

## What Was Implemented

### 0) Instructor Prompt Integration (`all_prompts.md`)
- Integrated instructor-provided prompt set into file-based prompt architecture.
- Added/updated prompt files under `shared/prompts/` from `all_prompts.md`:
  - `student_tutor_prompt.txt` (PROMPT1)
  - `instructor_control_prompt.txt` (PROMPT2)
  - `activity_generator_prompt.txt` (PROMPT3)
- Kept existing loader compatibility files:
  - `tutor_prompt.txt`
  - `system_prompt.txt`
  - `objective_detector_prompt.txt`
- No prompt text is hardcoded in Python code.

### 1) OpenRouter Provider Layer
Added provider-agnostic interface + OpenRouter implementation:
- `app/llm/providers/base.py`
  - `LLMProvider`
  - `LLMProviderError`
- `app/llm/providers/openrouter_provider.py`
  - Reads env-driven configuration:
    - `OPENROUTER_API_KEY`
    - `OPENROUTER_MODEL`
    - optional `OPENROUTER_BASE_URL`
    - optional `OPENROUTER_TIMEOUT_SECONDS`
    - optional `OPENROUTER_MAX_RETRIES`
  - Builds OpenRouter chat-completions request payload
  - Handles HTTP/network/JSON errors and retry-safe behavior
  - Added deterministic JSON-first request shaping:
    - `response_format={"type":"json_object"}`
    - `max_completion_tokens` aligned with `max_tokens`
  - Added DeepSeek non-thinking compatibility hint:
    - `thinking={"type":"disabled"}` for `deepseek/*` models
  - Added controlled retry path for `finish_reason="length"` with `content=null`:
    - retries with increased completion token budget instead of failing immediately
  - Removed always-on verbose raw payload logging; now only logs when `OPENROUTER_DEBUG=true`
- `app/llm/providers/__init__.py`
- `app/llm/__init__.py` exports provider classes and orchestration utilities

### 2) LLM Orchestration Layer
Created/updated cleanly separated modules:
- `app/llm/prompt_loader.py`
  - Loads prompt files from disk by name/path
  - Clear exceptions for missing/empty prompt files
- `app/llm/response_parser.py`
  - Safely parses structured LLM output (`APICall`, `response`)
  - Deterministic fallback on invalid JSON/malformed output
  - Strict whitelist validation for supported actions
  - Alias adaptation for prompt compatibility:
    - `getTopic` -> `getActivity`
    - `topic_no` -> `activity_no`
    - `topic_text` -> `activity_text`
- `app/llm/tool_dispatcher.py`
  - Whitelisted action dispatch only
  - Delegates to existing `app.services` functions
  - Rejects unknown/missing/invalid tool calls safely
- `app/llm/orchestrator.py`
  - Provider-agnostic orchestration flow
  - Loads prompts, prepares context, calls provider, parses output
  - Uses brace-safe prompt rendering (no brittle `.format()` over raw prompt body)
  - Injects runtime context JSON for deterministic parser-friendly prompting
  - Optionally dispatches approved tool calls
  - Adds short academic mini-lesson after successful score events
  - Improves score triggering reliability by defaulting missing `logScore` fields (`score=1`, fallback `meta`)
  - Safe fallback behavior for provider/prompt/parser/tool failures

### 3) Prompt Files (No hardcoded prompt text)
Added prompt templates under `shared/prompts/`:
- `shared/prompts/system_prompt.txt`
- `shared/prompts/tutor_prompt.txt`
- `shared/prompts/objective_detector_prompt.txt`
- `shared/prompts/student_tutor_prompt.txt`
- `shared/prompts/instructor_control_prompt.txt`
- `shared/prompts/activity_generator_prompt.txt`

Prompt content is file-based and can be updated without code changes.

### 4) Service Layer Integration (Thin)
Updated `app/services.py` minimally:
- Added `tutoringChat(...)` wrapper
- Wrapper keeps existing backend auth/activity checks authoritative by using existing service methods
- No direct Supabase access from LLM orchestration code

### 5) FastAPI Integration
Updated `app/main.py`:
- Added tutoring route: `POST /student/tutor-chat`
- Route remains thin: validate schema -> call service -> normalize response

Updated schema:
- `app/schemas/tutoring.py`
  - `StudentTutoringRequest`

### 6) Config Update
Updated `app/core/config.py` with OpenRouter env config support:
- `openrouter_api_key`
- `openrouter_model`
- `openrouter_base_url`
- `openrouter_timeout_seconds`
- `openrouter_max_retries`
- `openrouter_max_completion_tokens` (default `900`)
- `openrouter_debug` (`OPENROUTER_DEBUG=true` enables provider debug logs)

Still Python 3.8.18 compatible and dotenv loading remains centralized.

## Tests Added/Updated
Added new LLM-focused tests (no live network required):
- `tests/test_openrouter_provider.py`
  - request payload shaping
  - missing API key behavior
  - non-200 response behavior
- `tests/test_llm_prompt_loader.py`
- `tests/test_llm_parser.py`
  - includes topic->activity alias coverage
- `tests/test_llm_dispatcher.py`
- `tests/test_llm_orchestrator.py`
  - validates merged identity params and score defaulting path

Existing tests remain intact and passing.

## Test Result Snapshot
Run command:
- `python -m pytest -q tests`

Latest result:
- `50 passed`

## Runtime Issue Analysis + Fix (May 10, 2026)
Observed symptom from real `/student/tutor-chat` run:
- OpenRouter returned `status=200`, but `choices[0].message.content` was `null`
- `finish_reason` was `length`
- model output contained reasoning text and stopped before final assistant JSON
- API returned: `llm_call_failed: OpenRouter response missing assistant content`

Root cause:
- Completion budget was exhausted before the model produced final structured JSON (`APICall` + `response`), especially with long/strict tutoring instructions and reasoning-enabled model behavior.

Applied fix:
- Increased and centralized completion budget control (`OPENROUTER_MAX_COMPLETION_TOKENS`).
- Enforced JSON response format request in provider payload.
- Added non-thinking hint for DeepSeek models.
- Added retry-on-length strategy when content is missing.
- Kept architecture intact (`prompt_loader -> provider -> parser -> dispatcher -> services`), no repository/service contract break.

## Score Trigger Reliability Fix (May 10, 2026)
Observed behavior:
- Tutor response returned `APICall=""` and asked the student to provide email/password/course/activity again.
- Since no API call was emitted, `logScore` did not run and `score_logs` remained empty.

Root cause:
- Instructor prompt includes a generic "first obtain credentials" step.
- In our backend, credentials are already provided at endpoint call time, but the model can still follow that instruction literally and skip tool call generation.

Applied orchestration fix:
- Added runtime policy override in orchestrator prompt assembly:
  - do NOT ask for email/password/course/activity again
  - emit APICall directly when needed
  - prioritize `logScore` when understanding is detected
- Added deterministic recovery path:
  - if model returns no APICall,
  - orchestrator infers likely learned objective from student message + activity objectives,
  - dispatches `logScore` through existing `ToolDispatcher`/`services.logScore`,
  - appends mini-lesson on successful score event.

Validation:
- Updated tests in `tests/test_llm_orchestrator.py` for this specific recovery path.
- Added coverage for APICall-empty + non-credential assistant replies.
- Latest test result: `52 passed`.

## Compatibility Notes
- Python version target preserved: `3.8.18`
- No `str | None`, `list[str]`, `dict[str, object]` syntax used
- Existing instructor/student core endpoints and behavior preserved
- `instructor_tests/` untouched
