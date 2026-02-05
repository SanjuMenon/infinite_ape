"""Persistence and replay functionality for spec and patch log."""

import json
from pathlib import Path
from typing import Any

from instruction_sdk_compiler.spec.model import SdkSpec, ClassSpec
from instruction_sdk_compiler.patching.apply import PatchRecord


def save_spec(spec: SdkSpec, patch_log: list[PatchRecord], output_dir: str) -> None:
    """
    Save spec and patch log to disk.
    
    Args:
        spec: The SDK specification
        patch_log: List of patch records
        output_dir: Directory to save to
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Serialize spec to JSON-friendly form using Pydantic's model_dump()
    spec_dict = spec.model_dump()
    (output_path / "spec.json").write_text(json.dumps(spec_dict, indent=2, default=str))
    
    # Save patch log
    patch_log_dict = [record.to_dict() for record in patch_log]
    (output_path / "patch_log.json").write_text(json.dumps(patch_log_dict, indent=2))


def load_spec(output_dir: str) -> tuple[SdkSpec, list[PatchRecord]]:
    """
    Load spec and patch log from disk.
    
    Args:
        output_dir: Directory to load from
        
    Returns:
        Tuple of (SdkSpec, list of PatchRecord)
    """
    output_path = Path(output_dir)
    
    # Load spec
    spec_file = output_path / "spec.json"
    if not spec_file.exists():
        # Return empty spec if no saved spec
        spec = SdkSpec(version="1.0.0")
        return spec, []
    
    spec_dict = json.loads(spec_file.read_text())
    spec = SdkSpec.model_validate(spec_dict)
    
    # Load patch log
    patch_log_file = output_path / "patch_log.json"
    patch_log = []
    if patch_log_file.exists():
        patch_log_dict = json.loads(patch_log_file.read_text())
        patch_log = [PatchRecord.from_dict(record) for record in patch_log_dict]
    
    return spec, patch_log


def replay_patches(
    initial_spec: SdkSpec, patch_log: list[PatchRecord], up_to: int | None = None
) -> SdkSpec:
    """
    Replay patch log to rebuild spec.
    
    Args:
        initial_spec: Initial clean spec
        patch_log: List of patch records to replay
        up_to: Replay up to this many patches (None = all)
        
    Returns:
        Rebuilt SdkSpec
    """
    from instruction_sdk_compiler.patching.apply import apply_changeset
    from instruction_sdk_compiler.parser.ir import ChangeSet
    
    # Create a copy of the initial spec using Pydantic's model_copy()
    spec = initial_spec.model_copy(deep=True)
    
    # Apply patches up to the specified index
    patches_to_apply = patch_log[:up_to] if up_to is not None else patch_log
    
    for record in patches_to_apply:
        changeset_dict = json.loads(record.changeset_json)
        changeset = ChangeSet.model_validate(changeset_dict)
        _, spec = apply_changeset(spec, changeset, record.instruction_text)
    
    return spec
