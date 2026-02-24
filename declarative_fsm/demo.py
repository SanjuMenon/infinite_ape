#!/usr/bin/env python3
"""
Demo script for declarative FSM system.
"""

import json
from pathlib import Path
from declarative_fsm import FSMEngine, load_config


def main():
    """Run demo of declarative FSM system."""
    print("=" * 60)
    print("Declarative FSM Demo")
    print("=" * 60)
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    config_path = script_dir / "example_config.yaml"
    data_path = script_dir / "sample_data.json"
    
    # Load configuration
    print(f"\n1. Loading configuration from {config_path}...")
    try:
        config = load_config(str(config_path))
        print(f"   ✓ Loaded configuration with {len(config['fields'])} fields")
    except Exception as e:
        print(f"   ✗ Error loading config: {e}")
        return
    
    # Create engine
    print("\n2. Creating FSM engine...")
    engine = FSMEngine(config)
    print("   ✓ Engine created")
    
    # Load sample data
    print(f"\n3. Loading sample data from {data_path}...")
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   ✓ Data: {json.dumps(data, indent=2)}")
    except FileNotFoundError:
        print(f"   ✗ Error: Sample data file not found: {data_path}")
        return
    except json.JSONDecodeError as e:
        print(f"   ✗ Error: Invalid JSON in sample data file: {e}")
        return
    
    # Execute FSMs
    print("\n4. Executing FSMs...")
    print("   (Using strategy handlers for state validation)")
    report = engine.execute(data)
    
    # Display results
    print("\n5. Execution Report:")
    print("=" * 60)
    print(json.dumps(report, indent=2))
    
    # Summary
    print("\n6. Summary:")
    summary = report["execution_summary"]
    print(f"   Total fields: {summary['total_fields']}")
    print(f"   Fields passed: {summary['fields_passed']}")
    print(f"   Fields failed: {summary['fields_failed']}")
    
    # Field details
    print("\n7. Field Details:")
    for field_name, field_result in report["fields"].items():
        status_icon = "✓" if field_result["status"] == "passed" else "✗"
        print(f"   {status_icon} {field_name}: {field_result['status']}")
        
        for strategy_name, strategy_result in field_result["strategies"].items():
            strategy_status = strategy_result["status"]
            states_count = len(strategy_result["states_executed"])
            failed_at = strategy_result.get("failed_at")
            
            if failed_at:
                print(f"      - {strategy_name}: {strategy_status} (failed at: {failed_at}, executed {states_count} states)")
            else:
                print(f"      - {strategy_name}: {strategy_status} (executed {states_count} states)")
            
            # Show nested strategies
            if strategy_result.get("nested_strategies"):
                for nested_name, nested_result in strategy_result["nested_strategies"].items():
                    nested_status = nested_result["status"]
                    nested_states = len(nested_result["states_executed"])
                    nested_failed = nested_result.get("failed_at")
                    if nested_failed:
                        print(f"         └─ {nested_name}: {nested_status} (failed at: {nested_failed}, executed {nested_states} states)")
                    else:
                        print(f"         └─ {nested_name}: {nested_status} (executed {nested_states} states)")
    
    # Bundle demonstration (final payload after all strategies pass)
    print("\n8. Bundle (Final Payload) Demonstration:")
    print("=" * 60)
    for field_name, field_result in report["fields"].items():
        bundle = field_result.get("bundle", {})
        if bundle:
            print(f"\n   {field_name} bundle (final payload after all strategies pass):")
            print(f"   {json.dumps(bundle, indent=6)}")
            
            # Show bundle flow explanation
            if bundle.get('required_fields_found'):
                print(f"      → check_completeness stored: required_fields_found, field_data")
            if bundle.get('canonical_data'):
                print(f"      → convert_to_canon read from context and stored: canonical_data")
            if bundle.get('format_validated'):
                print(f"      → check_format read from context and stored: format_validated, validated_fields")
            if bundle.get('length_validated'):
                print(f"      → validate_length read from context and stored: length_validated, field_count")
        else:
            print(f"\n   {field_name}: No bundle (field may have failed early)")


if __name__ == "__main__":
    main()
