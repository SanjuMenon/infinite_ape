from __future__ import annotations

from typing import List

from map_reduce_arb.graph import build_map_reduce_graph
from map_reduce_arb.prompts import PROMPT_NONE
from map_reduce_arb.schemas import Bundle, BundleConfig, BundleTypeConfig, OutputSchema


def make_bundle(field_name: str, *, prompt: str | None, payload: str) -> Bundle:
    return Bundle(
        field_name=field_name,
        prompt=prompt,
        payload=payload,
    )


def test_build_map_reduce_graph_creates_callable_graph() -> None:
    graph = build_map_reduce_graph()
    assert callable(getattr(graph, "invoke", None))


def test_graph_basic_flow_without_evaluation() -> None:
    graph = build_map_reduce_graph()

    bundles: List[Bundle] = [
        make_bundle("field_one", prompt=PROMPT_NONE, payload="| key | value |\n|---|---|\n| a | b |"),
        make_bundle("field_two", prompt=PROMPT_NONE, payload="hello"),
    ]
    bundle_config = BundleConfig(
        bundle_order=[
            BundleTypeConfig(field_name="field_one", section_title="Section One", order=0),
            BundleTypeConfig(field_name="field_two", section_title="Section Two", order=1),
        ]
    )
    output_schema = OutputSchema(title="Test Report")

    final_state = graph.invoke(
        {
            # bypass enrich/build_bundles nodes by providing bundles directly
            "bundles": bundles,
            "bundle_config": bundle_config,
            "output_schema": output_schema,
        }
    )

    report = final_state["report"]
    dumped = report.model_dump(by_alias=True)
    assert dumped["requestId"]
    assert dumped["summary-sections"]


def test_passthrough_payload_can_be_json_or_md_based_on_section_type() -> None:
    """Unit-test the intended behavior:
    - collateral passthrough uses enriched JSON (not downstream json_str)
    - real_estate passthrough uses enriched JSON
    """
    graph = build_map_reduce_graph()

    state = graph.invoke(
        {
            "raw_obj": None,
            "raw_path": None,
            "enriched": {"collateral": {"a": 1}, "real_estate": [{"realEstateId": "x"}]},
            "downstream": {
                "collateral": {"json_str": '{"a": 1}', "table_md": "## collateral\n\n### collateral.aggregate\nx"},
                "real_estate": {"json_str": "[1]", "table_md": "## real_estate\n\n| a | b |\n|---|---|\n| 1 | 2 |"},
            },
            "bundle_config": BundleConfig(
                bundle_order=[
                    BundleTypeConfig(field_name="collateral", section_title="Collateral", order=0),
                    BundleTypeConfig(field_name="real_estate", section_title="Real Estate", order=1),
                ]
            ),
            "output_schema": OutputSchema(title="Test Report"),
        }
    )

    report = state["report"]
    dumped = report.model_dump(by_alias=True)
    sections = dumped["summary-sections"]
    # Flatten sub-sections by identifier
    sub_by_id = {}
    for sec in sections:
        for sub in sec.get("summary-sub-sections", []):
            sub_by_id[sub["identifier"]] = sub

    assert sub_by_id["collateral"]["content-format"] == "JSON"
    assert '"a": 1' in sub_by_id["collateral"]["content"]  # enriched JSON passthrough

    assert sub_by_id["real_estate"]["content-format"] == "JSON"
    assert '"realEstateId": "x"' in sub_by_id["real_estate"]["content"]  # enriched JSON passthrough

