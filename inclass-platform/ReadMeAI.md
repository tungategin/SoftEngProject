# ReadMeAI

Last updated: May 12, 2026 (Score trigger + schema alignment hardening)

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
- `57 passed`

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

## Score Trigger Root-Cause Fix (May 12, 2026)
Observed debug trace:
- LLM output was valid JSON but returned `APICall=""`.
- Parser worked (`action=None`).
- Orchestrator fallback objective inference returned `None`.
- Dispatcher was never called; `logScore` never reached services/repository.

Fixes applied:
- Service-level objective normalization in `getActivity`:
  - supports list / JSON-string / semicolon-comma-newline string formats.
- Orchestrator fallback strengthened:
  - objective extraction now supports list and string formats.
  - if APICall is empty and objective match is still unavailable, conceptual-answer heuristic triggers safe fallback score call with `meta="objective_detected"`.
- Parser robustness improved:
  - case-insensitive action alias mapping (`logscore` -> `logScore`, etc.).
- Prompt reinforcement:
  - tutor prompts now explicitly require `logScore` APICall when student message already demonstrates a learning point.
- Debug instrumentation added (non-architectural):
  - orchestrator, parser, dispatcher, services.logScore, score_repo, and activity status gate now print trace logs.

Validation:
- `python -m pytest -q tests` -> `55 passed`.

## Supabase Schema Mismatch Fix (May 12, 2026)
Observed runtime error:
- `PGRST204: Could not find the 'activity_no' column of 'score_logs' in the schema cache`

Confirmed root cause from schema export:
- `score_logs` table does **not** contain `activity_no`, `student_email`, or `score`.
- Actual required columns include:
  - `activity_id` (uuid)
  - `score_before` (integer)
  - `score_delta` (integer)
  - `score_after` (integer)
  - `source` (enum)
  - `meta` (jsonb)

Applied fixes:
1) Reworked `app/repositories/score_repo.py` to real schema:
- Resolves `activity_id` from `(course_id, activity_no)` via `activities`.
- Computes score progression using `student_progress.current_score`.
- Inserts proper `score_logs` payload with required fields.
- Resolves optional `objective_id` from `activity_objectives` using `meta`.
- Updates/inserts `student_progress` after score insert.
- `list_scores`/`delete_scores`/`find_existing_score_log` now filter using `activity_id`.

2) Prevented API 500 on repository insert failures:
- `services.logScore` now catches repository exceptions and returns:
  - `{"ok": False, "error": "score_log_insert_failed"}`

3) Added safety test:
- `tests/test_services_core.py` includes case for repo insert failure path.

Validation:
- `python -m pytest -q tests` -> `56 passed`.

## Post-Restart Continuation Fix (May 12, 2026)
Issue after restart:
- `/student/tutor-chat` returned `apicall=""` and `tool_result=null` despite clear assistant praise.
- This happened when student answer was short/keyword-based (e.g., message type names), so student-text heuristic alone did not always cross threshold.

Applied fix:
- In `app/llm/orchestrator.py`, APICall-empty fallback now also uses assistant-response signals:
  - objective inference from assistant response text
  - mastery phrase detection (e.g., "Excellent", "key concept", "fundamental", etc.)
- If mastery is indicated but APICall is empty, orchestrator triggers `logScore` fallback safely.

Additional validation:
- Added unit test:
  - `test_orchestrator_logs_score_when_assistant_confirms_mastery_but_apicall_empty`
- Updated test result:
  - `python -m pytest -q tests` -> `57 passed`

## Activity Schema Alignment (May 12, 2026)
Schema cross-check from Supabase export showed:
- `activities` stores prompt text in `activity_text` (not `text`).
- learning objectives are normalized in separate `activity_objectives` table (not a direct `learning_objectives` column on `activities`).

Applied repository fixes:
- `app/repositories/activity_repo.py`
  - `get_activity` now maps DB row into contract shape:
    - `text` <- `activity_text`
    - `learning_objectives` <- active `activity_objectives.description` list
  - `list_activities` now returns contract-shaped rows.
  - `create_activity` writes `activity_text` and inserts objective rows.
  - `update_activity` maps `text` -> `activity_text`; can replace objective rows.

Impact:
- Orchestrator now receives non-empty objective context much more reliably.
- Score trigger fallback has stronger signal quality even when model APICall is empty.

## score_source Enum Fix (May 12, 2026)
Root cause identified from runtime logs:
- `score_logs.source` is enum `score_source`.
- Live OpenAPI metadata shows allowed values:
  - `TUTORING_FLOW`
  - `MANUAL_GRADE`
  - `RESET_ADJUSTMENT`
- Previous retry list used invalid values (`LLM_TUTOR`, `AUTO`, `MANUAL`, etc.), so inserts always failed.

Applied fix:
- `app/repositories/score_repo.py` now writes:
  - `source = "TUTORING_FLOW"` for tutoring-triggered score logs.
- Removed invalid source probing loop.

Live verification:
- Executed direct `services.logScore(...)` call against Supabase.
- Insert succeeded and returned a created `score_logs` row with `source: "TUTORING_FLOW"`.

## Compatibility Notes
- Python version target preserved: `3.8.18`
- No `str | None`, `list[str]`, `dict[str, object]` syntax used
- Existing instructor/student core endpoints and behavior preserved
- `instructor_tests/` untouched

## Sprint-2 US Hardening Update (May 12, 2026)

### Implemented: US-L Manual Grading Flow
Added end-to-end manual grading support in backend:
- New service function: `manualGradeStudent(...)` in `app/services.py`
- New routes in `app/main.py`:
  - `POST /instructor/manual-grade`
  - `POST /instructor/grade-student` (alias)
- New request schema in `app/schemas/scoring.py`:
  - `ManualGradeRequest`
- Repository support in `app/repositories/score_repo.py`:
  - `create_manual_grade_event(...)`
  - score insert with `source="MANUAL_GRADE"`

Flow guarantees:
- Instructor auth + course authorization enforced server-side.
- Target student existence/role/course membership validated.
- Score log inserted first, then `manual_grade_events` row inserted and linked.

### Implemented: US-M Reset Activity Flow
Upgraded reset behavior from simple delete to full state transition:
- `services.resetActivity(...)` now:
  1. validates instructor + course access,
  2. validates activity existence,
  3. deletes activity score logs,
  4. resets `student_progress` (`current_score=0`, `completed_objective_ids=[]`, `is_completed=false`, `last_score_log_id=null`),
  5. marks activity as `ENDED` and stamps reset time.
- `app/repositories/activity_repo.py`:
  - added `mark_activity_reset(...)` (`status=ENDED`, `ended_at`, `reset_at`)
- `app/repositories/score_repo.py`:
  - added `reset_student_progress(...)`

Result:
- Reset closes the activity and blocks future score logs via existing `require_active_activity` guard.

### Activity Completion Gating + Objective Integrity
Strengthened scoring reliability for US-K/J behavior:
- `services.logScore(...)` now enforces:
  - positive score input,
  - completion guard (`activity_completed` => block),
  - objective resolution from activity objectives,
  - fallback to next unscored objective when needed,
  - duplicate objective guard (no second point for same objective),
  - fixed +1 scoring for tutoring objective achievement,
  - consistent completion metadata in response.
- `score_repo` now provides completion/objective helpers:
  - `get_completion_state(...)`
  - `resolve_objective(...)`
  - `pick_next_unscored_objective(...)`
  - `is_objective_completed(...)`

### Tutoring Flow Stability (Backend-Side)
- `services.tutoringChat(...)` now preloads completion state into progress context.
- If activity is already completed, tutoring returns deterministic completion response and does not continue scoring.
- `app/llm/orchestrator.py` now:
  - short-circuits on completed activities,
  - only emits mini-lesson when `score_added > 0`,
  - appends completion message when last objective is covered.

### Authorization Hardening Coverage
Manual grading/reset and score logging all pass through server-side role/course checks.
Unauthorized authenticated calls remain rejected in service layer.

### Tests Added/Updated
Updated tests for new behavior and regression safety:
- `tests/test_services_core.py`
  - duplicate objective no-rescore
  - completed activity score block
  - manual grade success + unauthorized rejection
  - reset flow with score delete + progress reset + ENDED transition
  - tutoring completion-stop behavior
- `tests/test_api_integration.py`
  - manual grade endpoint success
  - reset activity endpoint state assertions
- `tests/test_llm_orchestrator.py`
  - completed activity orchestration short-circuit
  - dispatcher score-added contract alignment

Validation:
- `pytest -q tests` -> `65 passed`

### Current US Status (Backend)
- US-C: Server-side role/course authorization -> implemented
- US-D/E/F/G/H/I: course/activity management + active access rules -> implemented
- US-J: tutoring loop backend orchestration path -> implemented (with completion stop)
- US-K: objective-based scoring with duplicate prevention + logging -> hardened
- US-L: manual grading -> implemented
- US-M: reset activity with close + score cleanup + score blocking -> implemented

## 2026-05-13 Debug & Fix: Tutor Chat Score Trigger Reliability

### Problem Observed
- In `/student/tutor-chat`, model sometimes produced:
  - `APICall` with `email:""` / `password:""` placeholders
  - pseudo-JSON responses that looked structured but occasionally failed strict JSON parsing
- Result:
  - `services.logScore(...)` received empty identity fields
  - `verify_user` failed with `invalid_credentials`
  - final objective score trigger was blocked

### Root Cause
- `app/llm/orchestrator.py` parameter merge logic accepted model identity placeholders in some paths.
- `app/llm/response_parser.py` strict parse could fail when model output included unescaped quotes in long tutoring text.

### Changes Applied
- `app/llm/orchestrator.py`
  - hardened `_merge_identity_params(...)`:
    - for `getActivity` and `logScore`, `email/password/course_id/activity_no` now always come from authenticated backend request context
    - prevents model placeholder identity from overriding trusted values
  - added blank-value helper for safe defaulting behavior where needed
- `app/llm/response_parser.py`
  - improved fallback parsing robustness:
    - strict string field regex now requires proper field delimiter lookahead
    - added lenient structured field extraction for malformed JSON-like outputs
  - reduces `invalid_json` failures for DeepSeek long responses

### Tests Added/Updated
- `tests/test_llm_orchestrator.py`
  - added test to verify blank model identity fields are overridden correctly
- `tests/test_llm_parser.py`
  - added malformed JSON recovery test (unescaped quotes in response body)

Validation:
- `pytest -q tests/test_llm_parser.py tests/test_llm_orchestrator.py` -> `14 passed`
- `pytest -q tests` -> `67 passed`

## 2026-05-13 Manual Grading Semantics + Instructor Preview

### Manual grade behavior fix (US-L alignment)
- Updated `services.manualGradeStudent(...)` so `manual_score` is treated as **absolute target score** for the selected student+activity.
- Previous behavior added/subtracted as raw delta; new behavior computes:
  - `score_delta = target_score - current_score`
  - applies only required delta to reach exact target.
- Manual grading event is still inserted and now includes richer metadata:
  - `target_score`
  - `score_before`
  - `applied_delta`
  - optional instructor-provided details.
- Unauthorized instructor/course checks remain unchanged and enforced server-side.

### Export preview improvement (frontend)
- Instructor dashboard now refreshes score preview rows automatically:
  - after selecting an activity row
  - after successful manual grading
- This makes the bottom "Export Preview" section show up-to-date student grades without requiring manual export click first.

### Score preview data consistency
- Updated `score_repo.list_scores(...)` to return **per-student current activity score** using `student_progress.current_score` (final grade view), instead of raw per-log `score_delta`.
- Preview now matches expected grading interpretation better for instructor workflows.

### Tests
- Added coverage:
  - `test_manual_grade_sets_absolute_score_not_increment` in `tests/test_services_core.py`
- Validation:
  - `pytest -q tests/test_services_core.py tests/test_api_integration.py` -> `35 passed`
  - `pytest -q tests` -> `68 passed`

## 2026-05-13 Final Hardening (US-A/B Excluded)

Scope:
- Completed remaining partial items except federated-auth stories (US-A and US-B), as requested.

### US-I hardening: hide objectives from student responses
- Updated `services.getActivity(...)` to stop returning `learning_objectives` in student-facing payload.
- Preserved objective-driven tutoring/scoring internally by loading full activity context in `services.tutoringChat(...)` before orchestration.

### US-F hardening: server-side required field validation for createActivity
- Added strict backend validation in `services.createActivity(...)`:
  - empty/whitespace `activity_text` -> `activity_text_required`
  - empty/whitespace-only objectives -> `learning_objectives_required`
- Keeps required-field enforcement in backend (not only frontend).

### US-J/US-K hardening: tutoring response stability
- Updated `app/llm/orchestrator.py`:
  - deterministic score announcement appended after successful `logScore` (`Your current score is now X.`),
  - first-turn tutoring response now ensures activity text inclusion when student initiates start flow,
  - response normalization enforces a single visible guidance question marker to keep step-by-step behavior tighter.
- Existing completion-stop and mini-lesson-after-score behavior remains intact.

### Tests Added/Updated
- `tests/test_services_core.py`
  - `test_get_activity_hides_learning_objectives_even_if_present_in_db_row`
  - `test_create_activity_rejects_empty_text`
  - `test_create_activity_rejects_empty_objectives`
- `tests/test_llm_orchestrator.py`
  - `test_orchestrator_enforces_single_question_in_response`
  - `test_orchestrator_includes_activity_text_on_start_turn`

Validation:
- `pytest -q tests/test_services_core.py tests/test_llm_orchestrator.py tests/test_api_integration.py` -> `47 passed`
- `pytest -q tests` -> `72 passed`

## 2026-05-13 Prompt Quality + Activity-Specific Tutoring Fix

### Problem addressed
- Tutor repeatedly reused the old pump scenario even for newly created activities.
- Off-topic student answers could still trigger `logScore`.
- Mini-lesson title could expose raw objective sentence (e.g., "Student should understand ...") directly.

### Changes implemented
- Rewrote:
  - `shared/prompts/student_tutor_prompt.txt`
  - `shared/prompts/tutor_prompt.txt`
- New prompt behavior is runtime-context driven:
  - use only `activity_text` + `learning_objectives` from runtime context,
  - ignore hardcoded sample scenarios,
  - no credential re-asking,
  - one-question guidance flow,
  - score only when relevant.

- Hardened `app/llm/orchestrator.py`:
  - added off-topic `logScore` gate (`_allow_log_score` + relevance checks),
  - removed unsafe assistant-response-based objective fallback,
  - added stronger runtime policy overrides in final prompt rendering,
  - sanitized mini-lesson topic labels (avoid raw "Student should understand ..." titles),
  - reduced repeated "Let's begin..." restart noise in later turns,
  - kept completion-stop behavior intact.

### Regression/validation
- `pytest -q tests/test_llm_orchestrator.py tests/test_llm_parser.py tests/test_services_core.py` -> `39 passed`
- `pytest -q tests` -> `72 passed`
