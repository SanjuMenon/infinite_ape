from __future__ import annotations

import json
from typing import Any

from enrich_transform.actions.summary_action import SummaryAction, summary_dict_to_markdown
from enrich_transform.actions.table_action import TableAction


def run_downstream_actions(
    enriched_payload: dict[str, Any],
    *,
    sections: list[str] | None = None,
    table_action: TableAction | None = None,
    summary_action: SummaryAction | None = None,
) -> dict[str, Any]:
    sections = sections or ["collateral", "business_model", "real_estate"]
    table_action = table_action or TableAction(max_rows=50, max_columns=200)
    summary_action = summary_action or SummaryAction()

    out: dict[str, Any] = {}
    for section_name in sections:
        section_payload = enriched_payload.get(section_name)
        if section_payload is None:
            continue

        json_str = json.dumps(section_payload, ensure_ascii=True, indent=2)
        table_md = table_action.run(section_name, section_payload)
        summary_obj = summary_action.run(section_name, section_payload)
        summary_md = summary_dict_to_markdown(summary_obj)

        out[section_name] = {
            "json_str": json_str,
            "table_md": table_md,
            "summary": summary_obj,
            "summary_md": summary_md,
        }

    return out

