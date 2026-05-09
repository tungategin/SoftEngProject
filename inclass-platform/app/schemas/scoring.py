"""Scoring request schemas."""

from typing import Optional

from pydantic import BaseModel


class LogScoreRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int
    score: float
    meta: Optional[str] = None
