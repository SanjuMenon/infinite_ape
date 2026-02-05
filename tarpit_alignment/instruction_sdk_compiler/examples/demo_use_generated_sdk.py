"""Demo of using a generated SDK."""

import sys
from pathlib import Path

# This assumes you've already run demo_end_to_end.py
# and have a generated SDK at demo_output/generated_sdk

def main():
    """Demonstrate using the generated SDK."""
    # Add generated SDK to path
    demo_output = Path("demo_output")
    if not demo_output.exists():
        print("Error: demo_output directory not found.")
        print("Please run demo_end_to_end.py first to generate the SDK.")
        return
    
    sys.path.insert(0, str(demo_output.absolute()))
    
    try:
        from generated_sdk import Client
        from generated_sdk.models import CreateUserInput, CreateInvoiceInput
        
        print("=" * 60)
        print("Using Generated SDK")
        print("=" * 60)
        
        # Create client
        sdk = Client()
        print("\n✓ Client created")
        
        # List capabilities
        print("\nAvailable capabilities:")
        for cap in sdk.list_capabilities():
            print(f"  - {cap}")
        
        # Use attribute access
        print("\nUsing attribute access:")
        print("  sdk.user_service.create_user(...)")
        
        # Use string dispatch
        print("\nUsing string dispatch:")
        print('  sdk.call("UserService.create_user", email="test@example.com", name="Test")')
        
        # Describe a capability
        print("\nDescribing UserService.create_user:")
        desc = sdk.describe("UserService.create_user")
        print(f"  {desc}")
        
        print("\n" + "=" * 60)
        print("Note: Methods use placeholder implementations.")
        print("Implement actual logic in the generated service files.")
        print("=" * 60)
        
    except ImportError as e:
        print(f"Error importing generated SDK: {e}")
        print("\nMake sure you've run demo_end_to_end.py first.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
