"""Activity schemas."""

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    activity_no: int
    text: str
    status: str
