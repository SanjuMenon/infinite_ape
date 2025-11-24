"DNUI computation utilities."

from __future__ import annotations

import math
from typing import Sequence


def _validate_distribution(p: Sequence[float]) -> list[float]:
    if not p:
        raise ValueError("Distribution must be non-empty.")
    probs = list(p)
    total = sum(probs)
    if not math.isfinite(total):
        raise ValueError("Probabilities must be finite.")
    if not math.isclose(total, 1.0, rel_tol=1e-8, abs_tol=1e-8):
        raise ValueError("Probabilities must sum to 1.")
    if any(pi < 0 for pi in probs):
        raise ValueError("Probabilities must be non-negative.")
    return probs


def compute_dnui_discrete(p: Sequence[float]) -> float:
    """
    Placeholder for Huang (2025) DNUI Eq. (11) over discrete distributions.

    Raises NotImplementedError so callers can fall back to the approximate
    implementation.
    """

    _validate_distribution(p)
    raise NotImplementedError(
        "Exact DNUI Eq. (11) not yet implemented; use compute_dnui_simple_l2."
    )


def compute_dnui_simple_l2(p: Sequence[float]) -> float:
    """Simple 0–1 scaled L2 deviation from uniform as DNUI fallback."""

    probs = _validate_distribution(p)
    n = len(probs)
    uniform = 1.0 / n
    numerator = sum((pi - uniform) ** 2 for pi in probs)
    denominator = (1.0 - uniform) ** 2 + (n - 1) * (uniform**2)
    if denominator == 0:
        return 0.0
    return math.sqrt(numerator / denominator)

