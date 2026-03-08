from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


BundleValue = Literal["freeform", "table"]


class Bundle(BaseModel):
    """A structured input unit.

    Notes:
    - `field_name` is used for aggregation headings (e.g. "collateral").
    - `format` selects the summarizer behavior ("freeform" vs "table").
    - The rest of the payload is intentionally flexible for now.
    """

    field_name: str = Field(..., min_length=1)
    format: BundleValue = Field(...)  # Required: "freeform" or "table"
    most_current_data: Dict[str, Any] = Field(...)  # Required field - always used for LLM summarization
    
    # Evaluation fields
    eval_type: Optional[str] = None  # e.g., "llm" - triggers evaluation if not None
    metrics: Optional[List[str]] = None  # List of metrics to evaluate (e.g., ["readability", "completeness"])

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
    field_names: List[str] = Field(default_factory=list)
    subsections: List["OutputSectionSchema"] = Field(default_factory=list)


class OutputSchema(BaseModel):
    title: str = "Bundle Report"
    sections: List[OutputSectionSchema] = Field(default_factory=list)


class BundleTypeConfig(BaseModel):
    """Configuration for a single bundle type."""
    field_name: str = Field(..., min_length=1)
    section_title: str = Field(..., min_length=1)
    order: int = Field(..., ge=0)  # Order in the report (0 = first)
    display_name: Optional[str] = None  # Optional display name for the report heading (defaults to field_name)


class BundleConfig(BaseModel):
    """Configuration for bundle ordering and section titles in the final report.
    
    Defines the order of bundles and which section title each bundle should appear under.
    """
    bundle_order: List[BundleTypeConfig] = Field(default_factory=list)

