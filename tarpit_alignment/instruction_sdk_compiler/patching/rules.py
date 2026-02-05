"""Helper functions for building patch rules and safe path operations."""

from typing import Any
from pydantic import BaseModel


def build_rebind_updates(changeset, spec) -> dict:
    """
    Build a dictionary of updates for applying changeset.
    
    This is a helper that converts changeset changes into update-compatible
    path->value mappings. The actual application uses direct assignment.
    
    Note: This function is mainly for documentation. The actual patching
    logic in apply.py directly mutates the spec using assignment.
    """
    updates = {}
    # This is a placeholder - actual logic is in apply.py
    return updates


def safe_get_path(spec: BaseModel, path: str, default: Any = None) -> Any:
    """
    Safely get a value from a Pydantic object by path.
    
    Args:
        spec: Pydantic object
        path: Dot-separated path (e.g., "classes.UserService.methods.create_user")
        default: Default value if path doesn't exist
        
    Returns:
        Value at path or default
    """
    parts = path.split(".")
    current = spec
    for part in parts:
        if not hasattr(current, part):
            return default
        current = getattr(current, part)
        if current is None:
            return default
    return current


def ensure_path_exists(spec: BaseModel, path: str, create_default: Any = None) -> None:
    """
    Ensure a path exists in the spec, creating intermediate objects if needed.
    
    Args:
        spec: Pydantic object
        path: Dot-separated path
        create_default: Default value to create if path doesn't exist
    """
    parts = path.split(".")
    current = spec
    for i, part in enumerate(parts[:-1]):
        if not hasattr(current, part):
            setattr(current, part, create_default if i == len(parts) - 2 else {})
        current = getattr(current, part)
        if current is None:
            setattr(current, part, create_default if i == len(parts) - 2 else {})
            current = getattr(current, part)
