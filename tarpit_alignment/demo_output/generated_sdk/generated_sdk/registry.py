"""Capability registry for SDK."""

from typing import Callable, Any, Dict
from generated_sdk.runtime.registry import CapabilityRegistry as BaseCapabilityRegistry


class CapabilityRegistry(BaseCapabilityRegistry):
    """Registry for SDK capabilities."""
    
    def __init__(self):
        """Initialize registry."""
        super().__init__()
