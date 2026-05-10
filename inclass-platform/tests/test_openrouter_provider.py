import json

import pytest

from app.llm.providers.openrouter_provider import OpenRouterProvider
from app.llm.providers.base import LLMProviderError


class FakeResponse(object):
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


def test_openrouter_provider_builds_expected_payload():
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse(
            status_code=200,
            payload={
                "choices": [
                    {"message": {"content": "{\"APICall\":\"\",\"response\":\"ok\"}"}},
                ],
            },
        )

    provider = OpenRouterProvider(
        api_key="key123",
        model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        timeout_seconds=9.5,
        max_retries=0,
        http_post=fake_post,
    )

    output = provider.generate(
        messages=[{"role": "user", "content": "hello"}],
        system_prompt="system prompt",
        temperature=0.1,
        max_tokens=123,
        metadata={"feature": "test"},
    )

    assert "response" in output
    assert captured["headers"]["Authorization"] == "Bearer key123"
    assert captured["json"]["model"] == "openai/gpt-4o-mini"
    assert captured["json"]["temperature"] == 0.1
    assert captured["json"]["max_tokens"] == 123
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["json"]["messages"][1]["role"] == "user"
    assert captured["timeout"] == 9.5


def test_openrouter_provider_handles_missing_api_key_cleanly():
    provider = OpenRouterProvider(
        api_key=None,
        model="openai/gpt-4o-mini",
        http_post=lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(LLMProviderError):
        provider.generate(messages=[{"role": "user", "content": "hello"}])


def test_openrouter_provider_handles_non_200_response():
    provider = OpenRouterProvider(
        api_key="key123",
        model="openai/gpt-4o-mini",
        max_retries=0,
        http_post=lambda *args, **kwargs: FakeResponse(status_code=401, text="Unauthorized"),
    )

    with pytest.raises(LLMProviderError):
        provider.generate(messages=[{"role": "user", "content": "hello"}])
