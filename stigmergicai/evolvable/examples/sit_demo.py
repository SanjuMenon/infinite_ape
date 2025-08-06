#!/usr/bin/env python3
"""
SIT Operations Demonstration

This script demonstrates how to use the SIT operations system to transform
Python classes using systematic inventive thinking principles.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stigmergicai.osi.model import SITOperationsManager
from stigmergicai.osi.pyglove_sit import PyGloveSITManager


def demo_basic_sit_operations():
    """Demonstrate basic SIT operations."""
    print("=" * 60)
    print("BASIC SIT OPERATIONS DEMONSTRATION")
    print("=" * 60)
    
    # Create a complex class for demonstration
    class Smartphone:
        def __init__(self):
            self.battery_level = 100
            self.screen_brightness = 50
            self.volume = 30
            self.network_type = "4G"
        
        def make_call(self):
            return "Making a call"
        
        def send_text(self):
            return "Sending text message"
        
        def take_photo(self):
            return "Taking photo"
        
        def play_music(self):
            return "Playing music"
        
        def browse_web(self):
            return "Browsing the web"
        
        def charge_battery(self):
            return "Charging battery"
    
    print("Original Smartphone class:")
    print(f"Methods: {[m for m in dir(Smartphone()) if not m.startswith('_') and callable(getattr(Smartphone(), m))]}")
    print(f"Attributes: {[a for a in dir(Smartphone()) if not a.startswith('_') and not callable(getattr(Smartphone(), a))]}")
    print()
    
    # Create SIT manager
    sit_manager = SITOperationsManager()
    
    # 1. SUBTRACTION - Create a basic phone by removing advanced features
    print("1. SUBTRACTION - Creating BasicPhone by removing advanced features")
    BasicPhone = sit_manager.apply_sit_operation(
        'subtraction',
        Smartphone,
        methods_to_remove=['take_photo', 'play_music', 'browse_web'],
        new_class_name='BasicPhone'
    )
    
    basic_phone = BasicPhone()
    print(f"BasicPhone methods: {[m for m in dir(basic_phone) if not m.startswith('_') and callable(getattr(basic_phone, m))]}")
    print(f"Removed: take_photo, play_music, browse_web")
    print()
    
    # 2. DIVISION - Separate communication and media features
    print("2. DIVISION - Separating communication and media features")
    CommunicationPhone = sit_manager.apply_sit_operation(
        'division',
        Smartphone,
        division_strategy='methods',
        methods_to_extract=['make_call', 'send_text'],
        extracted_class_name='CommunicationFeatures'
    )
    
    comm_phone = CommunicationPhone()
    print(f"CommunicationPhone methods: {[m for m in dir(comm_phone) if not m.startswith('_') and callable(getattr(comm_phone, m))]}")
    print("Extracted communication features into separate class")
    print()
    
    # 3. TASK UNIFICATION - Add navigation capabilities
    print("3. TASK UNIFICATION - Adding navigation capabilities")
    def navigate(self):
        return "Navigating to destination"
    
    def get_weather(self):
        return "Getting weather information"
    
    SmartphonePlus = sit_manager.apply_sit_operation(
        'task_unification',
        Smartphone,
        additional_methods={
            'navigate': navigate,
            'get_weather': get_weather
        },
        new_class_name='SmartphonePlus'
    )
    
    smartphone_plus = SmartphonePlus()
    print(f"SmartphonePlus methods: {[m for m in dir(smartphone_plus) if not m.startswith('_') and callable(getattr(smartphone_plus, m))]}")
    print("Added: navigate, get_weather")
    print()
    
    # 4. ATTRIBUTE DEPENDENCY - Make settings context-dependent
    print("4. ATTRIBUTE DEPENDENCY - Making settings context-dependent")
    def brightness_rule(context):
        return context.get('time', 'day') == 'night'
    
    def volume_rule(context):
        return context.get('location', 'home') == 'public'
    
    AdaptiveSmartphone = sit_manager.apply_sit_operation(
        'attribute_dependency',
        Smartphone,
        dependent_attributes={
            'screen_brightness': 50,
            'volume': 30
        },
        dependency_rules={
            'screen_brightness': [
                {
                    'condition': brightness_rule,
                    'value': 20  # Dimmer at night
                }
            ],
            'volume': [
                {
                    'condition': volume_rule,
                    'value': 10  # Quieter in public
                }
            ]
        },
        new_class_name='AdaptiveSmartphone'
    )
    
    adaptive_phone = AdaptiveSmartphone()
    print(f"AdaptiveSmartphone attributes: {[a for a in dir(adaptive_phone) if not a.startswith('_') and not callable(getattr(adaptive_phone, a))]}")
    print("Brightness and volume now adapt to context")
    print()
    
    # Show operation history
    print("SIT Operation History:")
    history = sit_manager.get_operation_history()
    for i, operation in enumerate(history, 1):
        print(f"{i}. {operation.operation_type.upper()}: {operation.description}")
        print(f"   Parameters: {operation.parameters}")
    print()


def demo_pyglove_sit_operations():
    """Demonstrate PyGlove-based SIT operations."""
    print("=" * 60)
    print("PYGLOVE SIT OPERATIONS DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Create PyGlove SIT manager
        pg_sit_manager = PyGloveSITManager()
        
        # Create a vehicle class for demonstration
        class Vehicle:
            def __init__(self):
                self.engine_type = "gasoline"
                self.fuel_capacity = 50
                self.max_speed = 120
                self.passenger_capacity = 5
            
            def start_engine(self):
                return "Engine started"
            
            def accelerate(self):
                return "Accelerating"
            
            def brake(self):
                return "Braking"
            
            def refuel(self):
                return "Refueling"
            
            def park(self):
                return "Parking"
        
        print("Original Vehicle class:")
        print(f"Methods: {[m for m in dir(Vehicle()) if not m.startswith('_') and callable(getattr(Vehicle(), m))]}")
        print(f"Attributes: {[a for a in dir(Vehicle()) if not a.startswith('_') and not callable(getattr(Vehicle(), a))]}")
        print()
        
        # Register the class
        vehicle_id = pg_sit_manager.register_class(Vehicle)
        print(f"Registered Vehicle with ID: {vehicle_id}")
        print()
        
        # Apply SIT operations
        print("Applying SIT operations...")
        
        # 1. Subtraction - Electric vehicle
        electric_vehicle_id = pg_sit_manager.apply_sit_operation(
            vehicle_id,
            'subtraction',
            methods_to_remove=['refuel'],
            attributes_to_remove=['fuel_capacity']
        )
        
        ElectricVehicle = pg_sit_manager.materialize_class(electric_vehicle_id)
        ev = ElectricVehicle()
        print(f"1. Electric Vehicle (Subtraction):")
        print(f"   Methods: {[m for m in dir(ev) if not m.startswith('_') and callable(getattr(ev, m))]}")
        print(f"   Removed: refuel, fuel_capacity")
        print()
        
        # 2. Division - Separate driving behavior
        driving_vehicle_id = pg_sit_manager.apply_sit_operation(
            vehicle_id,
            'division',
            division_groups={'driving': ['accelerate', 'brake']},
            division_type='methods'
        )
        
        DrivingVehicle = pg_sit_manager.materialize_class(driving_vehicle_id)
        dv = DrivingVehicle()
        print(f"2. Driving Vehicle (Division):")
        print(f"   Methods: {[m for m in dir(dv) if not m.startswith('_') and callable(getattr(dv, m))]}")
        print(f"   Extracted driving behavior into separate class")
        print()
        
        # 3. Task Unification - Add navigation
        def navigate(self):
            return "Navigating to destination"
        
        def get_traffic_info(self):
            return "Getting traffic information"
        
        smart_vehicle_id = pg_sit_manager.apply_sit_operation(
            vehicle_id,
            'task_unification',
            additional_methods={
                'navigate': navigate,
                'get_traffic_info': get_traffic_info
            }
        )
        
        SmartVehicle = pg_sit_manager.materialize_class(smart_vehicle_id)
        sv = SmartVehicle()
        print(f"3. Smart Vehicle (Task Unification):")
        print(f"   Methods: {[m for m in dir(sv) if not m.startswith('_') and callable(getattr(sv, m))]}")
        print(f"   Added: navigate, get_traffic_info")
        print()
        
        # 4. Attribute Dependency - Adaptive vehicle
        def engine_rule(context):
            return context.get('time', 'day') == 'night'
        
        def speed_rule(context):
            return context.get('location', 'city') == 'highway'
        
        adaptive_vehicle_id = pg_sit_manager.apply_sit_operation(
            vehicle_id,
            'attribute_dependency',
            dependent_attributes={
                'engine_type': 'gasoline',
                'max_speed': 120
            },
            dependency_rules={
                'engine_type': [
                    {
                        'condition': engine_rule,
                        'value': 'electric'
                    }
                ],
                'max_speed': [
                    {
                        'condition': speed_rule,
                        'value': 150
                    }
                ]
            }
        )
        
        AdaptiveVehicle = pg_sit_manager.materialize_class(adaptive_vehicle_id)
        av = AdaptiveVehicle()
        print(f"4. Adaptive Vehicle (Attribute Dependency):")
        print(f"   Attributes: {[a for a in dir(av) if not a.startswith('_') and not callable(getattr(av, a))]}")
        print(f"   Engine type and max speed adapt to context")
        print()
        
        # Show transformation visualization
        print("Transformation History:")
        print(pg_sit_manager.visualize_transformations())
        
    except ImportError as e:
        print(f"PyGlove not available: {e}")
        print("Install PyGlove with: pip install pyglove")


def demo_class_analysis():
    """Demonstrate class analysis capabilities."""
    print("=" * 60)
    print("CLASS ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    # Create a complex class for analysis
    class ComplexSystem:
        def __init__(self):
            self.temperature = 25
            self.pressure = 1013
            self.humidity = 60
            self.voltage = 220
            self.current = 5
            self.frequency = 50
        
        def measure_temperature(self):
            return "Measuring temperature"
        
        def measure_pressure(self):
            return "Measuring pressure"
        
        def measure_humidity(self):
            return "Measuring humidity"
        
        def control_voltage(self):
            return "Controlling voltage"
        
        def control_current(self):
            return "Controlling current"
        
        def control_frequency(self):
            return "Controlling frequency"
        
        def calibrate_sensors(self):
            return "Calibrating sensors"
        
        def validate_measurements(self):
            return "Validating measurements"
    
    # Create SIT manager and analyze
    sit_manager = SITOperationsManager()
    analysis = sit_manager.analyze_class(ComplexSystem)
    
    print(f"Class: {analysis['class_name']}")
    print(f"Methods: {analysis['methods']}")
    print(f"Attributes: {analysis['attributes']}")
    print()
    
    print("SIT Suggestions:")
    for operation, suggestion in analysis['suggestions'].items():
        print(f"- {operation.upper()}: {suggestion['description']}")
        if 'methods_to_remove' in suggestion:
            print(f"  Methods to remove: {suggestion['methods_to_remove']}")
        if 'methods_to_extract' in suggestion:
            print(f"  Methods to extract: {suggestion['methods_to_extract']}")
        if 'dependent_attributes' in suggestion:
            print(f"  Dependent attributes: {suggestion['dependent_attributes']}")
        print()


def main():
    """Run all demonstrations."""
    print("SIT Operations System Demonstration")
    print("Systematic Inventive Thinking applied to Object-Oriented Programming")
    print()
    
    # Run demonstrations
    demo_basic_sit_operations()
    demo_pyglove_sit_operations()
    demo_class_analysis()
    
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print()
    print("Key Benefits of SIT Operations:")
    print("1. Systematic approach to class transformation")
    print("2. Reusable transformation patterns")
    print("3. Clear mapping between SIT templates and OO operations")
    print("4. Support for both basic and advanced transformations")
    print("5. Comprehensive analysis and suggestion capabilities")


if __name__ == "__main__":
    main() 