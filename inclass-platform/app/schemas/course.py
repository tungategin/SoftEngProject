"""Course/activity request schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CourseRequest(BaseModel):
    email: str
    password: str
    course_id: str


class GetActivityRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int


class CreateActivityRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_text: str
    learning_objectives: List[str]
    activity_no_optional: Optional[int] = None


class UpdateActivityRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int
    patch: Dict[str, Any]


class StartEndActivityRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int


class ExportScoresRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int


class ResetActivityRequest(BaseModel):
    email: str
    password: str
    course_id: str
    activity_no: int
