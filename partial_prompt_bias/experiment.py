"Experiment orchestration for partial prompt bias probing."

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .bayesian_assistant import BayesianAssistant
from .config import ExperimentConfig
from .dnui import compute_dnui_discrete, compute_dnui_simple_l2
from .llm_client import LLMClient


@dataclass
class PFRow:
    """One row of the prediction-feedback table."""

    prediction_idx: int
    feedback_idx: int


@dataclass
class ExperimentResult:
    """Aggregated outcome of an experiment."""

    config: ExperimentConfig
    pf_table: List[PFRow]
    prediction_counts: List[int]
    prediction_probs: List[float]
    feedback_counts: List[int]
    feedback_probs: List[float]
    assistant_final_probs: List[float]
    dnui_prediction: float
    dnui_feedback: float
    dnui_assistant_final: float


async def run_experiment(config: ExperimentConfig, llm_client: LLMClient) -> ExperimentResult:
    """Run a partial prompt bias experiment using the provided config and LLM client."""

    labels = config.choice_set.labels
    n = len(labels)
    if n == 0:
        raise ValueError("ChoiceSet must have at least one label.")

    total_trials = config.trials_per_choice * n
    assistant = BayesianAssistant(n_choices=n, increment=config.bayes_increment)
    pf_rows: List[PFRow] = []
    prediction_counts = [0] * n
    feedback_counts = [0] * n

    for _ in range(total_trials):
        prediction_idx = await llm_client.choose_label(
            partial_prompt=config.partial_prompt,
            labels=labels,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            model=config.model,
        )
        prediction_counts[prediction_idx] += 1
        assistant.update(prediction_idx)
        feedback_idx = assistant.sample_feedback()
        feedback_counts[feedback_idx] += 1
        pf_rows.append(PFRow(prediction_idx=prediction_idx, feedback_idx=feedback_idx))

    prediction_probs = [count / total_trials for count in prediction_counts]
    feedback_probs = [count / total_trials for count in feedback_counts]
    assistant_probs = assistant.distribution

    def _dnui_or_fallback(dist: Sequence[float]) -> float:
        try:
            return compute_dnui_discrete(dist)
        except NotImplementedError:
            return compute_dnui_simple_l2(dist)

    return ExperimentResult(
        config=config,
        pf_table=pf_rows,
        prediction_counts=prediction_counts,
        prediction_probs=prediction_probs,
        feedback_counts=feedback_counts,
        feedback_probs=feedback_probs,
        assistant_final_probs=assistant_probs,
        dnui_prediction=_dnui_or_fallback(prediction_probs),
        dnui_feedback=_dnui_or_fallback(feedback_probs),
        dnui_assistant_final=_dnui_or_fallback(assistant_probs),
    )

