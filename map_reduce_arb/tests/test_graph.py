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

