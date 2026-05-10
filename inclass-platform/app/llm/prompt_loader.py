"""Prompt template loader for the LLM layer."""

import os
from typing import Optional


class PromptLoadError(RuntimeError):
    """Raised when a prompt cannot be loaded."""


class PromptLoader:
    """Loads prompt templates from disk by name or path."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            self.base_dir = os.path.join(os.getcwd(), "shared", "prompts")
        else:
            self.base_dir = base_dir

    def load_prompt(self, prompt_name_or_path: str) -> str:
        path = self._resolve_path(prompt_name_or_path)
        if not os.path.exists(path):
            raise PromptLoadError("Prompt file not found: {0}".format(path))

        try:
            with open(path, "r", encoding="utf-8") as prompt_file:
                content = prompt_file.read()
        except OSError as exc:
            raise PromptLoadError("Failed to read prompt file: {0}".format(path)) from exc

        if content.strip() == "":
            raise PromptLoadError("Prompt file is empty: {0}".format(path))
        return content

    def _resolve_path(self, prompt_name_or_path: str) -> str:
        if os.path.isabs(prompt_name_or_path):
            return prompt_name_or_path

        if os.path.sep in prompt_name_or_path or prompt_name_or_path.endswith(".txt"):
            return os.path.join(self.base_dir, prompt_name_or_path)

        return os.path.join(self.base_dir, "{0}.txt".format(prompt_name_or_path))
