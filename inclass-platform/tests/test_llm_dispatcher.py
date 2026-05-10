from app.llm.tool_dispatcher import ToolDispatcher
from app import services


def test_dispatcher_allows_whitelisted_log_score(monkeypatch):
    dispatcher = ToolDispatcher()

    monkeypatch.setattr(
        services,
        "logScore",
        lambda email, password, course_id, activity_no, score, meta=None: {
            "ok": True,
            "score_log": {
                "email": email,
                "activity_no": activity_no,
                "score": score,
                "meta": meta,
            },
        },
    )

    result = dispatcher.dispatch(
        "logScore",
        {
            "email": "s@test.com",
            "password": "pw",
            "course_id": "CSE101",
            "activity_no": 1,
            "score": 1,
            "meta": "Message types",
        },
    )

    assert result["ok"] is True
    assert result["score_log"]["score"] == 1.0


def test_dispatcher_rejects_unknown_action():
    dispatcher = ToolDispatcher()
    result = dispatcher.dispatch("dropAll", {})

    assert result["ok"] is False
    assert result["error"] == "unsupported_action"


def test_dispatcher_rejects_missing_params():
    dispatcher = ToolDispatcher()
    result = dispatcher.dispatch("getActivity", {"email": "s@test.com"})

    assert result["ok"] is False
    assert result["error"] == "missing_params"
