from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from .agents import summarize_freeform, summarize_table, summarize_template_fill
from .evaluator import evaluate_report, evaluate_summary
from .llm_client import is_llm_available, get_provider
from .report_schemas import (
    CreditSummaryGenAIResponse,
    SummarySection,
    SummarySubSection,
    OverallEvaluationReport,
    SummaryMetaData,
)
from .schemas import Bundle, BundleConfig, BundleTypeConfig, OutputSchema, OutputSectionSchema
from .splitter import split_bundle


class MapReduceState(TypedDict, total=False):
    bundles: List[Bundle]
    bundle_config: BundleConfig
    output_schema: OutputSchema
    metadata: Optional[Dict[str, Any]]  # Metadata from sample_data.json (_metadata section)

    # populated during execution
    subtasks: List[Bundle]
    partials: Annotated[List[Dict[str, str]], operator.add]  # [{"field_name": str, "text": str}]
    report: CreditSummaryGenAIResponse  # Changed from str to Pydantic model
    evaluation_scores: Dict[str, Any]  # {"summary_scores": Dict[str, Dict[str, float]], "report_scores": Dict[str, float]}


def _flatten_sections(sections: List[OutputSectionSchema]) -> List[OutputSectionSchema]:
    out: List[OutputSectionSchema] = []
    for s in sections:
        out.append(s)
        if s.subsections:
            out.extend(_flatten_sections(s.subsections))
    return out


def _determine_content_format(bundle_format: str) -> str:
    """Map bundle format to content format string."""
    if bundle_format == "table":
        return "MD"
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
    
    # Extract evaluation scores if available
    summary_scores: Dict[str, Dict[str, float]] = {}
    report_scores: Dict[str, float] = {}
    if evaluation_scores:
        summary_scores = evaluation_scores.get("summary_scores", {})
        report_scores = evaluation_scores.get("report_scores", {})
    
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
            
            content_format = _determine_content_format(bundle.format)
            
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
            
            content_format = _determine_content_format(bundle.format)
            
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
    
    # Build debug log
    debug_log_lines = []
    if is_llm_available():
        provider = get_provider()
        if provider:
            debug_log_lines.append(f"LLM Provider: {provider}")
        else:
            debug_log_lines.append("LLM Provider: Unknown")
    else:
        debug_log_lines.append("LLM Provider: Not available (using deterministic fallback)")
    
    debug_log = "\n".join(debug_log_lines) if debug_log_lines else "No debug information available."
    
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
    elif bundle.format == "fill_template":
        text = summarize_template_fill(bundle)
    else:
        text = summarize_freeform(bundle)
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


def _should_evaluate(state: MapReduceState) -> str:
    """Check if evaluation is needed based on bundles."""
    bundles = state.get("bundles", [])
    for bundle in bundles:
        if bundle.eval_type is not None and bundle.metrics is not None:
            return "evaluate"
    return "END"


def _evaluate_node(state: MapReduceState) -> Dict[str, Any]:
    """Evaluate individual summaries and overall report sequentially.
    
    Returns:
        Dictionary with "evaluation_scores" containing:
        - "summary_scores": Dict mapping field_name to scores
        - "report_scores": Dict mapping metric to score
    """
    bundles = state.get("bundles", [])
    partials = state.get("partials", [])
    report = state.get("report")
    
    # Create mapping from field_name to bundle and summary text
    bundle_by_field: Dict[str, Bundle] = {}
    summaries_by_field: Dict[str, List[str]] = defaultdict(list)
    
    for bundle in bundles:
        bundle_by_field[bundle.field_name] = bundle
    
    for partial in partials:
        field_name = partial["field_name"]
        summaries_by_field[field_name].append(partial["text"])
    
    # Step 1: Evaluate individual summaries (for bundles that need it)
    summary_scores: Dict[str, Dict[str, float]] = {}
    for bundle in bundles:
        if bundle.eval_type is not None and bundle.metrics is not None:
            field_name = bundle.field_name
            if field_name in summaries_by_field:
                # Combine all partial texts for this field_name (supports multiple collaterals)
                combined_text = "\n\n".join([t.strip() for t in summaries_by_field[field_name] if t and t.strip()])
                if combined_text.strip():
                    scores = evaluate_summary(bundle, combined_text)
                    summary_scores[field_name] = scores
    
    # Step 2: Evaluate overall report (need to render to markdown for evaluation)
    report_scores: Dict[str, float] = {}
    if bundles and any(b.eval_type is not None and b.metrics is not None for b in bundles):
        if report:
            report_markdown = render_to_markdown(report)
            report_scores = evaluate_report(report_markdown, bundles)
    
    evaluation_scores = {
        "summary_scores": summary_scores,
        "report_scores": report_scores
    }
    
    # Step 3: Regenerate report with evaluation scores included
    bundle_config = state.get("bundle_config", BundleConfig())
    output_schema = state.get("output_schema", OutputSchema())
    metadata = state.get("metadata")
    updated_report = _aggregate_report_pydantic(
        bundle_config=bundle_config,
        output_schema=output_schema,
        partials=partials,
        bundles=bundles,
        metadata=metadata,
        evaluation_scores=evaluation_scores
    )
    
    return {
        "evaluation_scores": evaluation_scores,
        "report": updated_report  # Update report with scores
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

