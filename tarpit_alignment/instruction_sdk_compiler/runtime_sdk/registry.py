"""Capability registry for runtime SDK."""

from typing import Callable, Any, Optional


class CapabilityRegistry:
    """Registry for registering and looking up capabilities."""
    
    def __init__(self):
        """Initialize registry."""
        self._capabilities: dict[str, Callable] = {}
    
    def register(self, name: str, callable: Callable) -> None:
        """Register a capability."""
        self._capabilities[name] = callable
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a capability by name."""
        return self._capabilities.get(name)
    
    def list_all(self) -> list[str]:
        """List all registered capabilities."""
        return list(self._capabilities.keys())
