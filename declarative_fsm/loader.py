"""
YAML configuration loader for declarative FSM.
"""

import yaml
from typing import Dict, Any, Set, List
from pathlib import Path


# Define allowed states per strategy (based on example_config.yaml)
ALLOWED_STATES: Dict[str, Set[str]] = {
    "field_selection_strategy": {
        "check_completeness",
        "convert_to_canon"
    },
    "extraction_strategy": {
        "validate_type",
        "check_format",
        "validate_length"
    },
    "generation_strategy": {
        "format"
    },
    "validation_strategy": {
        "llm_eval"
    },
    "calculation_strategy": {
        "calculation"
    }
}

# Strategies that can be nested (appear as nested strategies, not top-level states)
NESTED_STRATEGIES: Set[str] = {
    "generation_strategy"  # Can be nested under extraction_strategy
}


def _is_nested_strategy(key: str, value: Dict[str, Any]) -> bool:
    """
    Check if a key-value pair represents a nested strategy.
    
    A nested strategy is identified by having nested dicts (potential states or nested strategies).
    
    Args:
        key: The key name
        value: The value (should be a dict)
        
    Returns:
        True if this looks like a nested strategy, False otherwise
    """
    if not isinstance(value, dict):
        return False
    
    # Check if this looks like a nested strategy (has nested dicts)
    has_nested_dicts = any(isinstance(v, dict) for v in value.values())
    return has_nested_dicts


def _validate_strategy(field_name: str, strategy_name: str, strategy_config: Dict[str, Any], 
                      errors: List[str], path: str = "") -> None:
    """
    Validate that a strategy only uses allowed states.
    
    Args:
        field_name: Name of the field being validated
        strategy_name: Name of the strategy
        strategy_config: Strategy configuration dictionary
        errors: List to append validation errors to
        path: Current path in the config (for error messages)
    """
    if strategy_name not in ALLOWED_STATES:
        # Unknown strategy - allow it but don't validate states (for extensibility)
        # Still validate nested strategies if any
        for key, value in strategy_config.items():
            if _is_nested_strategy(key, value):
                nested_path = f"{path}.{strategy_name}.{key}" if path else f"{field_name}.{strategy_name}.{key}"
                _validate_strategy(field_name, key, value, errors, nested_path)
        return
    
    allowed_states = ALLOWED_STATES[strategy_name]
    states_found = []
    nested_strategies_found = []
    
    for key, value in strategy_config.items():
        if _is_nested_strategy(key, value):
            # This is a nested strategy (e.g., generation_strategy nested under extraction_strategy)
            nested_strategies_found.append(key)
            # Recursively validate the nested strategy
            nested_path = f"{path}.{strategy_name}.{key}" if path else f"{field_name}.{strategy_name}.{key}"
            _validate_strategy(field_name, key, value, errors, nested_path)
        else:
            # This is a state
            states_found.append(key)
    
    # Check if all states are allowed
    invalid_states = set(states_found) - allowed_states
    if invalid_states:
        error_path = path if path else f"{field_name}.{strategy_name}"
        errors.append(
            f"Invalid states in {error_path}: {sorted(invalid_states)}. "
            f"Allowed states for {strategy_name}: {sorted(allowed_states)}"
        )


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that the configuration follows the allowed state rules.
    
    Args:
        config: Configuration dictionary loaded from YAML
        
    Raises:
        ValueError: If configuration contains invalid state-strategy combinations
    """
    if 'fields' not in config:
        return  # Will be caught by load_config
    
    errors = []
    fields = config.get('fields', {})
    
    for field_name, field_config in fields.items():
        if not isinstance(field_config, dict):
            errors.append(f"Field '{field_name}' must be a dictionary")
            continue
        
        # Validate each strategy in the field
        for strategy_name, strategy_config in field_config.items():
            if not isinstance(strategy_config, dict):
                errors.append(f"Strategy '{strategy_name}' in field '{field_name}' must be a dictionary")
                continue
            
            _validate_strategy(field_name, strategy_name, strategy_config, errors)
    
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_message)


def load_config(config_path: str, validate: bool = True) -> Dict[str, Any]:
    """
    Load and parse YAML configuration file.
    
    Args:
        config_path: Path to YAML configuration file
        validate: If True, validate the configuration structure and allowed states
        
    Returns:
        Parsed configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValueError: If configuration structure is invalid or contains invalid states
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if not config:
        raise ValueError("Configuration file is empty")
    
    if 'fields' not in config:
        raise ValueError("Configuration must contain 'fields' key")
    
    # Validate configuration if requested
    if validate:
        validate_config(config)
    
    return config
