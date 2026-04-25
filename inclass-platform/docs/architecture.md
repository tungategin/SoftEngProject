# Architecture

## Overview
InClass Platform backend is organized with a layered architecture:

- `app/main.py`: HTTP layer (FastAPI routes)
- `app/services.py`: Service layer (application flow and contract functions)
- `app/repositories/`: Data access layer (Supabase table queries only)
- `app/core/`: Cross-cutting concerns (`config`, `security`, dependencies)
- `app/db/session.py`: Centralized Supabase client creation
- `app/schemas/`: Pydantic response/request models

## Data Flow
1. Request enters via `app/main.py`.
2. Route calls matching function in `app/services.py`.
3. Service calls `app/core/security.py` for auth checks.
4. Security/service reads or writes data through repository functions.
5. Repositories use `get_supabase_client()` from `app/db/session.py`.

## Current Repository Layer
- `user_repo.py`
  - `get_user_by_email(email)`
  - `update_password(user_id, new_password)`
  - `verify_password(user, password)` (plain compare for now)
- `course_repo.py`
  - `get_courses_for_user(user_id)`
  - `is_user_in_course(user_id, course_id)`
- `activity_repo.py`
  - `get_activity(course_id, activity_no)`
  - `list_activities(course_id)`

## Security Layer (Current)
- `verify_user(email, password) -> Optional[Dict[str, Any]]`
- `require_role(user, role)`
- `require_course_access(user, course_id)`
- `require_active_activity(activity)`
- `require_instructor_of_course(user, course_id)`

`verify_user` currently returns `None` for invalid credentials, as required by service integration.

## Python Compatibility
Project code is kept compatible with Python `3.8.18`:
- `Optional[str]`, `List[str]`, `Dict[str, Any]` typing style is used
- Python 3.10+ union syntax is avoided in updated backend files

## Environment Variables
The backend reads these variables:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`

They are loaded through `app/core/config.py` and consumed by `app/db/session.py`.
