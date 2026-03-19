"""
Unit tests for strategy handlers.

Tests all handler functions in strategy.py to ensure they work correctly
with various input scenarios, edge cases, and error conditions.
"""

import pytest
from declarative_fsm import strategy


class TestCheckCompletenessHandler:
    """Tests for check_completeness_handler."""
    
    def test_all_required_fields_present(self):
        """Test that handler passes when all required fields are present."""
        data = {"test_field": {"field1": "value1", "field2": "value2"}}
        state_config = {"description": ["field1", "field2"]}
        context = {}
        
        result = strategy.check_completeness_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["required_fields_found"] == ["field1", "field2"]
        assert context["field_data"] == {"field1": "value1", "field2": "value2"}
    
    def test_missing_required_field(self):
        """Test that handler fails when a required field is missing."""
        data = {"test_field": {"field1": "value1"}}
        state_config = {"description": ["field1", "field2"]}
        context = {}
        
        result = strategy.check_completeness_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_empty_required_fields_list(self):
        """Test that handler passes when no fields are required."""
        data = {"test_field": {"field1": "value1"}}
        state_config = {"description": []}
        context = {}
        
        result = strategy.check_completeness_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
    
    def test_field_data_not_dict(self):
        """Test that handler fails when field data is not a dict."""
        data = {"test_field": "not a dict"}
        state_config = {"description": ["field1"]}
        context = {}
        
        result = strategy.check_completeness_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_missing_field_in_data(self):
        """Test that handler fails when field is missing from data."""
        data = {}
        state_config = {"description": ["field1"]}
        context = {}
        
        result = strategy.check_completeness_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_description_not_list(self):
        """Test that handler handles non-list description (uses random fallback)."""
        data = {"test_field": {"field1": "value1"}}
        state_config = {"description": "not a list"}
        context = {}
        
        # This will use random fallback, so we just check it doesn't crash
        result = strategy.check_completeness_handler(
            data, state_config, "test_field", context
        )
        
        assert isinstance(result, bool)


class TestConvertToCanonHandler:
    """Tests for convert_to_canon_handler."""
    
    def test_description_true_with_mapping(self):
        """Test that handler passes and converts keys when description is True."""
        data = {}
        state_config = {"description": True}
        context = {
            "most_current_data": {"old_key1": "value1", "old_key2": "value2"},
            "canonical_mapping": {"old_key1": "new_key1", "old_key2": "new_key2"}
        }
        
        result = strategy.convert_to_canon_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["most_current_data"] == {"new_key1": "value1", "new_key2": "value2"}
        assert context["canonical_data"]["converted"] is True
    
    def test_description_true_no_mapping(self):
        """Test that handler passes but keeps original keys when no mapping exists."""
        data = {}
        state_config = {"description": True}
        context = {
            "most_current_data": {"key1": "value1"},
            "canonical_mapping": {}
        }
        
        result = strategy.convert_to_canon_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["most_current_data"] == {"key1": "value1"}
    
    def test_description_false(self):
        """Test that handler fails when description is False."""
        data = {}
        state_config = {"description": False}
        context = {"most_current_data": {"key1": "value1"}}
        
        result = strategy.convert_to_canon_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_partial_mapping(self):
        """Test that handler handles partial mappings correctly."""
        data = {}
        state_config = {"description": True}
        context = {
            "most_current_data": {"old_key1": "value1", "old_key2": "value2"},
            "canonical_mapping": {"old_key1": "new_key1"}
        }
        
        result = strategy.convert_to_canon_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert "new_key1" in context["most_current_data"]
        assert "old_key2" in context["most_current_data"]  # Unmapped key kept


class TestExtractionValidateTypeHandler:
    """Tests for extraction_validate_type_handler."""
    
    def test_validate_int_all_strings(self):
        """Test that handler validates and converts string integers."""
        data = {"test_field": {"amount": "15", "count": "30"}}
        state_config = {"description": "int"}
        context = {"most_current_data": {"amount": "15", "count": "30"}}
        
        result = strategy.extraction_validate_type_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["most_current_data"]["amount"] == 15
        assert context["most_current_data"]["count"] == 30
        assert context["type_validated"] is True
    
    def test_validate_int_mixed_types(self):
        """Test that handler fails when types don't match."""
        data = {"test_field": {"amount": "15", "name": "test"}}
        state_config = {"description": "int"}
        context = {"most_current_data": {"amount": "15", "name": "test"}}
        
        result = strategy.extraction_validate_type_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
        assert context["type_validated"] is False
    
    def test_validate_str(self):
        """Test that handler validates string types."""
        data = {"test_field": {"name": "test", "address": "123 Main St"}}
        state_config = {"description": "str"}
        context = {"most_current_data": {"name": "test", "address": "123 Main St"}}
        
        result = strategy.extraction_validate_type_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
    
    def test_validate_float(self):
        """Test that handler validates and converts float types."""
        data = {"test_field": {"price": "15.5", "rate": "3.14"}}
        state_config = {"description": "float"}
        context = {"most_current_data": {"price": "15.5", "rate": "3.14"}}
        
        result = strategy.extraction_validate_type_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["most_current_data"]["price"] == 15.5
        assert context["most_current_data"]["rate"] == 3.14
    
    def test_validate_empty(self):
        """Test that handler validates empty values."""
        data = {"test_field": {"field1": "", "field2": None}}
        state_config = {"description": "empty"}
        context = {"most_current_data": {"field1": "", "field2": None}}
        
        result = strategy.extraction_validate_type_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
    
    def test_most_current_data_not_dict(self):
        """Test that handler fails when most_current_data is not a dict."""
        data = {"test_field": "not a dict"}
        state_config = {"description": "int"}
        context = {"most_current_data": "not a dict"}
        
        result = strategy.extraction_validate_type_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_fallback_to_raw_data(self):
        """Test that handler falls back to raw data when most_current_data is empty."""
        data = {"test_field": {"amount": "15"}}
        state_config = {"description": "int"}
        context = {}
        
        result = strategy.extraction_validate_type_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True


class TestExtractionCheckFormatHandler:
    """Tests for extraction_check_format_handler."""
    
    def test_valid_dict_data(self):
        """Test that handler passes for valid dict data."""
        data = {"test_field": {"key1": "value1", "key2": "value2"}}
        state_config = {}
        context = {}
        
        result = strategy.extraction_check_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["format_validated"] is True
        assert context["validated_fields"] == ["key1", "key2"]
    
    def test_valid_string_data(self):
        """Test that handler passes for valid string data."""
        data = {"test_field": "some string"}
        state_config = {}
        context = {}
        
        result = strategy.extraction_check_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["format_validated"] is True
    
    def test_empty_dict(self):
        """Test that handler fails for empty dict."""
        data = {"test_field": {}}
        state_config = {}
        context = {}
        
        result = strategy.extraction_check_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_empty_string(self):
        """Test that handler fails for empty string."""
        data = {"test_field": "   "}
        state_config = {}
        context = {}
        
        result = strategy.extraction_check_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_missing_field(self):
        """Test that handler fails when field is missing."""
        data = {}
        state_config = {}
        context = {}
        
        result = strategy.extraction_check_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_uses_canonical_data(self):
        """Test that handler uses canonical data from context if available."""
        data = {"test_field": {"key1": "value1"}}
        state_config = {}
        context = {
            "canonical_data": {
                "original": {"canonical_key1": "value1"}
            }
        }
        
        result = strategy.extraction_check_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["format_check_source"] == "canonical"


class TestGenerationFormatHandler:
    """Tests for generation_format_handler."""
    
    def test_valid_table_format(self):
        """Test that handler passes for 'table' format."""
        data = {}
        state_config = {"description": "table"}
        context = {}
        
        result = strategy.generation_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["format"] == "table"
    
    def test_valid_freeform_format(self):
        """Test that handler passes for 'freeform' format."""
        data = {}
        state_config = {"description": "freeform"}
        context = {}
        
        result = strategy.generation_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["format"] == "freeform"
    
    def test_valid_fill_template_format(self):
        """Test that handler passes for 'fill_template' format."""
        data = {}
        state_config = {"description": "fill_template"}
        context = {}
        
        result = strategy.generation_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["format"] == "fill_template"
    
    def test_invalid_format(self):
        """Test that handler fails for invalid format."""
        data = {}
        state_config = {"description": "invalid_format"}
        context = {}
        
        result = strategy.generation_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
        assert "format" not in context
    
    def test_case_insensitive(self):
        """Test that handler is case insensitive."""
        data = {}
        state_config = {"description": "TABLE"}
        context = {}
        
        result = strategy.generation_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["format"] == "table"
    
    def test_description_not_string(self):
        """Test that handler fails when description is not a string."""
        data = {}
        state_config = {"description": 123}
        context = {}
        
        result = strategy.generation_format_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False


class TestValidationLLMEvalHandler:
    """Tests for validation_llm_eval_handler."""
    
    def test_valid_metrics_list(self):
        """Test that handler passes and stores metrics for valid list."""
        data = {}
        state_config = {
            "description": [
                "score how readable it is",
                "score how complete the information is"
            ]
        }
        context = {}
        
        result = strategy.validation_llm_eval_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["eval_type"] == "llm"
        assert context["metrics"] == [
            "score how readable it is",
            "score how complete the information is"
        ]
    
    def test_empty_metrics_list(self):
        """Test that handler passes for empty metrics list."""
        data = {}
        state_config = {"description": []}
        context = {}
        
        result = strategy.validation_llm_eval_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["eval_type"] == "llm"
        assert context["metrics"] == []
    
    def test_description_not_list(self):
        """Test that handler fails when description is not a list."""
        data = {}
        state_config = {"description": "not a list"}
        context = {}
        
        result = strategy.validation_llm_eval_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
        assert "eval_type" not in context


class TestCalculationHandler:
    """Tests for calculation_handler."""
    
    def test_aggregation_valid(self):
        """Test that handler performs aggregation correctly."""
        data = {}
        state_config = {
            "description": "aggregation",
            "key": "category",
            "value_key": "amount"
        }
        context = {
            "most_current_data": {
                "item1": {"category": "revenue", "amount": "1000"},
                "item2": {"category": "revenue", "amount": "2000"},
                "item3": {"category": "expense", "amount": "500"}
            }
        }
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert "aggregation" in context["most_current_data"]
        assert context["most_current_data"]["aggregation"]["revenue"] == 3000.0
        assert context["most_current_data"]["aggregation"]["expense"] == 500.0
        assert context["calculation_type"] == "aggregation"
    
    def test_aggregation_missing_key(self):
        """Test that handler fails when key is missing from state_config."""
        data = {}
        state_config = {
            "description": "aggregation",
            "value_key": "amount"
        }
        context = {"most_current_data": {"item1": {"amount": "1000"}}}
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_aggregation_default_value_key(self):
        """Test that handler uses default 'value' for value_key."""
        data = {}
        state_config = {
            "description": "aggregation",
            "key": "category"
        }
        context = {
            "most_current_data": {
                "item1": {"category": "revenue", "value": "1000"}
            }
        }
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
    
    def test_aggregation_non_numeric_values(self):
        """Test that handler skips non-numeric values."""
        data = {}
        state_config = {
            "description": "aggregation",
            "key": "category",
            "value_key": "amount"
        }
        context = {
            "most_current_data": {
                "item1": {"category": "revenue", "amount": "1000"},
                "item2": {"category": "revenue", "amount": "not a number"}
            }
        }
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert context["most_current_data"]["aggregation"]["revenue"] == 1000.0
    
    def test_debt_capacity_valid(self):
        """Test that handler calls debt_capacity function correctly."""
        data = {}
        state_config = {"description": "debt_capacity"}
        context = {
            "most_current_data": {
                "YEAR": 2024,
                "ER12": 15000000,
                "ER32": 3200000,
                "P88": -500000,
                "EM06": -200000,
                "ER13": 1000000,
                "ER41": 500000,
                "P19": 2000000,
                "P14": 5000000,
                "P03": 3000000,
                "P20": 1000000
            }
        }
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is True
        assert "debt_capacity" in context["most_current_data"]
        assert context["calculation_type"] == "debt_capacity"
        assert "FCF" in context["most_current_data"]
        assert "DC" in context["most_current_data"]
        assert "DCU" in context["most_current_data"]
    
    def test_debt_capacity_missing_fields(self):
        """Test that handler fails when required fields are missing."""
        data = {}
        state_config = {"description": "debt_capacity"}
        context = {
            "most_current_data": {
                "YEAR": 2024,
                "ER12": 15000000
                # Missing other required fields
            }
        }
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
        assert "calculation_error" in context
    
    def test_invalid_calculation_type(self):
        """Test that handler fails for invalid calculation type."""
        data = {}
        state_config = {"description": "invalid_type"}
        context = {"most_current_data": {}}
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False
    
    def test_most_current_data_not_dict(self):
        """Test that handler fails when most_current_data is not a dict."""
        data = {}
        state_config = {"description": "aggregation", "key": "category"}
        context = {"most_current_data": "not a dict"}
        
        result = strategy.calculation_handler(
            data, state_config, "test_field", context
        )
        
        assert result is False


class TestExecuteState:
    """Tests for execute_state function."""
    
    def test_execute_existing_handler(self):
        """Test that execute_state calls existing handler correctly."""
        data = {"test_field": {"field1": "value1", "field2": "value2"}}
        state_config = {"description": ["field1", "field2"]}
        context = {}
        
        result = strategy.execute_state(
            "field_selection_strategy",
            "check_completeness",
            data,
            state_config,
            "test_field",
            context
        )
        
        assert result is True
        assert "required_fields_found" in context
    
    def test_execute_missing_handler(self):
        """Test that execute_state falls back to random for missing handler."""
        data = {}
        state_config = {}
        context = {}
        
        # This will use random fallback
        result = strategy.execute_state(
            "unknown_strategy",
            "unknown_state",
            data,
            state_config,
            "test_field",
            context
        )
        
        assert isinstance(result, bool)
    
    def test_execute_handler_exception(self):
        """Test that execute_state handles handler exceptions gracefully."""
        # Create a handler that raises an exception
        def failing_handler(data, state_config, field_name, context):
            raise ValueError("Test exception")
        
        # Temporarily add failing handler
        original_handler = strategy.HANDLERS.get(("field_selection_strategy", "check_completeness"))
        strategy.HANDLERS[("field_selection_strategy", "check_completeness")] = failing_handler
        
        try:
            data = {}
            state_config = {}
            context = {}
            
            # Should not raise, but fall back to random
            result = strategy.execute_state(
                "field_selection_strategy",
                "check_completeness",
                data,
                state_config,
                "test_field",
                context
            )
            
            assert isinstance(result, bool)
        finally:
            # Restore original handler
            if original_handler:
                strategy.HANDLERS[("field_selection_strategy", "check_completeness")] = original_handler
