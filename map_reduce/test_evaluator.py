from __future__ import annotations

from typing import Any, Dict

import types

from .evaluator import evaluate_report, evaluate_summary
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


def make_bundle_with_eval(metrics: Dict[str, Any]) -> Bundle:
    return Bundle(
        field_name="test_field",
        format="freeform",
        most_current_data={"x": 1},
        eval_type="llm",
        metrics=list(metrics.keys()),
    )


def test_evaluate_summary_parses_scores(monkeypatch: Any) -> None:
    from . import evaluator

    # evaluator expects JSON mapping metric -> score (0-10)
    content = '{"readability": 8.5, "completeness": 7.0}'
    dummy_client = DummyClient(content)

    def fake_client() -> DummyClient:
        return dummy_client

    def fake_client_and_model():
        return dummy_client, "gpt-4o-mini"

    # Patch the symbols actually used inside evaluator.py
    monkeypatch.setattr(evaluator, "get_client_and_model", fake_client_and_model)

    metrics = {"readability": None, "completeness": None}
    bundle = make_bundle_with_eval(metrics)

    scores = evaluate_summary(bundle, "dummy summary text")
    assert "readability" in scores
    assert "completeness" in scores
    assert 0.0 <= scores["readability"] <= 10.0
    assert 0.0 <= scores["completeness"] <= 10.0


def test_evaluate_report_parses_scores(monkeypatch: Any) -> None:
    from . import evaluator

    content = '{"overall_quality": 9.0}'
    dummy_client = DummyClient(content)

    def fake_client() -> DummyClient:
        return dummy_client

    def fake_client_and_model():
        return dummy_client, "gpt-4o-mini"

    monkeypatch.setattr(evaluator, "get_client_and_model", fake_client_and_model)

    metrics = {"overall_quality": None}
    bundle = make_bundle_with_eval(metrics)
    scores = evaluate_report("dummy report", [bundle])
    assert "overall_quality" in scores
    assert 0.0 <= scores["overall_quality"] <= 10.0

