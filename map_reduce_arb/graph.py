from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import json
import operator
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from enrich_transform.cli import run as enrich_run
from enrich_transform.io.json_io import read_json

from .agents import summarize_passthrough, summarize_with_prompt
from .partner_shared_info import format_partner_shared_information
from .evaluator import DEFAULT_EVAL_METRICS, evaluate_report_text, evaluate_summary_text
from .llm_client import is_llm_available, get_provider
from .markdown_utils import prettify_section_table_md
from .prompts import PROMPT_NONE, get_prompt_for_section
from .report_schemas import (
    CreditSummaryGenAIResponse,
    SummarySection,
    SummarySubSection,
    OverallEvaluationReport,
    SummaryMetaData,
)
from .schemas import Bundle, BundleConfig, BundleTypeConfig, OutputSchema, OutputSectionSchema
from .splitter import split_bundle

# Order matters: partner block is first (generic client information).
_BUNDLE_SECTION_NAMES = (
    "partner_shared_information",
    "collateral",
    "business_model",
    "real_estate",
)


class MapReduceState(TypedDict, total=False):
    # inputs for enrich_transform
    raw_obj: Optional[Dict[str, Any]]
    raw_path: Optional[str]

    # enrich outputs
    enriched: Dict[str, Any]
    downstream: Dict[str, Any]

    # generated bundles
    bundles: List[Bundle]
    bundle_config: BundleConfig
    output_schema: OutputSchema
    metadata: Optional[Dict[str, Any]]  # Metadata from sample_data.json (_metadata section)

    # populated during execution
    subtasks: List[Bundle]
    partials: Annotated[List[Dict[str, str]], operator.add]  # [{"field_name": str, "text": str}]
    report: CreditSummaryGenAIResponse  # Changed from str to Pydantic model
    evaluation_scores: Dict[str, Any]


def _flatten_sections(sections: List[OutputSectionSchema]) -> List[OutputSectionSchema]:
    out: List[OutputSectionSchema] = []
    for s in sections:
        out.append(s)
        if s.subsections:
            out.extend(_flatten_sections(s.subsections))
    return out


def _infer_content_format(text: str) -> str:
    """Infer report content format from generated text."""
    t = (text or "")
    # Common heuristic: treat as markdown if it contains a markdown table anywhere.
    # This catches sections that start with headings (e.g. "## Real Estate") and then include tables.
    if "\n|" in t or t.lstrip().startswith("|"):
        return "MD"
    # If the content is valid JSON (object/array), mark it as JSON.
    s = t.lstrip()
    if s.startswith("{") or s.startswith("["):
        try:
            json.loads(s)
            return "JSON"
        except Exception:
            pass
    return "TEXT"


def _aggregate_report_pydantic(
    bundle_config: BundleConfig,
    output_schema: OutputSchema,
    partials: List[Dict[str, str]],
    bundles: List[Bundle],
    metadata: Optional[Dict[str, Any]],
    evaluation_scores: Optional[Dict[str, Any]] = None,
) -> CreditSummaryGenAIResponse:
    """Aggregate partial results into CreditSummaryGenAIResponse Pydantic model.
    
    Option B: Group bundles by section_title → one SummarySection per group,
    bundles become SummarySubSections.
    """
    # Build mapping from field_name to summary text
    by_bundle: Dict[str, List[str]] = defaultdict(list)
    bundle_by_field: Dict[str, Bundle] = {}
    for bundle in bundles:
        bundle_by_field[bundle.field_name] = bundle
    
    for p in partials:
        by_bundle[p["field_name"]].append(p["text"].strip())
    
    # Evaluation is not used in this simplified (prompt/payload) pipeline.
    summary_scores: Dict[str, Dict[str, float]] = {}
    report_scores: Dict[str, float] = {}
    
    # Create mapping from field_name to bundle config
    config_by_field_name: Dict[str, BundleTypeConfig] = {}
    for bundle_type in bundle_config.bundle_order:
        config_by_field_name[bundle_type.field_name] = bundle_type
    
    # Group bundles by section_title (Option B)
    sections: Dict[str, List[tuple[int, str]]] = defaultdict(list)  # section_title -> [(order, field_name), ...]
    seen_field_names: set[str] = set()
    
    # Process bundles according to bundle_config order
    for bundle_type in sorted(bundle_config.bundle_order, key=lambda x: x.order):
        field_name = bundle_type.field_name
        if field_name in by_bundle:
            seen_field_names.add(field_name)
            sections[bundle_type.section_title].append((bundle_type.order, field_name))
    
    # Process sections in order of first bundle in each section
    section_order: List[tuple[int, str]] = []
    for section_title, bundle_list in sections.items():
        min_order = min(order for order, _ in bundle_list)
        section_order.append((min_order, section_title))
    section_order.sort(key=lambda x: x[0])
    
    # Build SummarySections
    summary_sections: List[SummarySection] = []
    for _, section_title in section_order:
        bundle_list = sections[section_title]
        bundle_list.sort(key=lambda x: x[0])  # Sort by order
        
        # Build SummarySubSections for each bundle in this section
        sub_sections: List[SummarySubSection] = []
        for _, field_name in bundle_list:
            bundle = bundle_by_field.get(field_name)
            if not bundle:
                continue
            
            # Use display_name if available, otherwise use field_name
            display_name = field_name
            if field_name in config_by_field_name:
                bundle_config_item = config_by_field_name[field_name]
                if bundle_config_item.display_name:
                    display_name = bundle_config_item.display_name
            
            # Combine summary text
            content = "\n\n".join(by_bundle[field_name])

            content_format = _infer_content_format(content)

            sub_sections.append(SummarySubSection(
                identifier=field_name,
                heading=display_name,
                content_format=content_format,
                content=content
            ))
        
        # Create SummarySection for this group
        # Use first bundle's order to determine section identifier
        if bundle_list:
            first_field_name = bundle_list[0][1]
            # Create identifier from section_title (sanitize)
            section_identifier = section_title.lower().replace(" ", "-")
            
            summary_sections.append(SummarySection(
                identifier=section_identifier,
                heading=section_title,
                sub_heading=None,
                content="",  # Section-level content is empty, content is in subsections
                content_format="TEXT",
                summary_sub_sections=sub_sections
            ))
    
    # Handle bundles not in bundle_config (go to "Other" section)
    extras = sorted(set(by_bundle.keys()) - seen_field_names)
    if extras:
        extra_sub_sections: List[SummarySubSection] = []
        for field_name in extras:
            bundle = bundle_by_field.get(field_name)
            if not bundle:
                continue
            
            display_name = field_name
            if field_name in config_by_field_name:
                bundle_config_item = config_by_field_name[field_name]
                if bundle_config_item.display_name:
                    display_name = bundle_config_item.display_name
            
            content = "\n\n".join(by_bundle[field_name])

            content_format = _infer_content_format(content)

            extra_sub_sections.append(SummarySubSection(
                identifier=field_name,
                heading=display_name,
                content_format=content_format,
                content=content
            ))
        
        if extra_sub_sections:
            summary_sections.append(SummarySection(
                identifier="other",
                heading="Other",
                sub_heading=None,
                content="",
                content_format="TEXT",
                summary_sub_sections=extra_sub_sections
            ))
    
    # Build overall evaluation report
    overall_eval_lines: List[str] = []
    if summary_scores:
        overall_eval_lines.append("Summary Scores (combined by field_name):")
        for field_name in sorted(summary_scores.keys()):
            scores = summary_scores[field_name]
            if not scores:
                continue
            overall = sum(scores.values()) / len(scores)
            metric_scores = ", ".join([f"{metric}: {score:.1f}/10" for metric, score in scores.items()])
            overall_eval_lines.append(f"- {field_name}: {overall:.1f}/10 ({metric_scores})")
        overall_eval_lines.append("")

    if report_scores:
        overall_report = sum(report_scores.values()) / len(report_scores)
        metric_scores = ", ".join([f"{metric}: {score:.1f}/10" for metric, score in report_scores.items()])
        overall_eval_lines.append(f"Overall Report Score: {overall_report:.1f}/10 ({metric_scores})")

    if not overall_eval_lines:
        overall_eval_lines.append("No evaluation scores available.")

    overall_eval_content = "\n".join(overall_eval_lines).strip()
    
    # Build debug log (always set to AI Gateway for downstream consumers)
    debug_log = "LLM Provider: AI Gateway"
    
    # Extract metadata with defaults
    metadata_dict = metadata or {}
    request_id = metadata_dict.get("requestId", "REQ-UNKNOWN")
    language = metadata_dict.get("language", "en")
    generated_by = metadata_dict.get("generatedBy", "map_reduce")
    generated_at = metadata_dict.get("generatedAt")
    if not generated_at:
        generated_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Build the response
    return CreditSummaryGenAIResponse(
        schema_="https://json-schema.org/draft/2020-12/schema",
        id_="https://ubs.com/fso/cfbu/creditsummary/data-collection/domain/gen-ai/CreditSummaryGenAIResponse.json",
        request_id=request_id,
        language=language,
        generated_by=generated_by,
        generated_at=generated_at,
        summary_sections=summary_sections,
        summary_meta_data=SummaryMetaData(
            overall_evaluation_report=OverallEvaluationReport(
                content=overall_eval_content,
                content_format="TEXT"
            ),
            debug_log=debug_log
        )
    )


def _aggregate_report(
    bundle_config: BundleConfig, 
    output_schema: OutputSchema, 
    partials: List[Dict[str, str]],
    evaluation_scores: Dict[str, Any] = None
) -> str:
    """Aggregate partial results into final report using bundle_config for ordering and section titles.
    
    If evaluation_scores is provided, includes scores in the report.
    """
    by_bundle: Dict[str, List[str]] = defaultdict(list)
    for p in partials:
        by_bundle[p["field_name"]].append(p["text"].strip())
    
    # Extract evaluation scores if available
    summary_scores: Dict[str, Dict[str, float]] = {}
    report_scores: Dict[str, float] = {}
    if evaluation_scores:
        summary_scores = evaluation_scores.get("summary_scores", {})
        report_scores = evaluation_scores.get("report_scores", {})

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
            # Use display_name if available, otherwise use field_name
            display_name = field_name
            if field_name in config_by_field_name:
                bundle_config_item = config_by_field_name[field_name]
                if bundle_config_item.display_name:
                    display_name = bundle_config_item.display_name
            
            lines.append(f"### {display_name}")
            lines.append("")
            lines.append("\n\n".join(by_bundle[field_name]))
            
            # Add evaluation scores if available
            if field_name in summary_scores:
                scores = summary_scores[field_name]
                if scores:
                    lines.append("")
                    # Calculate overall score (average)
                    overall = sum(scores.values()) / len(scores)
                    lines.append(f"**Evaluation Score: {overall:.1f}/10**")
                    metric_scores = []
                    for metric, score in scores.items():
                        metric_scores.append(f"{metric}: {score:.1f}/10")
                    lines.append(f"*Detailed: {', '.join(metric_scores)}*")
            
            lines.append("")

    # Anything not in bundle_config goes to "Other"
    extras = sorted(set(by_bundle.keys()) - seen_field_names)
    if extras:
        lines.append("## Other")
        lines.append("")
        for field_name in extras:
            # Use display_name if available, otherwise use field_name
            display_name = field_name
            if field_name in config_by_field_name:
                bundle_config_item = config_by_field_name[field_name]
                if bundle_config_item.display_name:
                    display_name = bundle_config_item.display_name
            
            lines.append(f"### {display_name}")
            lines.append("")
            lines.append("\n\n".join(by_bundle[field_name]))
            
            # Add evaluation scores if available
            if field_name in summary_scores:
                scores = summary_scores[field_name]
                if scores:
                    lines.append("")
                    overall = sum(scores.values()) / len(scores)
                    lines.append(f"**Evaluation Score: {overall:.1f}/10**")
                    metric_scores = []
                    for metric, score in scores.items():
                        metric_scores.append(f"{metric}: {score:.1f}/10")
                    lines.append(f"*Detailed: {', '.join(metric_scores)}*")
            
            lines.append("")
    
    # Add overall report evaluation scores at the end
    if report_scores:
        lines.append("")
        lines.append("## Overall Report Evaluation")
        lines.append("")
        overall_report = sum(report_scores.values()) / len(report_scores)
        lines.append(f"**Overall Report Score: {overall_report:.1f}/10**")
        metric_scores = []
        for metric, score in report_scores.items():
            metric_scores.append(f"{metric}: {score:.1f}/10")
        lines.append(f"*Detailed: {', '.join(metric_scores)}*")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_to_markdown(response: CreditSummaryGenAIResponse) -> str:
    """Render CreditSummaryGenAIResponse to markdown string.
    
    This provides backward compatibility for code that expects markdown output.
    """
    lines: List[str] = []
    
    # Add title (from first section or default)
    if response.summary_sections:
        lines.append(f"# {response.summary_sections[0].heading}")
    else:
        lines.append("# Report")
    lines.append("")
    
    # Render each section
    for section in response.summary_sections:
        lines.append(f"## {section.heading}")
        if section.sub_heading:
            lines.append(f"### {section.sub_heading}")
        lines.append("")
        
        # Render section content if present
        if section.content:
            lines.append(section.content)
            lines.append("")
        
        # Render subsections
        for sub_section in section.summary_sub_sections:
            lines.append(f"### {sub_section.heading}")
            lines.append("")
            lines.append(sub_section.content)
            lines.append("")
    
    # Add overall evaluation report
    if response.summary_meta_data.overall_evaluation_report.content:
        lines.append("## Overall Report Evaluation")
        lines.append("")
        lines.append(response.summary_meta_data.overall_evaluation_report.content)
        lines.append("")
    
    return "\n".join(lines).rstrip() + "\n"


def _split_node(state: MapReduceState) -> Dict[str, List[Bundle]]:
    subtasks: List[Bundle] = []
    for b in state.get("bundles", []):
        subtasks.extend(split_bundle(b))
    return {"subtasks": subtasks}


def _enrich_node(state: MapReduceState) -> Dict[str, Any]:
    """Run enrich_transform and stash its result in state."""
    # Allow callers/tests to bypass enrich/build_bundles by providing bundles directly.
    if state.get("bundles"):
        return {}
    raw_obj = state.get("raw_obj")
    raw_path = state.get("raw_path")
    if raw_obj is None:
        path = Path(raw_path) if raw_path else Path(__file__).resolve().parent.parent / "enrich_transform" / "raw.json"
        raw_obj = read_json(path)
    result = enrich_run(raw_obj=raw_obj, raw_path=None, no_downstream=False)
    return {
        "enriched": result.get("enriched", {}),
        "downstream": result.get("downstream", {}),
        "raw_obj": raw_obj,
    }


def _build_bundles_node(state: MapReduceState) -> Dict[str, List[Bundle]]:
    """Create bundles for the sections we care about, attaching prompts + payloads."""
    # Allow callers/tests to bypass enrich/build_bundles by providing bundles directly.
    if state.get("bundles"):
        return {"bundles": state["bundles"]}
    enriched = state.get("enriched", {}) or {}
    downstream = state.get("downstream", {}) or {}

    bundles: List[Bundle] = []
    for section_name in _BUNDLE_SECTION_NAMES:
        if section_name == "partner_shared_information":
            raw_for_partner: Dict[str, Any] = dict(state.get("raw_obj") or {})
            meta = state.get("metadata")
            if isinstance(meta, dict) and meta:
                merged = dict(raw_for_partner.get("metadata") or {})
                merged.update(meta)
                raw_for_partner["metadata"] = merged
            payload = format_partner_shared_information(raw_for_partner)
            bundles.append(Bundle(field_name=section_name, prompt=PROMPT_NONE, payload=payload))
            continue

        prompt = get_prompt_for_section(section_name)
        artifacts = downstream.get(section_name, {}) if isinstance(downstream, dict) else {}
        if not isinstance(artifacts, dict):
            artifacts = {}

        if prompt == PROMPT_NONE:
            # passthrough: payload format depends on section type
            # - collateral: JSON passthrough (use enriched JSON, not downstream json_str)
            # - real_estate: JSON passthrough (use enriched JSON)
            # - default: markdown passthrough
            if section_name == "collateral":
                collateral_obj = enriched.get("collateral", {})
                payload = json.dumps(collateral_obj, ensure_ascii=False, indent=2, sort_keys=True)
                bundles.append(Bundle(field_name=section_name, prompt=PROMPT_NONE, payload=payload))
            elif section_name == "real_estate":
                real_estate_obj = enriched.get("real_estate", [])
                payload = json.dumps(real_estate_obj, ensure_ascii=False, indent=2, sort_keys=True)
                bundles.append(Bundle(field_name=section_name, prompt=PROMPT_NONE, payload=payload))
            else:
                table_md = artifacts.get("table_md", "") or ""
                table_md = prettify_section_table_md(section_name, str(table_md))
                bundles.append(Bundle(field_name=section_name, prompt=PROMPT_NONE, payload=table_md))
        else:
            # LLM path: use downstream json_str
            json_str = artifacts.get("json_str", "") or ""
            bundles.append(Bundle(field_name=section_name, prompt=prompt, payload=str(json_str)))

    return {"bundles": bundles}


def _dispatch_node(state: MapReduceState) -> List[Send]:
    sends: List[Send] = []
    for b in state.get("subtasks", []):
        sends.append(Send("summarize_one", {"bundle": b}))
    return sends


class SummarizeOneState(TypedDict):
    bundle: Bundle


def _summarize_one_node(state: SummarizeOneState) -> Dict[str, List[Dict[str, str]]]:
    bundle = state["bundle"]
    if bundle.prompt == PROMPT_NONE:
        text = summarize_passthrough(bundle)
    else:
        text = summarize_with_prompt(bundle)
    return {"partials": [{"field_name": bundle.field_name, "text": text}]}


def _reduce_node(state: MapReduceState) -> Dict[str, CreditSummaryGenAIResponse]:
    bundle_config = state.get("bundle_config", BundleConfig())
    output_schema = state.get("output_schema", OutputSchema())
    partials = state.get("partials", [])
    bundles = state.get("bundles", [])
    metadata = state.get("metadata")
    # Initial report without evaluation scores
    return {"report": _aggregate_report_pydantic(
        bundle_config=bundle_config,
        output_schema=output_schema,
        partials=partials,
        bundles=bundles,
        metadata=metadata
    )}


def _evaluate_node(state: MapReduceState) -> Dict[str, Any]:
    """Evaluate per-section (LLM summaries only) and the overall report.

    This is optional and runs only when LLM is available.
    """
    if not is_llm_available():
        return {}

    bundles = state.get("bundles", [])
    partials = state.get("partials", [])
    report = state.get("report")

    # Per-section: only evaluate sections that used the LLM path
    summary_scores: Dict[str, Dict[str, float]] = {}
    by_field: Dict[str, List[str]] = defaultdict(list)
    for p in partials:
        by_field[p["field_name"]].append(p["text"])

    for b in bundles:
        if b.prompt != PROMPT_NONE:
            combined = "\n\n".join([t.strip() for t in by_field.get(b.field_name, []) if t and t.strip()]).strip()
            if combined:
                summary_scores[b.field_name] = evaluate_summary_text(combined, DEFAULT_EVAL_METRICS)

    # Overall report eval
    report_scores: Dict[str, float] = {}
    if report:
        report_md = render_to_markdown(report)
        report_scores = evaluate_report_text(report_md, DEFAULT_EVAL_METRICS)

    evaluation_scores = {"summary_scores": summary_scores, "report_scores": report_scores}

    # Update report's overall evaluation content (keep structure; just replace content)
    if report:
        lines: List[str] = []
        if summary_scores:
            lines.append("Summary Scores (0-10):")
            for field_name in sorted(summary_scores.keys()):
                scores = summary_scores[field_name]
                if not scores:
                    continue
                overall = sum(scores.values()) / len(scores)
                metric_scores = ", ".join([f"{m}: {s:.1f}/10" for m, s in scores.items()])
                lines.append(f"- {field_name}: {overall:.1f}/10 ({metric_scores})")
            lines.append("")
        if report_scores:
            overall_report = sum(report_scores.values()) / len(report_scores)
            metric_scores = ", ".join([f"{m}: {s:.1f}/10" for m, s in report_scores.items()])
            lines.append(f"Overall Report Score: {overall_report:.1f}/10 ({metric_scores})")
        if not lines:
            lines.append("No evaluation scores available.")

        report.summary_meta_data.overall_evaluation_report.content = "\n".join(lines).strip()

    return {"evaluation_scores": evaluation_scores, "report": report}


def build_map_reduce_graph():
    """Build a LangGraph map-reduce pipeline.

    This simplified pipeline:
    - runs `enrich_transform` to produce an enriched JSON payload
    - extracts the `collateral` + `business_model` sections into two bundles
    - for each bundle:
        - if prompt != PROMPT_NONE -> LLM summarize(prompt + payload)
        - if prompt == PROMPT_NONE -> passthrough payload (typically downstream table_md)
    - reduces into a `CreditSummaryGenAIResponse`
    """

    g: StateGraph = StateGraph(MapReduceState)

    g.add_node("enrich", _enrich_node)
    g.add_node("build_bundles", _build_bundles_node)
    g.add_node("split", _split_node)
    g.add_node("summarize_one", _summarize_one_node)
    g.add_node("reduce", _reduce_node)
    g.add_node("evaluate", _evaluate_node)

    g.set_entry_point("enrich")
    g.add_edge("enrich", "build_bundles")
    g.add_edge("build_bundles", "split")
    g.add_conditional_edges("split", _dispatch_node, ["summarize_one"])
    g.add_edge("summarize_one", "reduce")
    g.add_edge("reduce", "evaluate")
    g.add_edge("evaluate", END)

    return g.compile()

