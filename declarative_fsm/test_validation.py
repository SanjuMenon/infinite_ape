#!/usr/bin/env python3
"""
Test script to verify config validation works correctly.
"""

from pathlib import Path
from declarative_fsm import load_config, validate_config
import yaml

def test_valid_config():
    """Test that the example config validates successfully."""
    script_dir = Path(__file__).parent
    config_path = script_dir / "example_config.yaml"
    
    print("Testing valid config...")
    try:
        config = load_config(str(config_path), validate=True)
        print("✓ Valid config passed validation")
        return True
    except ValueError as e:
        print(f"✗ Valid config failed validation: {e}")
        return False

def test_invalid_config():
    """Test that invalid configs are caught."""
    script_dir = Path(__file__).parent
    
    # Create a test config with invalid state
    invalid_config = {
        'fields': {
            'test_field': {
                'field_selection_strategy': {
                    'check_completeness': {'description': ['field1']},
                    'invalid_state': {'description': 'test'}  # Invalid state
                }
            }
        }
    }
    
    print("\nTesting invalid config (invalid state in field_selection_strategy)...")
    try:
        validate_config(invalid_config)
        print("✗ Invalid config passed validation (should have failed)")
        return False
    except ValueError as e:
        print(f"✓ Invalid config correctly rejected:")
        print(f"  {e}")
        return True

def test_nested_strategy_validation():
    """Test that nested strategies are validated correctly."""
    # Create a test config with invalid state in nested strategy
    invalid_nested_config = {
        'fields': {
            'test_field': {
                'extraction_strategy': {
                    'validate_type': {'description': 'int'},
                    'generation_strategy': {
                        'generate_template': {'description': 'test'},
                        'invalid_nested_state': {'description': 'test'}  # Invalid state
                    }
                }
            }
        }
    }
    
    print("\nTesting invalid nested strategy config...")
    try:
        validate_config(invalid_nested_config)
        print("✗ Invalid nested config passed validation (should have failed)")
        return False
    except ValueError as e:
        print(f"✓ Invalid nested config correctly rejected:")
        print(f"  {e}")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("Config Validation Tests")
    print("=" * 60)
    
    results = []
    results.append(test_valid_config())
    results.append(test_invalid_config())
    results.append(test_nested_strategy_validation())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
