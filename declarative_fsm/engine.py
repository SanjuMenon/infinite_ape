"""
FSM Engine for executing hierarchical FSMs from YAML configuration.
"""

import json
import copy
import pickle
from typing import Dict, Any, List
from pathlib import Path
import yaml
from . import strategy


class FSMEngine:
    """
    Engine for executing hierarchical FSMs defined in YAML configuration.
    """
    
    def __init__(self, config: Dict[str, Any], canonical_config_path: str = None):
        """
        Initialize FSM engine with configuration.
        
        Args:
            config: Configuration dictionary loaded from YAML
            canonical_config_path: Optional path to canonical mapping config file
        """
        self.config = config
        self.fields = config.get('fields', {})
        
        # Load canonical mappings if provided
        self.canonical_mappings = {}
        if canonical_config_path:
            self.canonical_mappings = self._load_canonical_config(canonical_config_path)
    
    def _load_canonical_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load canonical key mappings from YAML file.
        
        Args:
            config_path: Path to canonical config YAML file
            
        Returns:
            Dictionary mapping field names to their canonical key mappings
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Return empty dict if file doesn't exist (optional)
            return {}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config if config else {}
        
    def execute(self, data: Any) -> Dict[str, Any]:
        """
        Execute FSMs on provided data.
        
        Args:
            data: JSON data (dict or JSON string)
            
        Returns:
            JSON report dictionary with execution results, including 'most_current_data_list'
        """
        # Parse JSON if string
        if isinstance(data, str):
            data = json.loads(data)
        
        report = {
            "execution_summary": {
                "total_fields": len(self.fields),
                "fields_passed": 0,
                "fields_failed": 0
            },
            "fields": {},
            "list_of_bundles": []
        }
        
        # List to collect most_current_data for each field
        most_current_data_list: List[Dict[str, Any]] = []
        
        # Execute FSMs for each field
        for field_name, field_config in self.fields.items():
            # Create context dictionary for this field (shared across all strategies)
            context = {}
            
            # Initialize most_current_data with deep copy of original field data
            field_data = data.get(field_name, {})
            context['most_current_data'] = copy.deepcopy(field_data) if isinstance(field_data, dict) else {}
            
            # Get canonical mapping for this field (if available)
            canonical_mapping = self.canonical_mappings.get(field_name, {})
            context['canonical_mapping'] = canonical_mapping
            
            field_result = self._execute_field(field_name, field_config, data, context)
            # Include final bundle (context) in the report after all strategies pass
            field_result["bundle"] = context
            report["fields"][field_name] = field_result
            
            # Add bundle to list_of_bundles
            report["list_of_bundles"].append(context)
            
            # Collect most_current_data for this field
            most_current_data = context.get('most_current_data', {})
            eval_type = context.get('eval_type', None)
            metrics = context.get('metrics', None)
            format_value = context.get('format', None)
            
            most_current_data_list.append({
                'field_name': field_name,
                'most_current_data': most_current_data,
                'eval_type': eval_type,
                'metrics': metrics,
                'format': format_value
            })
            
            # Update summary
            if field_result["status"] == "passed":
                report["execution_summary"]["fields_passed"] += 1
            else:
                report["execution_summary"]["fields_failed"] += 1
        
        # Include most_current_data_list in the report
        report["most_current_data_list"] = most_current_data_list
        
        return report
    
    def _execute_field(self, field_name: str, field_config: Dict[str, Any], 
                      data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all strategy FSMs for a field.
        
        Args:
            field_name: Name of the field
            field_config: Configuration for this field
            data: Input data
            context: Mutable context dictionary shared across all strategies for this field
            
        Returns:
            Field execution result
        """
        result = {
            "status": "passed",
            "strategies": {}
        }
        
        # Execute each strategy FSM (context is shared across strategies)
        for strategy_name, strategy_config in field_config.items():
            strategy_result = self._execute_strategy(
                strategy_name, 
                strategy_config, 
                data,
                field_name,
                context,
                parent_passed=True
            )
            result["strategies"][strategy_name] = strategy_result
            
            # Field fails if any strategy fails
            if strategy_result["status"] == "not_passed":
                result["status"] = "not_passed"
        
        return result
    
    def _execute_strategy(self, strategy_name: str, strategy_config: Dict[str, Any], 
                         data: Any, field_name: str, context: Dict[str, Any],
                         parent_passed: bool = True) -> Dict[str, Any]:
        """
        Execute a strategy FSM (can be nested).
        
        Args:
            strategy_name: Name of the strategy
            strategy_config: Configuration for this strategy
            data: Input data
            field_name: Name of the field this strategy belongs to
            context: Mutable context dictionary shared across all strategies for this field
            parent_passed: Whether parent FSM passed (for nested FSMs)
            
        Returns:
            Strategy execution result
        """
        result = {
            "status": "not_passed",
            "states_executed": [],
            "failed_at": None,
            "nested_strategies": {}
        }
        
        # If parent didn't pass, don't execute
        if not parent_passed:
            return result
        
        # Separate states from nested strategies
        states, nested_strategies = self._separate_states_and_nested(strategy_config)
        
        if not states:
            # No states to execute, consider it passed (empty strategy)
            result["status"] = "passed"
            return result
        
        # Execute states sequentially (context is passed through)
        fsm_result = self._execute_linear_fsm(states, data, field_name, strategy_name, context)
        
        result["status"] = fsm_result["status"]
        result["states_executed"] = fsm_result["states_executed"]
        result["failed_at"] = fsm_result["failed_at"]
        
        # Only execute nested strategies if this FSM passed
        if fsm_result["status"] == "passed" and nested_strategies:
            for nested_name, nested_config in nested_strategies.items():
                nested_result = self._execute_strategy(
                    nested_name,
                    nested_config,
                    data,
                    field_name,
                    context,  # Same context shared with parent
                    parent_passed=(fsm_result["status"] == "passed")
                )
                result["nested_strategies"][nested_name] = nested_result
        
        return result
    
    def _separate_states_and_nested(self, strategy_config: Dict[str, Any]) -> tuple:
        """
        Separate state definitions from nested strategy definitions.
        
        A key is considered a nested strategy if its value is a dict
        that contains other dicts (potential states or nested strategies).
        
        Args:
            strategy_config: Strategy configuration dictionary
            
        Returns:
            Tuple of (states_dict, nested_strategies_dict)
        """
        states = {}
        nested_strategies = {}
        
        for key, value in strategy_config.items():
            if isinstance(value, dict):
                # Check if this looks like a nested strategy (has nested dicts)
                has_nested_dicts = any(isinstance(v, dict) for v in value.values())
                if has_nested_dicts:
                    nested_strategies[key] = value
                else:
                    # It's a state configuration
                    states[key] = value
            else:
                # Simple value, treat as state
                states[key] = value
        
        return states, nested_strategies
    
    def _execute_linear_fsm(self, states: Dict[str, Any], data: Any, 
                           field_name: str, strategy_name: str, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a linear FSM with sequential states.
        
        Args:
            states: Dictionary of state configurations
            data: Input data
            field_name: Name of the field
            strategy_name: Name of the strategy
            context: Mutable context dictionary shared across states
            
        Returns:
            FSM execution result
        """
        result = {
            "status": "not_passed",
            "states_executed": [],
            "failed_at": None
        }
        
        # Get state names in order
        state_names = list(states.keys())
        
        if not state_names:
            result["status"] = "passed"
            return result
        
        # Execute states sequentially (context persists across states)
        for i, state_name in enumerate(state_names):
            # Backup most_current_data before state execution (for revert on failure)
            most_current_data_backup = copy.deepcopy(context.get('most_current_data', {}))
            
            # Execute state check using strategy module (context is passed through)
            check_passed = self._execute_state_check(
                strategy_name, state_name, states[state_name], data, field_name, context
            )
            
            result["states_executed"].append(state_name)
            
            if not check_passed:
                # Revert most_current_data to previous successful state
                context['most_current_data'] = most_current_data_backup
                result["failed_at"] = state_name
                return result
        
        # All states passed
        result["status"] = "passed"
        return result
    
    def _execute_state_check(self, strategy_name: str, state_name: str, 
                            state_config: Any, data: Any, field_name: str,
                            context: Dict[str, Any]) -> bool:
        """
        Execute a state's criteria check by delegating to the strategy module.
        
        Args:
            strategy_name: Name of the strategy (e.g., "field_selection_strategy")
            state_name: Name of the state (e.g., "check_completeness")
            state_config: State configuration from YAML
            data: Input data
            field_name: Name of the field
            context: Mutable context dictionary shared across states for this field
            
        Returns:
            True if check passes, False otherwise
        """
        return strategy.execute_state(strategy_name, state_name, data, state_config, field_name, context)
