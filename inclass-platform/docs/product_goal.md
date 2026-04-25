# Product Goal

## InClass Platform Goal
Build a classroom activity backend where:
- Instructors manage course activities.
- Students access activities only when active.
- Scores are recorded and exported reliably.

## Phase 1 Technical Goal (Current Focus)
- Stabilize backend skeleton with a clean layered architecture.
- Keep API signatures exactly aligned with instructor contract.
- Centralize Supabase access and security checks.
- Prepare service/repository foundation for the remaining endpoints.

## Current Progress
- Core authentication path (`studentLogin`) is connected end-to-end.
- Repository primitives for users, course access, and activities are in place.
- Security helpers are reusable and service-oriented.
