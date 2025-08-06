"""
SIT (Systematic Inventive Thinking) Operations for Object-Oriented Programming

This module provides classes and methods to apply SIT templates to Python classes
using PyGlove for symbolic programming and class manipulation.
"""

import inspect
import types
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    import pyglove as pg
except ImportError:
    print("PyGlove not installed. Please install with: pip install pyglove")
    pg = None


@dataclass
class SITOperation:
    """Represents a SIT operation with its parameters and metadata."""
    operation_type: str
    target_class: type
    parameters: Dict[str, Any]
    description: str


class SITTransformer(ABC):
    """Abstract base class for SIT transformations."""
    
    @abstractmethod
    def apply(self, target_class: type, **kwargs) -> type:
        """Apply the SIT transformation to a target class."""
        pass
    
    @abstractmethod
    def validate(self, target_class: type, **kwargs) -> bool:
        """Validate if the transformation can be applied."""
        pass


class SubtractionTransformer(SITTransformer):
    """
    Implements SIT Subtraction template using OO Overriding and Composition.
    
    Subtraction involves taking away a component or function to achieve improvement.
    """
    
    def validate(self, target_class: type, **kwargs) -> bool:
        """Validate if subtraction can be applied."""
        methods_to_remove = kwargs.get('methods_to_remove', [])
        attributes_to_remove = kwargs.get('attributes_to_remove', [])
        
        if not methods_to_remove and not attributes_to_remove:
            return False
            
        # Check if methods exist
        for method_name in methods_to_remove:
            if not hasattr(target_class, method_name):
                return False
                
        return True
    
    def apply(self, target_class: type, **kwargs) -> type:
        """Apply subtraction transformation."""
        if not self.validate(target_class, **kwargs):
            raise ValueError("Invalid subtraction parameters")
        
        methods_to_remove = kwargs.get('methods_to_remove', [])
        attributes_to_remove = kwargs.get('attributes_to_remove', [])
        new_class_name = kwargs.get('new_class_name', f"{target_class.__name__}Subtracted")
        
        # Create new class with removed methods/attributes
        class_dict = {}
        
        # Copy all methods and attributes except those to be removed
        for name, value in target_class.__dict__.items():
            if name not in methods_to_remove and name not in attributes_to_remove:
                class_dict[name] = value
        
        # Create the new class
        new_class = type(new_class_name, (target_class,), class_dict)
        
        # Add documentation about the transformation
        new_class.__doc__ = f"""
        Subtracted version of {target_class.__name__}.
        
        Removed methods: {methods_to_remove}
        Removed attributes: {attributes_to_remove}
        
        Original class: {target_class.__name__}
        """
        
        return new_class


class DivisionTransformer(SITTransformer):
    """
    Implements SIT Division template using OO Subclassing and Method Extraction.
    
    Division involves breaking down a product or system into components and 
    rearranging them or reconfiguring their use.
    """
    
    def validate(self, target_class: type, **kwargs) -> bool:
        """Validate if division can be applied."""
        division_strategy = kwargs.get('division_strategy', 'methods')
        
        if division_strategy == 'methods':
            methods_to_extract = kwargs.get('methods_to_extract', [])
            return all(hasattr(target_class, method) for method in methods_to_extract)
        elif division_strategy == 'attributes':
            attributes_to_group = kwargs.get('attributes_to_group', [])
            return all(hasattr(target_class, attr) for attr in attributes_to_group)
        
        return False
    
    def apply(self, target_class: type, **kwargs) -> type:
        """Apply division transformation."""
        if not self.validate(target_class, **kwargs):
            raise ValueError("Invalid division parameters")
        
        division_strategy = kwargs.get('division_strategy', 'methods')
        new_class_name = kwargs.get('new_class_name', f"{target_class.__name__}Divided")
        
        if division_strategy == 'methods':
            return self._divide_by_methods(target_class, **kwargs)
        elif division_strategy == 'attributes':
            return self._divide_by_attributes(target_class, **kwargs)
        else:
            raise ValueError(f"Unknown division strategy: {division_strategy}")
    
    def _divide_by_methods(self, target_class: type, **kwargs) -> type:
        """Divide class by extracting methods into a separate class."""
        methods_to_extract = kwargs.get('methods_to_extract', [])
        extracted_class_name = kwargs.get('extracted_class_name', f"{target_class.__name__}Extracted")
        
        # Create extracted class with specific methods
        extracted_dict = {}
        for method_name in methods_to_extract:
            if hasattr(target_class, method_name):
                extracted_dict[method_name] = getattr(target_class, method_name)
        
        extracted_class = type(extracted_class_name, (), extracted_dict)
        
        # Create main class without extracted methods
        main_dict = {}
        for name, value in target_class.__dict__.items():
            if name not in methods_to_extract:
                main_dict[name] = value
        
        # Add reference to extracted class
        main_dict['_extracted'] = extracted_class()
        
        new_class = type(f"{target_class.__name__}Divided", (target_class,), main_dict)
        
        # Add delegation methods
        for method_name in methods_to_extract:
            def create_delegate(method_name):
                def delegate(self, *args, **kwargs):
                    return getattr(self._extracted, method_name)(*args, **kwargs)
                return delegate
            
            setattr(new_class, method_name, create_delegate(method_name))
        
        return new_class
    
    def _divide_by_attributes(self, target_class: type, **kwargs) -> type:
        """Divide class by grouping related attributes."""
        attribute_groups = kwargs.get('attribute_groups', {})
        
        # Create classes for each attribute group
        group_classes = {}
        for group_name, attributes in attribute_groups.items():
            group_dict = {}
            for attr in attributes:
                if hasattr(target_class, attr):
                    group_dict[attr] = getattr(target_class, attr)
            group_classes[group_name] = type(f"{target_class.__name__}{group_name.capitalize()}", (), group_dict)
        
        # Create main class with group references
        main_dict = {}
        for name, value in target_class.__dict__.items():
            if not any(attr in attribute_groups.values() for attr_group in attribute_groups.values() for attr in attr_group):
                main_dict[name] = value
        
        for group_name, group_class in group_classes.items():
            main_dict[f"_{group_name}_group"] = group_class()
        
        new_class = type(f"{target_class.__name__}Divided", (target_class,), main_dict)
        
        # Add property accessors for grouped attributes
        for group_name, attributes in attribute_groups.items():
            for attr in attributes:
                def create_property(attr_name, group_name):
                    def getter(self):
                        return getattr(getattr(self, f"_{group_name}_group"), attr_name)
                    def setter(self, value):
                        setattr(getattr(self, f"_{group_name}_group"), attr_name, value)
                    return property(getter, setter)
                
                setattr(new_class, attr, create_property(attr, group_name))
        
        return new_class


class TaskUnificationTransformer(SITTransformer):
    """
    Implements SIT Task Unification template using OO Interface Implementation and Composition.
    
    Task Unification involves assigning multiple roles or tasks to a single component,
    thereby improving efficiency and utility.
    """
    
    def validate(self, target_class: type, **kwargs) -> bool:
        """Validate if task unification can be applied."""
        interfaces_to_implement = kwargs.get('interfaces_to_implement', [])
        additional_methods = kwargs.get('additional_methods', {})
        
        # Check if interfaces exist
        for interface in interfaces_to_implement:
            if not isinstance(interface, type):
                return False
        
        return True
    
    def apply(self, target_class: type, **kwargs) -> type:
        """Apply task unification transformation."""
        if not self.validate(target_class, **kwargs):
            raise ValueError("Invalid task unification parameters")
        
        interfaces_to_implement = kwargs.get('interfaces_to_implement', [])
        additional_methods = kwargs.get('additional_methods', {})
        new_class_name = kwargs.get('new_class_name', f"{target_class.__name__}Unified")
        
        # Create new class with additional interfaces and methods
        class_dict = {}
        
        # Copy existing methods and attributes
        for name, value in target_class.__dict__.items():
            class_dict[name] = value
        
        # Add additional methods
        for method_name, method_impl in additional_methods.items():
            class_dict[method_name] = method_impl
        
        # Create the unified class
        bases = (target_class,) + tuple(interfaces_to_implement)
        new_class = type(new_class_name, bases, class_dict)
        
        # Add documentation
        new_class.__doc__ = f"""
        Task-unified version of {target_class.__name__}.
        
        Implements interfaces: {[i.__name__ for i in interfaces_to_implement]}
        Additional methods: {list(additional_methods.keys())}
        
        Original class: {target_class.__name__}
        """
        
        return new_class


class AttributeDependencyTransformer(SITTransformer):
    """
    Implements SIT Attribute Dependency template using OO Getter/Setter Methods and Observer Pattern.
    
    Attribute Dependency involves varying attributes based on context or environment,
    allowing dynamic adaptation for more nuanced capabilities.
    """
    
    def validate(self, target_class: type, **kwargs) -> bool:
        """Validate if attribute dependency can be applied."""
        dependent_attributes = kwargs.get('dependent_attributes', {})
        dependency_rules = kwargs.get('dependency_rules', {})
        
        if not dependent_attributes or not dependency_rules:
            return False
        
        # Check if attributes are mentioned in the class (they might be set in __init__)
        # We'll be more lenient here since attributes are often set in __init__
        return True
    
    def apply(self, target_class: type, **kwargs) -> type:
        """Apply attribute dependency transformation."""
        if not self.validate(target_class, **kwargs):
            raise ValueError("Invalid attribute dependency parameters")
        
        dependent_attributes = kwargs.get('dependent_attributes', {})
        dependency_rules = kwargs.get('dependency_rules', {})
        observers = kwargs.get('observers', [])
        new_class_name = kwargs.get('new_class_name', f"{target_class.__name__}Dependent")
        
        # Create new class with dependency-aware attributes
        class_dict = {}
        
        # Copy existing methods and attributes
        for name, value in target_class.__dict__.items():
            if name not in dependent_attributes:
                class_dict[name] = value
        
        # Add observer list
        class_dict['_observers'] = observers
        
        # Create dependent properties
        for attr_name, default_value in dependent_attributes.items():
            def create_dependent_property(attr_name, default_value, dependency_rules):
                def getter(self):
                    # Apply dependency rules
                    context = self._get_context()
                    for rule in dependency_rules.get(attr_name, []):
                        if rule['condition'](context):
                            return rule['value']
                    return getattr(self, f"_{attr_name}", default_value)
                
                def setter(self, value):
                    old_value = getattr(self, f"_{attr_name}", None)
                    setattr(self, f"_{attr_name}", value)
                    
                    # Notify observers
                    for observer in self._observers:
                        if hasattr(observer, 'on_attribute_changed'):
                            observer.on_attribute_changed(attr_name, old_value, value)
                
                return property(getter, setter)
            
            class_dict[attr_name] = create_dependent_property(attr_name, default_value, dependency_rules)
        
        # Add context method
        def get_context(self):
            """Get current context for dependency evaluation."""
            return {
                'time': getattr(self, '_current_time', None),
                'state': getattr(self, '_state', None),
                'environment': getattr(self, '_environment', None)
            }
        
        class_dict['_get_context'] = get_context
        
        # Create the dependent class
        new_class = type(new_class_name, (target_class,), class_dict)
        
        # Add documentation
        new_class.__doc__ = f"""
        Attribute-dependent version of {target_class.__name__}.
        
        Dependent attributes: {list(dependent_attributes.keys())}
        Dependency rules: {len(dependency_rules)} rules defined
        
        Original class: {target_class.__name__}
        """
        
        return new_class


class SITOperationsManager:
    """
    Main manager class for applying SIT operations to Python classes.
    """
    
    def __init__(self):
        self.transformers = {
            'subtraction': SubtractionTransformer(),
            'division': DivisionTransformer(),
            'task_unification': TaskUnificationTransformer(),
            'attribute_dependency': AttributeDependencyTransformer()
        }
        self.operation_history = []
    
    def apply_sit_operation(self, operation_type: str, target_class: type, **kwargs) -> type:
        """
        Apply a SIT operation to a target class.
        
        Args:
            operation_type: One of 'subtraction', 'division', 'task_unification', 'attribute_dependency'
            target_class: The class to transform
            **kwargs: Operation-specific parameters
        
        Returns:
            The transformed class
        """
        if operation_type not in self.transformers:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        transformer = self.transformers[operation_type]
        
        # Validate the operation
        if not transformer.validate(target_class, **kwargs):
            raise ValueError(f"Invalid parameters for {operation_type} operation")
        
        # Apply the transformation
        result_class = transformer.apply(target_class, **kwargs)
        
        # Record the operation
        operation = SITOperation(
            operation_type=operation_type,
            target_class=target_class,
            parameters=kwargs,
            description=f"Applied {operation_type} to {target_class.__name__}"
        )
        self.operation_history.append(operation)
        
        return result_class
    
    def get_operation_history(self) -> List[SITOperation]:
        """Get the history of applied SIT operations."""
        return self.operation_history.copy()
    
    def analyze_class(self, target_class: type) -> Dict[str, Any]:
        """
        Analyze a class to suggest potential SIT operations.
        
        Args:
            target_class: The class to analyze
        
        Returns:
            Dictionary with analysis results and suggestions
        """
        analysis = {
            'class_name': target_class.__name__,
            'methods': [],
            'attributes': [],
            'suggestions': {}
        }
        
        # Analyze methods
        for name, value in target_class.__dict__.items():
            if callable(value) and not name.startswith('_'):
                analysis['methods'].append(name)
            elif not callable(value) and not name.startswith('_'):
                analysis['attributes'].append(name)
        
        # Generate suggestions
        if len(analysis['methods']) > 3:
            analysis['suggestions']['subtraction'] = {
                'methods_to_remove': analysis['methods'][:2],
                'description': 'Consider removing some methods to focus the class'
            }
        
        if len(analysis['methods']) > 5:
            analysis['suggestions']['division'] = {
                'methods_to_extract': analysis['methods'][:3],
                'description': 'Consider extracting related methods into separate classes'
            }
        
        if len(analysis['attributes']) > 2:
            analysis['suggestions']['attribute_dependency'] = {
                'dependent_attributes': analysis['attributes'][:2],
                'description': 'Consider making attributes context-dependent'
            }
        
        return analysis


# Example usage and demonstration
if __name__ == "__main__":
    # Example class for demonstration
    class Car:
        def __init__(self):
            self.engine = "V8"
            self.fuel_type = "gasoline"
            self.max_speed = 200
        
        def start_engine(self):
            return "Engine started"
        
        def accelerate(self):
            return "Accelerating"
        
        def brake(self):
            return "Braking"
        
        def refuel(self):
            return "Refueling with gasoline"
    
    # Create SIT operations manager
    sit_manager = SITOperationsManager()
    
    # Example 1: Subtraction - Remove refuel method for electric car
    ElectricCar = sit_manager.apply_sit_operation(
        'subtraction',
        Car,
        methods_to_remove=['refuel'],
        new_class_name='ElectricCar'
    )
    
    # Example 2: Division - Extract driving methods
    DrivingCar = sit_manager.apply_sit_operation(
        'division',
        Car,
        division_strategy='methods',
        methods_to_extract=['accelerate', 'brake'],
        extracted_class_name='DrivingBehavior'
    )
    
    # Example 3: Task Unification - Add navigation capabilities
    def navigate(self):
        return "Navigating to destination"
    
    SmartCar = sit_manager.apply_sit_operation(
        'task_unification',
        Car,
        additional_methods={'navigate': navigate},
        new_class_name='SmartCar'
    )
    
    # Example 4: Attribute Dependency - Make fuel type context-dependent
    def fuel_rule(context):
        return context.get('time', 'day') == 'night'
    
    AdaptiveCar = sit_manager.apply_sit_operation(
        'attribute_dependency',
        Car,
        dependent_attributes={'fuel_type': 'gasoline'},
        dependency_rules={
            'fuel_type': [
                {
                    'condition': fuel_rule,
                    'value': 'electric'
                }
            ]
        },
        new_class_name='AdaptiveCar'
    )
    
    print("SIT Operations applied successfully!")
    print(f"Operation history: {len(sit_manager.get_operation_history())} operations")
