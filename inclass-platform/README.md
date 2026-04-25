# InClass Platform

Python + FastAPI + Supabase (PostgreSQL) classroom activity platform.

## Required entrypoints
- `app/main.py`
- `app/services.py`

## Current Backend Status
- Python version target: `3.8.18`
- Layered structure is active:
  - HTTP layer: `app/main.py`
  - Service layer: `app/services.py`
  - Repository layer: `app/repositories/`
  - Security helpers: `app/core/security.py`
  - Supabase session: `app/db/session.py`

## Implemented So Far
- User repository:
  - `get_user_by_email`
  - `update_password`
  - `verify_password` (plain compare for now)
- Course repository:
  - `get_courses_for_user`
  - `is_user_in_course`
- Activity repository:
  - `get_activity`
  - `list_activities`
- Security:
  - `verify_user`
  - role/course/activity guard helpers
- Services:
  - `studentLogin` implemented and integrated with security

## Test Status
- Command: `python -m pytest -q`
- Result: `9 passed` (local run)

## Run
```bash
uvicorn app.main:app --reload
```
