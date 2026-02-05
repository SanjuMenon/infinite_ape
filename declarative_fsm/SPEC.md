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
- For MVP: Random pass/fail (placeholder for future implementation)
- Each state can have criteria configuration (structure TBD)

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
   - Execute state criteria checks (random for MVP)
   - Track pass/fail status
   - Manage state transitions

4. **Reporting System**
   - Generate execution report
   - Track FSM initialization status
   - Identify field usability issues

### Phase 2: Future Enhancements (Out of Scope for MVP)

- Real criteria evaluation (not random)
- Retry mechanisms
- Fallback strategies
- Visualization
- Performance metrics

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
