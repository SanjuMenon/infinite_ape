"""
Strategy execution handlers for declarative FSM states.

Each state has its own handler function that implements the pass/fail logic
for that specific state within its strategy context.
"""

import random
from typing import Dict, Any, Callable, Optional


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
    field_data = context.get('field_data', {})
    required_fields = context.get('required_fields_found', [])
    
    # For MVP: if flag is True, pass; if False, fail
    # Future: could implement actual conversion logic here
    if isinstance(should_convert, bool):
        if should_convert and field_data:
            # Store converted data in context for next states
            context['canonical_data'] = {
                'original': field_data,
                'converted': True,
                'fields': required_fields
            }
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


# Registry mapping (strategy_name, state_name) -> handler function
HANDLERS: Dict[tuple, HandlerFunc] = {
    # field_selection_strategy handlers
    ("field_selection_strategy", "check_completeness"): check_completeness_handler,
    ("field_selection_strategy", "convert_to_canon"): convert_to_canon_handler,
    
    # extraction_strategy handlers
    ("extraction_strategy", "check_format"): extraction_check_format_handler,
    ("extraction_strategy", "validate_length"): extraction_validate_length_handler,
    
    # generation_strategy handlers (nested under extraction_strategy)
    ("generation_strategy", "generate_template"): generation_generate_template_handler,
    ("generation_strategy", "apply_formatting"): generation_apply_formatting_handler,
    
    # validation_strategy handlers
    ("validation_strategy", "check_required"): validation_check_required_handler,
    ("validation_strategy", "check_uniqueness"): validation_check_uniqueness_handler,
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
