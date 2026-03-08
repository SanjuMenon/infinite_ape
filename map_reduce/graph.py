from __future__ import annotations

from collections import defaultdict
import operator
from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from .agents import summarize_freeform, summarize_table
from .evaluator import evaluate_report, evaluate_summary
from .schemas import Bundle, BundleConfig, BundleTypeConfig, OutputSchema, OutputSectionSchema
from .splitter import split_bundle


class MapReduceState(TypedDict, total=False):
    bundles: List[Bundle]
    bundle_config: BundleConfig
    output_schema: OutputSchema

    # populated during execution
    subtasks: List[Bundle]
    partials: Annotated[List[Dict[str, str]], operator.add]  # [{"field_name": str, "text": str}]
    report: str
    evaluation_scores: Dict[str, Any]  # {"summary_scores": Dict[str, Dict[str, float]], "report_scores": Dict[str, float]}


def _flatten_sections(sections: List[OutputSectionSchema]) -> List[OutputSectionSchema]:
    out: List[OutputSectionSchema] = []
    for s in sections:
        out.append(s)
        if s.subsections:
            out.extend(_flatten_sections(s.subsections))
    return out


def _aggregate_report(
    bundle_config: BundleConfig, 
    output_schema: OutputSchema, 
    partials: List[Dict[str, str]]
) -> str:
    """Aggregate partial results into final report using bundle_config for ordering and section titles."""
    by_bundle: Dict[str, List[str]] = defaultdict(list)
    for p in partials:
        by_bundle[p["field_name"]].append(p["text"].strip())

    lines: List[str] = []
    if output_schema.title:
        lines.append(output_schema.title)
        lines.append("")

    # Create a mapping from field_name to bundle config (for ordering and section titles)
    config_by_field_name: Dict[str, BundleTypeConfig] = {}
    for bundle_type in bundle_config.bundle_order:
        config_by_field_name[bundle_type.field_name] = bundle_type

    # Group bundles by section_title and track order
    sections: Dict[str, List[tuple[int, str]]] = defaultdict(list)  # section_title -> [(order, field_name), ...]
    seen_field_names: set[str] = set()

    # Process bundles according to bundle_config order
    for bundle_type in sorted(bundle_config.bundle_order, key=lambda x: x.order):
        field_name = bundle_type.field_name
        if field_name in by_bundle:
            seen_field_names.add(field_name)
            sections[bundle_type.section_title].append((bundle_type.order, field_name))

    # Process sections in order of first bundle in each section
    section_order: List[tuple[int, str]] = []  # [(min_order, section_title), ...]
    for section_title, bundle_list in sections.items():
        min_order = min(order for order, _ in bundle_list)
        section_order.append((min_order, section_title))
    
    section_order.sort(key=lambda x: x[0])

    # Generate report sections
    for _, section_title in section_order:
        lines.append(f"## {section_title}")
        lines.append("")

        # Get bundles for this section, sorted by order
        bundle_list = sections[section_title]
        bundle_list.sort(key=lambda x: x[0])  # Sort by order

        for _, field_name in bundle_list:
            lines.append(f"### {field_name}")
            lines.append("")
            lines.append("\n\n".join(by_bundle[field_name]))
            lines.append("")

    # Anything not in bundle_config goes to "Other"
    extras = sorted(set(by_bundle.keys()) - seen_field_names)
    if extras:
        lines.append("## Other")
        lines.append("")
        for field_name in extras:
            lines.append(f"### {field_name}")
            lines.append("")
            lines.append("\n\n".join(by_bundle[field_name]))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _split_node(state: MapReduceState) -> Dict[str, List[Bundle]]:
    subtasks: List[Bundle] = []
    for b in state.get("bundles", []):
        subtasks.extend(split_bundle(b))
    return {"subtasks": subtasks}


def _dispatch_node(state: MapReduceState) -> List[Send]:
    sends: List[Send] = []
    for b in state.get("subtasks", []):
        sends.append(Send("summarize_one", {"bundle": b}))
    return sends


class SummarizeOneState(TypedDict):
    bundle: Bundle


def _summarize_one_node(state: SummarizeOneState) -> Dict[str, List[Dict[str, str]]]:
    bundle = state["bundle"]
    if bundle.format == "table":
        text = summarize_table(bundle)
    else:
        text = summarize_freeform(bundle)
    return {"partials": [{"field_name": bundle.field_name, "text": text}]}


def _reduce_node(state: MapReduceState) -> Dict[str, str]:
    bundle_config = state.get("bundle_config", BundleConfig())
    output_schema = state.get("output_schema", OutputSchema())
    partials = state.get("partials", [])
    return {"report": _aggregate_report(bundle_config=bundle_config, output_schema=output_schema, partials=partials)}


def _should_evaluate(state: MapReduceState) -> str:
    """Check if evaluation is needed based on bundles."""
    bundles = state.get("bundles", [])
    for bundle in bundles:
        if bundle.eval_type is not None and bundle.metrics is not None:
            return "evaluate"
    return "END"


def _evaluate_node(state: MapReduceState) -> Dict[str, Dict[str, Any]]:
    """Evaluate individual summaries and overall report sequentially.
    
    Returns:
        Dictionary with "evaluation_scores" containing:
        - "summary_scores": Dict mapping field_name to scores
        - "report_scores": Dict mapping metric to score
    """
    bundles = state.get("bundles", [])
    partials = state.get("partials", [])
    report = state.get("report", "")
    
    # Create mapping from field_name to bundle and summary text
    bundle_by_field: Dict[str, Bundle] = {}
    summary_by_field: Dict[str, str] = {}
    
    for bundle in bundles:
        bundle_by_field[bundle.field_name] = bundle
    
    for partial in partials:
        field_name = partial["field_name"]
        summary_by_field[field_name] = partial["text"]
    
    # Step 1: Evaluate individual summaries (for bundles that need it)
    summary_scores: Dict[str, Dict[str, float]] = {}
    for bundle in bundles:
        if bundle.eval_type is not None and bundle.metrics is not None:
            field_name = bundle.field_name
            if field_name in summary_by_field:
                summary_text = summary_by_field[field_name]
                scores = evaluate_summary(bundle, summary_text)
                summary_scores[field_name] = scores
    
    # Step 2: Evaluate overall report
    report_scores: Dict[str, float] = {}
    if bundles and any(b.eval_type is not None and b.metrics is not None for b in bundles):
        report_scores = evaluate_report(report, bundles)
    
    return {
        "evaluation_scores": {
            "summary_scores": summary_scores,
            "report_scores": report_scores
        }
    }


def build_map_reduce_graph():
    """Build a LangGraph map-reduce pipeline.

    Input state must include:
    - bundles: List[Bundle] (or dicts coercible into Bundle upstream)
    - bundle_config: BundleConfig (for ordering and section titles)
    - output_schema: OutputSchema (for report title)
    """

    g: StateGraph = StateGraph(MapReduceState)

    g.add_node("split", _split_node)
    g.add_node("summarize_one", _summarize_one_node)
    g.add_node("reduce", _reduce_node)
    g.add_node("evaluate", _evaluate_node)

    g.set_entry_point("split")
    g.add_conditional_edges("split", _dispatch_node, ["summarize_one"])
    g.add_edge("summarize_one", "reduce")
    # After reduce, conditionally evaluate if needed
    g.add_conditional_edges("reduce", _should_evaluate, {"evaluate": "evaluate", "END": END})
    g.add_edge("evaluate", END)

    return g.compile()

