"""
Unit tests for Pydantic models used to parse sample_data.json.
"""

from declarative_fsm.models import SampleData


def test_sample_data_aliases_roundtrip_to_engine_dict():
    raw = {
        "collateral": {"nominalValueAmount": "2500000"},
        "real estate assets": {"address": "123 Main St", "realEstateType": "Commercial"},
        "Financials": {"net_sales": "15000000", "ebitda": "3200000", "year_1": {"category": "revenue", "amount": "5"}},
        "financials_debt": {"YEAR": 2024, "ER12": 1, "ER32": 2, "P88": -3, "EM06": -4, "ER13": 5, "ER41": 6, "P19": 7, "P14": 8, "P03": 9, "P20": 10},
    }

    model = SampleData.model_validate(raw)
    engine_dict = model.to_engine_dict()

    # Aliases preserved (these are the keys used by the engine/config)
    assert "real estate assets" in engine_dict
    assert "Financials" in engine_dict

    # Values preserved (no coercion of numeric strings here)
    assert engine_dict["collateral"]["nominalValueAmount"] == "2500000"
    assert engine_dict["Financials"]["net_sales"] == "15000000"


def test_sample_data_allows_extra_fields():
    raw = {
        "collateral": {"nominalValueAmount": "1", "extra_collateral_key": "ok"},
        "Financials": {"net_sales": "1", "ebitda": "2", "some_new_metric": "3"},
        "unexpected_top_level": {"a": 1},
    }

    model = SampleData.model_validate(raw)
    engine_dict = model.to_engine_dict()

    # Extra fields are allowed and passed through
    assert engine_dict["collateral"]["extra_collateral_key"] == "ok"
    assert engine_dict["Financials"]["some_new_metric"] == "3"
    assert "unexpected_top_level" in engine_dict

