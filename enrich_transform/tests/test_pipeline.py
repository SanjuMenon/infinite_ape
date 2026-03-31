import copy
from pathlib import Path

import pytest

from enrich_transform.actions.dispatcher import run_downstream_actions
from enrich_transform.io.json_io import read_json
from enrich_transform.pipeline.build_enriched import build_enriched_payload


@pytest.mark.unit
def test_build_enriched_payload_from_raw_json_shape():
    raw_path = Path(__file__).resolve().parents[1] / "raw.json"
    raw_obj = read_json(raw_path)

    enriched = build_enriched_payload(raw_obj)

    assert isinstance(enriched, dict)
    assert "collateral" in enriched
    assert "business_model" in enriched
    assert "real_estate" in enriched

    assert isinstance(enriched["collateral"], dict)
    assert "aggregate" in enriched["collateral"]
    assert "grand_total" in enriched["collateral"]

    assert isinstance(enriched["collateral"]["aggregate"], list)
    assert isinstance(enriched["collateral"]["grand_total"], dict)
    assert isinstance(enriched["business_model"], list)
    assert isinstance(enriched["real_estate"], list)


@pytest.mark.unit
def test_downstream_actions_artifacts_present():
    raw_path = Path(__file__).resolve().parents[1] / "raw.json"
    raw_obj = read_json(raw_path)
    enriched = build_enriched_payload(raw_obj)

    downstream = run_downstream_actions(enriched)

    assert "collateral" in downstream
    assert "business_model" in downstream
    assert "real_estate" in downstream

    for section in ["collateral", "business_model", "real_estate"]:
        assert "json_str" in downstream[section]
        assert "table_md" in downstream[section]
        assert "summary" in downstream[section]
        assert "summary_md" in downstream[section]

        assert isinstance(downstream[section]["json_str"], str)
        assert isinstance(downstream[section]["table_md"], str)
        assert isinstance(downstream[section]["summary"], dict)
        assert isinstance(downstream[section]["summary_md"], str)


@pytest.mark.unit
def test_validation_fails_on_null_amounts():
    raw_path = Path(__file__).resolve().parents[1] / "raw.json"
    raw_obj = read_json(raw_path)

    mutated = copy.deepcopy(raw_obj)

    # Navigate: data.data.legalEntities[0].bankingRelations[0].collaterals[0].lendingValueAmount
    collateral0 = (
        mutated["data"]["data"]["legalEntities"][0]["bankingRelations"][0]["collaterals"][0]
    )
    collateral0["lendingValueAmount"] = None

    with pytest.raises(Exception):
        build_enriched_payload(mutated)

