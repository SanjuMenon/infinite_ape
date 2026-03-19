"""
Unit tests for filter_models.py (SampleData2 validation + extraction).
"""

import pytest
from pydantic import ValidationError

from declarative_fsm.filter_models import InputPayload


def test_extract_collaterals_returns_empty_list_when_missing_sections():
    raw = {
        "requestId": "x",
        "client": {"id": "c", "partnerType": "GROUP"},
        "requester": {"tNumber": "t"},
        "data": {"data": {"id": "y", "legalEntities": []}},
    }

    m = InputPayload.model_validate(raw)
    assert m.extract_collaterals() == []


def test_extract_collaterals_happy_path():
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
                                        "collateralType": "RE",
                                        "nominalValueAmount": 123,
                                        "mortgageDeed": {
                                            "realestates": [
                                                {
                                                    "realEstateType": "Commercial",
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

    m = InputPayload.model_validate(raw)
    collats = m.extract_collaterals()
    assert len(collats) == 1
    assert collats[0]["collateralId"] == "c1"


def test_to_fsm_input_maps_first_collateral_into_expected_fields():
    raw = {
        "requestId": "x",
        "client": {"id": "c", "partnerType": "GROUP"},
        "requester": {"tNumber": "t"},
        "data": {
            "data": {
                "id": "y",
                "legalEntities": [
                    {
                        "bankingRelations": [
                            {
                                "collaterals": [
                                    {
                                        "collateralType": "RealEstate",
                                        "nominalValueAmount": 2500000,
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
                                ]
                            }
                        ]
                    }
                ],
            }
        },
    }

    m = InputPayload.model_validate(raw)
    fsm_input = m.to_fsm_input()

    assert fsm_input["collaterals"] and len(fsm_input["collaterals"]) == 1
    assert fsm_input["collateral"]["nominalValueAmount"] == 2500000
    assert fsm_input["real estate assets"]["realEstateType"] == "Office"
    assert "Zurich" in fsm_input["real estate assets"]["address"]


def test_to_fsm_input_empty_when_no_collaterals():
    m = InputPayload.model_validate(
        {
            "requestId": "x",
            "client": {"id": "c", "partnerType": "GROUP"},
            "requester": {"tNumber": "t"},
            "data": {"data": {"id": "y", "legalEntities": []}},
        }
    )
    fsm_input = m.to_fsm_input()
    assert fsm_input["collaterals"] == []
    assert fsm_input["collateral"] == {}
    assert fsm_input["real estate assets"] == {}


def test_required_envelope_fields_are_mandatory():
    with pytest.raises(ValidationError):
        InputPayload.model_validate({"requestId": "x"})

