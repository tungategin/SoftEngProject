"""Tutoring request schemas."""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class StudentTutoringRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int
    message: str
    progress_context: Optional[Dict[str, Any]] = None
