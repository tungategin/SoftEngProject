from typing import Any, Dict, List, Optional

from app.core.security import verify_user

"""
IMPORTANT:
Instructor tests will import and call these functions directly.

Keep the function names and parameter order exactly as below.
Implement real logic later; this scaffold preserves contract compatibility.
"""

def studentLogin(email: str, password: str) -> Dict[str, Any]:
    user = verify_user(email, password)
    if not user:
        return {"ok": False}

    if user.get("role") != "STUDENT":
        return {"ok": False}

    return {"ok": True}

def changeStudentPassword(email: str, password: str, new_password: str, old_password: str) -> Dict[str, Any]:
    raise NotImplementedError

def setStudentPassword(email: str, password: str) -> Dict[str, Any]:
    raise NotImplementedError

def getActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    raise NotImplementedError

def logScore(
    email: str,
    password: str,
    course_id: str,
    activity_no: int,
    score: float,
    meta: Optional[str] = None
) -> Dict[str, Any]:
    raise NotImplementedError

def instructorLogin(email: str, password: str) -> Dict[str, Any]:
    raise NotImplementedError

def changeInstructorPassword(email: str, password: str, old_password: str, new_password: str) -> Dict[str, Any]:
    raise NotImplementedError

def setInstructorPassword(email: str, password: Optional[str] = None) -> Dict[str, Any]:
    raise NotImplementedError

def listMyCourses(email: str, password: str) -> Dict[str, Any]:
    raise NotImplementedError

def listActivities(email: str, password: str, course_id: str) -> Dict[str, Any]:
    raise NotImplementedError

def createActivity(
    email: str,
    password: str,
    course_id: str,
    activity_text: str,
    learning_objectives: List[str],
    activity_no_optional: Optional[int] = None
) -> Dict[str, Any]:
    raise NotImplementedError

def updateActivity(email: str, password: str, course_id: str, activity_no: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    raise NotImplementedError

def startActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    raise NotImplementedError

def endActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    raise NotImplementedError

def exportScores(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    raise NotImplementedError

def resetActivity(email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    raise NotImplementedError

def resetStudentPassword(email: str, password: str, course_id: str, student_email: str, new_password: str) -> Dict[str, Any]:
    raise NotImplementedError
