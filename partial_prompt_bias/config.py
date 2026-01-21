"""Configuration data structures for partial prompt bias experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ChoiceSet:
    """Finite set of possible labels for the classification decision."""

    labels: List[str]

    def __post_init__(self) -> None:
        if not self.labels:
            raise ValueError("ChoiceSet must contain at least one label.")
        if len({label.strip() for label in self.labels}) != len(self.labels):
            raise ValueError("ChoiceSet labels must be unique.")


@dataclass
class ExperimentConfig:
    """Configuration for a single partial-prompt bias experiment."""

    partial_prompt: str
    choice_set: ChoiceSet
    trials_per_choice: int = 50
    bayes_increment: float = 0.1
    bayes_initial_alpha: float = 1.0
    temperature: float = 0.7
    max_tokens: int = 16
    model: str = "gpt-4.1-mini"

    def __post_init__(self) -> None:
        if self.trials_per_choice <= 0:
            raise ValueError("trials_per_choice must be positive.")
        if self.bayes_increment <= 0:
            raise ValueError("bayes_increment must be positive.")
        if self.bayes_initial_alpha <= 0:
            raise ValueError("bayes_initial_alpha must be positive.")
        if self.temperature <= 0:
            raise ValueError("temperature must be positive.")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive.")

