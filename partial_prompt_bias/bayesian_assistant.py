"""Bayesian assistant maintaining Dirichlet-like scores."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class BayesianAssistant:
    """Maintains α_i scores and provides samples from the normalized distribution."""

    n_choices: int
    increment: float = 0.1
    initial_alpha: float = 1.0
    alpha: List[float] = field(init=False)

    def __post_init__(self) -> None:
        if self.n_choices <= 0:
            raise ValueError("n_choices must be positive.")
        if self.increment <= 0:
            raise ValueError("increment must be positive.")
        if self.initial_alpha <= 0:
            raise ValueError("initial_alpha must be positive.")
        self.alpha = [self.initial_alpha] * self.n_choices

    def update(self, chosen_idx: int) -> None:
        """Increment α for the chosen index."""
        if not 0 <= chosen_idx < self.n_choices:
            raise IndexError("chosen_idx out of range.")
        self.alpha[chosen_idx] += self.increment

    @property
    def distribution(self) -> List[float]:
        """Return the normalized probability distribution."""
        total = sum(self.alpha)
        if total == 0:
            raise ZeroDivisionError("Total alpha cannot be zero.")
        return [value / total for value in self.alpha]

    def sample_feedback(self, rng: random.Random | None = None) -> int:
        """Sample an index from the current distribution using inverse CDF."""
        if rng is None:
            rng = random
        dist = self.distribution
        threshold = rng.random()
        cumulative = 0.0
        for idx, prob in enumerate(dist):
            cumulative += prob
            if threshold <= cumulative:
                return idx
        return len(dist) - 1

