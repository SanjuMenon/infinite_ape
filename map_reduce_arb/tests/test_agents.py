from __future__ import annotations

from typing import Any

import types

from map_reduce_arb.agents import summarize_passthrough, summarize_with_prompt
from map_reduce_arb.prompts import PROMPT_NONE
from map_reduce_arb.schemas import Bundle


class DummyMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class DummyChoice:
    def __init__(self, content: str) -> None:
        self.message = DummyMessage(content)


class DummyChatCompletions:
    def __init__(self, content: str) -> None:
        self._content = content

    def create(self, *args: Any, **kwargs: Any) -> Any:
        return types.SimpleNamespace(choices=[DummyChoice(self._content)])


class DummyClient:
    def __init__(self, content: str) -> None:
        self.chat = types.SimpleNamespace(completions=DummyChatCompletions(content))


def make_bundle(*, prompt: str | None, payload: str) -> Bundle:
    return Bundle(
        field_name="test_field",
        prompt=prompt or "",
        payload=payload,
    )


def test_summarize_passthrough_returns_payload() -> None:
    bundle = make_bundle(prompt=PROMPT_NONE, payload="| key | value |\n|---|---|\n| a | b |")
    text = summarize_passthrough(bundle)
    assert "| key | value |" in text


def test_summarize_with_prompt_uses_llm(monkeypatch: Any) -> None:
    # monkeypatch get_openai_client to avoid real network calls
    import map_reduce_arb.agents as agents_mod

    dummy_client = DummyClient("This is a summary.")

    def fake_client_and_model():
        return dummy_client, "gpt-4o-mini"

    # Patch the symbols actually used inside agents.py
    monkeypatch.setattr(agents_mod, "get_client_and_model", fake_client_and_model)

    bundle = make_bundle(prompt="Summarize this JSON.", payload='{"a": 1}')
    text = summarize_with_prompt(bundle)
    assert "This is a summary." in text


def test_summarize_with_prompt_requires_prompt() -> None:
    bundle = make_bundle(prompt=PROMPT_NONE, payload='{"a": 1}')
    try:
        summarize_with_prompt(bundle)
        assert False, "Expected RuntimeError when prompt is PROMPT_NONE"
    except RuntimeError:
        pass

