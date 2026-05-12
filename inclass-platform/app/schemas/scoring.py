"""Scoring request schemas."""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class LogScoreRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int
    score: float
    meta: Optional[str] = None


class ManualGradeRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int
    student_email: str
    manual_score: int
    reason: str
    meta: Optional[Dict[str, Any]] = None
