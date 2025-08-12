"""
Demo script for the Constructivist Learning System.

This script demonstrates how the system works with example learner interactions
and shows the pattern evolution process.
"""

from core.learning_system import ConstructivistLearningSystem
import json


def print_separator(title: str):
    """Print a formatted separator with title."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_response(response):
    """Print a formatted learning response."""
    print(f"\n🤖 System Response:")
    print(f"   {response.message}")
    print(f"\n📊 Context:")
    print(f"   Pattern: {response.pattern_context}")
    if response.force_context:
        print(f"   Force: {response.force_context}")
    print(f"   Action: {response.next_action}")
    print(f"   Confidence: {response.confidence:.2f}")


def demo_basic_interaction():
    """Demonstrate basic learner interaction with the system."""
    
    print_separator("DEMO: Basic Learner Interaction")
    
    # Initialize the learning system
    system = ConstructivistLearningSystem()
    
    # Initialize a new learner
    learner_id = "demo_user_001"
    learner_state = system.initialize_learner(learner_id, domain="programming")
    
    print(f"👤 Learner initialized: {learner_id}")
    print(f"🎯 Starting pattern: {learner_state.current_pattern}")
    
    # Simulate some learner interactions
    interactions = [
        "I'm learning about variables. What are they?",
        "I understand that variables store data with names",
        "I can create variables like age = 25",
        "I'm confused about when to use different types",
        "I think I understand variables now"
    ]
    
    for i, interaction in enumerate(interactions, 1):
        print(f"\n💬 Learner Interaction {i}:")
        print(f"   {interaction}")
        
        # Process the interaction
        response = system.process_interaction(learner_id, interaction)
        print_response(response)
    
    # Show learner progress
    print_separator("Learner Progress Report")
    progress = system.get_learner_progress(learner_id)
    
    print(f"Current Pattern: {progress['current_pattern']['name']}")
    print(f"Pattern History: {progress['pattern_history']}")
    print(f"Mastery Level: {progress['mastery_assessment']['overall_mastery']:.2f}")
    print(f"Confidence: {progress['mastery_assessment']['confidence_level']:.2f}")
    
    if progress['evolution_status']['should_evolve']:
        print(f"🔄 Ready to evolve to: {progress['evolution_status']['target_pattern']}")
        print(f"   Triggering force: {progress['evolution_status']['triggering_force']}")
    
    print(f"\nAvailable Forces:")
    for force in progress['available_forces']:
        print(f"   • {force['name']} ({force['category']}, intensity: {force['intensity']})")


def demo_force_application():
    """Demonstrate force application and pattern evolution."""
    
    print_separator("DEMO: Force Application and Evolution")
    
    system = ConstructivistLearningSystem()
    learner_id = "demo_user_002"
    
    # Initialize learner with some progress
    learner_state = system.initialize_learner(learner_id, domain="programming")
    
    # Simulate some interactions to build up mastery
    for i in range(5):
        system.process_interaction(learner_id, "I understand variables and can use them effectively")
    
    print(f"👤 Learner: {learner_id}")
    print(f"🎯 Current pattern: {learner_state.current_pattern}")
    
    # Apply a force
    print("\n🔧 Applying Force: Type Safety Requirement")
    response = system.apply_force(learner_id, "type_safety")
    print_response(response)
    
    # Simulate more interactions with the force applied
    print("\n💬 Learner interactions with force applied:")
    force_interactions = [
        "I see why we need to specify types",
        "Type safety helps prevent errors",
        "I can now use int age = 25 instead of just age = 25"
    ]
    
    for interaction in force_interactions:
        print(f"\n   {interaction}")
        response = system.process_interaction(learner_id, interaction)
        print_response(response)
    
    # Check if ready to evolve
    progress = system.get_learner_progress(learner_id)
    if progress['evolution_status']['should_evolve']:
        print("\n🔄 Evolution Ready!")
        target_pattern = progress['evolution_status']['target_pattern']
        
        # Perform evolution
        print(f"Evolving to: {target_pattern}")
        evolution_response = system.evolve_pattern(learner_id, target_pattern)
        print_response(evolution_response)


def demo_cross_domain_patterns():
    """Demonstrate how patterns work across different domains."""
    
    print_separator("DEMO: Cross-Domain Pattern Similarities")
    
    system = ConstructivistLearningSystem()
    
    # Show patterns from different domains
    pattern_db = system.pattern_db
    
    domains = ["programming", "mathematics", "language"]
    
    for domain in domains:
        print(f"\n📚 {domain.upper()} DOMAIN:")
        
        # Get patterns for this domain
        domain_patterns = [
            pattern for pattern in pattern_db.patterns.values() 
            if domain in pattern.domain_tags
        ]
        
        for pattern in domain_patterns:
            print(f"   • {pattern.name}: {pattern.core_concept.simple_definition}")
            print(f"     Complexity: {pattern.complexity_level}/10")
            print(f"     Evolution paths: {len(pattern.evolution_paths)}")
    
    print("\n🔍 Notice how similar patterns exist across domains:")
    print("   • Programming: Variable Storage")
    print("   • Mathematics: Number Representation") 
    print("   • Language: Word Meaning")
    print("\n   All represent the basic concept of 'naming and storing information'")


def demo_struggle_detection():
    """Demonstrate how the system detects and responds to learner struggles."""
    
    print_separator("DEMO: Struggle Detection and Intervention")
    
    system = ConstructivistLearningSystem()
    learner_id = "demo_user_003"
    
    learner_state = system.initialize_learner(learner_id, domain="programming")
    
    print(f"👤 Learner: {learner_id}")
    print(f"🎯 Starting pattern: {learner_state.current_pattern}")
    
    # Simulate struggling learner interactions
    struggle_interactions = [
        "I don't understand what variables are",
        "This is confusing and frustrating",
        "I keep making mistakes with variables",
        "I'm not sure when to use variables",
        "This is too hard for me"
    ]
    
    print("\n💬 Simulating struggling learner:")
    
    for i, interaction in enumerate(struggle_interactions, 1):
        print(f"\n   Interaction {i}: {interaction}")
        
        response = system.process_interaction(learner_id, interaction)
        print_response(response)
        
        # Show struggle assessment
        progress = system.get_learner_progress(learner_id)
        struggle = progress['struggle_assessment']
        
        print(f"   📊 Struggle Assessment:")
        print(f"      Error rate: {struggle['error_rate']:.2f}")
        print(f"      Confusion: {struggle['confusion_level']:.2f}")
        print(f"      Frustration: {struggle['frustration_level']:.2f}")
        print(f"      Needs intervention: {struggle['needs_intervention']}")
        if struggle['needs_intervention']:
            print(f"      Intervention type: {struggle['intervention_type']}")


if __name__ == "__main__":
    print("🚀 Constructivist Learning System Demo")
    print("Using Pattern Language Principles for Domain-Agnostic Learning")
    
    # Run demos
    demo_basic_interaction()
    demo_force_application()
    demo_cross_domain_patterns()
    demo_struggle_detection()
    
    print_separator("Demo Complete")
    print("This demonstrates the core functionality of the constructivist learning system.")
    print("The system can be extended with more patterns, forces, and domains.") 