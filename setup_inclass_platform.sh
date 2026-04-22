#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-inclass-platform}"

mkdir -p "$ROOT_DIR"
cd "$ROOT_DIR"

# ----------------------------
# Root directories
# ----------------------------
mkdir -p \
  app/core \
  app/db \
  app/models \
  app/repositories \
  app/schemas \
  tests \
  instructor_tests \
  shared/contracts \
  shared/constants \
  docs/sprint_1/daily_scrum \
  docs/sprint_1/review \
  docs/sprint_1/retrospective \
  docs/sprint_1/burndown \
  docs/sprint_1/process \
  docs/sprint_2/daily_scrum \
  docs/sprint_2/review \
  docs/sprint_2/retrospective \
  docs/sprint_2/burndown \
  docs/sprint_2/process \
  frontend/src/api \
  frontend/src/components \
  frontend/src/pages \
  frontend/src/features/auth \
  frontend/src/features/instructor \
  frontend/src/features/student \
  frontend/src/utils \
  scripts \
  source_code

touch instructor_tests/.keep
touch source_code/.keep

# ----------------------------
# Git hygiene
# ----------------------------
cat > .gitignore <<'EOF'
.env
.env.*
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
dist/
build/
node_modules/
EOF

cat > .env.example <<'EOF'
SUPABASE_URL= თქვენს_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=postgresql://user:password@host:5432/dbname
EOF

# ----------------------------
# Requirements
# ----------------------------
cat > requirements.txt <<'EOF'
fastapi>=0.115
uvicorn[standard]>=0.30
pydantic>=2.8
python-dotenv>=1.0
supabase>=2.6
psycopg2-binary>=2.9
sqlalchemy>=2.0
alembic>=1.13
pytest>=8.0
httpx>=0.27
EOF

# ----------------------------
# Root docs
# ----------------------------
cat > README.md <<'EOF'
# InClass Platform

Python + FastAPI + Supabase (PostgreSQL) classroom activity platform.

## Required entrypoints
- `app/main.py`
- `app/services.py`

## Run
```bash
uvicorn app.main:app --reload
```
EOF

cat > REPO_INFO.txt <<'EOF'
GitHub repository URL: https://github.com/tungategin/SoftEngProject
Default branch: main
Sprint release tags: sprint-1, sprint-2
EOF

# ----------------------------
# Shared contract
# ----------------------------
cat > shared/contracts/api_contract.md <<'EOF'
# API Contract

Bu dosya, ekip içi ortak referans içindir.
Instructor testleri ile birebir uyumlu olması gereken kaynak: `app/services.py` içindeki fonksiyon imzalarıdır.

Not:
- Her protected request email + password içermelidir.
- API isimleri ve parametre sırası korunmalıdır.
EOF

cat > shared/constants/roles.py <<'EOF'
INSTRUCTOR = "instructor"
STUDENT = "student"
EOF

cat > shared/constants/activity_status.py <<'EOF'
NOT_STARTED = "NOT_STARTED"
ACTIVE = "ACTIVE"
ENDED = "ENDED"
EOF

# ----------------------------
# App package
# ----------------------------
cat > app/__init__.py <<'EOF'
"""InClass Platform app package."""
EOF

cat > app/core/config.py <<'EOF'
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    database_url: str | None = os.getenv("DATABASE_URL")

settings = Settings()
EOF

cat > app/core/security.py <<'EOF'
"""Auth/security helpers live here."""
EOF

cat > app/core/dependencies.py <<'EOF'
"""FastAPI dependencies live here."""
EOF

cat > app/db/base.py <<'EOF'
"""Database base metadata / models import hub."""
EOF

cat > app/db/session.py <<'EOF'
"""Database session helpers live here."""
EOF

cat > app/db/init_db.py <<'EOF'
"""Optional database initialization helpers live here."""
EOF

cat > app/models/__init__.py <<'EOF'
"""SQLAlchemy models package."""
EOF

cat > app/models/user.py <<'EOF'
"""User model."""
EOF

cat > app/models/course.py <<'EOF'
"""Course model."""
EOF

cat > app/models/activity.py <<'EOF'
"""Activity model."""
EOF

cat > app/models/progress.py <<'EOF'
"""Progress model."""
EOF

cat > app/models/score_log.py <<'EOF'
"""Score log model."""
EOF

cat > app/schemas/__init__.py <<'EOF'
"""Pydantic schemas package."""
EOF

cat > app/schemas/auth.py <<'EOF'
"""Auth schemas."""
EOF

cat > app/schemas/user.py <<'EOF'
"""User schemas."""
EOF

cat > app/schemas/course.py <<'EOF'
"""Course schemas."""
EOF

cat > app/schemas/activity.py <<'EOF'
"""Activity schemas."""
EOF

cat > app/schemas/tutoring.py <<'EOF'
"""Tutoring schemas."""
EOF

cat > app/schemas/scoring.py <<'EOF'
"""Scoring schemas."""
EOF

cat > app/repositories/__init__.py <<'EOF'
"""Repository layer package."""
EOF

cat > app/repositories/user_repo.py <<'EOF'
"""User repository."""
EOF

cat > app/repositories/course_repo.py <<'EOF'
"""Course repository."""
EOF

cat > app/repositories/activity_repo.py <<'EOF'
"""Activity repository."""
EOF

cat > app/repositories/progress_repo.py <<'EOF'
"""Progress repository."""
EOF

cat > app/repositories/score_repo.py <<'EOF'
"""Score repository."""
EOF

cat > app/utils.py <<'EOF'
"""General utility helpers."""
EOF

cat > app/services.py <<'EOF'
"""
IMPORTANT:
Instructor tests will import and call these functions directly.

Keep the function names and parameter order exactly as below.
Implement real logic later; this scaffold preserves contract compatibility.
"""

def studentLogin(email: str, password: str) -> dict:
    raise NotImplementedError

def changeStudentPassword(email: str, password: str, new_password: str, old_password: str) -> dict:
    raise NotImplementedError

def setStudentPassword(email: str, password: str) -> dict:
    raise NotImplementedError

def getActivity(email: str, password: str, course_id: str, activity_no: int) -> dict:
    raise NotImplementedError

def logScore(email: str, password: str, course_id: str, activity_no: int, score: float, meta: str | None = None) -> dict:
    raise NotImplementedError

def instructorLogin(email: str, password: str) -> dict:
    raise NotImplementedError

def changeInstructorPassword(email: str, password: str, old_password: str, new_password: str) -> dict:
    raise NotImplementedError

def setInstructorPassword(email: str, password: str | None = None) -> dict:
    raise NotImplementedError

def listMyCourses(email: str, password: str) -> dict:
    raise NotImplementedError

def listActivities(email: str, password: str, course_id: str) -> dict:
    raise NotImplementedError

def createActivity(email: str, password: str, course_id: str, activity_text: str, learning_objectives: list[str], activity_no_optional: int | None = None) -> dict[str, object]:
    raise NotImplementedError

def updateActivity(email: str, password: str, course_id: str, activity_no: int, patch: dict) -> dict:
    raise NotImplementedError

def startActivity(email: str, password: str, course_id: str, activity_no: int) -> dict:
    raise NotImplementedError

def endActivity(email: str, password: str, course_id: str, activity_no: int) -> dict:
    raise NotImplementedError

def exportScores(email: str, password: str, course_id: str, activity_no: int) -> dict:
    raise NotImplementedError

def resetActivity(email: str, password: str, course_id: str, activity_no: int) -> dict:
    raise NotImplementedError

def resetStudentPassword(email: str, password: str, course_id: str, student_email: str, new_password: str) -> dict:
    raise NotImplementedError
EOF

cat > app/main.py <<'EOF'
from fastapi import FastAPI
from app import services

app = FastAPI(title="InClass Platform")

@app.post("/student/login")
def studentLogin(*, email: str, password: str) -> dict:
    return services.studentLogin(email, password)

@app.post("/student/change-password")
def changeStudentPassword(*, email: str, password: str, new_password: str, old_password: str) -> dict:
    return services.changeStudentPassword(email, password, new_password, old_password)

@app.post("/student/set-password")
def setStudentPassword(*, email: str, password: str) -> dict:
    return services.setStudentPassword(email, password)

@app.post("/student/get-activity")
def getActivity(*, email: str, password: str, course_id: str, activity_no: int) -> dict:
    return services.getActivity(email, password, course_id, activity_no)

@app.post("/student/log-score")
def logScore(*, email: str, password: str, course_id: str, activity_no: int, score: float, meta: str | None = None) -> dict:
    return services.logScore(email, password, course_id, activity_no, score, meta)

@app.post("/instructor/login")
def instructorLogin(*, email: str, password: str) -> dict:
    return services.instructorLogin(email, password)

@app.post("/instructor/change-password")
def changeInstructorPassword(*, email: str, password: str, old_password: str, new_password: str) -> dict:
    return services.changeInstructorPassword(email, password, old_password, new_password)

@app.post("/instructor/set-password")
def setInstructorPassword(*, email: str, password: str | None = None) -> dict:
    return services.setInstructorPassword(email, password)

@app.post("/instructor/list-my-courses")
def listMyCourses(*, email: str, password: str) -> dict:
    return services.listMyCourses(email, password)

@app.post("/instructor/list-activities")
def listActivities(*, email: str, password: str, course_id: str) -> dict:
    return services.listActivities(email, password, course_id)

@app.post("/instructor/create-activity")
def createActivity(
    *,
    email: str,
    password: str,
    course_id: str,
    activity_text: str,
    learning_objectives: list[str],
    activity_no_optional: int | None = None,
) -> dict[str, object]:
    return services.createActivity(
        email,
        password,
        course_id,
        activity_text,
        learning_objectives,
        activity_no_optional,
    )

@app.post("/instructor/update-activity")
def updateActivity(*, email: str, password: str, course_id: str, activity_no: int, patch: dict) -> dict:
    return services.updateActivity(email, password, course_id, activity_no, patch)

@app.post("/instructor/start-activity")
def startActivity(*, email: str, password: str, course_id: str, activity_no: int) -> dict:
    return services.startActivity(email, password, course_id, activity_no)

@app.post("/instructor/end-activity")
def endActivity(*, email: str, password: str, course_id: str, activity_no: int) -> dict:
    return services.endActivity(email, password, course_id, activity_no)

@app.post("/instructor/export-scores")
def exportScores(*, email: str, password: str, course_id: str, activity_no: int) -> dict:
    return services.exportScores(email, password, course_id, activity_no)

@app.post("/instructor/reset-activity")
def resetActivity(*, email: str, password: str, course_id: str, activity_no: int) -> dict:
    return services.resetActivity(email, password, course_id, activity_no)

@app.post("/instructor/reset-student-password")
def resetStudentPassword(*, email: str, password: str, course_id: str, student_email: str, new_password: str) -> dict:
    return services.resetStudentPassword(email, password, course_id, student_email, new_password)
EOF

cat > tests/__init__.py <<'EOF'
EOF

cat > tests/test_smoke.py <<'EOF'
def test_smoke():
    assert True
EOF

# ----------------------------
# Frontend scaffold
# ----------------------------
cat > frontend/package.json <<'EOF'
{
  "name": "inclass-platform-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "echo \"Add your frontend here\""
  }
}
EOF

cat > frontend/src/api/authApi.js <<'EOF'
// API wrapper for auth calls
EOF

cat > frontend/src/api/instructorApi.js <<'EOF'
// API wrapper for instructor calls
EOF

cat > frontend/src/api/studentApi.js <<'EOF'
// API wrapper for student calls
EOF

cat > frontend/src/components/Button.jsx <<'EOF'
export default function Button({ children }) {
  return <button>{children}</button>;
}
EOF

cat > frontend/src/components/Layout.jsx <<'EOF'
export default function Layout({ children }) {
  return <div>{children}</div>;
}
EOF

cat > frontend/src/pages/LoginPage.jsx <<'EOF'
export default function LoginPage() {
  return <div>Login</div>;
}
EOF

cat > frontend/src/pages/InstructorDashboard.jsx <<'EOF'
export default function InstructorDashboard() {
  return <div>Instructor Dashboard</div>;
}
EOF

cat > frontend/src/pages/StudentActivityPage.jsx <<'EOF'
export default function StudentActivityPage() {
  return <div>Student Activity</div>;
}
EOF

cat > frontend/src/features/auth/.keep <<'EOF'
EOF

cat > frontend/src/features/instructor/.keep <<'EOF'
EOF

cat > frontend/src/features/student/.keep <<'EOF'
EOF

cat > frontend/src/utils/helpers.js <<'EOF'
// Shared frontend helpers
EOF

# ----------------------------
# Process/docs templates for 2-sprint work
# ----------------------------
cat > docs/product_goal.md <<'EOF'
# Product Goal
EOF

cat > docs/doD.md <<'EOF'
# Definition of Done
EOF

cat > docs/architecture.md <<'EOF'
# Architecture
EOF

cat > docs/PROMPT_CHANGES.md <<'EOF'
# PROMPT_CHANGES
EOF

for s in 1 2; do
  cat > "docs/sprint_${s}/backlog.md" <<EOF
# Sprint ${s} Backlog
EOF
  cat > "docs/sprint_${s}/scope_change_log.md" <<EOF
# Sprint ${s} Scope Change Log
EOF
  cat > "docs/sprint_${s}/daily_scrum/day1.md" <<EOF
# Sprint ${s} Daily Scrum 1
EOF
  cat > "docs/sprint_${s}/daily_scrum/day2.md" <<EOF
# Sprint ${s} Daily Scrum 2
EOF
  cat > "docs/sprint_${s}/review/review.md" <<EOF
# Sprint ${s} Review
EOF
  cat > "docs/sprint_${s}/retrospective/retro.md" <<EOF
# Sprint ${s} Retrospective
EOF
  cat > "docs/sprint_${s}/burndown/.keep" <<'EOF'
EOF
  cat > "docs/sprint_${s}/process/.keep" <<'EOF'
EOF
done

# ----------------------------
# Helper scripts
# ----------------------------
cat > scripts/setup.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
EOF
chmod +x scripts/setup.sh

cat > scripts/seed_db.py <<'EOF'
"""Seed script placeholder."""
EOF

echo "Scaffold created in: $ROOT_DIR"
