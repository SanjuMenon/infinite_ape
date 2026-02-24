#!/usr/bin/env python3
"""
Test script for strategy handlers.

This script demonstrates how to test individual strategy handlers
and verify they work correctly with different data scenarios.
"""

import json
from pathlib import Path
from declarative_fsm import FSMEngine, load_config
from declarative_fsm import strategy


def test_check_completeness():
    """Test check_completeness handler."""
    print("=" * 60)
    print("Testing: check_completeness handler")
    print("=" * 60)
    
    # Test case 1: All required fields present
    print("\nTest 1: All required fields present")
    data1 = {
        "collateral": {
            "value_type": "Real Estate",
            "amount": "100000"
        }
    }
    state_config1 = {
        "description": ["value_type", "amount"]
    }
    result1 = strategy.check_completeness_handler(
        data1, state_config1, "collateral", {}
    )
    print(f"   Data: {json.dumps(data1, indent=2)}")
    print(f"   Required fields: {state_config1['description']}")
    print(f"   Result: {'✓ PASS' if result1 else '✗ FAIL'}")
    assert result1 == True, "Should pass when all fields are present"
    
    # Test case 2: Missing required field
    print("\nTest 2: Missing required field")
    data2 = {
        "collateral": {
            "value_type": "Real Estate"
            # Missing "amount"
        }
    }
    state_config2 = {
        "description": ["value_type", "amount"]
    }
    result2 = strategy.check_completeness_handler(
        data2, state_config2, "collateral", {}
    )
    print(f"   Data: {json.dumps(data2, indent=2)}")
    print(f"   Required fields: {state_config2['description']}")
    print(f"   Result: {'✓ PASS' if result2 else '✗ FAIL'}")
    assert result2 == False, "Should fail when field is missing"
    
    print("\n✓ check_completeness tests passed!\n")


def test_convert_to_canon():
    """Test convert_to_canon handler."""
    print("=" * 60)
    print("Testing: convert_to_canon handler")
    print("=" * 60)
    
    # Test case 1: Description is True
    print("\nTest 1: Description is True (should convert)")
    state_config1 = {"description": True}
    result1 = strategy.convert_to_canon_handler({}, state_config1, "collateral", {})
    print(f"   State config: {state_config1}")
    print(f"   Result: {'✓ PASS' if result1 else '✗ FAIL'}")
    assert result1 == True, "Should pass when description is True"
    
    # Test case 2: Description is False
    print("\nTest 2: Description is False (should not convert)")
    state_config2 = {"description": False}
    result2 = strategy.convert_to_canon_handler({}, state_config2, "collateral", {})
    print(f"   State config: {state_config2}")
    print(f"   Result: {'✓ PASS' if result2 else '✗ FAIL'}")
    assert result2 == False, "Should fail when description is False"
    
    print("\n✓ convert_to_canon tests passed!\n")


def test_check_required():
    """Test check_required handler."""
    print("=" * 60)
    print("Testing: check_required handler")
    print("=" * 60)
    
    # Test case 1: Field is present
    print("\nTest 1: Field is present")
    data1 = {"collateral": {"value_type": "Real Estate"}}
    result1 = strategy.validation_check_required_handler(
        data1, {}, "collateral", {}
    )
    print(f"   Data: {json.dumps(data1, indent=2)}")
    print(f"   Result: {'✓ PASS' if result1 else '✗ FAIL'}")
    assert result1 == True, "Should pass when field is present"
    
    # Test case 2: Field is missing
    print("\nTest 2: Field is missing")
    data2 = {}
    result2 = strategy.validation_check_required_handler(
        data2, {}, "collateral", {}
    )
    print(f"   Data: {json.dumps(data2, indent=2)}")
    print(f"   Result: {'✓ PASS' if result2 else '✗ FAIL'}")
    assert result2 == False, "Should fail when field is missing"
    
    print("\n✓ check_required tests passed!\n")


def test_full_execution():
    """Test full FSM execution with real handlers."""
    print("=" * 60)
    print("Testing: Full FSM Execution")
    print("=" * 60)
    
    script_dir = Path(__file__).parent
    config_path = script_dir / "example_config.yaml"
    
    # Load config
    config = load_config(str(config_path))
    engine = FSMEngine(config)
    
    # Test case 1: Valid data (should pass check_completeness)
    print("\nTest 1: Valid data with all required fields")
    data1 = {
        "collateral": {
            "value_type": "Real Estate",
            "amount": "100000"
        },
        "real estate assets": {
            "address": "123 Main St",
            "real_estate_type": "Commercial"
        },
        "Financials": {
            "net_sales": "500000",
            "ebitda": "100000"
        }
    }
    print(f"   Data: {json.dumps(data1, indent=2)}")
    report1 = engine.execute(data1)
    
    # Check field_selection_strategy results
    for field_name, field_result in report1["fields"].items():
        field_selection = field_result["strategies"].get("field_selection_strategy")
        if field_selection:
            status = field_selection["status"]
            print(f"   {field_name}.field_selection_strategy: {status}")
            if status == "passed":
                print(f"      ✓ check_completeness passed (all required fields present)")
            else:
                print(f"      ✗ check_completeness failed at: {field_selection.get('failed_at')}")
    
    # Test case 2: Missing required field (should fail check_completeness)
    print("\nTest 2: Missing required field")
    data2 = {
        "collateral": {
            "value_type": "Real Estate"
            # Missing "amount"
        }
    }
    print(f"   Data: {json.dumps(data2, indent=2)}")
    report2 = engine.execute(data2)
    
    collateral_result = report2["fields"].get("collateral", {})
    field_selection = collateral_result.get("strategies", {}).get("field_selection_strategy")
    if field_selection:
        status = field_selection["status"]
        print(f"   collateral.field_selection_strategy: {status}")
        if status == "not_passed":
            print(f"      ✗ check_completeness failed (missing 'amount' field)")
        else:
            print(f"      ✓ Unexpected: check_completeness passed")
    
    print("\n✓ Full execution tests completed!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Strategy Handler Test Suite")
    print("=" * 60)
    
    try:
        # Test individual handlers
        test_check_completeness()
        test_convert_to_canon()
        test_check_required()
        
        # Test full execution
        test_full_execution()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
