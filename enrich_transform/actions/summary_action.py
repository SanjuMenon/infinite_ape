from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


def summarize_section(section_name: str, section_payload: Any) -> dict[str, Any]:
    if section_name == "collateral":
        if not isinstance(section_payload, dict):
            return {"section": section_name, "error": "expected dict payload"}

        aggregate = section_payload.get("aggregate", [])
        grand_total = section_payload.get("grand_total", {})

        unique_collaterals = len(aggregate) if isinstance(aggregate, list) else None
        total_nominal = None
        total_lending = None
        latest_date = None
        top_by_lending: list[dict[str, Any]] = []

        if isinstance(aggregate, list) and aggregate and isinstance(aggregate[0], dict):
            total_nominal = sum(float(r.get("total_nominal_value", 0.0) or 0.0) for r in aggregate)
            total_lending = sum(float(r.get("total_lending_value", 0.0) or 0.0) for r in aggregate)
            latest_date = max((r.get("latest_lendingValueDate") for r in aggregate if r.get("latest_lendingValueDate")), default=None)
            sorted_rows = sorted(
                aggregate,
                key=lambda r: float(r.get("total_lending_value", 0.0) or 0.0),
                reverse=True,
            )
            top_by_lending = [
                {"collateralId": r.get("collateralId"), "total_lending_value": r.get("total_lending_value")}
                for r in sorted_rows[:5]
            ]
        elif isinstance(grand_total, dict) and grand_total:
            # Fall back to the already-computed grand total if aggregate isn't present.
            total_nominal = grand_total.get("total_nominal_value")
            total_lending = grand_total.get("total_lending_value")
            latest_date = grand_total.get("latest_lendingValueDate")

        return {
            "section": section_name,
            "unique_collateral_count": unique_collaterals if unique_collaterals is not None else (grand_total.get("unique_collateral_count") if isinstance(grand_total, dict) else None),
            "total_nominal_value": total_nominal,
            "total_lending_value": total_lending,
            "latest_lendingValueDate": latest_date,
            "grand_total": grand_total if isinstance(grand_total, dict) else None,
            "top_collaterals_by_lending_value": top_by_lending,
        }

    if section_name == "business_model":
        if not isinstance(section_payload, list):
            return {"section": section_name, "error": "expected list payload"}

        num_rows = len(section_payload)
        is_main_counts: dict[str, int] = {"true": 0, "false": 0}
        relation_ids = set()
        legal_entity_ids = set()

        for row in section_payload:
            if not isinstance(row, dict):
                continue
            is_main = row.get("isMainBR")
            if is_main is True:
                is_main_counts["true"] += 1
            else:
                is_main_counts["false"] += 1

            relation_ids.add(row.get("relationId"))
            legal_entity_ids.add(row.get("legalEntityId"))

        # Diagnostics (renamed + moved under debug)
        keys: set[str] = set()
        for row in section_payload[:10]:
            if isinstance(row, dict):
                keys.update(row.keys())

        sample_rows: list[dict[str, Any]] = []
        for row in section_payload[:5]:
            if isinstance(row, dict):
                sample_rows.append(
                    {
                        "legalEntityId": row.get("legalEntityId"),
                        "relationId": row.get("relationId"),
                        "isMainBR": row.get("isMainBR"),
                    }
                )

        return {
            "section": section_name,
            "row_count": num_rows,
            "isMainBR_counts": is_main_counts,
            "unique_relationId_count": len([x for x in relation_ids if x is not None]),
            "unique_legalEntityId_count": len([x for x in legal_entity_ids if x is not None]),
            "sample_rows_first_5": sample_rows,
            "debug": {
                "columns_present_first_10_rows": sorted(keys),
            },
        }

    return {"section": section_name, "shape": type(section_payload).__name__}


def summary_dict_to_markdown(summary: dict[str, Any]) -> str:
    section = summary.get("section", "summary")
    lines: list[str] = [f"# {section} summary"]

    def add_line(label: str, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, (dict, list)):
            lines.append(f"- {label}: `{json.dumps(value, ensure_ascii=True)}`")
        else:
            lines.append(f"- {label}: {value}")

    if section == "collateral":
        add_line("unique_collateral_count", summary.get("unique_collateral_count"))
        add_line("total_nominal_value", summary.get("total_nominal_value"))
        add_line("total_lending_value", summary.get("total_lending_value"))
        add_line("latest_lendingValueDate", summary.get("latest_lendingValueDate"))
        add_line("top_collaterals_by_lending_value", summary.get("top_collaterals_by_lending_value"))
    elif section == "business_model":
        add_line("row_count", summary.get("row_count"))
        add_line("isMainBR_counts", summary.get("isMainBR_counts"))
        add_line("unique_relationId_count", summary.get("unique_relationId_count"))
        add_line("unique_legalEntityId_count", summary.get("unique_legalEntityId_count"))
        add_line("sample_rows_first_5", summary.get("sample_rows_first_5"))
    else:
        for k, v in summary.items():
            add_line(k, v)

    return "\n".join(lines)


@dataclass(frozen=True)
class SummaryAction:
    def run(self, section_name: str, section_payload: Any) -> dict[str, Any]:
        return summarize_section(section_name, section_payload)

