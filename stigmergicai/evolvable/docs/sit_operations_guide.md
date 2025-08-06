# SIT Operations System

A comprehensive system for applying Systematic Inventive Thinking (SIT) principles to Object-Oriented Programming using Python and PyGlove.

## Overview

This system provides a systematic approach to class transformation by mapping SIT templates to Object-Oriented operations:

| SIT Template | OO Operation | Description |
|--------------|--------------|-------------|
| **Subtraction** | Overriding, Composition | Removing functionality or delegating responsibility |
| **Division** | Subclassing, Method Extraction | Splitting functionality into manageable components |
| **Task Unification** | Interface Implementation, Composition | Using a single class to support multiple behaviors |
| **Attribute Dependency** | Getter/Setter Methods, Observer Pattern | Context-based adaptation and dynamic behavior |

## Installation

```bash
# Install the package with dependencies
pip install -e .

# Or install PyGlove separately if needed
pip install pyglove>=0.4.0
```

## Quick Start

### Running the Demo

The easiest way to see SIT operations in action is to run the demonstration script:

```bash
# Install dependencies
pip install -e .

# Run the SIT demo
python examples/sit_demo.py
```

The demo showcases all four SIT operations with practical examples:
- **Smartphone Evolution**: Transforming a basic phone into specialized versions
- **Vehicle Adaptation**: Creating electric, smart, and adaptive vehicles
- **Complex System Analysis**: Analyzing and suggesting transformations
- **Transformation History**: Tracking all applied operations

### Basic Usage

```python
from stigmergicai.osi.model import SITOperationsManager

# Create a class to transform
class Car:
    def __init__(self):
        self.engine = "V8"
        self.fuel_type = "gasoline"
    
    def start_engine(self):
        return "Engine started"
    
    def refuel(self):
        return "Refueling"

# Create SIT manager
sit_manager = SITOperationsManager()

# Apply SIT operations
ElectricCar = sit_manager.apply_sit_operation(
    'subtraction',
    Car,
    methods_to_remove=['refuel'],
    new_class_name='ElectricCar'
)

# Use the transformed class
ev = ElectricCar()
print(ev.start_engine())  # "Engine started"
# ev.refuel()  # AttributeError - method removed
```

### PyGlove Advanced Usage

```python
from stigmergicai.osi.pyglove_sit import PyGloveSITManager

# Create PyGlove SIT manager
pg_sit_manager = PyGloveSITManager()

# Register a class
vehicle_id = pg_sit_manager.register_class(Car)

# Apply multiple transformations
electric_vehicle_id = pg_sit_manager.apply_sit_operation(
    vehicle_id,
    'subtraction',
    methods_to_remove=['refuel']
)

# Materialize the transformed class
ElectricVehicle = pg_sit_manager.materialize_class(electric_vehicle_id)
```

## SIT Operations

### 1. Subtraction

Removes components or functions to achieve improvement.

```python
# Remove methods and attributes
SubtractedClass = sit_manager.apply_sit_operation(
    'subtraction',
    target_class,
    methods_to_remove=['method1', 'method2'],
    attributes_to_remove=['attr1'],
    new_class_name='SubtractedClass'
)
```

**Use Cases:**
- Creating simplified versions of complex classes
- Removing deprecated functionality
- Creating specialized subclasses

### 2. Division

Breaks down a class into components and rearranges them.

```python
# Divide by methods
DividedClass = sit_manager.apply_sit_operation(
    'division',
    target_class,
    division_strategy='methods',
    methods_to_extract=['method1', 'method2'],
    extracted_class_name='ExtractedClass'
)

# Divide by attributes
DividedClass = sit_manager.apply_sit_operation(
    'division',
    target_class,
    division_strategy='attributes',
    attribute_groups={
        'group1': ['attr1', 'attr2'],
        'group2': ['attr3', 'attr4']
    }
)
```

**Use Cases:**
- Separating concerns into different classes
- Creating reusable components
- Improving maintainability

### 3. Task Unification

Assigns multiple roles or tasks to a single component.

```python
# Add new methods and interfaces
def new_method(self):
    return "New functionality"

UnifiedClass = sit_manager.apply_sit_operation(
    'task_unification',
    target_class,
    additional_methods={'new_method': new_method},
    interfaces=[SomeInterface],
    new_class_name='UnifiedClass'
)
```

**Use Cases:**
- Adding new capabilities to existing classes
- Implementing multiple interfaces
- Creating multi-purpose objects

### 4. Attribute Dependency

Makes attributes context-dependent for dynamic adaptation.

```python
# Define dependency rules
def brightness_rule(context):
    return context.get('time', 'day') == 'night'

DependentClass = sit_manager.apply_sit_operation(
    'attribute_dependency',
    target_class,
    dependent_attributes={'brightness': 50},
    dependency_rules={
        'brightness': [
            {
                'condition': brightness_rule,
                'value': 20  # Dimmer at night
            }
        ]
    },
    observers=[observer1, observer2]
)
```

**Use Cases:**
- Context-aware behavior
- Adaptive systems
- Reactive programming patterns

## Class Analysis

The system can analyze classes and suggest appropriate SIT operations:

```python
# Analyze a class
analysis = sit_manager.analyze_class(ComplexClass)

print(f"Class: {analysis['class_name']}")
print(f"Methods: {analysis['methods']}")
print(f"Attributes: {analysis['attributes']}")

# Get suggestions
for operation, suggestion in analysis['suggestions'].items():
    print(f"{operation}: {suggestion['description']}")
```

## PyGlove Advanced Features

### Symbolic Class Manipulation

```python
# Create symbolic representation
symbolic_class = SITSymbolicClass.from_class(MyClass)

# Apply transformations symbolically
transformer = PyGloveSITTransformer()
new_symbolic_class = transformer.apply_subtraction(
    symbolic_class,
    methods_to_remove=['method1']
)

# Convert back to Python class
new_class = new_symbolic_class.to_class()
```

### Transformation History

```python
# Track all transformations
history = pg_sit_manager.get_transformation_history()

# Visualize transformations
print(pg_sit_manager.visualize_transformations())
```

## Examples

### Smartphone Evolution

```python
class Smartphone:
    def __init__(self):
        self.battery_level = 100
        self.screen_brightness = 50
    
    def make_call(self):
        return "Making call"
    
    def take_photo(self):
        return "Taking photo"
    
    def play_music(self):
        return "Playing music"

# 1. Subtraction - Basic phone
BasicPhone = sit_manager.apply_sit_operation(
    'subtraction',
    Smartphone,
    methods_to_remove=['take_photo', 'play_music']
)

# 2. Division - Separate communication
CommunicationPhone = sit_manager.apply_sit_operation(
    'division',
    Smartphone,
    methods_to_extract=['make_call']
)

# 3. Task Unification - Add navigation
def navigate(self):
    return "Navigating"

SmartphonePlus = sit_manager.apply_sit_operation(
    'task_unification',
    Smartphone,
    additional_methods={'navigate': navigate}
)

# 4. Attribute Dependency - Adaptive brightness
def brightness_rule(context):
    return context.get('time') == 'night'

AdaptiveSmartphone = sit_manager.apply_sit_operation(
    'attribute_dependency',
    Smartphone,
    dependent_attributes={'screen_brightness': 50},
    dependency_rules={
        'screen_brightness': [
            {'condition': brightness_rule, 'value': 20}
        ]
    }
)
```

## Best Practices

### 1. Start with Analysis
Always analyze your class before applying transformations:

```python
analysis = sit_manager.analyze_class(MyClass)
print("Suggested operations:", list(analysis['suggestions'].keys()))
```

### 2. Use Meaningful Names
Provide descriptive names for transformed classes:

```python
ElectricCar = sit_manager.apply_sit_operation(
    'subtraction',
    Car,
    new_class_name='ElectricCar'  # Clear, descriptive name
)
```

### 3. Document Transformations
Keep track of why transformations were applied:

```python
# Record the reasoning
transformation_reason = "Remove refuel method for electric vehicle variant"
```

### 4. Test Transformed Classes
Always test the behavior of transformed classes:

```python
transformed_instance = TransformedClass()
assert hasattr(transformed_instance, 'expected_method')
assert not hasattr(transformed_instance, 'removed_method')
```

## Architecture

### Core Components

1. **SITOperationsManager**: Main interface for basic operations
2. **PyGloveSITManager**: Advanced operations with symbolic programming
3. **SITTransformer**: Abstract base for transformation operations
4. **SITSymbolicClass**: Symbolic representation of classes

### Transformation Pipeline

1. **Analysis**: Analyze the target class
2. **Validation**: Check if transformation is applicable
3. **Transformation**: Apply the SIT operation
4. **Materialization**: Convert back to Python class (PyGlove)
5. **Documentation**: Record the transformation

## Contributing

To extend the system with new SIT operations:

1. Create a new transformer class inheriting from `SITTransformer`
2. Implement `validate()` and `apply()` methods
3. Add the transformer to the manager's transformer dictionary
4. Write tests for the new operation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- [Systematic Inventive Thinking (SIT)](https://www.sitsite.com/)
- [PyGlove Documentation](https://pyglove.readthedocs.io/)
- [Object-Oriented Design Principles](https://en.wikipedia.org/wiki/Object-oriented_design) 