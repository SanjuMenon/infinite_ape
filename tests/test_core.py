"""Tests for core SGI functions."""

import numpy as np
import pytest
from semantic_grounding_index.core import l2_normalize, angular_distance, sgi


class DummyEmbedder:
    """Deterministic embedder for testing."""

    def __init__(self):
        # Simple deterministic mapping: hash text -> fixed vector
        # Use a small dimension for testing
        self.dim = 128
        self._cache = {}

    def _get_vector(self, text: str) -> np.ndarray:
        """Generate deterministic vector from text."""
        if text not in self._cache:
            # Use hash to create deterministic but varied vectors
            np.random.seed(hash(text) % (2**31))
            vec = np.random.randn(self.dim).astype(np.float32)
            # Ensure non-zero norm
            vec = vec / np.linalg.norm(vec) * (1.0 + abs(hash(text)) % 10)
            self._cache[text] = vec
        return self._cache[text].copy()

    def embed(self, text: str) -> np.ndarray:
        """Embed text to vector."""
        return self._get_vector(text)


def test_l2_normalize_unit_norm():
    """Test that l2_normalize returns unit norm vectors."""
    vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    normalized = l2_normalize(vec)
    norm = np.linalg.norm(normalized)
    assert abs(norm - 1.0) < 1e-6, f"Expected norm ~1.0, got {norm}"
    assert normalized.dtype == np.float32


def test_l2_normalize_zero_vector():
    """Test that l2_normalize raises on zero vector."""
    vec = np.zeros(10, dtype=np.float32)
    with pytest.raises(ValueError, match="zero"):
        l2_normalize(vec)


def test_l2_normalize_nan():
    """Test that l2_normalize raises on NaN."""
    vec = np.array([1.0, np.nan, 3.0], dtype=np.float32)
    with pytest.raises(ValueError, match="NaN"):
        l2_normalize(vec)


def test_l2_normalize_inf():
    """Test that l2_normalize raises on Inf."""
    vec = np.array([1.0, np.inf, 3.0], dtype=np.float32)
    with pytest.raises(ValueError, match="Inf"):
        l2_normalize(vec)


def test_l2_normalize_not_1d():
    """Test that l2_normalize raises on non-1D array."""
    vec = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    with pytest.raises(ValueError, match="1D"):
        l2_normalize(vec)


def test_angular_distance_basic():
    """Test angular_distance with known vectors."""
    # Unit vectors pointing in same direction
    u = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    dist = angular_distance(u, v)
    assert abs(dist) < 1e-6, f"Expected ~0, got {dist}"

    # Orthogonal vectors
    u = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    dist = angular_distance(u, v)
    expected = np.pi / 2
    assert abs(dist - expected) < 1e-6, f"Expected ~π/2, got {dist}"

    # Opposite vectors
    u = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
    dist = angular_distance(u, v)
    expected = np.pi
    assert abs(dist - expected) < 1e-6, f"Expected ~π, got {dist}"


def test_angular_distance_clip_above_one():
    """Test that angular_distance clips dot products > 1."""
    # Create vectors that would have dot product slightly > 1 due to float error
    u = np.array([1.0, 0.0], dtype=np.float32)
    v = np.array([1.0 + 1e-7, 0.0], dtype=np.float32)
    # Normalize to ensure they're on unit sphere
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    dist = angular_distance(u, v)
    # Should be valid (not NaN) and small
    assert not np.isnan(dist)
    assert dist >= 0
    assert dist <= np.pi


def test_angular_distance_clip_below_neg_one():
    """Test that angular_distance clips dot products < -1."""
    u = np.array([1.0, 0.0], dtype=np.float32)
    v = np.array([-1.0 - 1e-7, 0.0], dtype=np.float32)
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    dist = angular_distance(u, v)
    assert not np.isnan(dist)
    assert dist >= 0
    assert dist <= np.pi


def test_sgi_basic():
    """Test sgi function with dummy embedder."""
    embedder = DummyEmbedder()
    result = sgi("question", "context", "response", embedder)

    assert "theta_rq" in result
    assert "theta_rc" in result
    assert "sgi" in result

    assert isinstance(result["theta_rq"], float)
    assert isinstance(result["theta_rc"], float)
    assert isinstance(result["sgi"], float)

    # SGI should be positive
    assert result["sgi"] > 0
    # Theta values should be in [0, π]
    assert 0 <= result["theta_rq"] <= np.pi
    assert 0 <= result["theta_rc"] <= np.pi


def test_sgi_empty_strings():
    """Test that sgi raises on empty strings."""
    embedder = DummyEmbedder()
    with pytest.raises(ValueError, match="non-empty"):
        sgi("", "context", "response", embedder)
    with pytest.raises(ValueError, match="non-empty"):
        sgi("question", "", "response", embedder)
    with pytest.raises(ValueError, match="non-empty"):
        sgi("question", "context", "", embedder)


def test_sgi_expected_values():
    """Test sgi with known vectors to verify computation."""
    embedder = DummyEmbedder()

    # Use specific texts that will produce known vectors
    q = "question_a"
    c = "context_b"
    r = "response_c"

    result = sgi(q, c, r, embedder)

    # Verify structure
    assert "theta_rq" in result
    assert "theta_rc" in result
    assert "sgi" in result

    # Verify SGI formula: theta_rq / (theta_rc + eps)
    expected_sgi = result["theta_rq"] / (result["theta_rc"] + 1e-8)
    assert abs(result["sgi"] - expected_sgi) < 1e-10

