from __future__ import annotations

import json
from pathlib import Path

from map_reduce.config import load_output_schema
from map_reduce.graph import build_map_reduce_graph
from map_reduce.llm_client import get_provider, is_llm_available
from map_reduce.schemas import Bundle


HERE = Path(__file__).resolve().parent


def main() -> None:
    # Check if LLM is available
    if is_llm_available():
        provider = get_provider()
        if provider == "azure":
            print("✓ Using Azure OpenAI for summarization")
        else:
            print("✓ Using OpenAI for summarization")
    else:
        print("⚠ LLM API credentials not found. Using deterministic fallback summarization.")
        print("  Set one of the following:")
        print("    - OPENAI_API_KEY (for OpenAI)")
        print("    - AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT (for Azure OpenAI)")
        print("  Or create a .env file with these variables.")
        print()
    
    output_schema = load_output_schema(HERE / "output_schema.json")
    bundles_raw = json.loads((HERE / "sample_bundles.json").read_text(encoding="utf-8"))
    bundles = [Bundle.model_validate(b) for b in bundles_raw]

    graph = build_map_reduce_graph()
    final_state = graph.invoke({"bundles": bundles, "output_schema": output_schema})
    print(final_state["report"])


if __name__ == "__main__":
    main()

