from __future__ import annotations

from pathlib import Path
import json

from map_reduce_arb.config import load_bundle_config, load_output_schema
from map_reduce_arb.graph import build_map_reduce_graph
from map_reduce_arb.llm_client import get_provider, is_llm_available


HERE = Path(__file__).resolve().parent


def main() -> None:
    print("=" * 60)
    print("Step 1: Running Enrich Transform")
    print("=" * 60)
    raw_path = str(HERE / ".." / "enrich_transform" / "raw.json")
    metadata = None
    
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
    
    bundle_config = load_bundle_config(HERE / "bundle_config.yaml")
    output_schema = load_output_schema(HERE / "output_schema.json")

    graph = build_map_reduce_graph()
    final_state = graph.invoke({
        "raw_path": raw_path,
        "bundle_config": bundle_config,
        "output_schema": output_schema,
        "metadata": metadata
    })
    
    # Print report as markdown (using renderer)
    from map_reduce_arb.graph import render_to_markdown
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

