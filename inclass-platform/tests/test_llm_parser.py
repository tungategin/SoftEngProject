from app.llm.response_parser import (
    get_action_name,
    get_action_params,
    get_response_text,
    parse_llm_response,
)


def test_parser_accepts_valid_json():
    raw = '{"APICall":"studentApi(action:\\\"logScore\\\", score=1, meta=\\\"Message types\\\")", "response":"Great work."}'
    parsed = parse_llm_response(raw)

    assert parsed["ok"] is True
    assert get_action_name(parsed) == "logScore"
    assert get_action_params(parsed)["score"] == 1
    assert get_action_params(parsed)["meta"] == "Message types"
    assert get_response_text(parsed) == "Great work."


def test_parser_rejects_invalid_json_safely():
    parsed = parse_llm_response("not a json")

    assert parsed["ok"] is False
    assert parsed["error"] == "invalid_json"
    assert parsed["apicall"] == ""
    assert isinstance(parsed["response"], str)


def test_parser_rejects_unknown_action():
    raw = '{"APICall":"studentApi(action:\\\"dropDatabase\\\")", "response":"No"}'
    parsed = parse_llm_response(raw)

    assert parsed["ok"] is False
    assert parsed["error"] == "unsupported_action"


def test_parser_maps_get_topic_to_get_activity_and_topic_no_alias():
    raw = '{"APICall":"studentApi(action:\\\"getTopic\\\", topic_no=3)", "response":"Checking..."}'
    parsed = parse_llm_response(raw)

    assert parsed["ok"] is True
    assert get_action_name(parsed) == "getActivity"
    assert get_action_params(parsed)["activity_no"] == 3


def test_parser_accepts_lowercase_action_alias():
    raw = '{"APICall":"studentApi(action:\\"logscore\\", score=1, meta=\\"Message format\\")", "response":"ok"}'
    parsed = parse_llm_response(raw)

    assert parsed["ok"] is True
    assert get_action_name(parsed) == "logScore"


def test_parser_leniently_recovers_when_response_contains_unescaped_quotes():
    raw = (
        '{"APICall":"studentApi(action:\\"logScore\\")",'
        '"response":"Protocol fields may include "ON" and "OFF" command values."}'
    )
    parsed = parse_llm_response(raw)

    assert parsed["ok"] is True
    assert get_action_name(parsed) == "logScore"
    assert "ON" in get_response_text(parsed)
