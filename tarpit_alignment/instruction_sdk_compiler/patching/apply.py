"""Apply ChangeSet to Pydantic spec in-place."""

import json
from datetime import datetime
from typing import Any

from instruction_sdk_compiler.parser.ir import ChangeSet
from instruction_sdk_compiler.spec.model import (
    SdkSpec,
    ClassSpec,
    MethodSpec,
    ModelSpec,
    FieldSpec,
    ConstraintSpec,
    StepSpec,
    ErrorSpec,
)


class PatchRecord:
    """Record of a patch application."""

    def __init__(
        self,
        timestamp: str,
        instruction_text: str | None,
        changeset_json: str,
        applied_patch_summary: str,
        spec_version_before: str,
        spec_version_after: str,
    ):
        self.timestamp = timestamp
        self.instruction_text = instruction_text
        self.changeset_json = changeset_json
        self.applied_patch_summary = applied_patch_summary
        self.spec_version_before = spec_version_before
        self.spec_version_after = spec_version_after

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "instruction_text": self.instruction_text,
            "changeset_json": self.changeset_json,
            "applied_patch_summary": self.applied_patch_summary,
            "spec_version_before": self.spec_version_before,
            "spec_version_after": self.spec_version_after,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatchRecord":
        """Create from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            instruction_text=data.get("instruction_text"),
            changeset_json=data["changeset_json"],
            applied_patch_summary=data["applied_patch_summary"],
            spec_version_before=data["spec_version_before"],
            spec_version_after=data["spec_version_after"],
        )


def _convert_field_spec(ir_field) -> FieldSpec:
    """Convert parser FieldSpec to spec FieldSpec."""
    return FieldSpec(
        name=ir_field.name,
        type=ir_field.type,
        optional=ir_field.optional,
        default=ir_field.default,
        description=ir_field.description or "",
    )


def _convert_model_spec(ir_model) -> ModelSpec:
    """Convert parser ModelSpec to spec ModelSpec."""
    # Create ModelSpec - if no fields, create with None (will be initialized when first field is added)
    if not ir_model.fields:
        model_spec = ModelSpec(name=ir_model.name, fields=None)
    else:
        # Create regular dict - Pydantic handles it fine
        fields_dict = {}
        for field in ir_model.fields:
            fields_dict[field.name] = _convert_field_spec(field)
        model_spec = ModelSpec(name=ir_model.name, fields=fields_dict)
    return model_spec


def _convert_constraint_spec(ir_constraint) -> ConstraintSpec:
    """Convert parser ConstraintSpec to spec ConstraintSpec."""
    return ConstraintSpec(
        kind=ir_constraint.kind,
        expression=ir_constraint.expression,
        message=ir_constraint.message or "",
    )


def _convert_step_spec(ir_step) -> StepSpec:
    """Convert parser StepSpec to spec StepSpec."""
    # Pass dict directly - Pydantic handles it fine
    return StepSpec(
        op=ir_step.op,
        params=ir_step.params,
        description=ir_step.description or "",
    )


def _add_doc_note(obj: ClassSpec | MethodSpec, note: str | None) -> None:
    """Add a doc note to a class or method, bounding to last 10."""
    if note:
        notes = list(obj.doc_notes) if obj.doc_notes else []
        notes.append(f"[{datetime.now().isoformat()}] {note}")
        # Bound to last 10 - direct assignment works with Pydantic
        obj.doc_notes = notes[-10:]


def _ensure_spec_initialized(spec: SdkSpec) -> None:
    """Ensure spec dict/list fields are initialized (not None)."""
    # With Pydantic, we can initialize empty dicts directly
    if spec.classes is None:
        spec.classes = {}
    if spec.metadata is None:
        spec.metadata = {}


def _ensure_model_spec_initialized(model_spec: ModelSpec) -> None:
    """Ensure ModelSpec fields dict is initialized (not None)."""
    # With Pydantic, we can initialize empty dicts directly
    if model_spec.fields is None:
        model_spec.fields = {}


def _ensure_class_initialized(class_spec: ClassSpec) -> None:
    """Ensure class dict/list fields are initialized (not None)."""
    # With Pydantic, we can initialize empty dicts/lists directly
    if class_spec.methods is None:
        class_spec.methods = {}
    if class_spec.doc_notes is None:
        class_spec.doc_notes = []
    if class_spec.aliases is None:
        class_spec.aliases = []


def _ensure_method_initialized(method_spec: MethodSpec) -> None:
    """Ensure method list fields are initialized (not None)."""
    # With Pydantic, we can initialize empty lists directly
    if method_spec.doc_notes is None:
        method_spec.doc_notes = []
    if method_spec.errors is None:
        method_spec.errors = []
    if method_spec.semantics_steps is None:
        method_spec.semantics_steps = []
    if method_spec.constraints is None:
        method_spec.constraints = []
    if method_spec.aliases is None:
        method_spec.aliases = []


def apply_changeset(
    spec: SdkSpec, changeset: ChangeSet, instruction_text: str | None = None
) -> tuple[PatchRecord, SdkSpec]:
    """
    Apply a ChangeSet to the spec. Returns new spec if mutation needed.
    
    Args:
        spec: The Pydantic SdkSpec to mutate
        instruction_text: Optional instruction text for the patch record
        
    Returns:
        Tuple of (PatchRecord documenting the changes, updated SdkSpec)
    """
    spec_id_before = id(spec)
    version_before = spec.version
    spec_was_cloned = False
    
    # Ensure spec is initialized
    _ensure_spec_initialized(spec)
    
    summary_parts = []
    
    for change in changeset.changes:
        if change.kind == "ADD_CLASS":
            if spec.classes and change.class_name in spec.classes:
                raise ValueError(f"Class {change.class_name} already exists")
            
            # Create class - methods will be initialized when we add first method
            class_spec = ClassSpec(
                name=change.class_name,
                doc_summary=change.doc or f"{change.class_name} service generated from instruction specs.",
                doc_notes=[],
                methods=None,  # Will be initialized when first method is added
                aliases=[],
            )
            # With Pydantic, we can directly assign to dict fields
            if spec.classes is None:
                spec.classes = {change.class_name: class_spec}
            else:
                spec.classes[change.class_name] = class_spec
            summary_parts.append(f"Added class {change.class_name}")
        
        elif change.kind == "ADD_METHOD":
            if not spec.classes or change.class_name not in spec.classes:
                raise ValueError(f"Class {change.class_name} does not exist")
            
            class_spec = spec.classes[change.class_name]
            if class_spec.methods and change.method_name in class_spec.methods:
                raise ValueError(
                    f"Method {change.class_name}.{change.method_name} already exists"
                )
            
            method_spec = MethodSpec(
                name=change.method_name,
                doc_summary=change.doc or f"{change.method_name} method",
                doc_notes=[],
                inputs=_convert_model_spec(change.inputs),
                outputs=_convert_model_spec(change.outputs),
                errors=[],
                semantics_steps=[_convert_step_spec(s) for s in change.steps],
                constraints=[_convert_constraint_spec(c) for c in change.constraints],
                deprecated=False,
                aliases=[],
            )
            # Add method - with Pydantic, we can directly assign to dict fields
            if class_spec.methods is None:
                class_spec.methods = {change.method_name: method_spec}
            else:
                class_spec.methods[change.method_name] = method_spec
            summary_parts.append(f"Added method {change.class_name}.{change.method_name}")
        
        elif change.kind == "MODIFY_METHOD_SIGNATURE":
            if not spec.classes or change.class_name not in spec.classes:
                raise ValueError(f"Class {change.class_name} does not exist")
            
            class_spec = spec.classes[change.class_name]
            if not class_spec.methods or change.method_name not in class_spec.methods:
                raise ValueError(
                    f"Method {change.class_name}.{change.method_name} does not exist"
                )
            
            method_spec = class_spec.methods[change.method_name]
            _ensure_method_initialized(method_spec)
            
            # Update inputs: add new params, remove old ones
            # Get current fields (may be None)
            new_fields = dict(method_spec.inputs.fields) if method_spec.inputs.fields else {}
            
            # Remove params
            for param_name in change.remove_params:
                if param_name in new_fields:
                    del new_fields[param_name]
            
            # Add params
            for field in change.add_params:
                new_fields[field.name] = _convert_field_spec(field)
            
            # Update fields - with Pydantic, we can directly assign
            if new_fields:
                method_spec.inputs.fields = new_fields
            else:
                method_spec.inputs.fields = {}
            
            # Update return type if specified
            if change.change_return:
                method_spec.outputs = _convert_model_spec(change.change_return)
            
            # Update doc
            if change.replace_doc_summary and change.new_doc_summary:
                method_spec.doc_summary = change.new_doc_summary
            
            _add_doc_note(method_spec, change.doc_note or "Method signature modified")
            summary_parts.append(f"Modified {change.class_name}.{change.method_name}")
        
        elif change.kind == "ADD_CONSTRAINT":
            if not spec.classes or change.class_name not in spec.classes:
                raise ValueError(f"Class {change.class_name} does not exist")
            
            class_spec = spec.classes[change.class_name]
            if not class_spec.methods or change.method_name not in class_spec.methods:
                raise ValueError(
                    f"Method {change.class_name}.{change.method_name} does not exist"
                )
            
            method_spec = class_spec.methods[change.method_name]
            constraints = list(method_spec.constraints) if method_spec.constraints else []
            constraints.append(_convert_constraint_spec(change.constraint))
            method_spec.constraints = constraints
            _add_doc_note(method_spec, change.doc_note or "Added constraint")
            summary_parts.append(f"Added constraint to {change.class_name}.{change.method_name}")
        
        elif change.kind == "RENAME":
            if change.target_type == "class":
                old_name = change.from_
                new_name = change.to
                if not spec.classes or old_name not in spec.classes:
                    raise ValueError(f"Class {old_name} does not exist")
                
                class_spec = spec.classes[old_name]
                class_spec.name = new_name
                
                # Update classes dict
                classes_dict = dict(spec.classes)
                classes_dict[new_name] = classes_dict.pop(old_name)
                spec.classes = classes_dict
                
                # Handle alias
                if change.alias_old:
                    aliases = list(class_spec.aliases) if class_spec.aliases else []
                    aliases.append(old_name)
                    class_spec.aliases = aliases
                    # Also add old name back to classes dict as alias
                    classes_dict[old_name] = class_spec
                    spec.classes = classes_dict
                
                _add_doc_note(class_spec, change.doc_note or f"Renamed from {old_name}")
                summary_parts.append(f"Renamed class {old_name} -> {new_name}")
            
            else:  # method
                parts = change.from_.split(".")
                if len(parts) != 2:
                    raise ValueError(f"Invalid method target format: {change.from_}")
                class_name, old_method_name = parts
                new_method_name = change.to
                
                if not spec.classes or class_name not in spec.classes:
                    raise ValueError(f"Class {class_name} does not exist")
                
                class_spec = spec.classes[class_name]
                if not class_spec.methods or old_method_name not in class_spec.methods:
                    raise ValueError(f"Method {class_name}.{old_method_name} does not exist")
                
                method_spec = class_spec.methods[old_method_name]
                method_spec.name = new_method_name
                
                # Update methods dict
                methods_dict = dict(class_spec.methods)
                methods_dict[new_method_name] = methods_dict.pop(old_method_name)
                class_spec.methods = methods_dict
                
                # Handle alias
                if change.alias_old:
                    _ensure_method_initialized(method_spec)
                    aliases = list(method_spec.aliases) if method_spec.aliases else []
                    aliases.append(old_method_name)
                    method_spec.aliases = aliases
                    # Also add old name back to methods dict as alias
                    methods_dict[old_method_name] = method_spec
                    class_spec.methods = methods_dict
                
                _add_doc_note(method_spec, change.doc_note or f"Renamed from {old_method_name}")
                summary_parts.append(f"Renamed method {change.from_} -> {new_method_name}")
        
        elif change.kind == "DEPRECATE":
            if change.target_type == "class":
                target = change.target
                if not spec.classes or target not in spec.classes:
                    raise ValueError(f"Class {target} does not exist")
                
                class_spec = spec.classes[target]
                class_spec.deprecated = True
                _add_doc_note(class_spec, change.doc_note or f"Deprecated: {change.message or ''}")
                summary_parts.append(f"Deprecated class {target}")
            
            else:  # method
                parts = change.target.split(".")
                if len(parts) != 2:
                    raise ValueError(f"Invalid method target format: {change.target}")
                class_name, method_name = parts
                
                if not spec.classes or class_name not in spec.classes:
                    raise ValueError(f"Class {class_name} does not exist")
                
                class_spec = spec.classes[class_name]
                if not class_spec.methods or method_name not in class_spec.methods:
                    raise ValueError(f"Method {class_name}.{method_name} does not exist")
                
                method_spec = class_spec.methods[method_name]
                method_spec.deprecated = True
                _add_doc_note(method_spec, change.doc_note or f"Deprecated: {change.message or ''}")
                summary_parts.append(f"Deprecated method {change.target}")
    
    # Increment version
    version_parts = version_before.split(".")
    if len(version_parts) == 3:
        try:
            patch = int(version_parts[2])
            version_after = f"{version_parts[0]}.{version_parts[1]}.{patch + 1}"
        except ValueError:
            version_after = version_before
    else:
        version_after = version_before
    
    spec.version = version_after
    
    patch_record = PatchRecord(
        timestamp=datetime.now().isoformat(),
        instruction_text=instruction_text,
        changeset_json=json.dumps(changeset.model_dump(), indent=2),
        applied_patch_summary="; ".join(summary_parts) if summary_parts else "No changes",
        spec_version_before=version_before,
        spec_version_after=version_after,
    )
    
    return patch_record, spec