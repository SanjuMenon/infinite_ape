"Experiment orchestration for partial prompt bias probing."

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from bayesian_assistant import BayesianAssistant
from config import ExperimentConfig
from dnui import compute_dnui_discrete, compute_dnui_simple_l2
from llm_client import LLMClient


def _bias_attribution(
    *,
    dnui_prediction: float,
    dnui_target: float,
    eps: float = 1e-12,
) -> tuple[float, float, float]:
    """
    Decompose skew into:
      - llm_bias: dnui_prediction
      - loop_amplification: max(0, dnui_target - dnui_prediction)
      - loop_fraction_of_target: loop_amplification / max(eps, dnui_target)

    Where dnui_target can be dnui_feedback or dnui_assistant_final.
    """

    llm_bias = dnui_prediction
    loop_amplification = max(0.0, dnui_target - dnui_prediction)
    loop_fraction = loop_amplification / max(eps, dnui_target)
    return llm_bias, loop_amplification, loop_fraction


def _signed_loop_effect(
    *,
    dnui_prediction: float,
    dnui_target: float,
    eps: float = 1e-12,
) -> tuple[float, float]:
    """
    Signed loop effect:
      loop_effect = dnui_target - dnui_prediction
        > 0  => loop amplifies skew
        < 0  => loop damps skew

    Also returns a normalized ratio relative to the prediction skew:
      loop_effect_over_prediction = loop_effect / max(eps, dnui_prediction)
    """

    loop_effect = dnui_target - dnui_prediction
    loop_effect_over_prediction = loop_effect / max(eps, dnui_prediction)
    return loop_effect, loop_effect_over_prediction


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
    # Attribution metrics: "where does the skew come from?"
    llm_bias_dnui: float
    loop_amplification_dnui_feedback: float
    loop_fraction_of_feedback_dnui: float
    loop_amplification_dnui_assistant_final: float
    loop_fraction_of_assistant_final_dnui: float
    # Signed versions (negative means damping vs LLM skew; positive means amplification)
    loop_effect_dnui_feedback: float
    loop_effect_over_prediction_dnui_feedback: float
    loop_effect_dnui_assistant_final: float
    loop_effect_over_prediction_dnui_assistant_final: float


async def run_experiment(config: ExperimentConfig, llm_client: LLMClient) -> ExperimentResult:
    """Run a partial prompt bias experiment using the provided config and LLM client."""

    labels = config.choice_set.labels
    n = len(labels)
    if n == 0:
        raise ValueError("ChoiceSet must have at least one label.")

    total_trials = config.trials_per_choice * n
    assistant = BayesianAssistant(
        n_choices=n,
        increment=config.bayes_increment,
        initial_alpha=config.bayes_initial_alpha,
    )
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

    dnui_prediction = _dnui_or_fallback(prediction_probs)
    dnui_feedback = _dnui_or_fallback(feedback_probs)
    dnui_assistant_final = _dnui_or_fallback(assistant_probs)

    llm_bias_dnui, loop_amp_feedback, loop_frac_feedback = _bias_attribution(
        dnui_prediction=dnui_prediction,
        dnui_target=dnui_feedback,
    )
    _, loop_amp_final, loop_frac_final = _bias_attribution(
        dnui_prediction=dnui_prediction,
        dnui_target=dnui_assistant_final,
    )
    loop_eff_feedback, loop_eff_over_pred_feedback = _signed_loop_effect(
        dnui_prediction=dnui_prediction,
        dnui_target=dnui_feedback,
    )
    loop_eff_final, loop_eff_over_pred_final = _signed_loop_effect(
        dnui_prediction=dnui_prediction,
        dnui_target=dnui_assistant_final,
    )

    return ExperimentResult(
        config=config,
        pf_table=pf_rows,
        prediction_counts=prediction_counts,
        prediction_probs=prediction_probs,
        feedback_counts=feedback_counts,
        feedback_probs=feedback_probs,
        assistant_final_probs=assistant_probs,
        dnui_prediction=dnui_prediction,
        dnui_feedback=dnui_feedback,
        dnui_assistant_final=dnui_assistant_final,
        llm_bias_dnui=llm_bias_dnui,
        loop_amplification_dnui_feedback=loop_amp_feedback,
        loop_fraction_of_feedback_dnui=loop_frac_feedback,
        loop_amplification_dnui_assistant_final=loop_amp_final,
        loop_fraction_of_assistant_final_dnui=loop_frac_final,
        loop_effect_dnui_feedback=loop_eff_feedback,
        loop_effect_over_prediction_dnui_feedback=loop_eff_over_pred_feedback,
        loop_effect_dnui_assistant_final=loop_eff_final,
        loop_effect_over_prediction_dnui_assistant_final=loop_eff_over_pred_final,
    )

