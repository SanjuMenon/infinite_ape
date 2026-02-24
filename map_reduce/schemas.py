from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


BundleValue = Literal["freeform", "table"]


class Bundle(BaseModel):
    """A structured input unit.

    Notes:
    - `bundle_name` is used for aggregation headings (e.g. "collateral").
    - `value` selects the summarizer behavior ("freeform" vs "table").
    - The rest of the payload is intentionally flexible for now.
    """

    bundle_name: str = Field(..., min_length=1)
    value: BundleValue

    # Flexible payload fields (examples from your prints)
    required_fields_found: Optional[List[str]] = None
    field_data: Optional[Dict[str, Any]] = None
    canonical_data: Optional[Dict[str, Any]] = None
    format_check_source: Optional[str] = None
    format_validated: Optional[bool] = None
    validated_fields: Optional[List[str]] = None
    length_validated: Optional[bool] = None
    field_count: Optional[int] = None
    validated_field_count: Optional[int] = None

    # allow future keys without schema churn
    model_config = {"extra": "allow"}


class OutputSectionSchema(BaseModel):
    """Defines ordering and hierarchy for the final report.

    No formatting rules—just structure (sections/subsections) and ordering.
    """

    name: str = Field(..., min_length=1)
    bundle_names: List[str] = Field(default_factory=list)
    subsections: List["OutputSectionSchema"] = Field(default_factory=list)


class OutputSchema(BaseModel):
    title: str = "Bundle Report"
    sections: List[OutputSectionSchema] = Field(default_factory=list)


class BundleConfig(BaseModel):
    """Placeholder for future per-bundle-type configuration.

    We keep it intentionally permissive for now; you’ll extend it as splitting logic evolves.
    """

    bundle_types: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

