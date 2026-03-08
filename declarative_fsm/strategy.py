"""
Strategy execution handlers for declarative FSM states.

Each state has its own handler function that implements the pass/fail logic
for that specific state within its strategy context.
"""

import random
from typing import Dict, Any, Callable, Optional

from .scripts.debt_capacity import debt_capacity


# Handler function type
# Handlers receive: data, state_config, field_name, context
# Context is a mutable dict that persists across states for the same field
HandlerFunc = Callable[[Any, Dict[str, Any], str, Dict[str, Any]], bool]


def check_completeness_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for check_completeness state in field_selection_strategy.
    
    Checks if all required fields (from description list) are present in the data.
    
    Args:
        data: Input data dictionary
        state_config: State configuration (should contain 'description' with list of required fields)
        field_name: Name of the field being validated
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if all required fields are present, False otherwise
    """
    # Get required fields from description
    required_fields = state_config.get('description', [])
    if not isinstance(required_fields, list):
        # Fallback to random if description is not a list
        return random.random() < 0.8
    
    # Get field data (could be nested)
    field_data = data.get(field_name, {})
    
    # Check if all required fields are present
    if isinstance(field_data, dict):
        for required_field in required_fields:
            if required_field not in field_data:
                return False
        # Store found fields in context for use by subsequent states
        context['required_fields_found'] = required_fields
        context['field_data'] = field_data
        return True
    
    # If field_data is not a dict, can't check completeness
    return False


def convert_to_canon_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for convert_to_canon state in field_selection_strategy.
    
    Checks if conversion to canonical form should be performed (based on description boolean).
    
    Args:
        data: Input data dictionary
        state_config: State configuration (should contain 'description' with boolean)
        field_name: Name of the field being processed
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if conversion should proceed, False otherwise
    """
    # Get conversion flag from description
    should_convert = state_config.get('description', True)
    
    # Read from context (set by check_completeness)
    required_fields = context.get('required_fields_found', [])
    
    # Get most_current_data (transformed data so far)
    most_current_data = context.get('most_current_data', {})
    
    # For MVP: if flag is True, pass; if False, fail
    # Future: could implement actual conversion logic here
    if isinstance(should_convert, bool):
        if should_convert and most_current_data:
            # Get canonical mapping from context
            canonical_mapping = context.get('canonical_mapping', {})
            
            # Transform keys to canonical form
            canonical_data = {}
            for old_key, value in most_current_data.items():
                # Use canonical key if mapping exists, otherwise keep original key
                new_key = canonical_mapping.get(old_key, old_key)
                canonical_data[new_key] = value
            
            # Store converted data in context for next states
            context['canonical_data'] = {
                'original': most_current_data,
                'converted': True,
                'fields': required_fields
            }
            
            # Update most_current_data with canonical keys (right before returning True)
            context['most_current_data'] = canonical_data
        return should_convert
    
    # Fallback to random if description is not boolean
    return random.random() < 0.8


def extraction_check_format_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for check_format state in extraction_strategy.
    
    Validates the format of the field data.
    
    Args:
        data: Input data dictionary
        state_config: State configuration
        field_name: Name of the field being validated
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if format is valid, False otherwise
    """
    # Try to read canonical data from context (set by convert_to_canon)
    canonical_data = context.get('canonical_data')
    if canonical_data:
        # Use canonical data if available
        field_data = canonical_data.get('original', {})
        context['format_check_source'] = 'canonical'
    else:
        # Fall back to raw data
        field_data = data.get(field_name)
        context['format_check_source'] = 'raw'
    
    # For MVP: basic check - if data exists and is not empty, pass
    # Future: implement actual format validation based on state_config
    if field_data is None:
        return False
    
    if isinstance(field_data, dict):
        # If it's a dict, check if it has any keys
        is_valid = len(field_data) > 0
        if is_valid:
            context['format_validated'] = True
            context['validated_fields'] = list(field_data.keys())
        return is_valid
    
    if isinstance(field_data, str):
        # If it's a string, check if it's not empty
        is_valid = len(field_data.strip()) > 0
        if is_valid:
            context['format_validated'] = True
        return is_valid
    
    # For other types, assume valid if not None
    context['format_validated'] = True
    return True


def extraction_validate_type_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for validate_type state in extraction_strategy.
    
    Validates data types based on allowed type specified in state_config description.
    Description should be a single value: "str", "int", "float", or "empty"
    All sub-fields must match the specified type.
    
    Args:
        data: Input data dictionary
        state_config: State configuration (should contain 'description' with single allowed type)
        field_name: Name of the field being validated
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if all sub-field values match the allowed type, False otherwise
    """
    # Get allowed type from description (single value: "str", "int", "float", or "empty")
    allowed_type = state_config.get('description', '')
    if not isinstance(allowed_type, str):
        # If description is not a string, fallback to accepting all
        allowed_type = None
    
    # Normalize allowed type (lowercase)
    if allowed_type:
        allowed_type = allowed_type.lower().strip()
        # Validate it's one of the supported types
        if allowed_type not in ["str", "int", "float", "empty"]:
            allowed_type = None
    
    # Get most_current_data (transformed data so far)
    most_current_data = context.get('most_current_data', {})
    
    # Fallback to raw field data if most_current_data is not available
    if not most_current_data:
        most_current_data = data.get(field_name, {})
    
    if not isinstance(most_current_data, dict):
        # If not a dict, can't validate sub-fields
        return False
    
    # Validate each sub-field's type against allowed types
    type_validation_results = {}
    all_valid = True
    converted_values = {}
    
    for key, value in most_current_data.items():
        detected_type = None
        
        # Detect the type of the value
        if value is None or value == "":
            detected_type = "empty"
        elif isinstance(value, str):
            value_stripped = value.strip()
            if value_stripped == "":
                detected_type = "empty"
            else:
                # Try to convert to int first
                try:
                    int_value = int(value_stripped)
                    detected_type = "int"
                    converted_values[key] = int_value
                except ValueError:
                    # Try to convert to float
                    try:
                        float_value = float(value_stripped)
                        detected_type = "float"
                        converted_values[key] = float_value
                    except ValueError:
                        # Not a number, it's a regular string
                        detected_type = "str"
        elif isinstance(value, int):
            detected_type = "int"
        elif isinstance(value, float):
            detected_type = "float"
        else:
            # Unknown type
            detected_type = f"unknown_{type(value).__name__}"
        
        type_validation_results[key] = detected_type
        
        # Check if detected type matches the allowed type
        if allowed_type and detected_type != allowed_type:
            all_valid = False
    
    # Store type validation results in context
    context['type_validated'] = all_valid
    context['type_validation_results'] = type_validation_results
    if converted_values:
        context['converted_values'] = converted_values
    
    # Update most_current_data with converted values if validation passed (right before returning True)
    if all_valid and converted_values:
        most_current_data = context.get('most_current_data', {})
        # Update values that were converted (e.g., "15" -> 15)
        for key, converted_value in converted_values.items():
            if key in most_current_data:
                most_current_data[key] = converted_value
        context['most_current_data'] = most_current_data
    
    return all_valid


def extraction_validate_length_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for validate_length state in extraction_strategy.
    
    Validates length constraints of the field data.
    
    Args:
        data: Input data dictionary
        state_config: State configuration
        field_name: Name of the field being validated
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if length is valid, False otherwise
    """
    # Read validated fields from context (set by check_format)
    validated_fields = context.get('validated_fields', [])
    format_validated = context.get('format_validated', False)
    
    # Get field data
    field_data = data.get(field_name)
    
    # For MVP: basic check - if data exists, pass
    # Future: implement actual length validation based on state_config
    if field_data is None:
        return False
    
    if isinstance(field_data, dict):
        is_valid = len(field_data) > 0
        if is_valid:
            # Store length validation results in context
            context['length_validated'] = True
            context['field_count'] = len(field_data)
            if validated_fields:
                context['validated_field_count'] = len(validated_fields)
        return is_valid
    
    if isinstance(field_data, str):
        is_valid = len(field_data.strip()) > 0
        if is_valid:
            context['length_validated'] = True
            context['string_length'] = len(field_data.strip())
        return is_valid
    
    context['length_validated'] = True
    return True


def generation_generate_template_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for generate_template state in generation_strategy.
    
    Generates a template for the field.
    
    Args:
        data: Input data dictionary
        state_config: State configuration
        field_name: Name of the field being processed
        
    Returns:
        True if template generation succeeds, False otherwise
    """
    # For MVP: if field data exists, pass
    # Future: implement actual template generation logic
    field_data = data.get(field_name)
    return field_data is not None


def generation_apply_formatting_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for apply_formatting state in generation_strategy.
    
    Applies formatting rules to the field.
    
    Args:
        data: Input data dictionary
        state_config: State configuration
        field_name: Name of the field being processed
        
    Returns:
        True if formatting succeeds, False otherwise
    """
    # For MVP: if field data exists, pass
    # Future: implement actual formatting logic
    field_data = data.get(field_name)
    return field_data is not None


def generation_format_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for format state in generation_strategy.
    
    Validates that the format description is one of the allowed enum values:
    "table", "freeform", or "fill_template"
    
    Args:
        data: Input data dictionary
        state_config: State configuration (should contain 'description' with enum value)
        field_name: Name of the field being processed
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if format is valid (one of: "table", "freeform", "fill_template"), False otherwise
    """
    # Get format from description (enum: "table", "freeform", or "fill_template")
    format_value = state_config.get('description', '')
    
    if not isinstance(format_value, str):
        return False
    
    format_value = format_value.lower().strip()
    
    # Validate enum value
    valid_formats = {"table", "freeform", "fill_template"}
    
    if format_value not in valid_formats:
        return False
    
    # Store format in context
    context['format'] = format_value
    
    return True


def validation_check_required_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for check_required state in validation_strategy.
    
    Checks if the field is required and present.
    
    Args:
        data: Input data dictionary
        state_config: State configuration
        field_name: Name of the field being validated
        
    Returns:
        True if field is present (or not required), False otherwise
    """
    # Check if field exists in data
    return field_name in data and data[field_name] is not None


def validation_check_uniqueness_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for check_uniqueness state in validation_strategy.
    
    Checks if the field value is unique.
    
    Args:
        data: Input data dictionary
        state_config: State configuration
        field_name: Name of the field being validated
        
    Returns:
        True if value is unique (or uniqueness not required), False otherwise
    """
    # For MVP: always pass (uniqueness check would require comparing with other records)
    # Future: implement actual uniqueness validation
    return True


def validation_llm_eval_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for llm_eval state in validation_strategy.
    
    Updates context with eval_type and metrics from description.
    Description should be a list of English sentence metrics (e.g., "score how readable it is").
    
    Args:
        data: Input data dictionary
        state_config: State configuration (should contain 'description' with list of metrics)
        field_name: Name of the field being validated
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if metrics are valid, False otherwise
    """
    # Get metrics from description (list of English sentences)
    metrics = state_config.get('description', [])
    
    if not isinstance(metrics, list):
        # If description is not a list, fail
        return False
    
    # Update context with eval_type and metrics
    context['eval_type'] = "llm"
    context['metrics'] = metrics
    
    return True


def calculation_handler(data: Any, state_config: Dict[str, Any], field_name: str, context: Dict[str, Any]) -> bool:
    """
    Handler for calculation state in calculation_strategy.
    
    Performs calculations based on description enum: "aggregation" or "debt_capacity"
    
    Args:
        data: Input data dictionary
        state_config: State configuration (should contain 'description' with enum value)
        field_name: Name of the field being processed
        context: Mutable context dictionary for passing data between states
        
    Returns:
        True if calculation succeeds, False otherwise
    """
    # Get calculation type from description (enum: "aggregation" or "debt_capacity")
    calculation_type = state_config.get('description', '')
    
    if not isinstance(calculation_type, str):
        return False
    
    calculation_type = calculation_type.lower().strip()
    
    # Validate enum value
    if calculation_type not in ["aggregation", "debt_capacity"]:
        return False
    
    # Get most_current_data (transformed data so far)
    most_current_data = context.get('most_current_data', {})
    
    if not isinstance(most_current_data, dict):
        return False
    
    if calculation_type == "aggregation":
        # Aggregation: take a "key" from the data and add all values that share the same key
        # The key to group by should be specified in state_config
        group_key = state_config.get('key')
        value_key = state_config.get('value_key', 'value')  # Default to 'value' if not specified
        
        if not group_key:
            # If no key specified, can't perform aggregation
            return False
        
        # Group values by the specified key and sum them
        aggregated_values = {}
        for item_key, item_value in most_current_data.items():
            if isinstance(item_value, dict):
                group_value = item_value.get(group_key)
                if group_value is not None:
                    # Get the value to aggregate
                    value_to_add = item_value.get(value_key, 0)
                    
                    # Try to convert to number
                    try:
                        if isinstance(value_to_add, str):
                            numeric_value = float(value_to_add)
                        else:
                            numeric_value = float(value_to_add)
                        
                        # Add to aggregated values
                        if group_value not in aggregated_values:
                            aggregated_values[group_value] = 0
                        aggregated_values[group_value] += numeric_value
                    except (ValueError, TypeError):
                        # Can't convert to number, skip
                        continue
        
        # Store aggregated results in context
        context['calculation_type'] = 'aggregation'
        context['aggregated_values'] = aggregated_values
        context['calculation_complete'] = True
        
        # Update most_current_data with calculation results (right before returning True)
        most_current_data['aggregation'] = aggregated_values
        context['most_current_data'] = most_current_data
        
        return True
    
    elif calculation_type == "debt_capacity":
        # Call the debt_capacity function with the financials data
        try:
            # The most_current_data should contain all the required fields for debt_capacity
            # (YEAR, ER12, ER32, P88, EM06, ER13, ER41, P19, P14, P03, P20)
            financials = most_current_data.copy()
            
            # Call debt_capacity function (exposure parameter is not used, pass None)
            debt_capacity_results = debt_capacity(financials, exposure=None)
            
            # Replace most_current_data with only the calculated results
            # This prevents duplicate fields (input fields vs calculated results) in the final output
            # The debt_capacity function returns: year, ER12, ER32, P88, EM06, Re_CapEx, int_sub, int_hypo, FCF, DC, DCU
            most_current_data = debt_capacity_results.copy()
            
            # Store the full results under 'debt_capacity' key for reference
            most_current_data['debt_capacity'] = debt_capacity_results
            
            context['calculation_type'] = 'debt_capacity'
            context['calculation_complete'] = True
            context['most_current_data'] = most_current_data
            
            return True
        except (ValueError, KeyError, TypeError) as e:
            # If debt_capacity calculation fails (missing fields, wrong types, etc.), return False
            context['calculation_error'] = str(e)
            return False
    
    return False


# Registry mapping (strategy_name, state_name) -> handler function
HANDLERS: Dict[tuple, HandlerFunc] = {
    # field_selection_strategy handlers
    ("field_selection_strategy", "check_completeness"): check_completeness_handler,
    ("field_selection_strategy", "convert_to_canon"): convert_to_canon_handler,
    
    # extraction_strategy handlers
    ("extraction_strategy", "check_format"): extraction_check_format_handler,
    ("extraction_strategy", "validate_type"): extraction_validate_type_handler,
    ("extraction_strategy", "validate_length"): extraction_validate_length_handler,
    
    # generation_strategy handlers (nested under extraction_strategy)
    ("generation_strategy", "generate_template"): generation_generate_template_handler,  # Deprecated, kept for backward compatibility
    ("generation_strategy", "apply_formatting"): generation_apply_formatting_handler,  # Deprecated, kept for backward compatibility
    ("generation_strategy", "format"): generation_format_handler,
    
    # validation_strategy handlers
    ("validation_strategy", "check_required"): validation_check_required_handler,  # Deprecated, kept for backward compatibility
    ("validation_strategy", "check_uniqueness"): validation_check_uniqueness_handler,  # Deprecated, kept for backward compatibility
    ("validation_strategy", "llm_eval"): validation_llm_eval_handler,
    
    # calculation_strategy handlers
    ("calculation_strategy", "calculation"): calculation_handler,
}


def execute_state(strategy_name: str, state_name: str, data: Any, 
                 state_config: Dict[str, Any], field_name: str, 
                 context: Dict[str, Any]) -> bool:
    """
    Execute a state's criteria check by dispatching to the appropriate handler.
    
    Args:
        strategy_name: Name of the strategy (e.g., "field_selection_strategy")
        state_name: Name of the state (e.g., "check_completeness")
        data: Input data dictionary
        state_config: State configuration from YAML
        field_name: Name of the field being processed
        context: Mutable context dictionary shared across all states for this field.
                 Handlers can read from and write to this context to pass data between states.
        
    Returns:
        True if check passes, False otherwise
        
    Note:
        If no handler is found for the (strategy_name, state_name) combination,
        falls back to random pass/fail (80% pass rate) for MVP compatibility.
        
        The context dictionary persists across all states within the same field,
        allowing states to pass payloads to subsequent states, even across
        different strategies (e.g., field_selection_strategy → extraction_strategy).
    """
    key = (strategy_name, state_name)
    handler = HANDLERS.get(key)
    
    if handler:
        try:
            return handler(data, state_config, field_name, context)
        except Exception as e:
            # If handler raises an exception, log and fallback to random
            # In production, you might want to log this error
            print(f"Warning: Handler for {key} raised exception: {e}. Using fallback.")
            return random.random() < 0.8
    
    # Fallback to random if no handler found
    # This allows the system to work even if new states are added without handlers
    return random.random() < 0.8
