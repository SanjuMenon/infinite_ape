from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Bundle(BaseModel):
    """Minimal unit of work for the map-reduce pipeline.

    - `field_name`: section identifier (e.g. "collateral", "business_model")
    - `prompt`: prompt text to apply; when it equals the sentinel value, the section is passed through without LLM
    - `payload`: a string payload; typically a JSON string for LLM, or markdown table for passthrough
    """

    field_name: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=0)
    payload: str = Field(..., min_length=0)


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

