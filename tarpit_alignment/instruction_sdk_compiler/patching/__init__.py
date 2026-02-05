"""Patching module for applying ChangeSets to Pydantic specs in-place."""

from instruction_sdk_compiler.patching.apply import apply_changeset, PatchRecord

__all__ = ["apply_changeset", "PatchRecord"]
