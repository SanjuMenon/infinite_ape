from __future__ import annotations

from typing import List

from .graph import build_map_reduce_graph
from .schemas import Bundle, BundleConfig, BundleTypeConfig, OutputSchema


def make_bundle(field_name: str, format: str = "freeform") -> Bundle:
    return Bundle(
        field_name=field_name,
        format=format,
        most_current_data={"value": f"{field_name}-value"},
    )


def test_build_map_reduce_graph_creates_callable_graph() -> None:
    graph = build_map_reduce_graph()
    assert callable(getattr(graph, "invoke", None))


def test_graph_basic_flow_without_evaluation() -> None:
    graph = build_map_reduce_graph()

    bundles: List[Bundle] = [
        make_bundle("field_one", format="fill_template"),
        make_bundle("field_two", format="fill_template"),
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
            "bundles": bundles,
            "bundle_config": bundle_config,
            "output_schema": output_schema,
        }
    )

    # should produce a report string with our sections and no evaluation header
    report = final_state["report"]
    # report is now a Pydantic model
    dumped = report.model_dump(by_alias=True)
    assert dumped["requestId"]
    assert dumped["summary-sections"]

