"""OpenRouter chat-completions provider implementation."""

import json
import time
from typing import Any, Callable, Dict, List, Optional

import httpx

from app.core.config import settings
from app.llm.providers.base import LLMProvider, LLMProviderError


class OpenRouterProvider(LLMProvider):
    """LLM provider backed by OpenRouter Chat Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        http_post: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.model = model if model is not None else settings.openrouter_model
        self.base_url = base_url if base_url is not None else settings.openrouter_base_url
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.openrouter_timeout_seconds
        )
        self.max_retries = max_retries if max_retries is not None else settings.openrouter_max_retries
        self.http_post = http_post if http_post is not None else self._default_http_post

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 400,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        self._validate_configuration()

        payload = self.build_payload(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )
        headers = self.build_headers()

        attempts = 0
        last_error = None
        while attempts <= max(0, self.max_retries):
            attempts += 1
            try:
                response = self.http_post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
            except Exception as exc:
                last_error = exc
                if attempts > max(0, self.max_retries):
                    raise LLMProviderError("OpenRouter request failed: {0}".format(exc))
                time.sleep(0.15)
                continue

            status_code = getattr(response, "status_code", None)
            print("OPENROUTER STATUS:", status_code)
            print("OPENROUTER RAW TEXT:")
            print(response.text)
            if status_code != 200:
                body_text = getattr(response, "text", "")
                if status_code in (429, 500, 502, 503, 504) and attempts <= max(0, self.max_retries):
                    time.sleep(0.2)
                    continue
                raise LLMProviderError(
                    "OpenRouter error status={0} body={1}".format(status_code, body_text),
                )

            try:
                data = response.json()
            except Exception as exc:
                raise LLMProviderError("OpenRouter returned invalid JSON: {0}".format(exc))

            content = self._extract_content(data)
            if content is None:
                raise LLMProviderError("OpenRouter response missing assistant content")
            return content

        raise LLMProviderError("OpenRouter failed after retries: {0}".format(last_error))

    def build_payload(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        outbound_messages = []
        if system_prompt:
            outbound_messages.append({"role": "system", "content": system_prompt})
        outbound_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": outbound_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if metadata:
            payload["metadata"] = metadata
        return payload

    def build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": "Bearer {0}".format(self.api_key),
            "Content-Type": "application/json",
        }

    def _validate_configuration(self) -> None:
        if not self.api_key:
            raise LLMProviderError("OPENROUTER_API_KEY is not configured")
        if not self.model:
            raise LLMProviderError("OPENROUTER_MODEL is not configured")
        if not self.base_url:
            raise LLMProviderError("OPENROUTER_BASE_URL is not configured")

    def _default_http_post(self, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.post(url, **kwargs)

    def _extract_content(self, payload: Dict[str, Any]) -> Optional[str]:
        choices = payload.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            return None

        first = choices[0]
        if not isinstance(first, dict):
            return None

        message = first.get("message")
        if not isinstance(message, dict):
            return None

        content = message.get("content")
        if content is None:
            return None

        if isinstance(content, str):
            return content

        # Some providers return a list of content parts; flatten safely.
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    parts.append(part["text"])
            if parts:
                return "\n".join(parts)

        try:
            return json.dumps(content)
        except Exception:
            return str(content)
