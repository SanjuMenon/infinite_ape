from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .llm_client import get_deployment_name, get_openai_client, get_provider, is_llm_available
from .schemas import Bundle


def _as_compact_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def _summarize_freeform_deterministic(bundle: Bundle) -> str:
    """Deterministic fallback for freeform summarization (no LLM)."""
    lines: List[str] = []
    lines.append(f"Bundle: {bundle.bundle_name}")

    if bundle.required_fields_found:
        lines.append(f"- required_fields_found: {', '.join(bundle.required_fields_found)}")

    if bundle.field_data:
        lines.append("- field_data:")
        for k, v in bundle.field_data.items():
            lines.append(f"  - {k}: {v}")

    # include a small amount of validation metadata when present
    meta_parts: List[str] = []
    if bundle.format_validated is not None:
        meta_parts.append(f"format_validated={bundle.format_validated}")
    if bundle.length_validated is not None:
        meta_parts.append(f"length_validated={bundle.length_validated}")
    if bundle.validated_field_count is not None:
        meta_parts.append(f"validated_field_count={bundle.validated_field_count}")
    if bundle.field_count is not None:
        meta_parts.append(f"field_count={bundle.field_count}")
    if meta_parts:
        lines.append(f"- checks: {', '.join(meta_parts)}")

    # fall back to showing payload if we have nothing else
    if len(lines) <= 1:
        lines.append("- payload:")
        lines.append(_as_compact_json(bundle.model_dump()))

    return "\n".join(lines).strip()


def summarize_freeform(bundle: Bundle) -> str:
    """Summarize bundle in freeform text using LLM if available, else deterministic fallback."""
    client = get_openai_client()
    
    if client is None:
        return _summarize_freeform_deterministic(bundle)
    
    try:
        # Prepare bundle data as JSON for the prompt
        bundle_json = _as_compact_json(bundle.model_dump())
        
        prompt = f"""Summarize the following bundle data in a clear, freeform narrative format.
Focus on the key information and provide context about what this bundle represents.

Bundle Name: {bundle.bundle_name}
Bundle Data:
{bundle_json}

Provide a concise, readable summary that highlights the important fields and their values."""

        # Use deployment name for Azure, model name for OpenAI
        provider = get_provider()
        if provider == "azure":
            model_or_deployment = get_deployment_name() or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        else:
            model_or_deployment = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        response = client.chat.completions.create(
            model=model_or_deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes structured data bundles in clear, readable text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content
        if summary:
            return summary.strip()
        
        # Fallback if response is empty
        return _summarize_freeform_deterministic(bundle)
        
    except Exception:
        # On any error, fall back to deterministic behavior
        return _summarize_freeform_deterministic(bundle)


def _markdown_table(rows: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
    if not rows:
        return "| key | value |\n|---|---|\n| (empty) | (empty) |"

    if columns is None:
        # stable ordering: all keys seen across rows, sorted
        keys = set()
        for r in rows:
            keys.update(r.keys())
        columns = sorted(keys)

    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body_lines: List[str] = []
    for r in rows:
        body_lines.append("| " + " | ".join(str(r.get(c, "")) for c in columns) + " |")
    return "\n".join([header, sep, *body_lines])


def _summarize_table_deterministic(bundle: Bundle) -> str:
    """Deterministic fallback for table summarization (no LLM)."""
    # Primary: field_data as 2-col table
    if bundle.field_data:
        rows = [{"key": k, "value": v} for k, v in bundle.field_data.items()]
        table = _markdown_table(rows, columns=["key", "value"])
        return f"Bundle: {bundle.bundle_name}\n\n{table}".strip()

    # Secondary: show canonical_data if present
    if bundle.canonical_data:
        rows = [{"key": k, "value": v} for k, v in bundle.canonical_data.items()]
        table = _markdown_table(rows, columns=["key", "value"])
        return f"Bundle: {bundle.bundle_name}\n\n{table}".strip()

    # Fallback: table of top-level keys
    d = bundle.model_dump()
    rows = [{"key": k, "value": v} for k, v in d.items()]
    table = _markdown_table(rows, columns=["key", "value"])
    return f"Bundle: {bundle.bundle_name}\n\n{table}".strip()


def summarize_table(bundle: Bundle) -> str:
    """Summarize bundle as a markdown table using LLM if available, else deterministic fallback."""
    client = get_openai_client()
    
    if client is None:
        return _summarize_table_deterministic(bundle)
    
    try:
        # Prepare bundle data as JSON for the prompt
        bundle_json = _as_compact_json(bundle.model_dump())
        
        prompt = f"""Summarize the following bundle data as a well-formatted markdown table.
The table should have clear column headers and organize the key information from the bundle.

Bundle Name: {bundle.bundle_name}
Bundle Data:
{bundle_json}

Create a markdown table that presents the important fields and their values in a structured, readable format.
Use appropriate column headers based on the data structure."""

        # Use deployment name for Azure, model name for OpenAI
        provider = get_provider()
        if provider == "azure":
            model_or_deployment = get_deployment_name() or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        else:
            model_or_deployment = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        response = client.chat.completions.create(
            model=model_or_deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats structured data as markdown tables. Always output valid markdown table syntax."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Lower temperature for more structured output
            max_tokens=500
        )
        
        table = response.choices[0].message.content
        if table:
            # Ensure we have a heading
            result = f"Bundle: {bundle.bundle_name}\n\n{table}".strip()
            return result
        
        # Fallback if response is empty
        return _summarize_table_deterministic(bundle)
        
    except Exception:
        # On any error, fall back to deterministic behavior
        return _summarize_table_deterministic(bundle)

