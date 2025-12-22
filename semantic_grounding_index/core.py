"""Core SGI metric computation functions."""

import numpy as np
from typing import Protocol


class Embedder(Protocol):
    """Protocol for embedding functions."""

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string into a vector."""
        ...


def l2_normalize(vec: np.ndarray) -> np.ndarray:
    """
    L2-normalize a vector to unit length.

    Args:
        vec: 1D numpy array

    Returns:
        Normalized vector as float32

    Raises:
        ValueError: If vec contains NaN/Inf or has zero norm
    """
    if vec.ndim != 1:
        raise ValueError(f"Expected 1D array, got {vec.ndim}D")

    # Check for NaN/Inf
    if np.any(np.isnan(vec)) or np.any(np.isinf(vec)):
        raise ValueError("Vector contains NaN or Inf values")

    # Compute norm
    norm = np.linalg.norm(vec)

    # Check for zero vector
    if norm < 1e-30:
        raise ValueError("Vector has zero or near-zero norm")

    # Normalize with small constant for numerical stability
    normalized = vec / (norm + 1e-12)
    return normalized.astype(np.float32)


def angular_distance(u: np.ndarray, v: np.ndarray) -> float:
    """
    Compute angular distance between two normalized vectors on unit sphere.

    Args:
        u: Normalized vector (1D numpy array)
        v: Normalized vector (1D numpy array)

    Returns:
        Angular distance in radians (arccos of clipped dot product)
    """
    dot = float(np.dot(u, v))
    # Clip for numerical stability
    dot = np.clip(dot, -1.0, 1.0)
    return float(np.arccos(dot))


def sgi(q: str, c: str, r: str, embedder: Embedder) -> dict[str, float]:
    """
    Compute SGI (Semantic Grounding Index) metric.

    SGI = θ(r,q) / (θ(r,c) + ε)

    Where:
    - θ(r,q) is the angular distance between response and question
    - θ(r,c) is the angular distance between response and context
    - ε = 1e-8 to avoid division by zero

    Args:
        q: Question string
        c: Context string (retrieved evidence)
        r: Response string (model output)
        embedder: Embedder instance with embed() method

    Returns:
        Dictionary with keys: 'theta_rq', 'theta_rc', 'sgi'

    Raises:
        ValueError: If any input string is empty
    """
    # Validate inputs
    if not q or not isinstance(q, str):
        raise ValueError("Question (q) must be a non-empty string")
    if not c or not isinstance(c, str):
        raise ValueError("Context (c) must be a non-empty string")
    if not r or not isinstance(r, str):
        raise ValueError("Response (r) must be a non-empty string")

    # Embed each string
    qv = embedder.embed(q)
    cv = embedder.embed(c)
    rv = embedder.embed(r)

    # Normalize embeddings
    qv_norm = l2_normalize(qv)
    cv_norm = l2_normalize(cv)
    rv_norm = l2_normalize(rv)

    # Compute angular distances
    theta_rq = angular_distance(rv_norm, qv_norm)
    theta_rc = angular_distance(rv_norm, cv_norm)

    # Compute SGI with epsilon to avoid division by zero
    EPS = 1e-8
    sgi_value = theta_rq / (theta_rc + EPS)

    return {
        "theta_rq": theta_rq,
        "theta_rc": theta_rc,
        "sgi": sgi_value,
    }

