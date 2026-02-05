"""Pydantic models for InstructionIR and ChangeSet (source of truth schema)."""

import re
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


def validate_python_identifier(value: str) -> str:
    """Validate that a string is a valid Python identifier."""
    if not value or not value.replace("_", "").isalnum() or value[0].isdigit():
        raise ValueError(f"'{value}' is not a valid Python identifier")
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", value):
        raise ValueError(f"'{value}' is not a valid Python identifier")
    return value


class FieldSpec(BaseModel):
    """Specification for a single field in a model."""

    name: str
    type: str
    optional: bool = False
    default: Optional[Union[str, int, float, bool, None]] = None
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_python_identifier(v)


class ModelSpec(BaseModel):
    """Specification for an input or output model."""

    name: str
    fields: list[FieldSpec] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_python_identifier(v)


class ConstraintSpec(BaseModel):
    """Specification for a constraint (precondition, postcondition, or policy)."""

    kind: Literal["precondition", "postcondition", "policy"]
    expression: str
    message: Optional[str] = None


class StepSpec(BaseModel):
    """Specification for a semantic step in a method."""

    op: str
    params: dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
    description: Optional[str] = None


class ErrorSpec(BaseModel):
    """Specification for an error that a method may raise."""

    name: str
    message: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_python_identifier(v)


class AddClassChange(BaseModel):
    """Add a new class to the SDK."""

    kind: Literal["ADD_CLASS"] = "ADD_CLASS"
    class_name: str
    doc: Optional[str] = None

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        return validate_python_identifier(v)


class AddMethodChange(BaseModel):
    """Add a new method to an existing class."""

    kind: Literal["ADD_METHOD"] = "ADD_METHOD"
    class_name: str
    method_name: str
    inputs: ModelSpec
    outputs: ModelSpec
    doc: Optional[str] = None
    constraints: list[ConstraintSpec] = Field(default_factory=list)
    steps: list[StepSpec] = Field(default_factory=list)

    @field_validator("class_name", "method_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        return validate_python_identifier(v)


class ModifyMethodSignatureChange(BaseModel):
    """Modify an existing method's signature."""

    kind: Literal["MODIFY_METHOD_SIGNATURE"] = "MODIFY_METHOD_SIGNATURE"
    class_name: str
    method_name: str
    add_params: list[FieldSpec] = Field(default_factory=list)
    remove_params: list[str] = Field(default_factory=list)
    change_return: Optional[ModelSpec] = None
    doc_note: Optional[str] = None
    replace_doc_summary: bool = False
    new_doc_summary: Optional[str] = None

    @field_validator("class_name", "method_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        return validate_python_identifier(v)

    @field_validator("remove_params")
    @classmethod
    def validate_remove_params(cls, v: list[str]) -> list[str]:
        return [validate_python_identifier(p) for p in v]

    @field_validator("new_doc_summary")
    @classmethod
    def validate_new_doc_summary(cls, v: Optional[str], info) -> Optional[str]:
        if info.data.get("replace_doc_summary") and not v:
            raise ValueError("new_doc_summary is required when replace_doc_summary=true")
        return v


class AddConstraintChange(BaseModel):
    """Add a constraint to an existing method."""

    kind: Literal["ADD_CONSTRAINT"] = "ADD_CONSTRAINT"
    class_name: str
    method_name: str
    constraint: ConstraintSpec
    doc_note: Optional[str] = None

    @field_validator("class_name", "method_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        return validate_python_identifier(v)


class RenameChange(BaseModel):
    """Rename a class or method."""

    kind: Literal["RENAME"] = "RENAME"
    target_type: Literal["class", "method"]
    from_: str = Field(alias="from")
    to: str
    alias_old: bool = True
    doc_note: Optional[str] = None

    @field_validator("to")
    @classmethod
    def validate_to(cls, v: str) -> str:
        return validate_python_identifier(v.split(".")[-1])


class DeprecateChange(BaseModel):
    """Deprecate a class or method."""

    kind: Literal["DEPRECATE"] = "DEPRECATE"
    target_type: Literal["class", "method"]
    target: str
    message: Optional[str] = None
    doc_note: Optional[str] = None


# Discriminated union of all change types
Change = Union[
    AddClassChange,
    AddMethodChange,
    ModifyMethodSignatureChange,
    AddConstraintChange,
    RenameChange,
    DeprecateChange,
]


class ChangeSet(BaseModel):
    """Top-level container for a set of changes to apply to the SDK spec."""

    changes: list[Change] = Field(default_factory=list)


class InstructionIR(BaseModel):
    """Intermediate representation of an instruction (for future use)."""

    text: str
    changeset: ChangeSet
