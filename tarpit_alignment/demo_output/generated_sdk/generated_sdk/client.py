"""Client front door for generated SDK."""

from typing import Any
from generated_sdk.registry import CapabilityRegistry
from generated_sdk.services.userservice import UserService
from generated_sdk.services.invoiceservice import InvoiceService

    userservice: UserService
    invoiceservice: InvoiceService


class Client:
    """Main client for accessing SDK services.
    
    Provides attribute-based access to services:
        client.user_service.create_user(...)
    
    Also supports string-based dispatch:
        client.call("UserService.create_user", **kwargs)
    """
    
    def __init__(self):
        """Initialize client with all services."""
        self._registry = CapabilityRegistry()
        self.userservice = UserService(registry=self._registry)
        self.invoiceservice = InvoiceService(registry=self._registry)
        self._register_capabilities()
    
    def _register_capabilities(self):
        """Register all capabilities with the registry."""
        # Capabilities are registered by service instances
        pass
    
    def call(self, capability: str, **kwargs) -> Any:
        """
        Call a capability by string name.
        
        Args:
            capability: Capability name in format "ClassName.method_name"
            **kwargs: Arguments to pass to the method
            
        Returns:
            Method result
        """
        parts = capability.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid capability format: {capability}")
        
        class_name, method_name = parts
        service_name = class_name.lower()
        
        if not hasattr(self, service_name):
            raise ValueError(f"Service {class_name} not found")
        
        service = getattr(self, service_name)
        if not hasattr(service, method_name):
            raise ValueError(f"Method {method_name} not found on {class_name}")
        
        method = getattr(service, method_name)
        return method(**kwargs)
    
    def list_capabilities(self) -> list[str]:
        """
        List all available capabilities.
        
        Returns:
            List of capability names in format "ClassName.method_name"
        """
        capabilities = []
        capabilities.append("UserService.create_user")
        capabilities.append("InvoiceService.create_invoice")
        return capabilities
    
    def describe(self, capability: str) -> dict:
        """
        Describe a capability.
        
        Args:
            capability: Capability name
            
        Returns:
            Dictionary with capability description
        """
        parts = capability.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid capability format: {capability}")
        
        class_name, method_name = parts
        service_name = class_name.lower()
        
        if not hasattr(self, service_name):
            raise ValueError(f"Service {class_name} not found")
        
        service = getattr(self, service_name)
        if not hasattr(service, method_name):
            raise ValueError(f"Method {method_name} not found on {class_name}")
        
        method = getattr(service, method_name)
        return {
            "capability": capability,
            "doc": method.__doc__ or "",
        }
