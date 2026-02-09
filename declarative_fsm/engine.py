"""
FSM Engine for executing hierarchical FSMs from YAML configuration.
"""

import json
import random
from typing import Dict, Any


class FSMEngine:
    """
    Engine for executing hierarchical FSMs defined in YAML configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FSM engine with configuration.
        
        Args:
            config: Configuration dictionary loaded from YAML
        """
        self.config = config
        self.fields = config.get('fields', {})
        
    def execute(self, data: Any) -> Dict[str, Any]:
        """
        Execute FSMs on provided data.
        
        Args:
            data: JSON data (dict or JSON string)
            
        Returns:
            JSON report dictionary with execution results
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
            "fields": {}
        }
        
        # Execute FSMs for each field
        for field_name, field_config in self.fields.items():
            field_result = self._execute_field(field_name, field_config, data)
            report["fields"][field_name] = field_result
            
            # Update summary
            if field_result["status"] == "passed":
                report["execution_summary"]["fields_passed"] += 1
            else:
                report["execution_summary"]["fields_failed"] += 1
        
        return report
    
    def _execute_field(self, field_name: str, field_config: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """
        Execute all strategy FSMs for a field.
        
        Args:
            field_name: Name of the field
            field_config: Configuration for this field
            data: Input data
            
        Returns:
            Field execution result
        """
        result = {
            "status": "passed",
            "strategies": {}
        }
        
        # Execute each strategy FSM
        for strategy_name, strategy_config in field_config.items():
            strategy_result = self._execute_strategy(
                strategy_name, 
                strategy_config, 
                data,
                field_name
            )
            result["strategies"][strategy_name] = strategy_result
            
            # Field fails if any strategy fails
            if strategy_result["status"] == "not_passed":
                result["status"] = "not_passed"
        
        return result
    
    def _execute_strategy(self, strategy_name: str, strategy_config: Dict[str, Any], 
                         data: Any, field_name: str, parent_passed: bool = True) -> Dict[str, Any]:
        """
        Execute a strategy FSM (can be nested).
        
        Args:
            strategy_name: Name of the strategy
            strategy_config: Configuration for this strategy
            data: Input data
            field_name: Name of the field this strategy belongs to
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
        
        # Execute states sequentially
        fsm_result = self._execute_linear_fsm(states, data, field_name, strategy_name)
        
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
                           field_name: str, strategy_name: str) -> Dict[str, Any]:
        """
        Execute a linear FSM with sequential states.
        
        Args:
            states: Dictionary of state configurations
            data: Input data
            field_name: Name of the field
            strategy_name: Name of the strategy
            
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
        
        # Execute states sequentially
        for i, state_name in enumerate(state_names):
            # Execute state check (random for MVP)
            check_passed = self._execute_state_check(state_name, states[state_name], data, field_name)
            
            result["states_executed"].append(state_name)
            
            if not check_passed:
                result["failed_at"] = state_name
                return result
        
        # All states passed
        result["status"] = "passed"
        return result
    
    def _execute_state_check(self, state_name: str, state_config: Any, 
                            data: Any, field_name: str) -> bool:
        """
        Execute a state's criteria check.
        
        For MVP: Returns random pass/fail with 80% pass rate (for demo purposes).
        Future: Will evaluate actual criteria from state_config.
        
        Args:
            state_name: Name of the state
            state_config: State configuration
            data: Input data
            field_name: Name of the field
            
        Returns:
            True if check passes, False otherwise
        """
        # MVP: Random pass/fail with 80% pass rate (for better demo experience)
        # This gives a reasonable chance of seeing both pass and fail scenarios
        return random.random() < 0.8
