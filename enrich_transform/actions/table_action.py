from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


def _escape_markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value).replace("|", "\\|")


def _collect_columns_from_records(records: list[dict[str, Any]]) -> list[str]:
    cols: list[str] = []
    seen = set()
    for r in records:
        for k in r.keys():
            if k not in seen:
                cols.append(k)
                seen.add(k)
    return cols


def render_records_as_markdown_table(
    records: list[dict[str, Any]],
    *,
    max_rows: int | None = 50,
    max_columns: int | None = 200,
    column_order: list[str] | None = None,
) -> str:
    if not records:
        return "_No rows._"

    if max_rows is not None:
        records = records[:max_rows]

    cols = column_order if column_order is not None else _collect_columns_from_records(records)
    if max_columns is not None:
        cols = cols[:max_columns]

    header = "| " + " | ".join(cols) + " |"
    separator = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows_md = ["| " + " | ".join(_escape_markdown_cell(r.get(c)) for c in cols) + " |" for r in records]
    return "\n".join([header, separator, *rows_md])


def render_dict_as_key_value_markdown_table(d: Mapping[str, Any]) -> str:
    rows = [{"key": k, "value": v} for k, v in d.items()]
    return render_records_as_markdown_table(rows, max_rows=None, column_order=["key", "value"], max_columns=2)


def render_section_to_markdown(section_name: str, section_payload: Any, *, max_rows: int | None = 50, max_columns: int | None = 200) -> str:
    md_parts: list[str] = [f"## {section_name}"]

    if isinstance(section_payload, list):
        if section_payload and isinstance(section_payload[0], dict):
            md_parts.append(render_records_as_markdown_table(section_payload, max_rows=max_rows, max_columns=max_columns))
        else:
            md_parts.append(render_records_as_markdown_table([{"value": x} for x in section_payload], max_rows=max_rows, max_columns=max_columns))
        return "\n\n".join(md_parts)

    if isinstance(section_payload, dict):
        if "aggregate" in section_payload and "grand_total" in section_payload:
            md_parts.append("### collateral.aggregate")
            agg = section_payload.get("aggregate", [])
            if isinstance(agg, list):
                md_parts.append(render_records_as_markdown_table(agg, max_rows=max_rows, max_columns=max_columns))
            elif isinstance(agg, dict):
                md_parts.append(render_dict_as_key_value_markdown_table(agg))
            else:
                md_parts.append(render_dict_as_key_value_markdown_table({"value": agg}))

            md_parts.append("\n### collateral.grand_total")
            gt = section_payload.get("grand_total", {})
            if isinstance(gt, dict):
                md_parts.append(render_dict_as_key_value_markdown_table(gt))
            else:
                md_parts.append(render_dict_as_key_value_markdown_table({"value": gt}))

            return "\n\n".join(md_parts)

        md_parts.append(render_dict_as_key_value_markdown_table(section_payload))
        return "\n\n".join(md_parts)

    md_parts.append(render_records_as_markdown_table([{"value": section_payload}]))
    return "\n\n".join(md_parts)


@dataclass(frozen=True)
class TableAction:
    max_rows: int | None = 50
    max_columns: int | None = 200

    def run(self, section_name: str, section_payload: Any) -> str:
        return render_section_to_markdown(section_name, section_payload, max_rows=self.max_rows, max_columns=self.max_columns)

