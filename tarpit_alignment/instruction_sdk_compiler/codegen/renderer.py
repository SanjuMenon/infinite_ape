"""Renderer for converting SdkSpec to Python SDK code."""

import os
from pathlib import Path
from typing import Any

from instruction_sdk_compiler.spec.model import SdkSpec, ClassSpec, MethodSpec
from instruction_sdk_compiler.codegen.sanitize import (
    sanitize_identifier,
    sanitize_docstring,
    format_type_string,
    escape_string,
)


def render_sdk(spec: SdkSpec, output_dir: str) -> None:
    """
    Generate Python SDK from SdkSpec.
    
    Args:
        spec: The SDK specification
        output_dir: Directory to write generated SDK
    """
    output_path = Path(output_dir)
    sdk_path = output_path / "generated_sdk"
    
    # Create directory structure
    (sdk_path / "services").mkdir(parents=True, exist_ok=True)
    (sdk_path / "runtime").mkdir(parents=True, exist_ok=True)
    
    # Generate __init__.py
    _render_init(sdk_path, spec)
    
    # Generate client.py
    _render_client(sdk_path, spec)
    
    # Generate models.py
    _render_models(sdk_path, spec)
    
    # Generate registry.py
    _render_registry(sdk_path, spec)
    
    # Generate service files
    if spec.classes:
        for class_name, class_spec in spec.classes.items():
            _render_service(sdk_path, class_spec)
    
    # Copy runtime base classes
    _render_runtime_base(sdk_path)


def _render_init(sdk_path: Path, spec: SdkSpec) -> None:
    """Generate __init__.py for generated SDK."""
    content = f'''"""Generated SDK version {spec.version}."""

from generated_sdk.client import Client
from generated_sdk.registry import CapabilityRegistry

__all__ = ["Client", "CapabilityRegistry"]
'''
    (sdk_path / "__init__.py").write_text(content)


def _render_client(sdk_path: Path, spec: SdkSpec) -> None:
    """Generate client.py front door."""
    service_imports = []
    service_instances = []
    service_attrs = []
    
    for class_name, class_spec in spec.classes.items():
        service_name = sanitize_identifier(class_name.lower())
        service_class = sanitize_identifier(class_name)
        service_imports.append(f"from generated_sdk.services.{service_name} import {service_class}")
        service_instances.append(f"        self.{service_name} = {service_class}(registry=self._registry)")
        service_attrs.append(f"    {service_name}: {service_class}")
    
    imports = "\n".join(service_imports) if service_imports else "# No services defined"
    instances = "\n".join(service_instances) if service_instances else "        # No services to initialize"
    attrs = "\n".join(service_attrs) if service_attrs else "    # No services defined"
    
    # Build capability list code
    cap_lines = []
    for class_name, class_spec in spec.classes.items():
        for method_name in class_spec.methods.keys():
            cap_lines.append(f'        capabilities.append("{class_name}.{method_name}")')
    capabilities_code = "\n".join(cap_lines) if cap_lines else "        pass"
    
    content = f'''"""Client front door for generated SDK."""

from typing import Any
from generated_sdk.registry import CapabilityRegistry
{imports}

{attrs}


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
{instances}
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
            raise ValueError(f"Invalid capability format: {{capability}}")
        
        class_name, method_name = parts
        service_name = class_name.lower()
        
        if not hasattr(self, service_name):
            raise ValueError(f"Service {{class_name}} not found")
        
        service = getattr(self, service_name)
        if not hasattr(service, method_name):
            raise ValueError(f"Method {{method_name}} not found on {{class_name}}")
        
        method = getattr(service, method_name)
        return method(**kwargs)
    
    def list_capabilities(self) -> list[str]:
        """
        List all available capabilities.
        
        Returns:
            List of capability names in format "ClassName.method_name"
        """
        capabilities = []
{capabilities_code}
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
            raise ValueError(f"Invalid capability format: {{capability}}")
        
        class_name, method_name = parts
        service_name = class_name.lower()
        
        if not hasattr(self, service_name):
            raise ValueError(f"Service {{class_name}} not found")
        
        service = getattr(self, service_name)
        if not hasattr(service, method_name):
            raise ValueError(f"Method {{method_name}} not found on {{class_name}}")
        
        method = getattr(service, method_name)
        return {{
            "capability": capability,
            "doc": method.__doc__ or "",
        }}
'''
    (sdk_path / "client.py").write_text(content)


def _render_models(sdk_path: Path, spec: SdkSpec) -> None:
    """Generate models.py with Pydantic models."""
    model_defs = []
    model_names = set()
    
    # Collect all model names from inputs and outputs
    for class_spec in spec.classes.values():
        for method_spec in class_spec.methods.values():
            if method_spec.inputs.name not in model_names:
                model_names.add(method_spec.inputs.name)
                model_defs.append(_render_pydantic_model(method_spec.inputs, "input"))
            if method_spec.outputs.name not in model_names:
                model_names.add(method_spec.outputs.name)
                model_defs.append(_render_pydantic_model(method_spec.outputs, "output"))
    
    content = f'''"""Pydantic models for SDK inputs and outputs."""

from typing import Optional, Any
from pydantic import BaseModel, Field

{chr(10).join(model_defs)}
'''
    (sdk_path / "models.py").write_text(content)


def _render_pydantic_model(model_spec, prefix: str) -> str:
    """Render a single Pydantic model."""
    class_name = sanitize_identifier(model_spec.name)
    fields = []
    
    for field_name, field_spec in (model_spec.fields.items() if model_spec.fields else []):
        field_name_safe = sanitize_identifier(field_name)
        type_str = format_type_string(field_spec.type)
        
        if field_spec.optional:
            type_str = f"Optional[{type_str}]"
        
        default = ""
        if field_spec.default is not None:
            default = f" = {escape_string(field_spec.default)}"
        elif field_spec.optional:
            default = " = None"
        
        field_desc = sanitize_docstring(field_spec.description or "")
        if field_desc:
            fields.append(
                f'    {field_name_safe}: {type_str} = Field(default={escape_string(field_spec.default) if field_spec.default is not None else "None"}, description={escape_string(field_desc)})'
            )
        else:
            fields.append(f"    {field_name_safe}: {type_str}{default}")
    
    fields_str = "\n".join(fields) if fields else "    pass"
    
    return f'''
class {class_name}(BaseModel):
    """{sanitize_docstring(model_spec.name)} model."""
    
{fields_str}
'''


def _render_service(sdk_path: Path, class_spec: ClassSpec) -> None:
    """Generate a service class file."""
    class_name = sanitize_identifier(class_spec.name)
    service_name = sanitize_identifier(class_spec.name.lower())
    
    # Build docstring
    doc_summary = sanitize_docstring(class_spec.doc_summary or f"{class_name} service generated from instruction specs.")
    doc_notes = "\n".join(f"    - {sanitize_docstring(note)}" for note in class_spec.doc_notes)
    docstring = f'"""{doc_summary}'
    if doc_notes:
        docstring += "\n\n    Notes:\n" + doc_notes
    docstring += '\n"""'
    
    # Generate methods
    methods = []
    for method_name, method_spec in class_spec.methods.items():
        methods.append(_render_method(method_spec, class_spec.name))
    
    methods_str = "\n\n".join(methods)
    
    content = f'''"""Service: {class_name}"""

import warnings
from typing import Any, Optional
from generated_sdk.models import *
from generated_sdk.runtime.base import BaseService
from generated_sdk.registry import CapabilityRegistry


class {class_name}(BaseService):
    {docstring}
    
    def __init__(self, registry: CapabilityRegistry):
        """Initialize {class_name} service."""
        super().__init__(registry)
        if {str(class_spec.deprecated).lower()}:
            warnings.warn(
                "{class_name} is deprecated",
                DeprecationWarning,
                stacklevel=2
            )
    
{methods_str}
'''
    (sdk_path / "services" / f"{service_name}.py").write_text(content)


def _render_method(method_spec: MethodSpec, class_name: str) -> str:
    """Render a single method."""
    method_name = sanitize_identifier(method_spec.name)
    
    # Build signature with individual parameters
    input_model = sanitize_identifier(method_spec.inputs.name)
    params = ["self"]
    
    if method_spec.inputs.fields:
        for field_name, field_spec in method_spec.inputs.fields.items():
            field_name_safe = sanitize_identifier(field_name)
            type_str = format_type_string(field_spec.type)
            if field_spec.optional:
                type_str = f"Optional[{type_str}]"
            default = ""
            if field_spec.default is not None:
                default = f" = {escape_string(field_spec.default)}"
            elif field_spec.optional:
                default = " = None"
            params.append(f"{field_name_safe}: {type_str}{default}")
    
    sig = f"    def {method_name}({', '.join(params)}) -> {sanitize_identifier(method_spec.outputs.name)}:"
    
    # Build docstring
    doc_summary = sanitize_docstring(method_spec.doc_summary or f"{method_name} method")
    doc_notes = "\n".join(f"        - {sanitize_docstring(note)}" for note in (method_spec.doc_notes or []))
    
    # Build Args section
    args_section = ""
    if method_spec.inputs.fields:
        args_section = "\n        Args:\n"
        for field_name, field_spec in method_spec.inputs.fields.items():
            field_desc = sanitize_docstring(field_spec.description or "")
            args_section += f"            {field_name}: {field_desc}\n"
    
    # Build Returns section
    returns_section = f"\n        Returns:\n            {sanitize_identifier(method_spec.outputs.name)}: Result"
    
    docstring = f'        """{doc_summary}'
    if args_section:
        docstring += args_section
    if returns_section:
        docstring += returns_section
    if doc_notes:
        docstring += "\n\n        Notes:\n" + doc_notes
    docstring += '\n        """'
    
    # Build method body
    deprecated_check = ""
    if method_spec.deprecated:
        deprecated_check = f'''        if True:  # Method is deprecated
            warnings.warn(
                "{class_name}.{method_name} is deprecated",
                DeprecationWarning,
                stacklevel=2
            )
'''
    
    # Build method body - validate inputs and create output
    input_model = sanitize_identifier(method_spec.inputs.name)
    output_model = sanitize_identifier(method_spec.outputs.name)
    
    # Build input model instantiation from parameters
    if method_spec.inputs.fields:
        input_fields = ", ".join(
            f"{sanitize_identifier(field_name)}={sanitize_identifier(field_name)}"
            for field_name in method_spec.inputs.fields.keys()
        )
        input_validation = f"        input_data = {input_model}({input_fields})"
        output_creation = f"        result = {output_model}(**input_data.model_dump())"
    else:
        input_validation = f"        input_data = {input_model}()"
        output_creation = f"        result = {output_model}()"
    
    body = f'''{deprecated_check}        # Validate inputs
{input_validation}
        
        # TODO: Implement actual logic
        # Input: {input_model}
        # Output: {output_model}
        
        # For now, return a basic output model
{output_creation}
        return result'''
    
    return f"{sig}\n{docstring}\n{body}"


def _render_registry(sdk_path: Path, spec: SdkSpec) -> None:
    """Generate registry.py."""
    content = '''"""Capability registry for SDK."""

from typing import Callable, Any, Dict
from generated_sdk.runtime.registry import CapabilityRegistry as BaseCapabilityRegistry


class CapabilityRegistry(BaseCapabilityRegistry):
    """Registry for SDK capabilities."""
    
    def __init__(self):
        """Initialize registry."""
        super().__init__()
'''
    (sdk_path / "registry.py").write_text(content)


def _render_runtime_base(sdk_path: Path) -> None:
    """Generate runtime base classes."""
    # Base service
    base_service_content = '''"""Base service class."""

from abc import ABC
from generated_sdk.runtime.registry import CapabilityRegistry


class BaseService(ABC):
    """Base class for all services."""
    
    def __init__(self, registry: CapabilityRegistry):
        """Initialize base service."""
        self._registry = registry
'''
    (sdk_path / "runtime" / "base.py").write_text(base_service_content)
    
    # Registry (minimal implementation)
    registry_content = '''"""Capability registry."""

from typing import Callable, Any, Dict, Optional


class CapabilityRegistry:
    """Registry for registering and looking up capabilities."""
    
    def __init__(self):
        """Initialize registry."""
        self._capabilities: Dict[str, Callable] = {}
    
    def register(self, name: str, callable: Callable) -> None:
        """Register a capability."""
        self._capabilities[name] = callable
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a capability by name."""
        return self._capabilities.get(name)
    
    def list_all(self) -> list[str]:
        """List all registered capabilities."""
        return list(self._capabilities.keys())
'''
    (sdk_path / "runtime" / "registry.py").write_text(registry_content)
    
    # Runtime __init__
    (sdk_path / "runtime" / "__init__.py").write_text('"""Runtime components."""\n')
