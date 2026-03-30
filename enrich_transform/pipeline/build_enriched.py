from __future__ import annotations

from typing import Any

import pandas as pd

from enrich_transform.io.json_io import dataframe_to_json_records
from enrich_transform.pipeline.normalize import (
    aggregate_collateral_values,
    business_model_rows,
    collateral_rows,
    collateral_value_grand_total,
)
from enrich_transform.schemas.raw_models import RawPayloadModel


def build_enriched_payload(raw_obj: dict[str, Any]) -> dict[str, Any]:
    payload = RawPayloadModel.model_validate(raw_obj)

    collateral_records = collateral_rows(payload)
    collateral_df = pd.DataFrame.from_records(collateral_records)
    collateral_agg_df = aggregate_collateral_values(collateral_df)

    grand_total_df = collateral_value_grand_total(collateral_agg_df)
    grand_total_out = dataframe_to_json_records(grand_total_df)

    bm_records = business_model_rows(payload)
    bm_df = pd.DataFrame.from_records(bm_records)
    bm_out = dataframe_to_json_records(bm_df)

    collateral_out = dataframe_to_json_records(collateral_agg_df)

    return {
        "collateral": {
            "aggregate": collateral_out,
            "grand_total": grand_total_out[0] if grand_total_out else {},
        },
        "business_model": bm_out,
    }

