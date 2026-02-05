"""Base service class."""

from abc import ABC
from generated_sdk.runtime.registry import CapabilityRegistry


class BaseService(ABC):
    """Base class for all services."""
    
    def __init__(self, registry: CapabilityRegistry):
        """Initialize base service."""
        self._registry = registry
