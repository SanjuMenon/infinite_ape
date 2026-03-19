from __future__ import annotations

from typing import Dict, Any

import types

from .agents import summarize_freeform, summarize_table, summarize_template_fill
from .schemas import Bundle


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


def make_bundle(format: str = "freeform", data: Dict[str, Any] | None = None) -> Bundle:
    return Bundle(
        field_name="test_field",
        format=format,
        most_current_data=data or {"a": 1, "b": 2},
    )


def test_summarize_template_fill_basic() -> None:
    bundle = make_bundle(format="fill_template", data={"foo": "bar", "x": 42})
    text = summarize_template_fill(bundle)
    # deterministic, no LLM; should include keys and values with template structure
    assert "- data:" in text
    assert "  - foo: bar" in text
    assert "  - x: 42" in text


def test_summarize_template_fill_empty_uses_payload() -> None:
    # Explicitly create a bundle whose most_current_data is empty
    bundle = Bundle(field_name="test_field", format="fill_template", most_current_data={})
    text = summarize_template_fill(bundle)
    # when most_current_data is empty, it falls back to serialising the bundle payload
    assert "- payload:" in text
    assert "test_field" in text


def test_summarize_freeform_uses_llm(monkeypatch: Any) -> None:
    # monkeypatch get_openai_client to avoid real network calls
    from . import agents

    dummy_client = DummyClient("This is a summary.")

    def fake_client() -> DummyClient:
        return dummy_client

    def fake_client_and_model():
        return dummy_client, "gpt-4o-mini"

    # Patch the symbols actually used inside agents.py
    monkeypatch.setattr(agents, "get_client_and_model", fake_client_and_model)

    bundle = make_bundle(format="freeform")
    text = summarize_freeform(bundle)
    assert "This is a summary." in text


def test_summarize_table_llm_path(monkeypatch: Any) -> None:
    # monkeypatch get_openai_client to avoid real network calls
    from . import agents

    # return a simple markdown table from the dummy client
    table_text = "| col1 | col2 |\n|---|---|\n| a | b |"
    dummy_client = DummyClient(table_text)

    def fake_client() -> DummyClient:
        return dummy_client

    def fake_client_and_model():
        return dummy_client, "gpt-4o-mini"

    monkeypatch.setattr(agents, "get_client_and_model", fake_client_and_model)

    bundle = make_bundle(format="table")
    text = summarize_table(bundle)
    # should come directly from our dummy client
    assert table_text in text

