from __future__ import annotations

from pathlib import Path

from map_reduce_arb.config import load_bundle_config, load_output_schema
from map_reduce_arb.schemas import Bundle, BundleConfig, OutputSchema


def test_bundle_requires_minimal_fields() -> None:
    bundle = Bundle(
        field_name="example",
        prompt="Say hello",
        payload="{}",
    )
    assert bundle.field_name == "example"
    assert bundle.prompt == "Say hello"
    assert bundle.payload == "{}"


def test_load_bundle_config_works(tmp_path: Path) -> None:
    yaml_path = tmp_path / "bundle_config.yaml"
    yaml_path.write_text(
        "bundle_order:\n"
        "  - field_name: foo\n"
        "    section_title: Section Foo\n"
        "    order: 0\n",
        encoding="utf-8",
    )
    cfg: BundleConfig = load_bundle_config(yaml_path)
    assert len(cfg.bundle_order) == 1
    assert cfg.bundle_order[0].field_name == "foo"
    assert cfg.bundle_order[0].section_title == "Section Foo"
    assert cfg.bundle_order[0].order == 0


def test_load_output_schema_builtin() -> None:
    here = Path(__file__).resolve().parents[1]  # map_reduce_arb/
    schema_path = here / "output_schema.json"
    schema: OutputSchema = load_output_schema(schema_path)
    assert isinstance(schema.title, str)

