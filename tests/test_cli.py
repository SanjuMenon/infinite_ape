"""Tests for CLI functionality."""

import json
import sys
from unittest.mock import patch

import pytest

from semantic_grounding_index.cli import compute_sgi
from tests.test_core import DummyEmbedder


def test_compute_sgi_with_dummy_embedder():
    """Test compute_sgi function with DummyEmbedder."""
    embedder = DummyEmbedder()
    result = compute_sgi("q", "c", "r", embedder=embedder)

    assert "theta_rq" in result
    assert "theta_rc" in result
    assert "sgi" in result

    assert isinstance(result["theta_rq"], float)
    assert isinstance(result["theta_rc"], float)
    assert isinstance(result["sgi"], float)


def test_compute_sgi_json_output_keys():
    """Test that JSON output contains expected keys."""
    embedder = DummyEmbedder()
    result = compute_sgi("question", "context", "response", embedder=embedder)

    # Convert to JSON and back to verify serializability
    json_str = json.dumps(result)
    parsed = json.loads(json_str)

    assert "theta_rq" in parsed
    assert "theta_rc" in parsed
    assert "sgi" in parsed

    # All values should be floats (or numbers that can be floats)
    assert isinstance(parsed["theta_rq"], (int, float))
    assert isinstance(parsed["theta_rc"], (int, float))
    assert isinstance(parsed["sgi"], (int, float))


def test_compute_sgi_with_deployment_parameter():
    """Test compute_sgi with deployment parameter (should use DummyEmbedder when injected)."""
    embedder = DummyEmbedder()
    result = compute_sgi("q", "c", "r", embedder=embedder, deployment="test-deployment")

    # Deployment parameter should be ignored when embedder is provided
    assert "sgi" in result


@patch("sgi.cli.AzureOpenAIEmbedder")
def test_cli_main_success(mock_azure_openai_embedder_class):
    """Test CLI main() function with mocked Azure OpenAI."""
    # Create a mock embedder that returns deterministic results
    mock_embedder = DummyEmbedder()
    mock_azure_openai_embedder_class.return_value = mock_embedder

    # Mock sys.argv
    test_args = [
        "sgi",
        "compute",
        "--q",
        "What is AI?",
        "--c",
        "AI is artificial intelligence",
        "--r",
        "AI stands for artificial intelligence",
    ]

    with patch.object(sys, "argv", test_args):
        from semantic_grounding_index.cli import main

        exit_code = main()
        assert exit_code == 0


@patch("sgi.cli.AzureOpenAIEmbedder")
def test_cli_main_json_output(mock_azure_openai_embedder_class):
    """Test CLI main() with --json flag."""
    mock_embedder = DummyEmbedder()
    mock_azure_openai_embedder_class.return_value = mock_embedder

    test_args = [
        "sgi",
        "compute",
        "--q",
        "q",
        "--c",
        "c",
        "--r",
        "r",
        "--json",
    ]

    with patch.object(sys, "argv", test_args):
        from semantic_grounding_index.cli import main
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main()
        output = f.getvalue()

        assert exit_code == 0
        # Should be valid JSON
        parsed = json.loads(output)
        assert "sgi" in parsed
        assert "theta_rq" in parsed
        assert "theta_rc" in parsed


@patch("sgi.cli.AzureOpenAIEmbedder")
def test_cli_main_missing_args(mock_azure_openai_embedder_class):
    """Test CLI main() with missing arguments."""
    test_args = ["sgi", "compute", "--q", "q"]

    with patch.object(sys, "argv", test_args):
        from semantic_grounding_index.cli import main

        # Should exit with code 2 (argparse will handle this)
        # Actually, argparse will raise SystemExit, so we catch that
        with pytest.raises(SystemExit):
            main()

