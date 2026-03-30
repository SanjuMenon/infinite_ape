from __future__ import annotations

import json
from typing import Any

import pandas as pd

from enrich_transform.schemas.raw_models import RawPayloadModel


def _json_serialize_if_needed(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=True)


def collateral_rows(payload: RawPayloadModel) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entity in payload.data.data.legalEntities:
        legal_entity_id = entity.legalEntityIdGPID
        for br in entity.bankingRelations:
            relation_id = br.bankingRelationNumber
            for c in br.collaterals:
                rows.append(
                    {
                        "collateralId": c.collateralId,
                        "collateralType": c.collateralType,
                        "currency": c.currency,
                        "nominalValueAmount": c.nominalValueAmount,
                        "lendingValueAmount": c.lendingValueAmount,
                        "lendingValueDate": c.lendingValueDate,
                        "legalEntityId": legal_entity_id,
                        "relationId": relation_id,
                        "isMainBR": br.isMainBR,
                    }
                )
    return rows


def business_model_rows(payload: RawPayloadModel) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entity in payload.data.data.legalEntities:
        legal_entity_id = entity.legalEntityIdGPID
        for br in entity.bankingRelations:
            relation_id = br.bankingRelationNumber
            for bm in br.businessModel:
                row: dict[str, Any] = {
                    "legalEntityId": legal_entity_id,
                    "relationId": relation_id,
                    "isMainBR": br.isMainBR,
                }
                for k, v in bm.items():
                    row[k] = _json_serialize_if_needed(v)
                rows.append(row)
    return rows


def aggregate_collateral_values(collateral_df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "collateralId",
        "collateralType",
        "nominalValueAmount",
        "lendingValueAmount",
        "lendingValueDate",
    }
    missing = required.difference(collateral_df.columns)
    if missing:
        raise ValueError(f"Missing required collateral columns: {sorted(missing)}")

    df = collateral_df.copy()
    df = df.sort_values(["collateralId", "lendingValueDate"], ascending=[True, False])

    agg = (
        df.groupby("collateralId", as_index=False)
        .agg(
            collateralType=("collateralType", "first"),
            latest_lendingValueDate=("lendingValueDate", "max"),
            total_nominal_value=("nominalValueAmount", "sum"),
            total_lending_value=("lendingValueAmount", "sum"),
        )
    )
    agg["currency"] = "CHF"
    return agg


def collateral_value_grand_total(collateral_agg_df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "collateralId",
        "latest_lendingValueDate",
        "total_nominal_value",
        "total_lending_value",
    }
    missing = required.difference(collateral_agg_df.columns)
    if missing:
        raise ValueError(f"Missing required collateral aggregate columns: {sorted(missing)}")

    total_nominal = float(collateral_agg_df["total_nominal_value"].sum())
    total_lending = float(collateral_agg_df["total_lending_value"].sum())
    unique_collateral_count = int(collateral_agg_df["collateralId"].nunique())
    latest_date = collateral_agg_df["latest_lendingValueDate"].max()

    return pd.DataFrame(
        [
            {
                "total_nominal_value": total_nominal,
                "total_lending_value": total_lending,
                "unique_collateral_count": unique_collateral_count,
                "latest_lendingValueDate": latest_date,
                "currency": "CHF",
            }
        ]
    )

