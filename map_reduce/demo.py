from __future__ import annotations

from pathlib import Path

from declarative_fsm import demo as fsm_demo

from map_reduce.config import load_bundle_config, load_output_schema
from map_reduce.graph import build_map_reduce_graph
from map_reduce.llm_client import get_provider, is_llm_available
from map_reduce.schemas import Bundle


HERE = Path(__file__).resolve().parent


def main() -> None:
    # Run declarative_fsm to get bundles
    print("=" * 60)
    print("Step 1: Running Declarative FSM")
    print("=" * 60)
    most_current_data_list = fsm_demo.main()
    
    if not most_current_data_list:
        print("⚠ No bundles generated from declarative_fsm. Exiting.")
        return
    
    print("\n" + "=" * 60)
    print("Step 2: Running Map-Reduce Pipeline")
    print("=" * 60)
    
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
    
    # Convert most_current_data_list to Bundle objects
    bundle_config = load_bundle_config(HERE / "bundle_config.yaml")
    output_schema = load_output_schema(HERE / "output_schema.json")
    bundles = [Bundle.model_validate(item) for item in most_current_data_list]

    graph = build_map_reduce_graph()
    final_state = graph.invoke({
        "bundles": bundles,
        "bundle_config": bundle_config,
        "output_schema": output_schema
    })
    print(final_state["report"])


if __name__ == "__main__":
    main()

