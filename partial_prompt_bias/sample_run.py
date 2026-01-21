"""
Sample programmatic run for the partial_prompt_bias package (cash-flow based lending).

Run from repo root:
  python -m partial_prompt_bias.sample_run

Requirements:
- Set OPENAI_API_KEY (or Azure env vars; see below).
- The example JSON file is expected at: mere/json_examples/cash_flow_lending_positive/data.json
"""

from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path

from dotenv import load_dotenv

# Support running either:
# - from repo root as a module:  python -m partial_prompt_bias.sample_run
# - from within this folder:     cd partial_prompt_bias && python sample_run.py
try:
    from .config import ChoiceSet, ExperimentConfig
    from .experiment import run_experiment
    from .llm_client import AzureOpenAIClient, OpenAIClient
except ImportError:  # pragma: no cover
    from config import ChoiceSet, ExperimentConfig
    from experiment import run_experiment
    from llm_client import AzureOpenAIClient, OpenAIClient


def _build_prompt_new(*, include_evidence: bool, evidence: dict | None = None) -> str:
    """
    NEW prompt version.

    When include_evidence=False this is a true "partial prompt" (pre-evidence).
    When include_evidence=True this becomes an end-to-end decision prompt.
    """

    base = (
        "You are a cash-flow based lending underwriter.\n"
        "Based ONLY on the Evidence JSON, pick exactly one risk tier label from the provided labels.\n"
        "Consider DSCR vs minimum policy, NSF count, and stability of net cash flow.\n"
    )
    if not include_evidence:
        return base
    if evidence is None:
        raise ValueError("evidence must be provided when include_evidence=True")
    evidence_json = json.dumps(evidence, indent=2)
    return base + "\nEvidence:\n" + evidence_json + "\n"


def _build_prompt_old(*, include_evidence: bool, evidence: dict | None = None) -> str:
    """
    OLD prompt version: same as NEW but with one sentence removed.

    We delete: "Consider DSCR vs minimum policy, NSF count, and stability of net cash flow."
    """

    base = (
        "You are a cash-flow based lending underwriter.\n"
        "Based ONLY on the Evidence JSON, pick exactly one risk tier label from the provided labels.\n"
    )
    if not include_evidence:
        return base
    if evidence is None:
        raise ValueError("evidence must be provided when include_evidence=True")
    evidence_json = json.dumps(evidence, indent=2)
    return base + "\nEvidence:\n" + evidence_json + "\n"

def _build_framing_only_partial_prompt() -> str:
    # This is the "partial prompt" in the intended sense: framing that comes
    # *before* any case-specific evidence is shown to the model.
    return (
        "You are a cash-flow based lending underwriter.\n"
        "You will later be given bank-transaction-derived cash-flow evidence for a small business.\n"
        "Before seeing any evidence, choose a risk tier label.\n"
        "Respond with exactly one label from the provided labels.\n"
    )


def _total_variation_distance(p: list[float], q: list[float]) -> float:
    """Compute Total Variation Distance between two probability distributions."""
    if len(p) != len(q):
        raise ValueError("Distributions must have same length")
    return 0.5 * sum(abs(pi - qi) for pi, qi in zip(p, q))


def _jensen_shannon_divergence(p: list[float], q: list[float]) -> float:
    """Compute Jensen-Shannon Divergence between two probability distributions."""
    if len(p) != len(q):
        raise ValueError("Distributions must have same length")
    
    def kl_divergence(p_dist: list[float], q_dist: list[float]) -> float:
        """KL divergence KL(P || Q)."""
        return sum(pi * math.log(pi / qi) if pi > 0 else 0.0 for pi, qi in zip(p_dist, q_dist))
    
    m = [(pi + qi) / 2.0 for pi, qi in zip(p, q)]
    return 0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m)


def _print_result_summary(title: str, labels: list[str], result) -> None:
    print("-" * 70)
    print(title)
    print("-" * 70)
    print("Key bias scores (0=uniform, 1=maximally skewed):")
    print(f"  dnui_prediction:      {result.dnui_prediction:.4f}")
    print(f"  dnui_feedback:        {result.dnui_feedback:.4f}")
    print(f"  dnui_assistant_final: {result.dnui_assistant_final:.4f}")
    print("Bias attribution (DNUI-based):")
    print(f"  llm_bias_dnui:                     {result.llm_bias_dnui:.4f}")
    print(f"  loop_amplification_dnui_feedback:  {result.loop_amplification_dnui_feedback:.4f}")
    print(f"  loop_fraction_of_feedback_dnui:    {result.loop_fraction_of_feedback_dnui:.2%}")
    print(f"  loop_amplification_dnui_final:     {result.loop_amplification_dnui_assistant_final:.4f}")
    print(f"  loop_fraction_of_final_dnui:       {result.loop_fraction_of_assistant_final_dnui:.2%}")
    print("Signed loop effect (DNUI_target - DNUI_prediction):")
    print("  Interpretation:")
    print("    > 0: loop amplifies bias")
    print("    < 0: loop damps bias")
    print("    ≈ 0: loop is basically neutral")
    print(f"  loop_effect_dnui_feedback:         {result.loop_effect_dnui_feedback:+.4f}")
    print(f"  loop_effect/prediction (feedback): {result.loop_effect_over_prediction_dnui_feedback:+.2%}")
    print(f"  loop_effect/prediction (final):    {result.loop_effect_over_prediction_dnui_assistant_final:+.2%}")
    print()
    print("  >>> KEY METRIC <<<")
    print(f"  loop_effect_dnui_assistant_final:  {result.loop_effect_dnui_assistant_final:+.4f}")
    print()
    tol = 1e-3
    
    if result.loop_effect_dnui_assistant_final > tol:
        verdict = "Loop AMPLIFIES bias (vs the LLM's raw picks)."
    elif result.loop_effect_dnui_assistant_final < -tol:
        verdict = "Loop DAMPS bias (vs the LLM's raw picks)."
    else:
        verdict = "Loop is approximately NEUTRAL (vs the LLM's raw picks)."
    print(f"Verdict: {verdict}\n")
    print("Prediction probabilities:")
    for label, prob, count in zip(labels, result.prediction_probs, result.prediction_counts):
        print(f"  {label:>10}: {prob:>7.3%}  (count={count})")
    print("")
    print("Assistant final probabilities:")
    for label, prob in zip(labels, result.assistant_final_probs):
        print(f"  {label:>10}: {prob:>7.3%}")
    print("")


async def main() -> int:
    load_dotenv()

    # Load cash-flow lending evidence from the repo's existing example JSON.
    repo_root = Path(__file__).resolve().parents[1]
    evidence_path = repo_root / "mere" / "json_examples" / "cash_flow_lending_positive" / "data.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    labels = ["LOW_RISK", "BORDERLINE", "HIGH_RISK", "DECLINE"]
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    base_kwargs = dict(
        choice_set=ChoiceSet(labels=labels),
        trials_per_choice=25,
        bayes_increment=0.05,  # Smaller increment to reduce skew accumulation
        bayes_initial_alpha=10.0,  # Stronger uniform prior (10x stronger than default)
        temperature=0.7,
        max_tokens=5,
        model=model,
    )

    provider = os.environ.get("PPB_PROVIDER", "openai").strip().lower()
    if provider == "azure":
        client = AzureOpenAIClient()
    else:
        client = OpenAIClient()

    # Run four conditions (OLD vs NEW) × (pre-evidence vs evidence).
    conditions = [
        (
            "Condition 1 — OLD (no evidence): pre-evidence partial-prompt bias",
            _build_prompt_old(include_evidence=False),
        ),
        (
            "Condition 2 — NEW (no evidence): pre-evidence partial-prompt bias",
            _build_prompt_new(include_evidence=False),
        ),
        (
            "Condition 3 — OLD + Evidence: end-to-end decision skew for this case",
            _build_prompt_old(include_evidence=True, evidence=evidence),
        ),
        (
            "Condition 4 — NEW + Evidence: end-to-end decision skew for this case",
            _build_prompt_new(include_evidence=True, evidence=evidence),
        ),
    ]

    results: list[tuple[str, object]] = []
    for title, prompt in conditions:
        cfg = ExperimentConfig(partial_prompt=prompt, **base_kwargs)
        res = await run_experiment(cfg, client)
        results.append((title, res))

    print("=" * 70)
    print("PARTIAL PROMPT BIAS — CASH-FLOW LENDING EXAMPLE")
    print("=" * 70)
    print(f"Labels: {labels}")
    print("")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print("")

    for title, res in results:
        _print_result_summary(title, labels, res)

    # Compute distribution shifts
    # Extract results by condition
    old_no_evidence = None
    new_no_evidence = None
    old_with_evidence = None
    new_with_evidence = None
    
    for title, res in results:
        if "Condition 1" in title:
            old_no_evidence = res
        elif "Condition 2" in title:
            new_no_evidence = res
        elif "Condition 3" in title:
            old_with_evidence = res
        elif "Condition 4" in title:
            new_with_evidence = res
    
    print("=" * 70)
    print("DISTRIBUTION SHIFT ANALYSIS")
    print("=" * 70)
    print()
    
    # OLD vs NEW comparisons (same evidence condition)
    if old_no_evidence and new_no_evidence:
        tvd_old_vs_new_no_ev = _total_variation_distance(
            old_no_evidence.prediction_probs, new_no_evidence.prediction_probs
        )
        js_old_vs_new_no_ev = _jensen_shannon_divergence(
            old_no_evidence.prediction_probs, new_no_evidence.prediction_probs
        )
        print("OLD vs NEW (no evidence):")
        print(f"  Total Variation Distance: {tvd_old_vs_new_no_ev:.4f} (0=identical, 1=completely different)")
        print(f"  Jensen-Shannon Divergence: {js_old_vs_new_no_ev:.4f} (0=identical, 1=completely different)")
        print()
    
    if old_with_evidence and new_with_evidence:
        tvd_old_vs_new_ev = _total_variation_distance(
            old_with_evidence.prediction_probs, new_with_evidence.prediction_probs
        )
        js_old_vs_new_ev = _jensen_shannon_divergence(
            old_with_evidence.prediction_probs, new_with_evidence.prediction_probs
        )
        print("OLD vs NEW (with evidence):")
        print(f"  Total Variation Distance: {tvd_old_vs_new_ev:.4f} (0=identical, 1=completely different)")
        print(f"  Jensen-Shannon Divergence: {js_old_vs_new_ev:.4f} (0=identical, 1=completely different)")
        print()
    
    # No-evidence vs evidence comparisons (same prompt)
    if old_no_evidence and old_with_evidence:
        tvd_old_no_ev_vs_ev = _total_variation_distance(
            old_no_evidence.prediction_probs, old_with_evidence.prediction_probs
        )
        js_old_no_ev_vs_ev = _jensen_shannon_divergence(
            old_no_evidence.prediction_probs, old_with_evidence.prediction_probs
        )
        print("OLD: No-evidence vs Evidence:")
        print(f"  Total Variation Distance: {tvd_old_no_ev_vs_ev:.4f} (0=identical, 1=completely different)")
        print(f"  Jensen-Shannon Divergence: {js_old_no_ev_vs_ev:.4f} (0=identical, 1=completely different)")
        print()
    
    if new_no_evidence and new_with_evidence:
        tvd_new_no_ev_vs_ev = _total_variation_distance(
            new_no_evidence.prediction_probs, new_with_evidence.prediction_probs
        )
        js_new_no_ev_vs_ev = _jensen_shannon_divergence(
            new_no_evidence.prediction_probs, new_with_evidence.prediction_probs
        )
        print("NEW: No-evidence vs Evidence:")
        print(f"  Total Variation Distance: {tvd_new_no_ev_vs_ev:.4f} (0=identical, 1=completely different)")
        print(f"  Jensen-Shannon Divergence: {js_new_no_ev_vs_ev:.4f} (0=identical, 1=completely different)")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

