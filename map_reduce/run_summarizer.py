from __future__ import annotations

from pathlib import Path
import json

from declarative_fsm import data_handler as fsm_demo

from map_reduce.config import load_bundle_config, load_output_schema
from map_reduce.graph import build_map_reduce_graph
from map_reduce.llm_client import get_provider, is_llm_available
from map_reduce.schemas import Bundle


HERE = Path(__file__).resolve().parent


def main() -> None:
    # Run declarative_fsm to get bundles and metadata
    print("=" * 60)
    print("Step 1: Running Declarative FSM")
    print("=" * 60)
    fsm_result = fsm_demo.main()
    
    # Handle both old format (list) and new formats (dict)
    if isinstance(fsm_result, dict):
        # Contract A (declarative_fsm.demo): {"bundles": [...], "metadata": {...}}
        most_current_data_list = fsm_result.get("bundles")
        metadata = fsm_result.get("metadata")

        # Contract B (data_handler): {"most_current_data_list": [...], "meta": {...}}
        if most_current_data_list is None:
            most_current_data_list = fsm_result.get("most_current_data_list", [])
        if metadata is None:
            metadata = fsm_result.get("meta")
    else:
        # Backward compatibility: old format returns list directly
        most_current_data_list = fsm_result
        metadata = None
    
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
        "output_schema": output_schema,
        "metadata": metadata
    })
    
    # Print report as markdown (using renderer)
    from map_reduce.graph import render_to_markdown
    report = final_state["report"]

    # Persist report as JSON in Pydantic (aliased) form
    output_path = HERE / "pydantic_output.json"
    output_path.write_text(
        json.dumps(report.model_dump(by_alias=True), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✓ Saved Pydantic report JSON to: {output_path}")

    markdown_output = render_to_markdown(report)
    print(markdown_output)


if __name__ == "__main__":
    main()

