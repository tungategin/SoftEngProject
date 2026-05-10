from app.llm.orchestrator import TutorOrchestrator


class FakeLLMClient(object):
    def __init__(self, output):
        self.output = output

    def generate(self, prompt):
        return self.output


class RaisingLLMClient(object):
    def generate(self, prompt):
        raise RuntimeError("provider_down")


class FakeProvider(object):
    def __init__(self, output):
        self.output = output
        self.calls = []

    def generate(self, messages, system_prompt=None, temperature=0.2, max_tokens=400, metadata=None):
        self.calls.append(
            {
                "messages": messages,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "metadata": metadata,
            },
        )
        return self.output


class RaisingProvider(object):
    def generate(self, messages, system_prompt=None, temperature=0.2, max_tokens=400, metadata=None):
        del messages, system_prompt, temperature, max_tokens, metadata
        raise RuntimeError("provider_down")


class FakePromptLoader(object):
    def load_prompt(self, prompt_name_or_path):
        prompts = {
            "system_prompt": "system",
            "tutor_prompt": "Student said: {student_message}",
            "objective_detector_prompt": "objective detector",
        }
        return prompts[prompt_name_or_path]


class FakeDispatcher(object):
    def __init__(self):
        self.calls = []

    def dispatch(self, action, params):
        self.calls.append((action, params))
        if action == "logScore":
            return {"ok": True, "score_log": {"score": 1}}
        return {"ok": True}


def test_orchestrator_runs_with_mocked_llm_and_dispatcher():
    llm_output = '{"APICall":"studentApi(action:\\\"logScore\\\", score=1, meta=\\\"Message flow\\\")", "response":"Great improvement."}'
    dispatcher = FakeDispatcher()
    provider = FakeProvider(llm_output)
    orchestrator = TutorOrchestrator(
        provider=provider,
        prompt_loader=FakePromptLoader(),
        tool_dispatcher=dispatcher,
    )

    result = orchestrator.run(
        email="s@test.com",
        password="pw",
        course_id="CSE101",
        activity_no=1,
        student_message="I now understand message order.",
        activity_context={"text": "Activity", "learning_objectives": ["Message flow"]},
        progress_context={"score": 0},
    )

    assert result["ok"] is True
    assert result["apicall"] != ""
    assert "Mini Lesson" in result["response"]
    assert len(dispatcher.calls) == 1
    assert len(provider.calls) == 1
    # Score default and identity merge should always be present for logScore dispatch.
    action, params = dispatcher.calls[0]
    assert action == "logScore"
    assert params["score"] == 1
    assert params["email"] == "s@test.com"
    assert params["course_id"] == "CSE101"


def test_orchestrator_fallback_when_llm_raises():
    orchestrator = TutorOrchestrator(
        provider=RaisingProvider(),
        prompt_loader=FakePromptLoader(),
        tool_dispatcher=FakeDispatcher(),
    )

    result = orchestrator.run(
        email="s@test.com",
        password="pw",
        course_id="CSE101",
        activity_no=1,
        student_message="hello",
        activity_context={"text": "Activity", "learning_objectives": []},
        progress_context={},
    )

    assert result["ok"] is False
    assert result["error"].startswith("llm_call_failed")
    assert result["apicall"] == ""
