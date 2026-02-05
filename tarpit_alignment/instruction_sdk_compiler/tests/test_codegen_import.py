"""Test that generated SDK can be imported."""

import tempfile
import shutil
from pathlib import Path
import sys

from instruction_sdk_compiler.spec.model import SdkSpec, ClassSpec, MethodSpec, ModelSpec, FieldSpec
from instruction_sdk_compiler.codegen.renderer import render_sdk


def test_generated_sdk_imports():
    """Test that generated SDK code can be imported."""
    # Create a minimal spec
    spec = SdkSpec(version="1.0.0")
    spec.rebind(classes={}, metadata={})
    
    # Add a simple class with a method
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
        outputs=user_output,
        doc_summary="Create a user"
    )
    
    user_service = ClassSpec(
        name="UserService",
        methods={"create_user": method},
        doc_summary="User service"
    )
    
    spec.classes.rebind({"UserService": user_service})
    
    # Generate SDK to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        render_sdk(spec, tmpdir)
        
        # Add generated_sdk to path
        sdk_path = Path(tmpdir) / "generated_sdk"
        sys.path.insert(0, str(Path(tmpdir)))
        
        try:
            # Try to import
            from generated_sdk import Client
            from generated_sdk.client import Client as ClientDirect
            from generated_sdk.services.userservice import UserService
            from generated_sdk.models import CreateUserInput, User
            
            # Verify classes exist
            assert Client is not None
            assert UserService is not None
            assert CreateUserInput is not None
            assert User is not None
            
        finally:
            sys.path.remove(str(Path(tmpdir)))
