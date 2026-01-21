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
        n_samples=7,
        m=6,
        skeleton_policy="auto",  # auto → evidence-erase because Evidence: is present
        fields_to_erase=["Evidence"],  # be explicit: erase Evidence in skeletons
    )

    h_star = 0.30
    metric = planner.run([item], h_star=h_star)[0]

    print("=" * 70)
    print("EXTRACTIVE JSON HALLUCINATION CHECK")
    print("=" * 70)
    print(f"Decision: {'ANSWER' if metric.decision_answer else 'ABSTAIN'}")
    print(f"ISR: {metric.isr:.3f}")
    print(f"Delta_bar: {metric.delta_bar:.4f} nats")
    print(f"RoH bound: {metric.roh_bound:.4f}")
    print(f"Rationale: {metric.rationale}")

    if metric.decision_answer:
        answer = generate_answer_if_allowed(backend, item, metric)
        print(f"\nAnswer (only when allowed): {answer}")


if __name__ == "__main__":
    main("cash_flow_lending_negative") # or "basic_order"    

