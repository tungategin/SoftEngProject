# Definition of Done

## Backend Story DoD
A backend task is considered done when all of the following are true:

1. Code is compatible with Python `3.8.18`.
2. API contract function names and parameter order in `app/services.py` are preserved.
3. Service layer does not directly import Supabase client or run raw table queries.
4. DB operations are implemented only in repository layer (`app/repositories/*`).
5. Authentication/authorization checks are implemented in `app/core/security.py`.
6. Required docs are updated (`README.md`, `docs/architecture.md`, this file).
7. Tests pass in local environment (`python -m pytest -q`).
8. No secrets are hardcoded in code files.

## Current Validation Snapshot
As of April 25, 2026:
- Repository layer for user/course/activity has been implemented.
- `studentLogin` flow has been integrated with `verify_user`.
- Auth/security tests and login tests are green.
- Local test result: `9 passed`.
