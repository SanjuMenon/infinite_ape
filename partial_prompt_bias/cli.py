"Command-line interface for running partial prompt bias experiments."

from __future__ import annotations

import argparse
import asyncio
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .config import ChoiceSet, ExperimentConfig
from .experiment import run_experiment
from .llm_client import AzureOpenAIClient, OpenAIClient


def _read_prompt_from_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _labels_from_args(labels: Sequence[str] | None) -> List[str]:
    if not labels:
        raise ValueError("At least one label must be provided.")
    return [label.strip() for label in labels if label.strip()]


def _config_from_dict(payload: Dict[str, Any]) -> ExperimentConfig:
    required = {"partial_prompt", "labels"}
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing configuration keys: {', '.join(missing)}")
    labels = payload.pop("labels")
    choice_set = ChoiceSet(labels=labels)
    return ExperimentConfig(choice_set=choice_set, **payload)


def build_config_from_args(args: argparse.Namespace, provider: str) -> ExperimentConfig:
    if args.config:
        cfg_data = json.loads(Path(args.config).read_text(encoding="utf-8"))
        return _config_from_dict(cfg_data)

    if args.prompt_file:
        partial_prompt = _read_prompt_from_file(Path(args.prompt_file))
    elif args.partial_prompt:
        partial_prompt = args.partial_prompt
    else:
        raise ValueError("Provide --partial-prompt or --prompt-file when not using --config.")

    labels = _labels_from_args(args.labels)
    model_value = args.model
    if provider == "azure" and args.azure_deployment:
        model_value = args.azure_deployment
    return ExperimentConfig(
        partial_prompt=partial_prompt,
        choice_set=ChoiceSet(labels=labels),
        trials_per_choice=args.trials_per_choice,
        bayes_increment=args.bayes_increment,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        model=model_value,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a partial prompt latent-bias probe over an LLM."
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "azure"],
        default="openai",
        help="LLM provider to use (default: openai).",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON config file containing ExperimentConfig fields.",
    )
    parser.add_argument(
        "--partial-prompt",
        "-p",
        type=str,
        help="Partial prompt string (ignored if --prompt-file or --config is used).",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        help="Path to a text file containing the partial prompt.",
    )
    parser.add_argument(
        "--labels",
        "-l",
        nargs="+",
        help="Space-separated list of labels (ignored if --config is used).",
    )
    parser.add_argument(
        "--trials-per-choice",
        type=int,
        default=50,
        help="Number of trials per label (default: 50).",
    )
    parser.add_argument(
        "--bayes-increment",
        type=float,
        default=0.1,
        help="Increment δ applied to the Bayesian assistant (default: 0.1).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="LLM sampling temperature (default: 0.7).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=16,
        help="Max tokens allocated to the label response (default: 16).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4.1-mini",
        help="LLM model identifier (default: gpt-4.1-mini).",
    )
    parser.add_argument(
        "--openai-api-key",
        type=str,
        help="Explicit OpenAI API key (falls back to OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--azure-endpoint",
        type=str,
        help="Azure OpenAI endpoint, e.g. https://example.openai.azure.com/.",
    )
    parser.add_argument(
        "--azure-api-version",
        type=str,
        help="Azure OpenAI API version, e.g. 2024-05-01-preview.",
    )
    parser.add_argument(
        "--azure-deployment",
        type=str,
        help="Azure OpenAI deployment name to target.",
    )
    parser.add_argument(
        "--azure-api-key",
        type=str,
        help="Azure OpenAI API key (falls back to AZURE_OPENAI_KEY or OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for Bayesian assistant feedback sampling.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Optional path for writing the JSON result (stdout by default).",
    )
    parser.add_argument(
        "--include-table",
        action="store_true",
        help="Include the full prediction-feedback table in the output JSON.",
    )
    return parser


async def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    provider = args.provider

    if args.seed is not None:
        random.seed(args.seed)

    config = build_config_from_args(args, provider)
    if provider == "azure":
        deployment = args.azure_deployment or config.model
        client = AzureOpenAIClient(
            endpoint=args.azure_endpoint,
            api_version=args.azure_api_version,
            deployment=deployment,
            api_key=args.azure_api_key,
        )
    else:
        client = OpenAIClient(api_key=args.openai_api_key)
    result = await run_experiment(config, client)

    output: Dict[str, Any] = {
        "labels": config.choice_set.labels,
        "prediction_counts": result.prediction_counts,
        "prediction_probs": result.prediction_probs,
        "feedback_counts": result.feedback_counts,
        "feedback_probs": result.feedback_probs,
        "assistant_final_probs": result.assistant_final_probs,
        "dnui_prediction": result.dnui_prediction,
        "dnui_feedback": result.dnui_feedback,
        "dnui_assistant_final": result.dnui_assistant_final,
    }
    if args.include_table:
        output["pf_table"] = [
            {"prediction_idx": row.prediction_idx, "feedback_idx": row.feedback_idx}
            for row in result.pf_table
        ]

    json_payload = json.dumps(output, indent=2)
    if args.output:
        Path(args.output).write_text(json_payload + "\n", encoding="utf-8")
    else:
        print(json_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

