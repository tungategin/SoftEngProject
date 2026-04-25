from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from app import services

app = FastAPI(title="InClass Platform")

@app.post("/student/login")
def studentLogin(*, email: str, password: str) -> Dict[str, Any]:
    return services.studentLogin(email, password)

@app.post("/student/change-password")
def changeStudentPassword(*, email: str, password: str, new_password: str, old_password: str) -> Dict[str, Any]:
    return services.changeStudentPassword(email, password, new_password, old_password)

@app.post("/student/set-password")
def setStudentPassword(*, email: str, password: str) -> Dict[str, Any]:
    return services.setStudentPassword(email, password)

@app.post("/student/get-activity")
def getActivity(*, email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    return services.getActivity(email, password, course_id, activity_no)

@app.post("/student/log-score")
def logScore(*, email: str, password: str, course_id: str, activity_no: int, score: float, meta: Optional[str] = None) -> Dict[str, Any]:
    return services.logScore(email, password, course_id, activity_no, score, meta)

@app.post("/instructor/login")
def instructorLogin(*, email: str, password: str) -> Dict[str, Any]:
    return services.instructorLogin(email, password)

@app.post("/instructor/change-password")
def changeInstructorPassword(*, email: str, password: str, old_password: str, new_password: str) -> Dict[str, Any]:
    return services.changeInstructorPassword(email, password, old_password, new_password)

@app.post("/instructor/set-password")
def setInstructorPassword(*, email: str, password: Optional[str] = None) -> Dict[str, Any]:
    return services.setInstructorPassword(email, password)

@app.post("/instructor/list-my-courses")
def listMyCourses(*, email: str, password: str) -> Dict[str, Any]:
    return services.listMyCourses(email, password)

@app.post("/instructor/list-activities")
def listActivities(*, email: str, password: str, course_id: str) -> Dict[str, Any]:
    return services.listActivities(email, password, course_id)

@app.post("/instructor/create-activity")
def createActivity(
    *,
    email: str,
    password: str,
    course_id: str,
    activity_text: str,
    learning_objectives: List[str],
    activity_no_optional: Optional[int] = None,
) -> Dict[str, Any]:
    return services.createActivity(
        email,
        password,
        course_id,
        activity_text,
        learning_objectives,
        activity_no_optional,
    )

@app.post("/instructor/update-activity")
def updateActivity(*, email: str, password: str, course_id: str, activity_no: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    return services.updateActivity(email, password, course_id, activity_no, patch)

@app.post("/instructor/start-activity")
def startActivity(*, email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    return services.startActivity(email, password, course_id, activity_no)

@app.post("/instructor/end-activity")
def endActivity(*, email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    return services.endActivity(email, password, course_id, activity_no)

@app.post("/instructor/export-scores")
def exportScores(*, email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    return services.exportScores(email, password, course_id, activity_no)

@app.post("/instructor/reset-activity")
def resetActivity(*, email: str, password: str, course_id: str, activity_no: int) -> Dict[str, Any]:
    return services.resetActivity(email, password, course_id, activity_no)

@app.post("/instructor/reset-student-password")
def resetStudentPassword(*, email: str, password: str, course_id: str, student_email: str, new_password: str) -> Dict[str, Any]:
    return services.resetStudentPassword(email, password, course_id, student_email, new_password)
