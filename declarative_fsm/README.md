# Declarative FSM

A hierarchical Finite State Machine (FSM) system that validates data processing strategies at runtime. FSMs are loaded from a YAML configuration file and check whether field-specific strategies can be successfully applied to raw data.

## Features

- **Hierarchical FSMs**: Support for nested strategy FSMs (e.g., extraction strategy containing generation strategy)
- **Linear Sequential Execution**: States execute in order with pass/fail criteria checks
- **YAML Configuration**: Define FSMs declaratively in YAML files
- **Runtime Execution**: FSMs are instantiated dynamically from configuration
- **Execution Reporting**: JSON reports showing which FSMs passed/failed and where failures occurred

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Create a YAML configuration file** (see `example_config.yaml`):

```yaml
fields:
  customer_name:
    extraction_strategy:
      check_format:
        description: "Check if customer name format is valid"
      validate_length:
        description: "Validate name length constraints"
      generation_strategy:
        # Nested FSM - only executes if extraction_strategy passes
        generate_template:
          description: "Generate name template"
        apply_formatting:
          description: "Apply formatting rules"
```

2. **Use the FSM Engine**:

```python
from declarative_fsm import FSMEngine, load_config
import json

# Load configuration
config = load_config("example_config.yaml")

# Create engine
engine = FSMEngine(config)

# Execute FSMs on data
data = {
    "customer_name": "John Doe",
    "email_address": "john@example.com"
}

report = engine.execute(data)

# Report is a JSON dictionary
print(json.dumps(report, indent=2))
```

3. **Run the demo**:

```bash
python demo.py
```

## YAML Configuration Structure

```yaml
fields:
  field_name:
    strategy_type:
      state_1:
        # State configuration (optional metadata)
      state_2:
        # State configuration
      nested_strategy_type:
        # Nested FSM - only executes if parent passes
        nested_state_1:
        nested_state_2:
```

**Key Points:**
- `fields` is the top-level key
- Each field can have multiple strategy types
- States are defined as keys under strategy types
- States execute in the order they appear in YAML
- Nested strategies create nested FSMs that only execute if parent passes

## Execution Model

- **Linear Progression**: States execute sequentially in order
- **Pass/Fail**: Each state performs a criteria check (random for MVP)
- **FSM Status**: An FSM is "passed" only if all states pass
- **Nested Execution**: Nested FSMs execute only after parent FSM fully passes
- **Failure Handling**: If any state fails, FSM execution stops immediately

## Report Format

The execution report is a JSON dictionary with the following structure:

```json
{
  "execution_summary": {
    "total_fields": 2,
    "fields_passed": 1,
    "fields_failed": 1
  },
  "fields": {
    "field_name": {
      "status": "passed" | "not_passed",
      "strategies": {
        "strategy_type": {
          "status": "passed" | "not_passed",
          "states_executed": ["state1", "state2"],
          "failed_at": null | "state_name",
          "nested_strategies": {
            "nested_strategy": {
              "status": "passed" | "not_passed",
              "states_executed": [...],
              "failed_at": null | "state_name"
            }
          }
        }
      }
    }
  }
}
```

## Project Structure

```
declarative_fsm/
├── __init__.py          # Package exports
├── loader.py             # YAML configuration loader
├── engine.py             # FSM execution engine
├── requirements.txt     # Dependencies
├── example_config.yaml   # Example configuration
├── demo.py              # Demo script
├── README.md            # This file
└── SPEC.md              # Detailed specification
```

## Dependencies

- `transitions>=0.9.0` - FSM library (for future extensibility)
- `pyyaml>=6.0` - YAML parsing

## MVP Status

Currently implements:
- ✅ YAML configuration loading
- ✅ Hierarchical FSM structure
- ✅ Linear sequential state execution
- ✅ Random pass/fail criteria (placeholder)
- ✅ Nested FSM execution (only after parent passes)
- ✅ JSON execution reports

Future enhancements:
- Real criteria evaluation (not random)
- Integration with transitions library for advanced features
- Retry mechanisms
- Fallback strategies
- Visualization tools

## License

See parent repository license.
