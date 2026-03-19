"""
Pydantic models + filtering helpers for the large enterprise payload in
`declarative_fsm/sample_data2.json`.

Purpose:
- Validate the payload shape (permissively: extra fields allowed).
- Provide helpers to extract sections (starting with collaterals) into a shape
  that can eventually be fed into `FSMEngine.execute()`.

Decisions (per user):
- allow extra fields
- keep dates/timestamps as strings (do not parse into date/datetime)
- missing sections should yield empty lists (not validation errors)
"""

from __future__ import annotations

import argparse
import json
import codecs
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class _ExtraAllowedModel(BaseModel):
    """Base model that allows extra keys and doesn't coerce aggressively."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Address(_ExtraAllowedModel):
    street: Optional[str] = None
    houseNumber: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

    def to_single_line(self) -> str:
        parts: List[str] = []
        if self.street:
            if self.houseNumber:
                parts.append(f"{self.street} {self.houseNumber}".strip())
            else:
                parts.append(self.street)
        if self.postalCode or self.city:
            parts.append(" ".join([p for p in [self.postalCode, self.city] if p]).strip())
        if self.country:
            parts.append(self.country)
        return ", ".join([p for p in parts if p])


class RealEstate(_ExtraAllowedModel):
    realEstateId: Optional[str] = None
    realEstateType: Optional[str] = None
    marketValue: Optional[Any] = None
    marketValueDate: Optional[str] = None
    address: Optional[Address] = None


class MortgageDeed(_ExtraAllowedModel):
    mortgageDeedType: Optional[str] = None
    mortgageDeedSecuringType: Optional[str] = None
    realestates: Optional[List[RealEstate]] = None


class Collateral(_ExtraAllowedModel):
    collateralId: Optional[str] = None
    collateralType: Optional[str] = None
    collateralStatus: Optional[str] = None
    lendingValueAmount: Optional[Any] = None
    nominalValueAmount: Optional[Any] = None
    currency: Optional[str] = None
    mortgageDeed: Optional[MortgageDeed] = None


class BankingRelation(_ExtraAllowedModel):
    isMainBR: Optional[bool] = None
    bankingRelationNumber: Optional[str] = None
    collaterals: Optional[List[Collateral]] = None


class LegalEntity(_ExtraAllowedModel):
    entityType: Optional[str] = None
    organizationName: Optional[str] = None
    foundationDate: Optional[str] = None
    bankingRelations: Optional[List[BankingRelation]] = None


class InnerData(_ExtraAllowedModel):
    id: Optional[str] = None
    legalEntities: Optional[List[LegalEntity]] = None
    dataStatus: Optional[str] = None


class OuterData(_ExtraAllowedModel):
    data: Optional[InnerData] = None


class InputPayload(_ExtraAllowedModel):
    """
    Root model for `sample_data2.json`.
    """

    # Required top-level envelope fields
    requestId: str
    client: Dict[str, Any]
    requester: Dict[str, Any]
    data: OuterData

    # ----------------------------
    # Filtering / extraction APIs
    # ----------------------------
    def extract_collaterals(self) -> List[Dict[str, Any]]:
        """
        Extract `data.data.legalEntities[*].bankingRelations[*].collaterals[*]`.

        Returns:
            A list of dicts (raw-ish collateral records) suitable for downstream
            mapping into FSM fields. Missing sections return [].
        """
        out: List[Dict[str, Any]] = []

        inner = self.data.data if self.data and self.data.data else None
        if not inner or not inner.legalEntities:
            return out

        for le in inner.legalEntities:
            if not le.bankingRelations:
                continue
            for br in le.bankingRelations:
                if not br.collaterals:
                    continue
                for c in br.collaterals:
                    out.append(c.model_dump(exclude_none=True))

        return out

    def to_fsm_input(self) -> Dict[str, Any]:
        """
        Create an FSMEngine-friendly dict.

        Today: produce a minimal shape centered around the first collateral, to
        align with the existing example FSM field `collateral`:
          - collateral.nominalValueAmount <- nominalValueAmount (fallback lendingValueAmount)

        Also includes:
          - collaterals: list of all extracted collaterals (for future strategies)
          - real estate assets: derived from first collateral's first real estate (if present)

        Missing sections yield empty lists / empty dicts.
        """
        collaterals = self.extract_collaterals()

        collateral_field: Dict[str, Any] = {}
        real_estate_assets_field: Dict[str, Any] = {}

        if collaterals:
            first = collaterals[0]
            collateral_field = {
                # FSM expects camelCase key from sample_data2.json
                "nominalValueAmount": first.get("nominalValueAmount", first.get("lendingValueAmount")),
            }

            # Try to derive real estate assets from mortgage deed
            mortgage = first.get("mortgageDeed") or {}
            realestates = mortgage.get("realestates") or []
            if realestates:
                re0 = realestates[0]
                addr = re0.get("address") or {}
                # If address is structured, keep a simple human-readable string too.
                address_str = ""
                if isinstance(addr, dict):
                    address_str = ", ".join(
                        [p for p in [
                            " ".join([x for x in [addr.get("street"), addr.get("houseNumber")] if x]).strip(),
                            " ".join([x for x in [addr.get("postalCode"), addr.get("city")] if x]).strip(),
                            addr.get("country"),
                        ] if p]
                    )
                real_estate_assets_field = {
                    "address": address_str or None,
                    # FSM expects camelCase key from sample_data2.json
                    "realEstateType": re0.get("realEstateType"),
                }

        return {
            # Existing FSM field names (from example_config.yaml)
            "collateral": {k: v for k, v in collateral_field.items() if v is not None},
            "real estate assets": {k: v for k, v in real_estate_assets_field.items() if v is not None},
            # Additional extracted section for future use
            "collaterals": collaterals,
        }


def _main() -> int:
    parser = argparse.ArgumentParser(description="Validate and filter sample_data2.json using InputPayload.")
    parser.add_argument(
        "--input",
        default="declarative_fsm/sample_data2.json",
        help="Path to input JSON (default: declarative_fsm/sample_data2.json)",
    )
    parser.add_argument(
        "--mode",
        choices=["collaterals", "fsm"],
        default="collaterals",
        help="What to print: collaterals-only list, or FSM-shaped dict (default: collaterals)",
    )
    args = parser.parse_args()

    def _decode_json_bytes(b: bytes) -> str:
        """
        Decode JSON bytes into text, handling common encodings (utf-8/utf-16 with BOM).
        """
        # BOM-based detection first
        if b.startswith(codecs.BOM_UTF8):
            return b.decode("utf-8-sig")
        if b.startswith(codecs.BOM_UTF16_LE) or b.startswith(codecs.BOM_UTF16_BE):
            return b.decode("utf-16")
        if b.startswith(codecs.BOM_UTF32_LE) or b.startswith(codecs.BOM_UTF32_BE):
            return b.decode("utf-32")

        # Heuristic: lots of NUL bytes usually means utf-16 without BOM
        head = b[:200]
        if b"\x00" in head:
            # Try utf-16 first (most common on Windows)
            try:
                return b.decode("utf-16")
            except UnicodeDecodeError:
                pass

        # Default: utf-8 (no BOM)
        return b.decode("utf-8")

    try:
        with open(args.input, "rb") as f:
            raw_bytes = f.read()
        if not raw_bytes:
            raise ValueError(f"Input file is empty: {args.input}")
        raw_text = _decode_json_bytes(raw_bytes)
        raw = json.loads(raw_text)
    except FileNotFoundError as e:
        print(f"Error: input file not found: {args.input}")
        raise e
    except ValueError as e:
        # e.g., empty file
        print(f"Error: {e}")
        raise e
    except json.JSONDecodeError as e:
        size = len(raw_bytes) if "raw_bytes" in locals() else 0
        preview = raw_text[:80].replace("\n", "\\n").replace("\r", "\\r") if "raw_text" in locals() else ""
        bytes_preview = (raw_bytes[:40] if "raw_bytes" in locals() else b"")
        print(f"Error: failed to parse JSON from: {args.input}")
        print(f"  File size (bytes): {size}")
        print(f"  JSONDecodeError: {e}")
        print(f"  First 40 bytes: {bytes_preview!r}")
        print(f"  First 80 chars: {preview!r}")
        raise e

    payload = InputPayload.model_validate(raw)

    if args.mode == "collaterals":
        print(json.dumps(payload.extract_collaterals(), indent=2))
    else:
        print(json.dumps(payload.to_fsm_input(), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

