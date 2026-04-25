from app.services import studentLogin

def test_student_login_success():
    res = studentLogin("student@test.com", "123456")
    assert res["ok"] is True

def test_student_login_fail():
    res = studentLogin("student@test.com", "wrong")
    assert res["ok"] is False