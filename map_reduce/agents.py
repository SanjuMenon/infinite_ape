from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .llm_client import get_client_and_model, get_openai_client
from .schemas import Bundle


def _as_compact_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def summarize_template_fill(bundle: Bundle) -> str:
    """Template-based summarization (no LLM required).
    
    Creates a structured text summary using a template format.
    """
    lines: List[str] = []

    # Always use most_current_data
    if bundle.most_current_data:
        lines.append("- data:")
        for k, v in bundle.most_current_data.items():
            lines.append(f"  - {k}: {v}")
    else:
        # Fallback if most_current_data is empty
        lines.append("- payload:")
        lines.append(_as_compact_json(bundle.model_dump()))

    return "\n".join(lines).strip()


def summarize_freeform(bundle: Bundle) -> str:
    """Summarize bundle in freeform text using LLM (requires LLM to be available)."""
    client, model_or_deployment = get_client_and_model()
    if client is None or model_or_deployment is None:
        raise RuntimeError(
            "LLM is required for summarize_freeform. "
            "Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT, "
            "or use summarize_template_fill() for non-LLM summarization."
        )
    
    # Always use most_current_data for LLM summarization
    bundle_json = _as_compact_json(bundle.most_current_data)
    
    prompt = f"""Summarize the following data in a clear, freeform narrative format.
Focus on the key information present in the data.

Data:
{bundle_json}

Provide a concise, readable summary that highlights the important fields and their values.

IMPORTANT:
- Do NOT add any facts, numbers, totals, categories, or interpretations that are not explicitly present in the data.
- Do NOT rename fields or imply relationships that are not explicitly present.
- Do NOT mention the bundle name / field name.
- Do NOT add headings like "Bundle:", "Field:", or similar.
- Return only the summary text."""

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
    if not summary:
        raise RuntimeError("LLM returned empty response for summarize_freeform")
    
    return summary.strip()


def _extract_markdown_table(text: str) -> str:
    """Extract markdown table from text that may contain extra content.
    
    Looks for the first markdown table (lines starting with |) and returns it.
    """
    lines = text.split('\n')
    table_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        # Check if this line is part of a markdown table
        if stripped.startswith('|') and '|' in stripped[1:]:
            in_table = True
            table_lines.append(line)
        elif in_table:
            # If we were in a table and hit a non-table line, check if it's a separator
            if stripped.startswith('|') or (stripped.startswith('-') and '|' in line):
                # This might be a table separator row
                table_lines.append(line)
            elif stripped == '':
                # Empty line might be within table, keep it
                table_lines.append(line)
            else:
                # Non-table line after table has started - table is complete
                break
    
    if table_lines:
        return '\n'.join(table_lines).strip()
    return text.strip()


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
    # Always use most_current_data for consistency with LLM mode
    if bundle.most_current_data:
        rows = [{"key": k, "value": v} for k, v in bundle.most_current_data.items()]
        table = _markdown_table(rows, columns=["key", "value"])
        return table.strip()
    
    # Fallback if most_current_data is empty
    d = bundle.model_dump()
    rows = [{"key": k, "value": v} for k, v in d.items()]
    table = _markdown_table(rows, columns=["key", "value"])
    return table.strip()


def summarize_table(bundle: Bundle) -> str:
    """Summarize bundle as a markdown table using LLM if available, else deterministic fallback."""
    client, model_or_deployment = get_client_and_model()
    if client is None or model_or_deployment is None:
        return _summarize_table_deterministic(bundle)
    
    try:
        # Always use most_current_data for LLM summarization
        bundle_json = _as_compact_json(bundle.most_current_data)
        
        prompt = f"""Format the following data as a STRICT markdown table.

Data:
{bundle_json}

Create a markdown table that lists ONLY fields that appear in the provided JSON data.
Use a simple two-column schema: | key | value |.
If a value is an object/array, render the value as compact JSON on a single line (do not expand into invented rows).

IMPORTANT: 
- Do NOT add, infer, compute, group, rename, or normalize anything. No totals. No categories. No derived fields.
- Do NOT include "Bundle Name" or the bundle name as a row in the table.
- Do NOT mention the bundle name / field name anywhere in the response.
- Return ONLY the markdown table. Do not include any explanatory text, headings, or additional content before or after the table.
- Start your response directly with the table (e.g., "| Column1 | Column2 |")"""

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
            # Extract just the table from the response (in case LLM adds extra text)
            table = _extract_markdown_table(table)
            if table:
                return table.strip()
        
        # Fallback if response is empty
        return _summarize_table_deterministic(bundle)
        
    except Exception:
        # On any error, fall back to deterministic behavior
        return _summarize_table_deterministic(bundle)

