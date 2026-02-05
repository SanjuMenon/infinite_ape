"""Base service class and exceptions."""

from abc import ABC
from instruction_sdk_compiler.runtime_sdk.registry import CapabilityRegistry


class SDKError(Exception):
    """Base exception for SDK errors."""
    pass


class ServiceNotFoundError(SDKError):
    """Raised when a service is not found."""
    pass


class MethodNotFoundError(SDKError):
    """Raised when a method is not found."""
    pass


class BaseService(ABC):
    """Base class for all services."""
    
    def __init__(self, registry: CapabilityRegistry):
        """Initialize base service."""
        self._registry = registry
