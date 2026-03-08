from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from .llm_client import get_deployment_name, get_openai_client, get_provider
from .schemas import Bundle


def evaluate_summary(bundle: Bundle, summary_text: str) -> Dict[str, float]:
    """Evaluate a summary against the specified metrics using LLM.
    
    Args:
        bundle: The bundle containing eval_type and metrics
        summary_text: The generated summary text to evaluate
        
    Returns:
        Dictionary mapping metric names to scores (0-10)
        
    Raises:
        RuntimeError: If LLM is not available or evaluation fails
    """
    if not bundle.metrics:
        return {}
    
    client = get_openai_client()
    if client is None:
        raise RuntimeError(
            "LLM is required for evaluation. "
            "Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT."
        )
    
    # Build metrics list for prompt - use exact metric names as keys
    metrics_list = "\n".join([f"- {metric}" for metric in bundle.metrics])
    # Create a mapping of normalized names to original names for matching
    metric_keys = [f'"{metric}"' for metric in bundle.metrics]
    example_dict = "{" + ", ".join([f'"{m}": 8' for m in bundle.metrics[:3]]) + "}"
    
    prompt = f"""Evaluate the following summary text and score it on a scale of 0-10 for each metric.

Metrics to evaluate:
{metrics_list}

Summary Text:
{summary_text}

Provide scores as a JSON object. Use the EXACT metric names as keys (including the full phrase).
Example format: {example_dict}

IMPORTANT: Use the exact metric names provided above as the JSON keys. Return only the JSON object, no additional text."""

    # Use deployment name for Azure, model name for OpenAI
    provider = get_provider()
    if provider == "azure":
        model_or_deployment = get_deployment_name() or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
    else:
        model_or_deployment = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    response = client.chat.completions.create(
        model=model_or_deployment,
        messages=[
            {"role": "system", "content": "You are an evaluation assistant that scores text quality. Always return valid JSON with scores from 0-10."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # Low temperature for consistent scoring
        max_tokens=200
    )
    
    result_text = response.choices[0].message.content
    if not result_text:
        raise RuntimeError("LLM returned empty response for evaluation")
    
    # Parse JSON response
    try:
        # Extract JSON if wrapped in markdown code blocks
        result_text = result_text.strip()
        if result_text.startswith("```"):
            # Remove markdown code block markers
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1]) if len(lines) > 2 else result_text
        
        scores = json.loads(result_text)
        
        # Validate scores are in 0-10 range and match metrics
        validated_scores: Dict[str, float] = {}
        for metric in bundle.metrics:
            score = None
            
            # Try exact match first
            if metric in scores:
                score = scores[metric]
            else:
                # Try case-insensitive exact match
                metric_lower = metric.lower()
                for key, value in scores.items():
                    if key.lower() == metric_lower:
                        score = value
                        break
                
                # Try partial matching (metric phrase contains key or vice versa)
                if score is None:
                    for key, value in scores.items():
                        key_lower = key.lower()
                        # Check if key words appear in metric or metric words appear in key
                        metric_words = set(metric_lower.split())
                        key_words = set(key_lower.split())
                        # If there's significant overlap (at least 2 words), consider it a match
                        if len(metric_words & key_words) >= 2 or metric_lower in key_lower or key_lower in metric_lower:
                            score = value
                            break
                
                # Last resort: try to extract meaningful words from metric
                if score is None:
                    # Extract key words like "readable", "complete", "accurate"
                    metric_keywords = {
                        "readable": ["readable", "readability"],
                        "complete": ["complete", "completeness", "comprehensive"],
                        "accurate": ["accurate", "accuracy", "correct"]
                    }
                    for keyword, variants in metric_keywords.items():
                        if any(v in metric_lower for v in variants):
                            for key, value in scores.items():
                                if keyword in key.lower() or any(v in key.lower() for v in variants):
                                    score = value
                                    break
                            if score is not None:
                                break
            
            # Default to 0.0 if no match found
            if score is None:
                score = 0.0
            else:
                score = float(score)
            
            # Clamp to 0-10 range
            validated_scores[metric] = max(0.0, min(10.0, score))
        
        return validated_scores
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise RuntimeError(f"Failed to parse evaluation scores: {e}. Response was: {result_text[:200]}") from e


def evaluate_report(report: str, bundles: List[Bundle]) -> Dict[str, float]:
    """Evaluate the overall report against metrics from bundles.
    
    Args:
        report: The final aggregated report text
        bundles: List of bundles (at least one should have metrics)
        
    Returns:
        Dictionary mapping metric names to scores (0-10)
        
    Raises:
        RuntimeError: If LLM is not available or evaluation fails
    """
    # Get metrics from first bundle that has them
    metrics = None
    for bundle in bundles:
        if bundle.metrics:
            metrics = bundle.metrics
            break
    
    if not metrics:
        return {}
    
    client = get_openai_client()
    if client is None:
        raise RuntimeError(
            "LLM is required for evaluation. "
            "Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT."
        )
    
    # Build metrics list for prompt - use exact metric names as keys
    metrics_list = "\n".join([f"- {metric}" for metric in metrics])
    example_dict = "{" + ", ".join([f'"{m}": 8' for m in metrics[:3]]) + "}"
    
    prompt = f"""Evaluate the following report and score it on a scale of 0-10 for each metric.

Metrics to evaluate:
{metrics_list}

Report:
{report}

Provide scores as a JSON object. Use the EXACT metric names as keys (including the full phrase).
Example format: {example_dict}

IMPORTANT: Use the exact metric names provided above as the JSON keys. Return only the JSON object, no additional text."""

    # Use deployment name for Azure, model name for OpenAI
    provider = get_provider()
    if provider == "azure":
        model_or_deployment = get_deployment_name() or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
    else:
        model_or_deployment = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    response = client.chat.completions.create(
        model=model_or_deployment,
        messages=[
            {"role": "system", "content": "You are an evaluation assistant that scores text quality. Always return valid JSON with scores from 0-10."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # Low temperature for consistent scoring
        max_tokens=200
    )
    
    result_text = response.choices[0].message.content
    if not result_text:
        raise RuntimeError("LLM returned empty response for evaluation")
    
    # Parse JSON response
    try:
        # Extract JSON if wrapped in markdown code blocks
        result_text = result_text.strip()
        if result_text.startswith("```"):
            # Remove markdown code block markers
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1]) if len(lines) > 2 else result_text
        
        scores = json.loads(result_text)
        
        # Validate scores are in 0-10 range and match metrics
        validated_scores: Dict[str, float] = {}
        for metric in metrics:
            score = None
            
            # Try exact match first
            if metric in scores:
                score = scores[metric]
            else:
                # Try case-insensitive exact match
                metric_lower = metric.lower()
                for key, value in scores.items():
                    if key.lower() == metric_lower:
                        score = value
                        break
                
                # Try partial matching (metric phrase contains key or vice versa)
                if score is None:
                    for key, value in scores.items():
                        key_lower = key.lower()
                        # Check if key words appear in metric or metric words appear in key
                        metric_words = set(metric_lower.split())
                        key_words = set(key_lower.split())
                        # If there's significant overlap (at least 2 words), consider it a match
                        if len(metric_words & key_words) >= 2 or metric_lower in key_lower or key_lower in metric_lower:
                            score = value
                            break
                
                # Last resort: try to extract meaningful words from metric
                if score is None:
                    # Extract key words like "readable", "complete", "accurate"
                    metric_keywords = {
                        "readable": ["readable", "readability"],
                        "complete": ["complete", "completeness", "comprehensive"],
                        "accurate": ["accurate", "accuracy", "correct"]
                    }
                    for keyword, variants in metric_keywords.items():
                        if any(v in metric_lower for v in variants):
                            for key, value in scores.items():
                                if keyword in key.lower() or any(v in key.lower() for v in variants):
                                    score = value
                                    break
                            if score is not None:
                                break
            
            # Default to 0.0 if no match found
            if score is None:
                score = 0.0
            else:
                score = float(score)
            
            # Clamp to 0-10 range
            validated_scores[metric] = max(0.0, min(10.0, score))
        
        return validated_scores
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise RuntimeError(f"Failed to parse evaluation scores: {e}. Response was: {result_text[:200]}") from e
