"""Pydantic spec classes for SDK specification."""

from typing import Any
from pydantic import BaseModel, Field


class FieldSpec(BaseModel):
    """Field specification in a model."""

    name: str
    type: str
    optional: bool = False
    default: Any = None
    description: str = ""


class ModelSpec(BaseModel):
    """Model specification (input or output)."""

    name: str
    fields: dict[str, FieldSpec] | None = Field(default=None)  # Optional - will be set to empty dict if None


class ConstraintSpec(BaseModel):
    """Constraint specification."""

    kind: str  # "precondition" | "postcondition" | "policy"
    expression: str
    message: str = ""


class StepSpec(BaseModel):
    """Semantic step specification."""

    op: str
    params: dict[str, Any] | None = Field(default=None)  # Optional - will be set to empty dict if None
    description: str = ""


class ErrorSpec(BaseModel):
    """Error specification."""

    name: str
    message: str


class MethodSpec(BaseModel):
    """Method specification."""

    name: str
    doc_summary: str = ""
    doc_notes: list[str] | None = Field(default=None)  # Optional - will be set to empty list if None
    inputs: ModelSpec
    outputs: ModelSpec
    errors: list[ErrorSpec] | None = Field(default=None)  # Optional - will be set to empty list if None
    semantics_steps: list[StepSpec] | None = Field(default=None)  # Optional - will be set to empty list if None
    constraints: list[ConstraintSpec] | None = Field(default=None)  # Optional - will be set to empty list if None
    deprecated: bool = False
    aliases: list[str] | None = Field(default=None)  # Optional - will be set to empty list if None


class ClassSpec(BaseModel):
    """Class specification."""

    name: str
    doc_summary: str = ""
    doc_notes: list[str] | None = Field(default=None)  # Optional - will be set to empty list if None
    methods: dict[str, MethodSpec] | None = Field(default=None)  # Optional - will be set to empty dict if None
    deprecated: bool = False
    aliases: list[str] | None = Field(default=None)  # Optional - will be set to empty list if None


class SdkSpec(BaseModel):
    """Top-level SDK specification."""

    classes: dict[str, ClassSpec] | None = Field(default=None)  # Optional - will be set to empty dict if None
    version: str = "1.0.0"
    metadata: dict[str, Any] | None = Field(default=None)  # Optional - will be set to empty dict if None
