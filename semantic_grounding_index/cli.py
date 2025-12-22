"""Command-line interface for SGI computation."""

import argparse
import json
import sys
from typing import Optional

from semantic_grounding_index.core import sgi, Embedder
from semantic_grounding_index.openai_embedder import AzureOpenAIEmbedder


def compute_sgi(
    q: str, c: str, r: str, embedder: Optional[Embedder] = None, deployment: Optional[str] = None
) -> dict[str, float]:
    """
    Compute SGI metric (wrapper for core.sgi with embedder setup).

    Args:
        q: Question string
        c: Context string
        r: Response string
        embedder: Optional embedder instance (if None, creates AzureOpenAIEmbedder)
        deployment: Optional deployment name for AzureOpenAIEmbedder

    Returns:
        Dictionary with 'theta_rq', 'theta_rc', 'sgi'
    """
    if embedder is None:
        if deployment:
            embedder = AzureOpenAIEmbedder(deployment=deployment)
        else:
            embedder = AzureOpenAIEmbedder()

    return sgi(q, c, r, embedder)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Compute SGI (Semantic Grounding Index) metric"
    )
    parser.add_argument(
        "command",
        choices=["compute"],
        help="Command to execute",
    )
    parser.add_argument(
        "--q",
        required=True,
        help="Question string",
    )
    parser.add_argument(
        "--c",
        required=True,
        help="Context string (retrieved evidence)",
    )
    parser.add_argument(
        "--r",
        required=True,
        help="Response string (model output)",
    )
    parser.add_argument(
        "--deployment",
        default=None,
        help=f"Azure OpenAI deployment name (default: {AzureOpenAIEmbedder.DEFAULT_DEPLOYMENT})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.q or not args.c or not args.r:
        print("Error: --q, --c, and --r must be non-empty", file=sys.stderr)
        return 2

    try:
        result = compute_sgi(args.q, args.c, args.r, deployment=args.deployment)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(
                f"SGI={result['sgi']:.6f}  "
                f"theta_rq={result['theta_rq']:.6f}  "
                f"theta_rc={result['theta_rc']:.6f}"
            )

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

