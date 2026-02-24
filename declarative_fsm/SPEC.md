# Declarative FSM Specification

## Overview
A hierarchical Finite State Machine (FSM) system that validates data processing strategies at runtime. FSMs are loaded from a YAML configuration file and check whether field-specific strategies can be successfully applied to raw data.

## Core Concepts

### 1. Hierarchical FSM Structure
- Each FSM represents a **strategy type** (e.g., `extraction_strategy`, `generation_strategy`)
- FSMs can be **nested** within other FSMs
- Each FSM has **linear state transitions** - states execute sequentially
- A state transitions to the next only if its **criteria check passes**

### 2. YAML Configuration Structure

```yaml
fields:
  field_name:
    strategy_type_1:
      state_1:
        # State configuration (criteria, metadata, etc.)
      state_2:
        # State configuration
      nested_strategy_type:
        state_1:
          # Nested FSM states
        state_2:
          # Nested FSM states
    strategy_type_2:
      state_1:
        # Another strategy FSM
```

**Key Points:**
- Fields are top-level keys
- Strategy types are nested under fields
- States are implicit - keys at the strategy level represent states
- States execute in the order they appear in YAML
- Nested strategies create nested FSMs

### 3. State Execution Model

**Linear Progression:**
- States execute in order (as defined in YAML)
- Each state performs a criteria check
- If check **passes**: move to next state
- If check **fails**: FSM execution stops immediately, FSM marked as "not passed"

**FSM Pass/Fail:**
- An FSM is considered **"passed"** only if **all states** in the sequence pass
- If any state fails, the FSM is **"not passed"** and execution stops
- Nested FSMs execute **only if parent FSM fully passes**

**Criteria Evaluation:**
- Each state has its own handler function in the `strategy.py` module
- Handlers are registered by (strategy_name, state_name) combination
- Handlers receive: data, state_config, field_name, and context
- If no handler is found, falls back to random pass/fail (80% pass rate)
- Each handler implements specific validation logic for that state

**Context/Payload Passing:**
- Each field has a mutable context dictionary that persists across all states
- Context is shared across sequential strategies (e.g., field_selection_strategy → extraction_strategy)
- Handlers can read from and write to the context to pass data between states
- Context is scoped per field (not shared across different fields)
- Context is initialized as an empty dictionary `{}` for each field
- Nested strategies share the same context as their parent strategy

### 4. FSM Execution Flow

1. **Load YAML configuration** at runtime
2. **Parse hierarchical structure** into FSM objects
3. **For each field:**
   - Instantiate top-level strategy FSMs
   - Execute states sequentially
   - If state passes, continue to next state
   - If state fails, mark FSM as "not passed" and stop execution
   - **Only if all states pass**: Execute nested FSMs (if any)
   - If nested FSM exists and parent passed, execute nested FSM with same rules
4. **Generate execution report** (JSON format)

### 5. Execution Report

The system should produce a report containing:

- **FSM Initialization Status**
  - Which FSMs were successfully loaded
  - Which FSMs failed to initialize
  
- **Field Usability**
  - Fields with all strategy FSMs passing
  - Fields with failed strategy FSMs (and which ones)
  - Impact assessment (which fields are hard/unusable)
  
- **Execution Details**
  - State-by-state execution results
  - Which criteria checks passed/failed
  - Execution path through nested FSMs

**Report Format:** JSON

**Report Structure (Proposed):**
```json
{
  "execution_summary": {
    "total_fields": 5,
    "fields_passed": 3,
    "fields_failed": 2
  },
  "fields": {
    "field_name": {
      "status": "passed" | "not_passed",
      "strategies": {
        "strategy_type": {
          "status": "passed" | "not_passed",
          "states_executed": ["state1", "state2", "state3"],
          "failed_at": null | "state_name",
          "nested_strategies": {
            "nested_strategy_type": {
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

## Implementation Requirements

### Phase 1: Core Functionality

1. **YAML Parser**
   - Load and parse YAML configuration
   - Validate structure
   - Build hierarchical FSM representation

2. **FSM Engine**
   - Instantiate FSMs from configuration
   - Execute states sequentially
   - Handle linear transitions
   - Support nested FSM execution

3. **State Execution**
   - Execute state criteria checks via strategy module handlers
   - Each state has its own handler function in `strategy.py`
   - Handler registry maps (strategy_name, state_name) to handler functions
   - Track pass/fail status
   - Manage state transitions
   
4. **Strategy Module** (`strategy.py`)
   - Contains handler functions for each state
   - Centralized dispatch via `execute_state()` function
   - Handlers receive: data, state_config, field_name
   - Fallback to random pass/fail if handler not found

5. **Reporting System**
   - Generate execution report
   - Track FSM initialization status
   - Identify field usability issues

### Phase 2: Future Enhancements (Out of Scope for MVP)

- Enhanced criteria evaluation (more sophisticated validation logic)
- Retry mechanisms
- Fallback strategies
- Visualization
- Performance metrics
- Dynamic handler registration

## API/Interface Design

### Python API (Proposed)

```python
from declarative_fsm import FSMEngine, load_config

# Load configuration
config = load_config("strategies.yaml")

# Create engine
engine = FSMEngine(config)

# Execute FSMs on data
data = {...}  # JSON data (dict or JSON string)
report = engine.execute(data)  # Returns JSON report

# Access report
print(report.summary())
print(report.failed_fields())
print(report.execution_details())
```

## Technology Decision

### FSM Library Choice

**Decision: Use `transitions` library (pytransitions)**

**Rationale:**
- ✅ Supports hierarchical/nested states (required for nested strategy FSMs)
- ✅ Linear sequential execution is straightforward - just define sequential transitions with conditions
- ✅ Conditions and callbacks map directly to pass/fail criteria checks
- ✅ Well-maintained, mature library with good documentation
- ✅ Future-proof: Easy to extend to complex transitions, retries, branching if needed
- ✅ No added complexity for linear use case - library handles it naturally

**Implementation Approach:**
- Define states in sequential order from YAML
- Create transitions: `state_n → state_n+1` with condition checks
- Use `on_enter` callbacks for validation logic
- Use transition conditions for pass/fail gates
- Nested FSMs use hierarchical state support

## Decisions Made

1. **FSM Library**: ✅ Use `transitions` (pytransitions)
2. **Report Format**: ✅ JSON
3. **Data Input**: ✅ JSON format
4. **Nested FSM Execution**: ✅ Nested FSMs execute **only after parent FSM fully passes** (all states pass). If any state fails, the FSM fails and children do not execute.
5. **FSM Failure Model**: If any state check fails, the entire FSM is marked as "not passed" and execution stops for that FSM branch (no nested execution).

## Final Decisions

1. **State Metadata**: Optional - states can include metadata (descriptions, purposes, etc.) but it's not required
2. **Error Handling**: Standard Python exceptions (ValueError, KeyError, etc.) for malformed YAML or invalid configurations

## Strategy Module Architecture

### Handler-Based State Execution

The system uses a handler-based architecture where each state has its own handler function:

**Key Components:**

1. **Handler Functions** (`strategy.py`)
   - Each state has a dedicated handler function
   - Handler signature: `handler(data, state_config, field_name) -> bool`
   - Handlers implement specific validation logic for their state

2. **Handler Registry**
   - Maps `(strategy_name, state_name)` tuples to handler functions
   - Example: `("field_selection_strategy", "check_completeness")` → `check_completeness_handler`
   - Allows same state name in different strategies to have different logic

3. **Dispatch Function**
   - `execute_state(strategy_name, state_name, data, state_config, field_name)`
   - Looks up handler in registry
   - Falls back to random pass/fail (80%) if handler not found
   - Handles exceptions gracefully

**Benefits:**
- Separation of concerns: Engine handles flow, strategy module handles validation
- Extensibility: Add new handlers without modifying engine code
- Flexibility: Same state name can have different logic in different strategies
- Maintainability: Each state's logic is isolated and testable

**Current Handlers:**
- `field_selection_strategy`: `check_completeness`, `convert_to_canon`
- `extraction_strategy`: `check_format`, `validate_length`
- `generation_strategy`: `generate_template`, `apply_formatting`
- `validation_strategy`: `check_required`, `check_uniqueness`

**Context/Payload System:**
- Each handler receives a `context` parameter (mutable dictionary)
- Context persists across all states within the same field
- Handlers can read from context: `value = context.get('key')`
- Handlers can write to context: `context['key'] = value`
- Context is initialized as `{}` for each field
- Context is shared across sequential strategies (e.g., field_selection_strategy → extraction_strategy → validation_strategy)
- Context is NOT shared across different fields (collateral's context is separate from "real estate assets" context)
- Nested strategies share the same context as their parent

**Example Usage:**
```python
def my_handler(data, state_config, field_name, context):
    # Read from context (set by previous state)
    previous_value = context.get('some_key')
    
    # Write to context (available to next state)
    context['processed_data'] = process(data)
    
    return True  # pass/fail
```

## Example YAML Structure

```yaml
fields:
  customer_name:
    extraction_strategy:
      check_format:
        # State 1: Check if format is valid
      validate_length:
        # State 2: Validate length constraints
      generation_strategy:
        # Nested FSM
        generate_template:
          # Nested state 1
        apply_formatting:
          # Nested state 2
    validation_strategy:
      check_required:
        # Another top-level strategy FSM
      check_uniqueness:
        # State 2
```

---

**Next Steps:**
1. Review and refine this spec
2. Clarify open questions
3. Agree on YAML structure details
4. Define report format
5. Begin implementation
