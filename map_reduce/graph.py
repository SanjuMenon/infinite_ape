from __future__ import annotations

from collections import defaultdict
import operator
from typing import Annotated, Dict, List, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from .agents import summarize_freeform, summarize_table
from .schemas import Bundle, OutputSchema, OutputSectionSchema
from .splitter import split_bundle


class MapReduceState(TypedDict, total=False):
    bundles: List[Bundle]
    output_schema: OutputSchema

    # populated during execution
    subtasks: List[Bundle]
    partials: Annotated[List[Dict[str, str]], operator.add]  # [{"bundle_name": str, "text": str}]
    report: str


def _flatten_sections(sections: List[OutputSectionSchema]) -> List[OutputSectionSchema]:
    out: List[OutputSectionSchema] = []
    for s in sections:
        out.append(s)
        if s.subsections:
            out.extend(_flatten_sections(s.subsections))
    return out


def _aggregate_report(output_schema: OutputSchema, partials: List[Dict[str, str]]) -> str:
    by_bundle: Dict[str, List[str]] = defaultdict(list)
    for p in partials:
        by_bundle[p["bundle_name"]].append(p["text"].strip())

    lines: List[str] = []
    if output_schema.title:
        lines.append(output_schema.title)
        lines.append("")

    seen_bundle_names: set[str] = set()

    for section in _flatten_sections(output_schema.sections):
        lines.append(f"## {section.name}")
        lines.append("")

        for bundle_name in section.bundle_names:
            if bundle_name not in by_bundle:
                continue
            seen_bundle_names.add(bundle_name)
            lines.append(f"### {bundle_name}")
            lines.append("")
            lines.append("\n\n".join(by_bundle[bundle_name]))
            lines.append("")

    # Anything not explicitly ordered goes to "Other"
    extras = sorted(set(by_bundle.keys()) - seen_bundle_names)
    if extras:
        lines.append("## Other")
        lines.append("")
        for bundle_name in extras:
            lines.append(f"### {bundle_name}")
            lines.append("")
            lines.append("\n\n".join(by_bundle[bundle_name]))
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
    if bundle.value == "table":
        text = summarize_table(bundle)
    else:
        text = summarize_freeform(bundle)
    return {"partials": [{"bundle_name": bundle.bundle_name, "text": text}]}


def _reduce_node(state: MapReduceState) -> Dict[str, str]:
    output_schema = state.get("output_schema", OutputSchema())
    partials = state.get("partials", [])
    return {"report": _aggregate_report(output_schema=output_schema, partials=partials)}


def build_map_reduce_graph():
    """Build a LangGraph map-reduce pipeline.

    Input state must include:
    - bundles: List[Bundle] (or dicts coercible into Bundle upstream)
    - output_schema: OutputSchema
    """

    g: StateGraph = StateGraph(MapReduceState)

    g.add_node("split", _split_node)
    g.add_node("summarize_one", _summarize_one_node)
    g.add_node("reduce", _reduce_node)

    g.set_entry_point("split")
    g.add_conditional_edges("split", _dispatch_node, ["summarize_one"])
    g.add_edge("summarize_one", "reduce")
    g.add_edge("reduce", END)

    return g.compile()

