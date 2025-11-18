"""
Example script demonstrating how to use MERE (Minimal Evidence for Reproducibility).

This script loads evidence from a YAML file, tests all combinations,
and saves the optimal evidence subset to another YAML file.
"""

import os
import sys
from evidence_optimizer import EvidenceOptimizer


def main():
    print("=" * 70)
    print("MERE: Minimal Evidence for Reproducibility Example")
    print("=" * 70)
    print()
    
    # Configuration
    input_yaml = "evidence_input_example.yaml"
    output_yaml = "evidence_output_optimal.yaml"
    
    # Check if input file exists
    if not os.path.exists(input_yaml):
        print(f"Error: Input file '{input_yaml}' not found.")
        print("Please create a YAML file with 'prompt' and 'evidence' fields.")
        return
    
    # Create MERE optimizer
    print("Initializing MERE (Minimal Evidence for Reproducibility) Optimizer...")
    try:
        optimizer = EvidenceOptimizer(
            model="gpt-4o-mini",  # Change to your preferred model
            temperature=0.3,
            n_samples=5,  # Number of samples per evaluation (lower = faster, less accurate)
            m=6,          # Number of skeleton variants
            h_star=0.05,  # Target hallucination rate (5%)
            skeleton_policy="auto",  # Will use evidence_erase mode when evidence is present
        )
        print("✓ Optimizer initialized")
    except Exception as e:
        print(f"✗ Failed to initialize optimizer: {e}")
        return
    
    print()
    
    # Load evidence from YAML
    print(f"Loading evidence from '{input_yaml}'...")
    try:
        prompt, evidence_list = optimizer.load_evidence_from_yaml(input_yaml)
        print(f"✓ Loaded {len(evidence_list)} evidence items")
        print(f"  Prompt: {prompt}")
        print()
    except Exception as e:
        print(f"✗ Failed to load evidence: {e}")
        return
    
    # Run optimization
    print("Starting optimization...")
    print("  (This will test all combinations of evidence subsets)")
    print()
    
    try:
        result = optimizer.optimize(
            prompt=prompt,
            evidence_list=evidence_list,
            min_evidence=1,      # Test combinations with at least 1 evidence item
            max_evidence=None,    # Test all sizes (None = test all)
            optimize_for="roh_bound",  # Minimize hallucination risk bound
            prefer_minimal=True,  # Prefer smaller evidence sets when metrics are equal
        )
    except KeyboardInterrupt:
        print("\n✗ Optimization interrupted by user")
        return
    except Exception as e:
        print(f"✗ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Save results
    print(f"\nSaving results to '{output_yaml}'...")
    try:
        optimizer.save_results_to_yaml(
            result,
            output_yaml,
            include_all_results=False,  # Set to True to include all tested combinations
        )
        print("✓ Results saved")
    except Exception as e:
        print(f"✗ Failed to save results: {e}")
        return
    
    # Display summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total evidence items tested: {result.total_evidence_count}")
    print(f"Total combinations tested: {len(result.all_results)}")
    print(f"\nOptimal evidence subset ({result.best_evidence.num_evidence} items):")
    for i, item in enumerate(result.best_evidence.evidence_items, 1):
        print(f"  {i}. {item}")
    print(f"\nBest metrics:")
    print(f"  Hallucination Risk Bound (RoH): {result.best_evidence.roh_bound:.4f}")
    print(f"  Decision: {'✓ ANSWER' if result.best_evidence.decision_answer else '✗ ABSTAIN'}")
    print(f"  Information Budget (Δ̄): {result.best_evidence.delta_bar:.3f} nats")
    print(f"  ISR: {result.best_evidence.isr:.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()

