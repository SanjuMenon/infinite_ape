"""End-to-end demo of the instruction SDK compiler."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from instruction_sdk_compiler import CompilerClient

load_dotenv()

def main():
    """Run end-to-end demo."""
    print("=" * 60)
    print("Instruction SDK Compiler - End-to-End Demo")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set. Using mock mode.")
        print("   Set OPENAI_API_KEY environment variable to use real LLM.\n")
    
    # Create compiler client
    project_dir = "demo_output"
    print(f"\n1. Creating CompilerClient with project_dir='{project_dir}'")
    c = CompilerClient(project_dir=project_dir)
    
    # Ingest instructions
    print("\n2. Ingesting instructions...")
    
    print("   Instruction 1: Create a UserService with method create_user(email: str) -> User")
    c.ingest_instruction("Create a UserService with method create_user(email: str) -> User")
    
    print("   Instruction 2: Modify UserService.create_user to also accept name: str")
    c.ingest_instruction("Modify UserService.create_user to also accept name: str")
    
    print("   Instruction 3: Add InvoiceService with method create_invoice(user_id: str, amount: float) -> Invoice")
    c.ingest_instruction("Add InvoiceService with method create_invoice(user_id: str, amount: float) -> Invoice")
    
    # Show current spec
    print("\n3. Current SDK Specification:")
    spec = c.current_spec()
    for class_name, class_spec in spec.classes.items():
        print(f"   {class_name}:")
        for method_name, method_spec in class_spec.methods.items():
            input_fields = ", ".join(
                f"{name}: {field.type}" 
                for name, field in (method_spec.inputs.fields.items() if method_spec.inputs.fields else [])
            )
            print(f"     {method_name}({input_fields}) -> {method_spec.outputs.name}")
    
    # Build SDK
    print("\n4. Building generated SDK...")
    build_result = c.build()
    
    if build_result.success:
        print(f"   ✓ SDK generated successfully to {build_result.output_dir}")
    else:
        print(f"   ✗ Build failed: {build_result.message}")
        return
    
    # Show history
    print("\n5. Patch History:")
    history = c.history()
    for i, record in enumerate(history, 1):
        print(f"   Patch {i}: {record.applied_patch_summary}")
        print(f"            Version: {record.spec_version_before} -> {record.spec_version_after}")
    
    # Try to import and use generated SDK
    print("\n6. Testing generated SDK...")
    try:
        sys.path.insert(0, str(Path(project_dir).absolute()))
        from generated_sdk import Client
        
        sdk = Client()
        print("   ✓ Client imported and instantiated")
        
        # List capabilities
        capabilities = sdk.list_capabilities()
        print(f"   ✓ Found {len(capabilities)} capabilities:")
        for cap in capabilities:
            print(f"     - {cap}")
        
        # Try calling a method (will use placeholder implementation)
        print("\n   Attempting to call user_service.create_user...")
        from generated_sdk.models import CreateUserInput
        
        # Note: This will use the placeholder implementation
        result = sdk.user_service.create_user(email="test@example.com", name="Test User")
        print(f"   ✓ Method call succeeded (placeholder implementation)")
        
    except Exception as e:
        print(f"   ✗ Error using generated SDK: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print(f"\nGenerated SDK is available at: {Path(project_dir).absolute() / 'generated_sdk'}")
    print("\nYou can now use it like:")
    print("  from generated_sdk import Client")
    print("  sdk = Client()")
    print("  user = sdk.user_service.create_user(email='a@b.com', name='Ada')")


if __name__ == "__main__":
    main()
