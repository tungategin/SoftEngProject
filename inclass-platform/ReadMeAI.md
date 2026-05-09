# ReadMeAI

Last updated: May 9, 2026

## Current Project State
Backend foundation is now established for Phase 1 with a repository-driven architecture.
Core service logic is now broadly implemented for instructor/student workflows.

## What Was Implemented

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

### 5. Tests Added/Updated
- `tests/test_services_core.py` created:
  - covers main core service flows and authorization/error paths
- existing auth/security tests kept and compatible with current logic
- local test run result:
  - `python -m pytest -q`
  - `22 passed`

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
- Latest result: `22 passed`

## Next Suggested Work
1. Add FastAPI endpoint integration tests (TestClient) for critical routes.
2. Add stricter DB schema validation and migration scripts.
3. Replace plain password comparison with secure hashing in repository/security layer.
