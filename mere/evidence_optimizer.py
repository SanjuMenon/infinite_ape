"""
MERE: Minimal Evidence for Reproducibility Optimizer

This module implements MERE (Minimal Evidence for Reproducibility), a tool that determines
which evidence items help improve reproducibility of outcomes in LLM responses.

Given a list of evidence items, it tests all combinations (not permutations) of
evidence subsets and identifies the minimal set that ensures consistent, reliable
results while minimizing hallucination risk.
"""

import itertools
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import yaml
from pathlib import Path

# Import from credence module
from credence import (
    OpenAIBackend,
    OpenAIItem,
    OpenAIPlanner,
    ItemMetrics,
    AggregateReport,
    AnthropicBackend,
    OllamaBackend,
)


@dataclass
class EvidenceResult:
    """Results for a specific evidence combination"""
    evidence_indices: List[int]
    evidence_items: List[str]
    roh_bound: float
    decision_answer: bool
    delta_bar: float
    isr: float
    rationale: str
    num_evidence: int


@dataclass
class OptimizationResult:
    """Overall optimization results"""
    prompt: str
    total_evidence_count: int
    best_evidence: EvidenceResult
    all_results: List[EvidenceResult]
    evaluation_config: Dict


class EvidenceOptimizer:
    """
    MERE: Minimal Evidence for Reproducibility Optimizer.
    
    Tests all combinations of evidence to find the minimal set that
    maximizes outcome reproducibility while minimizing hallucination risk.
    """
    
    def __init__(
        self,
        backend=None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        n_samples: int = 5,
        m: int = 6,
        h_star: float = 0.05,
        skeleton_policy: str = "auto",
    ):
        """
        Initialize the MERE (Minimal Evidence for Reproducibility) Optimizer.
        
        Args:
            backend: Pre-configured backend (OpenAIBackend, AnthropicBackend, etc.)
                    If None, will try to auto-detect from environment
            model: Model name (used if backend is None)
            temperature: Temperature for LLM sampling
            n_samples: Number of samples to collect per evaluation
            m: Number of skeleton variants
            h_star: Target maximum hallucination rate
            skeleton_policy: "auto" | "evidence_erase" | "closed_book"
        """
        if backend is None:
            backend = self._create_backend(model)
        
        self.backend = backend
        self.temperature = temperature
        self.n_samples = n_samples
        self.m = m
        self.h_star = h_star
        self.skeleton_policy = skeleton_policy
        self.planner = OpenAIPlanner(
            backend=backend,
            temperature=temperature,
        )
    
    def _create_backend(self, model: str):
        """Try to create a backend from available options"""
        # Try OpenAI
        try:
            return OpenAIBackend(model=model)
        except Exception:
            pass
        
        # Try Anthropic
        try:
            return AnthropicBackend(model="claude-3-5-sonnet-latest")
        except Exception:
            pass
        
        # Try Ollama
        try:
            return OllamaBackend(model="llama3.1:8b-instruct")
        except Exception:
            pass
        
        raise RuntimeError(
            "No backend available. Please set up at least one:\n"
            "  - OPENAI_API_KEY for OpenAI\n"
            "  - ANTHROPIC_API_KEY for Anthropic\n"
            "  - Or have Ollama running locally"
        )
    
    def _format_prompt_with_evidence(
        self,
        base_prompt: str,
        evidence_items: List[str]
    ) -> str:
        """
        Format a prompt with evidence in the expected format.
        
        Args:
            base_prompt: The question/prompt
            evidence_items: List of evidence strings to include
            
        Returns:
            Formatted prompt with Evidence: section
        """
        if not evidence_items:
            return base_prompt
        
        evidence_section = "Evidence:\n" + "\n".join([f"- {item}" for item in evidence_items])
        
        # If prompt already has Evidence: section, replace it
        if "Evidence:" in base_prompt:
            lines = base_prompt.split("\n")
            new_lines = []
            skip_until_empty = False
            for line in lines:
                if line.strip().lower().startswith("evidence:"):
                    skip_until_empty = True
                    new_lines.append(evidence_section)
                    continue
                if skip_until_empty:
                    if not line.strip():  # Empty line
                        skip_until_empty = False
                        new_lines.append(line)
                    # Otherwise skip this line (it's part of old evidence)
                    continue
                new_lines.append(line)
            return "\n".join(new_lines)
        else:
            return f"{base_prompt}\n\n{evidence_section}"
    
    def _evaluate_evidence_combination(
        self,
        base_prompt: str,
        evidence_items: List[str],
        evidence_indices: List[int],
    ) -> EvidenceResult:
        """
        Evaluate a specific combination of evidence.
        
        Args:
            base_prompt: The base question/prompt
            evidence_items: List of evidence strings for this combination
            evidence_indices: Original indices of these evidence items
            
        Returns:
            EvidenceResult with evaluation metrics
        """
        # Format prompt with evidence
        prompt = self._format_prompt_with_evidence(base_prompt, evidence_items)
        
        # Create evaluation item
        item = OpenAIItem(
            prompt=prompt,
            n_samples=self.n_samples,
            m=self.m,
            skeleton_policy=self.skeleton_policy,
        )
        
        # Evaluate
        metric = self.planner.evaluate_item(
            idx=0,
            item=item,
            h_star=self.h_star,
        )
        
        return EvidenceResult(
            evidence_indices=evidence_indices,
            evidence_items=evidence_items,
            roh_bound=metric.roh_bound,
            decision_answer=metric.decision_answer,
            delta_bar=metric.delta_bar,
            isr=metric.isr,
            rationale=metric.rationale,
            num_evidence=len(evidence_items),
        )
    
    def optimize(
        self,
        prompt: str,
        evidence_list: List[str],
        min_evidence: int = 1,
        max_evidence: Optional[int] = None,
        optimize_for: str = "roh_bound",  # "roh_bound" or "decision_answer"
        prefer_minimal: bool = True,
    ) -> OptimizationResult:
        """
        Find the optimal evidence subset that minimizes hallucination.
        
        Args:
            prompt: The base question/prompt to evaluate
            evidence_list: List of all available evidence items
            min_evidence: Minimum number of evidence items to include
            max_evidence: Maximum number of evidence items to include (None = all)
            optimize_for: What to optimize for:
                - "roh_bound": Minimize hallucination risk bound
                - "decision_answer": Prefer combinations that result in ANSWER decision
            prefer_minimal: If True, prefer smaller evidence sets when metrics are equal
            
        Returns:
            OptimizationResult with best evidence subset and all results
        """
        if not evidence_list:
            raise ValueError("evidence_list cannot be empty")
        
        max_evidence = max_evidence or len(evidence_list)
        max_evidence = min(max_evidence, len(evidence_list))
        
        print(f"Testing all combinations of {len(evidence_list)} evidence items...")
        print(f"  Range: {min_evidence} to {max_evidence} items per combination")
        
        all_results: List[EvidenceResult] = []
        total_combinations = sum(
            len(list(itertools.combinations(evidence_list, r)))
            for r in range(min_evidence, max_evidence + 1)
        )
        print(f"  Total combinations to test: {total_combinations}")
        print()
        
        # Test all combinations
        for r in range(min_evidence, max_evidence + 1):
            for indices in itertools.combinations(range(len(evidence_list)), r):
                evidence_subset = [evidence_list[i] for i in indices]
                
                print(f"Testing combination {len(all_results) + 1}/{total_combinations}: "
                      f"{len(evidence_subset)} evidence items (indices: {list(indices)})")
                
                result = self._evaluate_evidence_combination(
                    base_prompt=prompt,
                    evidence_items=evidence_subset,
                    evidence_indices=list(indices),
                )
                all_results.append(result)
                
                print(f"  RoH bound: {result.roh_bound:.4f}, "
                      f"Decision: {'ANSWER' if result.decision_answer else 'ABSTAIN'}")
                print()
        
        # Find best result
        if optimize_for == "roh_bound":
            # Sort by roh_bound (lower is better), then by num_evidence if prefer_minimal
            if prefer_minimal:
                all_results.sort(key=lambda x: (x.roh_bound, x.num_evidence))
            else:
                all_results.sort(key=lambda x: x.roh_bound)
            best = all_results[0]
        elif optimize_for == "decision_answer":
            # Prefer ANSWER decisions, then by roh_bound
            answered = [r for r in all_results if r.decision_answer]
            if answered:
                if prefer_minimal:
                    answered.sort(key=lambda x: (x.roh_bound, x.num_evidence))
                else:
                    answered.sort(key=lambda x: x.roh_bound)
                best = answered[0]
            else:
                # No ANSWER decisions, use lowest roh_bound
                if prefer_minimal:
                    all_results.sort(key=lambda x: (x.roh_bound, x.num_evidence))
                else:
                    all_results.sort(key=lambda x: x.roh_bound)
                best = all_results[0]
        else:
            raise ValueError(f"Unknown optimize_for: {optimize_for}")
        
        print("=" * 70)
        print("OPTIMIZATION COMPLETE")
        print("=" * 70)
        print(f"Best evidence subset ({len(best.evidence_items)} items):")
        for i, item in enumerate(best.evidence_items, 1):
            print(f"  {i}. {item}")
        print(f"\nMetrics:")
        print(f"  RoH bound: {best.roh_bound:.4f}")
        print(f"  Decision: {'ANSWER' if best.decision_answer else 'ABSTAIN'}")
        print(f"  Information Budget (Δ̄): {best.delta_bar:.3f} nats")
        print(f"  ISR: {best.isr:.3f}")
        print("=" * 70)
        
        return OptimizationResult(
            prompt=prompt,
            total_evidence_count=len(evidence_list),
            best_evidence=best,
            all_results=all_results,
            evaluation_config={
                "n_samples": self.n_samples,
                "m": self.m,
                "h_star": self.h_star,
                "skeleton_policy": self.skeleton_policy,
                "temperature": self.temperature,
            },
        )
    
    def load_evidence_from_yaml(self, yaml_path: str) -> Tuple[str, List[str]]:
        """
        Load prompt and evidence list from YAML file.
        
        Expected YAML format:
        ```yaml
        prompt: "Your question here"
        evidence:
          - "Evidence item 1"
          - "Evidence item 2"
          - ...
        ```
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Tuple of (prompt, evidence_list)
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'prompt' not in data:
            raise ValueError("YAML file must contain 'prompt' field")
        if 'evidence' not in data:
            raise ValueError("YAML file must contain 'evidence' field")
        
        prompt = data['prompt']
        evidence = data['evidence']
        
        if not isinstance(evidence, list):
            raise ValueError("'evidence' must be a list")
        
        return prompt, evidence
    
    def save_results_to_yaml(
        self,
        result: OptimizationResult,
        yaml_path: str,
        include_all_results: bool = False,
    ):
        """
        Save optimization results to YAML file.
        
        Args:
            result: OptimizationResult to save
            yaml_path: Path to save YAML file
            include_all_results: If True, include all tested combinations
        """
        output = {
            "prompt": result.prompt,
            "optimization_summary": {
                "total_evidence_count": result.total_evidence_count,
                "best_evidence_count": result.best_evidence.num_evidence,
                "best_roh_bound": result.best_evidence.roh_bound,
                "best_decision": "ANSWER" if result.best_evidence.decision_answer else "ABSTAIN",
            },
            "best_evidence": {
                "indices": result.best_evidence.evidence_indices,
                "items": result.best_evidence.evidence_items,
                "metrics": {
                    "roh_bound": result.best_evidence.roh_bound,
                    "decision_answer": result.best_evidence.decision_answer,
                    "delta_bar": result.best_evidence.delta_bar,
                    "isr": result.best_evidence.isr,
                    "rationale": result.best_evidence.rationale,
                },
            },
            "evaluation_config": result.evaluation_config,
        }
        
        if include_all_results:
            output["all_results"] = [
                {
                    "indices": r.evidence_indices,
                    "items": r.evidence_items,
                    "num_evidence": r.num_evidence,
                    "roh_bound": r.roh_bound,
                    "decision_answer": r.decision_answer,
                }
                for r in result.all_results
            ]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(yaml_path) if os.path.dirname(yaml_path) else '.', exist_ok=True)
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"\nResults saved to: {yaml_path}")


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MERE (Minimal Evidence for Reproducibility): Optimize evidence subsets for reproducibility and hallucination reduction")
    parser.add_argument("--input", "-i", required=True, help="Input YAML file with prompt and evidence")
    parser.add_argument("--output", "-o", required=True, help="Output YAML file for results")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model name (if using OpenAI)")
    parser.add_argument("--min-evidence", type=int, default=1, help="Minimum evidence items per combination")
    parser.add_argument("--max-evidence", type=int, default=None, help="Maximum evidence items per combination")
    parser.add_argument("--optimize-for", choices=["roh_bound", "decision_answer"], default="roh_bound",
                       help="What to optimize for")
    parser.add_argument("--n-samples", type=int, default=5, help="Number of samples per evaluation")
    parser.add_argument("--h-star", type=float, default=0.05, help="Target hallucination rate")
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = EvidenceOptimizer(
        model=args.model,
        n_samples=args.n_samples,
        h_star=args.h_star,
    )
    
    # Load evidence
    prompt, evidence_list = optimizer.load_evidence_from_yaml(args.input)
    
    # Optimize
    result = optimizer.optimize(
        prompt=prompt,
        evidence_list=evidence_list,
        min_evidence=args.min_evidence,
        max_evidence=args.max_evidence,
        optimize_for=args.optimize_for,
    )
    
    # Save results
    optimizer.save_results_to_yaml(result, args.output, include_all_results=False)


if __name__ == "__main__":
    main()

