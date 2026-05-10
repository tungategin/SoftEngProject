import os

import pytest

from app.llm.prompt_loader import PromptLoadError, PromptLoader


def test_prompt_loader_loads_text_successfully(tmp_path):
    prompt_file = tmp_path / "tutor_prompt.txt"
    prompt_file.write_text("Hello {student_message}", encoding="utf-8")

    loader = PromptLoader(base_dir=str(tmp_path))
    text = loader.load_prompt("tutor_prompt")

    assert text == "Hello {student_message}"


def test_prompt_loader_raises_for_missing_file(tmp_path):
    loader = PromptLoader(base_dir=str(tmp_path))

    with pytest.raises(PromptLoadError):
        loader.load_prompt("missing_prompt")
