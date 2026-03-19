"""
Tests for wrapper_sample_data2.py.

We validate that:
- The wrapper builds an FSM-friendly payload from collaterals
- It runs FSMEngine for each collateral
- It flattens results and attaches `source_collateral_id`
"""

import pytest

from declarative_fsm import FSMEngine, load_config
from declarative_fsm.filter_models import InputPayload
from declarative_fsm.wrapper_sample_data2 import run_over_all_collaterals


def test_wrapper_flattens_results_with_source_collateral_id(tmp_path):
    config = load_config("declarative_fsm/example_config.yaml", validate=True)
    engine = FSMEngine(config, canonical_config_path="declarative_fsm/canonical_config.yaml")

    raw = {
        "requestId": "x",
        "client": {"id": "c", "partnerType": "GROUP"},
        "requester": {"tNumber": "t"},
        "data": {
            "data": {
                "id": "y",
                "legalEntities": [
                    {
                        "entityType": "GROUP",
                        "bankingRelations": [
                            {
                                "isMainBR": True,
                                "collaterals": [
                                    {
                                        "collateralId": "c1",
                                        "nominalValueAmount": 123,
                                        "mortgageDeed": {
                                            "realestates": [
                                                {
                                                    "realEstateType": "Office",
                                                    "address": {
                                                        "street": "Main",
                                                        "houseNumber": "1",
                                                        "postalCode": "1000",
                                                        "city": "Zurich",
                                                        "country": "CH",
                                                    },
                                                }
                                            ]
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        },
    }

    payload = InputPayload.model_validate(raw)
    flattened = run_over_all_collaterals(payload, engine)

    assert flattened, "Expected at least one most_current_data_list item"
    assert all("source_collateral_id" in x for x in flattened)

    collateral_items = [x for x in flattened if x.get("field_name") == "collateral"]
    assert collateral_items, "Expected a collateral field item"
    assert collateral_items[0]["source_collateral_id"] == "c1"

    most_current = collateral_items[0].get("most_current_data", {})
    assert "canonical_nominal_amount" in most_current
    assert most_current["canonical_nominal_amount"] == 123

