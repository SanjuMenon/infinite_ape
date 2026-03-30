from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from enrich_transform.actions.dispatcher import run_downstream_actions
from enrich_transform.io.json_io import read_json, write_json
from enrich_transform.pipeline.build_enriched import build_enriched_payload


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build enriched JSON and run downstream actions.")
    p.add_argument(
        "--raw",
        default=str(Path(__file__).resolve().parent / "raw.json"),
        help="Path to input raw.json",
    )
    p.add_argument(
        "--no-downstream",
        action="store_true",
        help="If set, do not generate downstream table/summary outputs.",
    )
    p.add_argument(
        "--write-enriched-json",
        default="",
        help="Optional: path to write enriched JSON (default: do not write).",
    )
    p.add_argument(
        "--write-result-json",
        default="",
        help="Optional: path to write the full final result JSON (enriched + downstream).",
    )
    p.add_argument(
        "--write-downstream-dir",
        default="",
        help="Optional: directory to write downstream outputs (default: do not write).",
    )
    return p.parse_args()


def run(
    *,
    raw_obj: dict[str, Any] | None = None,
    raw_path: str | Path | None = None,
    no_downstream: bool = False,
) -> dict[str, Any]:
    """
    Programmatic entrypoint.

    - Provide `raw_obj` to run purely in-memory
    - Or provide `raw_path` to load JSON from disk
    """
    if raw_obj is None:
        raw_path = raw_path or (Path(__file__).resolve().parent / "raw.json")
        raw_obj = read_json(raw_path)

    enriched_payload = build_enriched_payload(raw_obj)

    if not no_downstream:
        downstream = run_downstream_actions(enriched_payload)
    else:
        downstream = {}

    return {"enriched": enriched_payload, "downstream": downstream}


def main() -> dict[str, Any]:
    """
    CLI entrypoint (parses args, optionally persists outputs).
    """
    args = _parse_args()

    result = run(raw_path=args.raw, no_downstream=args.no_downstream)

    # Optional persistence (explicit only)
    if args.write_enriched_json:
        write_json(args.write_enriched_json, result["enriched"])

    if args.write_result_json:
        write_json(args.write_result_json, result)

    if args.write_downstream_dir:
        out_dir = Path(args.write_downstream_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for section_name, artifacts in result["downstream"].items():
            (out_dir / f"{section_name}.table.md").write_text(artifacts.get("table_md", ""), encoding="utf-8")
            write_json(out_dir / f"{section_name}.summary.json", artifacts.get("summary", {}))
            (out_dir / f"{section_name}.summary.md").write_text(artifacts.get("summary_md", ""), encoding="utf-8")

    return result

