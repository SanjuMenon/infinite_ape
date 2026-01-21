"""
Sample Hallucination Check using HallBayes

This script demonstrates how to use the HallBayes toolkit to check for
hallucinations in LLM responses using the EDFL (Expected Disagreement from First Look)
framework.

Based on: https://github.com/leochlon/hallbayes
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Import from credence module
from credence import (
    OpenAIBackend,
    OpenAIItem,
    OpenAIPlanner,
    make_sla_certificate,
    save_sla_certificate_json,
    generate_answer_if_allowed,
    AnthropicBackend,
    OllamaBackend,
    # HuggingFaceBackend,  # Uncomment if you want to use HuggingFace
    # OpenRouterBackend,   # Uncomment if you want to use OpenRouter
)


def run_hallucination_check_example():
    """
    Example: Run hallucination check on a sample prompt
    """
    print("=" * 70)
    print("HallBayes Hallucination Check Example")
    print("=" * 70)
    print()
    
    # ============================================================================
    # Step 1: Choose your backend
    # ============================================================================
    # Option 1: OpenAI (requires OPENAI_API_KEY environment variable)
    try:
        backend = OpenAIBackend(model="gpt-4o-mini")
        print("✓ Using OpenAI backend (gpt-4o-mini)")
    except Exception as e:
        print(f"✗ OpenAI backend failed: {e}")
        print("  Trying Anthropic backend instead...")
        try:
            backend = AnthropicBackend(model="claude-3-5-sonnet-latest")
            print("✓ Using Anthropic backend (claude-3-5-sonnet-latest)")
        except Exception as e2:
            print(f"✗ Anthropic backend failed: {e2}")
            print("  Trying Ollama backend instead...")
            try:
                backend = OllamaBackend(model="llama3.1:8b-instruct")
                print("✓ Using Ollama backend (llama3.1:8b-instruct)")
            except Exception as e3:
                print(f"✗ All backends failed. Please set up at least one:")
                print("  - OPENAI_API_KEY for OpenAI")
                print("  - ANTHROPIC_API_KEY for Anthropic")
                print("  - Or have Ollama running locally")
                return
    
    print()
    
    # ============================================================================
    # Step 2: Create evaluation items
    # ============================================================================
    # Example prompts to test
    items: List[OpenAIItem] = [
        OpenAIItem(
            prompt="Who won the 2019 Nobel Prize in Physics?",
            n_samples=7,  # Number of samples to collect
            m=6,          # Number of skeleton variants
            skeleton_policy="closed_book"  # Use closed-book mode (no evidence required)
        ),
        OpenAIItem(
            prompt="What is the capital of France?",
            n_samples=5,
            m=6,
            skeleton_policy="closed_book"
        ),
        OpenAIItem(
            prompt="Explain quantum entanglement in simple terms.",
            n_samples=5,
            m=6,
            skeleton_policy="closed_book"
        ),
    ]
    
    print(f"Created {len(items)} evaluation items:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item.prompt[:60]}...")
    print()
    
    # ============================================================================
    # Step 3: Configure and run the planner
    # ============================================================================
    print("Running hallucination check...")
    print("  (This may take a minute as it collects multiple samples)")
    print()
    
    planner = OpenAIPlanner(
        backend=backend,
        temperature=0.3,  # Lower temperature for more consistent results
    )
    
    # Run the evaluation
    # h_star: target maximum hallucination rate (5% = 0.05)
    h_star = 0.05
    metrics = planner.run(items, h_star=h_star)
    
    print("✓ Evaluation complete!")
    print()
    
    # ============================================================================
    # Step 4: Display results
    # ============================================================================
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    
    for i, (item, metric) in enumerate(zip(items, metrics), 1):
        print(f"Item {i}: {item.prompt}")
        print(f"  Decision: {'✓ ANSWER' if metric.decision_answer else '✗ ABSTAIN'}")
        print(f"  Information Budget (Δ̄): {metric.delta_bar:.3f} nats")
        print(f"  Conservative Prior (q_lo): {metric.q_conservative:.4f}")
        print(f"  Average Prior (q̄): {metric.q_avg:.4f}")
        print(f"  Bits-to-Trust (B2T): {metric.b2t:.3f} bits")
        print(f"  Information Sufficiency Ratio (ISR): {metric.isr:.3f}")
        print(f"  Hallucination Risk Bound (RoH): {metric.roh_bound:.4f}")
        print(f"  Rationale: {metric.rationale}")
        print()
    
    # ============================================================================
    # Step 5: Generate aggregate report
    # ============================================================================
    report = planner.aggregate(items, metrics, h_star=h_star)
    
    print("=" * 70)
    print("AGGREGATE REPORT")
    print("=" * 70)
    print(f"Total Items: {report.n_items}")
    print(f"Answer Rate: {report.answer_rate:.1%}")
    print(f"Abstention Rate: {report.abstention_rate:.1%}")
    print(f"Worst-case RoH Bound: {report.worst_item_roh_bound:.4f}")
    print(f"Median RoH Bound: {report.median_item_roh_bound:.4f}")
    print(f"Target h*: {h_star:.1%}")
    print()
    
    # ============================================================================
    # Step 6: Generate SLA certificate (optional)
    # ============================================================================
    model_name = getattr(backend, 'model', 'Unknown Model')
    cert = make_sla_certificate(report, model_name=model_name)
    
    cert_path = "sla_certificate.json"
    save_sla_certificate_json(cert, cert_path)
    print(f"✓ SLA certificate saved to: {cert_path}")
    print()
    
    # ============================================================================
    # Step 7: Generate answers only if allowed (optional)
    # ============================================================================
    print("=" * 70)
    print("ANSWERS (only for items where decision was ANSWER)")
    print("=" * 70)
    print()
    
    for i, (item, metric) in enumerate(zip(items, metrics), 1):
        if metric.decision_answer:
            print(f"Item {i}: {item.prompt}")
            try:
                answer = generate_answer_if_allowed(backend, item, metric)
                if answer:
                    print(f"  Answer: {answer}")
                else:
                    print("  (Answer generation skipped)")
            except Exception as e:
                print(f"  Error generating answer: {e}")
            print()
    
    print("=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    run_hallucination_check_example()

