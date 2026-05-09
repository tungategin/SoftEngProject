"""Auth request schemas."""

from pydantic import BaseModel


class StudentLoginRequest(BaseModel):
    email: str
    password: str


class InstructorLoginRequest(BaseModel):
    email: str
    password: str


class StudentChangePasswordRequest(BaseModel):
    email: str
    password: str
    new_password: str
    old_password: str
