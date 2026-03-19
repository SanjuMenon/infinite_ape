"""
Pydantic models for declarative_fsm sample data.

These models are intentionally permissive (extra fields allowed) because the
FSM is designed to be driven by YAML-defined strategies/handlers rather than a
fixed schema.

Key goals:
- Validate that sample_data.json is structurally a dict with expected top-level keys.
- Support JSON keys that are not valid Python identifiers via aliases
  (e.g. "real estate assets", "Financials").
- Preserve values as-provided (no coercion of numeric strings), so handler logic
  (e.g., validate_type) continues to be the source of truth for transformations.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class _ExtraAllowedModel(BaseModel):
    """Base model: allow extra keys and allow populating via aliases."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Collateral(_ExtraAllowedModel):
    nominalValueAmount: Optional[Any] = None  # handlers decide typing


class RealEstateAssets(_ExtraAllowedModel):
    address: Optional[str] = None
    realEstateType: Optional[str] = None


class Financials(_ExtraAllowedModel):
    # Known keys used by example_config.yaml
    net_sales: Optional[Any] = None
    ebitda: Optional[Any] = None

    # Allow dynamic keys like year_1/year_2/... or other nested items
    # via extra="allow" on the base model.


class FinancialsDebt(_ExtraAllowedModel):
    # Keep permissive: sample_data.json currently uses ints for these.
    YEAR: Optional[Any] = None
    ER12: Optional[Any] = None
    ER32: Optional[Any] = None
    P88: Optional[Any] = None
    EM06: Optional[Any] = None
    ER13: Optional[Any] = None
    ER41: Optional[Any] = None
    P19: Optional[Any] = None
    P14: Optional[Any] = None
    P03: Optional[Any] = None
    P20: Optional[Any] = None


class SampleData(_ExtraAllowedModel):
    """
    Root model for sample_data.json.

    Uses aliases to support JSON keys that include spaces/case.
    """

    # Metadata fields (top-level)
    request_id: Optional[str] = Field(default=None, alias="requestId")
    language: Optional[str] = Field(default="en")
    generated_by: Optional[str] = Field(default="map_reduce", alias="generatedBy")
    generated_at: Optional[str] = Field(default=None, alias="generatedAt")
    
    # Business data fields
    collateral: Optional[Collateral] = None
    real_estate_assets: Optional[RealEstateAssets] = Field(default=None, alias="real estate assets")
    financials: Optional[Financials] = Field(default=None, alias="Financials")
    financials_debt: Optional[FinancialsDebt] = None

    def to_engine_dict(self) -> Dict[str, Any]:
        """
        Dump a plain dict suitable for FSMEngine.execute().

        We intentionally keep aliases (original JSON keys) so the engine/handlers
        can continue using field names like "Financials" and "real estate assets".
        Excludes metadata fields as they're not part of the business data.
        """
        result = self.model_dump(by_alias=True, exclude_none=True)
        # Remove metadata fields from engine dict as they're not business data
        result.pop("requestId", None)
        result.pop("language", None)
        result.pop("generatedBy", None)
        result.pop("generatedAt", None)
        return result

