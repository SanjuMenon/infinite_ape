# Declarative FSM Test Suite

This directory contains comprehensive unit tests for the declarative FSM system.

## Test Structure

The test suite is organized into the following modules:

- **`test_strategy_handlers.py`**: Unit tests for all strategy handler functions
  - Tests for `check_completeness_handler`
  - Tests for `convert_to_canon_handler`
  - Tests for `extraction_validate_type_handler`
  - Tests for `extraction_check_format_handler`
  - Tests for `generation_format_handler`
  - Tests for `validation_llm_eval_handler`
  - Tests for `calculation_handler` (aggregation and debt_capacity)
  - Tests for `execute_state` function

- **`test_engine.py`**: Unit tests for the FSMEngine class
  - Tests for engine initialization
  - Tests for `execute()` method
  - Tests for `_execute_field()` method
  - Tests for `_execute_strategy()` method
  - Tests for `_execute_linear_fsm()` method
  - Tests for `_load_canonical_config()` method

- **`test_loader.py`**: Unit tests for config loading and validation
  - Tests for `load_config()` function
  - Tests for `validate_config()` function
  - Tests for config validation rules

- **`test_integration.py`**: Integration tests for full system
  - End-to-end execution tests
  - Tests with real-world scenarios
  - Tests for context persistence
  - Tests for data transformations

- **`conftest.py`**: Pytest fixtures and configuration
  - Common fixtures for test data
  - Sample configs and data

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests
pytest declarative_fsm/

# Run with verbose output
pytest declarative_fsm/ -v

# Run with coverage report
pytest declarative_fsm/ --cov=declarative_fsm --cov-report=term-missing
```

### Run Specific Test Files

```bash
# Run only handler tests
pytest declarative_fsm/test_strategy_handlers.py

# Run only engine tests
pytest declarative_fsm/test_engine.py

# Run only loader tests
pytest declarative_fsm/test_loader.py

# Run only integration tests
pytest declarative_fsm/test_integration.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest declarative_fsm/test_strategy_handlers.py::TestCheckCompletenessHandler

# Run a specific test function
pytest declarative_fsm/test_strategy_handlers.py::TestCheckCompletenessHandler::test_all_required_fields_present
```

### Test Markers

Tests can be marked for selective execution:

```bash
# Run only unit tests
pytest declarative_fsm/ -m unit

# Run only integration tests
pytest declarative_fsm/ -m integration

# Skip slow tests
pytest declarative_fsm/ -m "not slow"
```

## Test Coverage

The test suite covers:

- ✅ All handler functions with various input scenarios
- ✅ Edge cases (empty data, missing fields, invalid types)
- ✅ Error handling and exception scenarios
- ✅ Context persistence across states and strategies
- ✅ Data transformations (canonical mapping, type conversion)
- ✅ Calculation handlers (aggregation, debt_capacity)
- ✅ Config validation and loading
- ✅ Engine execution flow
- ✅ Nested strategy execution
- ✅ State failure and revert mechanisms

## Writing New Tests

When adding new functionality:

1. **Add unit tests** for new handlers in `test_strategy_handlers.py`
2. **Add engine tests** if new engine functionality is added
3. **Add integration tests** for end-to-end scenarios
4. **Update fixtures** in `conftest.py` if needed

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<description>`

### Example Test Structure

```python
class TestNewHandler:
    """Tests for new_handler function."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        data = {}
        state_config = {}
        context = {}
        
        # Act
        result = strategy.new_handler(data, state_config, "field", context)
        
        # Assert
        assert result is True
        assert "expected_key" in context
```

## Continuous Integration

These tests are designed to be run in CI/CD pipelines. The `pytest.ini` configuration file ensures consistent test execution across environments.

## Troubleshooting

### Import Errors

If you encounter import errors, ensure you're running tests from the project root:

```bash
cd /path/to/infinite_ape
pytest declarative_fsm/
```

### Missing Dependencies

Install all dependencies:

```bash
pip install -r declarative_fsm/requirements.txt
```

### Test Failures

If tests fail:

1. Check that sample data files exist (`sample_data.json`, `example_config.yaml`)
2. Verify that all handlers are properly registered in `strategy.py`
3. Ensure config validation rules match the test expectations
