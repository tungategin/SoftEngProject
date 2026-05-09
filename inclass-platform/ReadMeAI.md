# ReadMeAI

Last updated: May 9, 2026 (FastAPI integration update)

## Current Project State
Backend foundation is now established for Phase 1 with a repository-driven architecture.
Core service logic is now broadly implemented for instructor/student workflows.

## What Was Implemented

### 0. FastAPI Integration Layer
- `app/main.py` was refactored to keep routes thin and schema-driven.
- Added POST endpoints for the requested student/instructor operations:
  - `/student/login`
  - `/student/change-password`
  - `/student/get-activity`
  - `/student/log-score`
  - `/instructor/login`
  - `/instructor/list-courses` (plus legacy alias `/instructor/list-my-courses`)
  - `/instructor/list-activities`
  - `/instructor/create-activity`
  - `/instructor/update-activity`
  - `/instructor/start-activity`
  - `/instructor/end-activity`
  - `/instructor/export-scores`
  - `/instructor/reset-activity`
- Route responsibilities are limited to:
  - request validation
  - service function invocation
  - consistent response shaping

### 0.1 Response Consistency
- Added response normalization in `app/main.py`.
- Endpoint output now follows:
  - success: `{"ok": True, "data": {...}}`
  - failure: `{"ok": False, "error": "..."}`

### 1. Data Layer (Repository)
- `app/repositories/user_repo.py`
  - `get_user_by_email(email: str) -> Optional[Dict]`
  - `update_password(user_id: str, new_password: str) -> None`
  - `verify_password(user: Dict, password: str) -> bool`
- `app/repositories/course_repo.py`
  - `get_courses_for_user(user_id: str) -> List[Dict]`
  - `is_user_in_course(user_id: str, course_id: str) -> bool`
- `app/repositories/activity_repo.py`
  - `get_activity(course_id: str, activity_no: int) -> Optional[Dict]`
  - `list_activities(course_id: str) -> List[Dict]`
  - `create_activity(...) -> Dict`
  - `update_activity(...) -> Optional[Dict]`
  - `set_activity_status(...) -> Optional[Dict]`
  - `get_next_activity_no(course_id: str) -> int`
- `app/repositories/score_repo.py`
  - `log_score(...) -> Dict`
  - `list_scores(course_id: str, activity_no: int) -> List[Dict]`
  - `delete_scores(course_id: str, activity_no: int) -> int`

### 2. Security Layer
- `app/core/security.py`
  - `verify_user(email, password)` returns user dict or `None`
  - role and authorization helper functions are reusable for other endpoints

### 3. Service Layer
- `app/services.py`
  - `studentLogin`
  - `changeStudentPassword`
  - `setStudentPassword`
  - `instructorLogin`
  - `changeInstructorPassword`
  - `setInstructorPassword`
  - `listMyCourses`
  - `listActivities`
  - `getActivity`
  - `logScore`
  - `createActivity`
  - `updateActivity`
  - `startActivity`
  - `endActivity`
  - `exportScores`
  - `resetActivity`
  - `resetStudentPassword`

These functions now contain end-to-end service logic using:
- authentication via `verify_user`
- authorization via security helpers
- data operations via repository layer
- consistent dict-based success/failure responses

### 4. Schemas
- `app/schemas/user.py` -> `UserResponse`
- `app/schemas/activity.py` -> `ActivityResponse`
- New request schemas for endpoint validation:
  - `app/schemas/auth.py`
  - `app/schemas/course.py`
  - `app/schemas/scoring.py`

### 5. Tests Added/Updated
- `tests/test_services_core.py` created:
  - covers main core service flows and authorization/error paths
- `tests/test_api_integration.py` created:
  - endpoint-level integration tests using `TestClient`
  - covers login, authorization checks, activity state checks, create/start/end/export flows
- existing auth/security tests kept and compatible with current logic
- local test run result:
  - `python -m pytest -q`
  - `22 passed, 1 skipped`

### 6. Documentation Updated
- `README.md`
- `docs/architecture.md`
- `docs/doD.md`
- `docs/product_goal.md`
- `ReadMeAI.md` (this file)

## Python Compatibility Note
All updated backend files were kept Python `3.8.18` compatible.
No Python 3.10+ typing syntax is used in the updated implementation.

## Test Snapshot
- Run command: `python -m pytest -q`
- Latest result: `22 passed, 1 skipped`
- Note: skipped test module is the FastAPI integration suite on environments where `fastapi` is not installed.

## Next Suggested Work
1. Add FastAPI endpoint integration tests (TestClient) for critical routes.
2. Add stricter DB schema validation and migration scripts.
3. Replace plain password comparison with secure hashing in repository/security layer.

## Debug Investigation Note (500 Internal Server Error)

Date: May 9, 2026

### Investigated symptom
- `/student/login` was returning 500.

### Root cause chain identified
1. `.env` was not being loaded into process environment at runtime.
   - `settings.supabase_url` and `settings.supabase_service_role_key` were `None`.
2. After enabling `.env` loading, a second error appeared:
   - Supabase client initialization failed with `Invalid API key`.
   - This indicates the provided key format/value is not accepted by `supabase-py` in current setup.

### Applied code changes
- `app/core/config.py`
  - Added dotenv loading via:
    - `load_dotenv(find_dotenv(usecwd=True), override=False)`
- `app/db/session.py`
  - Wrapped `create_client(...)` with explicit error handling.
  - Raised actionable `RuntimeError` with guidance when Supabase client init fails.

### Practical fix required in environment
- Verify that `SUPABASE_SERVICE_ROLE_KEY` is a valid JWT-style `service_role`/`anon` key that your current `supabase` client version accepts.
- Re-check copied key value (no extra spaces/newlines, no quoting mistakes).
