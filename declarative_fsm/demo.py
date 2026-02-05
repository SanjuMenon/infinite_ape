#!/usr/bin/env python3
"""
Demo script for declarative FSM system.
"""

import json
import os
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
    
    # Sample data
    print("\n3. Preparing sample data...")
    data = {
        "customer_name": "John Doe",
        "email_address": "john@example.com"
    }
    print(f"   ✓ Data: {json.dumps(data, indent=2)}")
    
    # Execute FSMs
    print("\n4. Executing FSMs...")
    print("   (Note: Using random pass/fail for MVP)")
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


if __name__ == "__main__":
    main()
