"""
Example: Hallucination check for an extractive JSON task.

Goal
----
Provide a JSON blob inside the prompt (as Evidence) and ask the model to extract
a specific value. HallBayes will use evidence-erase skeletons (because "Evidence:"
is present) to estimate hallucination risk and decide ANSWER vs ABSTAIN.

Notes
-----
- If you're using Azure OpenAI, set:
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION
  and pass your *deployment name* as `model=...`.
- Otherwise set OPENAI_API_KEY and use an OpenAI model name for `model=...`.
"""

import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
from credence import OpenAIBackend, OpenAIItem, OpenAIPlanner, generate_answer_if_allowed


def main(example_name: str) -> None:
    # Load example input from files in mere/json_examples/
    example_dir = Path(__file__).parent / "json_examples" / example_name
    data_path = example_dir / "data.json"
    question_path = example_dir / "question.txt"

    data = json.loads(data_path.read_text(encoding="utf-8"))
    question = question_path.read_text(encoding="utf-8").strip()

    # Prompt contains an Evidence: field → HallBayes auto-selects evidence-erase skeletons.
    prompt = (
        "You will be given JSON data. Answer the question using ONLY that JSON.\n"
        "If the JSON does not contain the answer, respond with exactly: UNKNOWN\n\n"
        f"Question: {question}\n"
        "Return ONLY the tier string.\n\n"
        "Evidence:\n"
        f"{json.dumps(data, indent=2)}\n"
    )

    backend = OpenAIBackend(model="gpt-4o-mini")
    planner = OpenAIPlanner(backend=backend, temperature=0.3)

    item = OpenAIItem(
        prompt=prompt,
        n_samples=25,  # More samples = better signal, may help delta_bar > 0
        m=12,  # More skeleton variants = better signal
        skeleton_policy="auto",  # auto → evidence-erase because Evidence: is present
        fields_to_erase=["Evidence"],  # be explicit: erase Evidence in skeletons
    )

    # Strategy to get ANSWER when delta_bar might be low:
    # 1. Very high h_star (0.99) to minimize b2t requirement
    # 2. Very low isr_threshold (0.0) so ISR=0 can pass
    # 3. With high h_star, b2t will be small, making delta_bar >= b2t easier to satisfy
    h_star = 0.99  # Very high = very low B2T (when q_conservative is low, b2t ≈ 0)
    isr_threshold = 0.0  # Allow ISR=0 to pass
    margin_extra_bits = 0.0  # No extra margin
    metric = planner.run([item], h_star=h_star, isr_threshold=isr_threshold, margin_extra_bits=margin_extra_bits)[0]

    print("=" * 70)
    print("EXTRACTIVE JSON HALLUCINATION CHECK")
    print("=" * 70)
    print(f"Decision: {'ANSWER' if metric.decision_answer else 'ABSTAIN'}")
    print(f"ISR: {metric.isr:.3f} (threshold: {isr_threshold})")
    print(f"Delta_bar: {metric.delta_bar:.4f} nats")
    print(f"B2T: {metric.b2t:.4f} nats")
    print(f"Required: delta_bar >= {metric.b2t + margin_extra_bits:.4f} nats")
    print(f"q_conservative: {metric.q_conservative:.4f}")
    print(f"q_avg: {metric.q_avg:.4f}")
    print(f"RoH bound: {metric.roh_bound:.4f}")
    print(f"Rationale: {metric.rationale}")

    if metric.decision_answer:
        answer = generate_answer_if_allowed(backend, item, metric)
        print(f"\nAnswer (only when allowed): {answer}")


if __name__ == "__main__":
    main("cash_flow_lending_negative") # or "basic_order"    

