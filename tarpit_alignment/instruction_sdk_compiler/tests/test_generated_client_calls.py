"""Test that generated Client can call methods and handle aliases/deprecation."""

import tempfile
import warnings
from pathlib import Path
import sys

from instruction_sdk_compiler.spec.model import SdkSpec, ClassSpec, MethodSpec, ModelSpec, FieldSpec
from instruction_sdk_compiler.codegen.renderer import render_sdk


def test_client_calls_method():
    """Test that Client can instantiate and call a method."""
    # Create spec
    spec = SdkSpec(version="1.0.0")
    spec.rebind(classes={}, metadata={})
    
    user_input = ModelSpec(
        name="CreateUserInput",
        fields={"email": FieldSpec(name="email", type="str", optional=False)}
    )
    user_output = ModelSpec(
        name="User",
        fields={"id": FieldSpec(name="id", type="str", optional=False)}
    )
    
    method = MethodSpec(
        name="create_user",
        inputs=user_input,
        outputs=user_output
    )
    
    user_service = ClassSpec(
        name="UserService",
        methods={"create_user": method}
    )
    
    spec.classes.rebind({"UserService": user_service})
    
    # Generate SDK
    with tempfile.TemporaryDirectory() as tmpdir:
        render_sdk(spec, tmpdir)
        sys.path.insert(0, str(Path(tmpdir)))
        
        try:
            from generated_sdk import Client
            from generated_sdk.models import CreateUserInput
            
            client = Client()
            
            # Test attribute access
            assert hasattr(client, "user_service")
            assert hasattr(client.user_service, "create_user")
            
            # Test method call (will use placeholder implementation)
            result = client.user_service.create_user(email="test@example.com")
            assert result is not None
            
        finally:
            sys.path.remove(str(Path(tmpdir)))


def test_deprecation_warning():
    """Test that deprecated methods emit warnings."""
    spec = SdkSpec(version="1.0.0")
    spec.rebind(classes={}, metadata={})
    
    method = MethodSpec(
        name="old_method",
        inputs=ModelSpec(name="Input", fields={}),
        outputs=ModelSpec(name="Output", fields={}),
        deprecated=True
    )
    
    service = ClassSpec(
        name="TestService",
        methods={"old_method": method}
    )
    
    spec.classes.rebind({"TestService": service})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        render_sdk(spec, tmpdir)
        sys.path.insert(0, str(Path(tmpdir)))
        
        try:
            from generated_sdk import Client
            
            client = Client()
            
            # Capture warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                client.test_service.old_method()
                
                # Check that deprecation warning was issued
                assert len(w) > 0
                assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
        
        finally:
            sys.path.remove(str(Path(tmpdir)))
