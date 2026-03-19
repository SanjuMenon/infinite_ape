"""
Wrapper to run the declarative FSM over all collaterals in `raw.json`.

Flow:
1. Validate input payload via InputPayload (Pydantic) in `filter_models.py`
2. Extract all collateral records: data.data.legalEntities[*].bankingRelations[*].collaterals
3. For each collateral record:
   - Build an FSM-friendly payload with only:
     - `collateral.nominalValueAmount`
     - `real estate assets.address` (flattened) + `realEstateType`
   - Run `FSMEngine.execute()` once per collateral record
4. Flatten all runs' `most_current_data_list` and attach `source_collateral_id`
5. Save the flattened list to `map_reduce/most_current_data_sample_data2.pkl`
"""

from __future__ import annotations

import argparse
import json
import pickle
import codecs
from pathlib import Path
from typing import Any, Dict, List

from declarative_fsm import FSMEngine, load_config
from declarative_fsm.filter_models import InputPayload


def _decode_json_bytes(b: bytes) -> str:
    """
    Decode JSON bytes into text, handling common encodings used on Windows:
    utf-8, utf-16, utf-32 (BOM-based) and utf-16 heuristic (null bytes).
    """
    if b.startswith(codecs.BOM_UTF8):
        return b.decode("utf-8-sig")
    if b.startswith(codecs.BOM_UTF16_LE) or b.startswith(codecs.BOM_UTF16_BE):
        return b.decode("utf-16")
    if b.startswith(codecs.BOM_UTF32_LE) or b.startswith(codecs.BOM_UTF32_BE):
        return b.decode("utf-32")

    head = b[:200]
    if b"\x00" in head:
        try:
            return b.decode("utf-16")
        except UnicodeDecodeError:
            pass

    return b.decode("utf-8")


def _flatten_address(address_obj: Any) -> str:
    """Convert structured address object into a single human-readable line."""
    if not isinstance(address_obj, dict):
        return ""

    street = address_obj.get("street")
    house_number = address_obj.get("houseNumber")
    postal_code = address_obj.get("postalCode")
    city = address_obj.get("city")
    country = address_obj.get("country")

    parts: List[str] = []

    line1 = ""
    if street:
        if house_number:
            line1 = f"{street} {house_number}".strip()
        else:
            line1 = str(street).strip()
    if line1:
        parts.append(line1)

    line2 = ""
    if postal_code or city:
        line2 = " ".join([str(x).strip() for x in [postal_code, city] if x])
        line2 = line2.strip()
    if line2:
        parts.append(line2)

    if country:
        parts.append(str(country).strip())

    return ", ".join([p for p in parts if p])


def _build_fsm_payload_from_collateral(collateral: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build FSM-friendly payload from a single collateral record.

    Output matches `example_config.yaml` field expectations:
    - `collateral.nominalValueAmount` (int-like)
    - `real estate assets.address` (flattened str) + `realEstateType` (str)
    """
    nominal_value = collateral.get("nominalValueAmount")
    lending_value = collateral.get("lendingValueAmount")

    # Real estate assets: mortgageDeed.realestates[0]
    mortgage = collateral.get("mortgageDeed") or {}
    realestates = mortgage.get("realestates") or []
    re0 = realestates[0] if realestates else {}

    real_estate_type = re0.get("realEstateType")
    address_obj = re0.get("address") or {}
    address_str = _flatten_address(address_obj)

    payload: Dict[str, Any] = {}
    collateral_obj: Dict[str, Any] = {}
    if nominal_value is not None:
        collateral_obj["nominalValueAmount"] = nominal_value
    if lending_value is not None:
        collateral_obj["lendingValueAmount"] = lending_value
    payload["collateral"] = collateral_obj

    if address_str and real_estate_type is not None:
        payload["real estate assets"] = {
            "address": address_str,
            "realEstateType": real_estate_type,
        }
    else:
        payload["real estate assets"] = {}

    return payload


def run_over_all_collaterals(
    input_payload: InputPayload,
    engine: FSMEngine,
) -> List[Dict[str, Any]]:
    """Run FSM per collateral and flatten results with source_collateral_id."""
    collaterals = input_payload.extract_collaterals()

    flattened: List[Dict[str, Any]] = []
    for i, collateral in enumerate(collaterals):
        collateral_id = collateral.get("collateralId") or str(i)

        fsm_payload = _build_fsm_payload_from_collateral(collateral)
        report = engine.execute(fsm_payload)

        for item in report.get("most_current_data_list", []):
            item["source_collateral_id"] = collateral_id
            flattened.append(item)

    return flattened


def _as_number(x: Any) -> float:
    """Best-effort conversion to float for aggregation."""
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    try:
        # handle numeric strings, strip commas/currency symbols if present
        s = str(x).strip().replace(",", "")
        s = s.replace("$", "")
        return float(s)
    except Exception:
        return 0.0


def main() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Run declarative FSM over raw.json collaterals.")
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    parser.add_argument(
        "--input",
        default=script_dir / "raw.json",
        help="Path to raw.json (default: declarative_fsm/raw.json)",
    )
    parser.add_argument(
        "--output",
        default=project_root / "map_reduce" / "most_current_data_sample_data2.pkl",
        help="Output pickle path (default: map_reduce/most_current_data_sample_data2.pkl)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Load configuration
    print("\nLoading FSM config + canonical mappings...")
    config_path = script_dir / "example_config.yaml"
    canonical_config_path = script_dir / "canonical_config.yaml"

    config = load_config(str(config_path))
    engine = FSMEngine(config, canonical_config_path=str(canonical_config_path))

    # Load input JSON with robust decoder
    try:
        input_path_rel = input_path.relative_to(project_root)
    except ValueError:
        input_path_rel = input_path

    try:
        output_path_rel = output_path.relative_to(project_root)
    except ValueError:
        output_path_rel = output_path

    print(f"\nLoading input: {input_path_rel}")
    raw_bytes = input_path.read_bytes()
    if not raw_bytes:
        raise ValueError(f"Input file is empty: {input_path}")
    raw_text = _decode_json_bytes(raw_bytes)
    raw = json.loads(raw_text)

    input_payload = InputPayload.model_validate(raw)

    # Run-level metadata extracted from the input envelope
    generated_by = None
    if isinstance(input_payload.requester, dict):
        generated_by = input_payload.requester.get("tNumber")

    meta = {
        "requestId": input_payload.requestId,
        "language": "en",
        "generatedBy": generated_by,
    }

    print("\nRunning FSM over collaterals...")
    flattened = run_over_all_collaterals(input_payload, engine)

    # Run-level aggregation across all collaterals (Option A)
    collaterals = input_payload.extract_collaterals()
    total_nominal = sum(_as_number(c.get("nominalValueAmount")) for c in collaterals)
    total_lending = sum(_as_number(c.get("lendingValueAmount")) for c in collaterals)
    collateral_count = len(collaterals)

    flattened.append(
        {
            "field_name": "collateral_aggregation",
            "format": "table",
            "most_current_data": {
                "collateral_count": collateral_count,
                "total_nominalValueAmount": total_nominal,
                "total_lendingValueAmount": total_lending,
            },
            "eval_type": "llm",
            "metrics": [
                "score how readable it is",
                "score how complete the information is",
                "score how accurate the data appears",
            ],
            "source_collateral_id": "ALL",
        }
    )
    print(f"✓ Collaterals extracted: {len(input_payload.extract_collaterals())}")
    print(f"✓ Flattened items: {len(flattened)}")

    output_obj = {
        "meta": meta,
        "most_current_data_list": flattened,
    }

    # Persist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(output_obj, f)
    print(f"\n✓ Saved pickle: {output_path_rel}")

    return output_obj


if __name__ == "__main__":
    main()

