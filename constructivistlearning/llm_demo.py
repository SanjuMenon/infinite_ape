"""
LLM-Enhanced Constructivist Learning System Demo.

This script demonstrates the LLM integration capabilities of the constructivist
learning system. It requires an OpenAI API key to run.
"""

import os
import sys
from typing import Optional

# Add the parent directory to the path so we can import the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constructivistlearning import LLM_AVAILABLE, LLMEnhancedLearningSystem
from constructivistlearning.core.learning_system import ConstructivistLearningSystem


def get_api_key() -> Optional[str]:
    """Get OpenAI API key from environment or user input."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI API key not found in environment variables.")
        print("Please set OPENAI_API_KEY environment variable or enter it below:")
        api_key = input("Enter your OpenAI API key: ").strip()
        if not api_key:
            print("❌ No API key provided. Running demo without LLM integration.")
            return None
    return api_key


def demo_llm_enhanced_system():
    """Demonstrate the LLM-enhanced learning system."""
    
    print("🚀 LLM-Enhanced Constructivist Learning System Demo")
    print("=" * 60)
    
    # Check if LLM integration is available
    if not LLM_AVAILABLE:
        print("❌ LLM integration not available. Please install openai package:")
        print("   pip install openai")
        return
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("🔄 Running demo with basic system (no LLM integration)...")
        demo_basic_system()
        return
    
    try:
        # Initialize LLM-enhanced system
        print("🔧 Initializing LLM-enhanced learning system...")
        system = LLMEnhancedLearningSystem(api_key=api_key, model="gpt-4")
        
        # Initialize a learner
        learner_id = "llm_demo_user"
        learner_state = system.initialize_learner(
            learner_id, 
            domain="programming",
            starting_pattern="var_basic"
        )
        
        print(f"✅ Learner initialized: {learner_id}")
        print(f"🎯 Starting pattern: {learner_state.current_pattern}")
        print(f"🌐 Domain: {learner_state.learning_preferences['domain_interest']}")
        
        # Demo interactions
        demo_interactions = [
            "I'm new to programming and want to understand variables",
            "I see that variables store data, but I'm confused about when to use them",
            "I understand variables now! I can create them like age = 25",
            "I'm ready to learn more advanced concepts"
        ]
        
        print("\n💬 Demo Interactions:")
        print("-" * 40)
        
        for i, interaction in enumerate(demo_interactions, 1):
            print(f"\n📝 Interaction {i}:")
            print(f"   Learner: {interaction}")
            
            try:
                # Process interaction with LLM
                response = system.process_interaction(learner_id, interaction)
                
                print(f"\n🤖 LLM Response:")
                print(f"   {response['message']}")
                print(f"\n📊 Analysis:")
                print(f"   Understanding Level: {response['llm_analysis']['understanding_level']:.2f}")
                print(f"   Next Action: {response['next_action']}")
                print(f"   Confidence: {response['confidence']:.2f}")
                
                if response['llm_analysis']['mastery_signals']:
                    print(f"   Mastery Signals: {', '.join(response['llm_analysis']['mastery_signals'])}")
                if response['llm_analysis']['struggle_signals']:
                    print(f"   Struggle Signals: {', '.join(response['llm_analysis']['struggle_signals'])}")
                
            except Exception as e:
                print(f"   ❌ Error processing interaction: {e}")
                continue
        
        # Show enhanced progress report
        print("\n📈 Enhanced Progress Report:")
        print("-" * 40)
        
        try:
            progress = system.get_learner_progress(learner_id)
            
            print(f"Current Pattern: {progress['current_pattern']['name']}")
            print(f"Mastery Level: {progress['mastery_assessment']['overall_mastery']:.2f}")
            print(f"Confidence: {progress['mastery_assessment']['confidence_level']:.2f}")
            
            if 'llm_insights' in progress:
                print(f"\n🧠 LLM Insights:")
                print(f"   Reflection Prompt: {progress['llm_insights']['reflection_prompt'][:100]}...")
                print(f"   Learning Style Recommendations:")
                for rec in progress['llm_insights']['learning_style_recommendations'][:3]:
                    print(f"     • {rec}")
                print(f"   Next Steps Suggestions:")
                for step in progress['llm_insights']['next_steps_suggestions'][:3]:
                    print(f"     • {step}")
            
        except Exception as e:
            print(f"❌ Error getting progress: {e}")
    
    except Exception as e:
        print(f"❌ Error initializing LLM system: {e}")
        print("🔄 Falling back to basic system...")
        demo_basic_system()


def demo_basic_system():
    """Demonstrate the basic learning system without LLM integration."""
    
    print("\n🔄 Basic Constructivist Learning System Demo")
    print("=" * 50)
    
    try:
        # Initialize basic system
        system = ConstructivistLearningSystem()
        
        # Initialize a learner
        learner_id = "basic_demo_user"
        learner_state = system.initialize_learner(learner_id, domain="programming")
        
        print(f"✅ Learner initialized: {learner_id}")
        print(f"🎯 Starting pattern: {learner_state.current_pattern}")
        
        # Demo interactions
        demo_interactions = [
            "I'm learning about variables",
            "I understand variables now",
            "I want to learn more"
        ]
        
        print("\n💬 Demo Interactions:")
        print("-" * 30)
        
        for i, interaction in enumerate(demo_interactions, 1):
            print(f"\n📝 Interaction {i}:")
            print(f"   Learner: {interaction}")
            
            try:
                response = system.process_interaction(learner_id, interaction)
                print(f"\n🤖 System Response:")
                print(f"   {response.message}")
                print(f"   Next Action: {response.next_action}")
                print(f"   Confidence: {response.confidence:.2f}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Show progress
        print("\n📈 Progress Report:")
        print("-" * 30)
        
        try:
            progress = system.get_learner_progress(learner_id)
            print(f"Current Pattern: {progress['current_pattern']['name']}")
            print(f"Mastery Level: {progress['mastery_assessment']['overall_mastery']:.2f}")
            print(f"Ready to Evolve: {progress['evolution_status']['should_evolve']}")
            
        except Exception as e:
            print(f"❌ Error getting progress: {e}")
    
    except Exception as e:
        print(f"❌ Error with basic system: {e}")


def demo_prompt_templates():
    """Demonstrate the prompt templates without making API calls."""
    
    print("\n📝 Prompt Templates Demo")
    print("=" * 40)
    
    try:
        from constructivistlearning.llm.prompt_templates import ConstructivistPromptTemplates, PromptContext
        from constructivistlearning.core.schemas import Pattern, CoreConcept, LearningIndicators, ForceEvolutionMap
        
        # Create a sample pattern
        sample_pattern = Pattern(
            pattern_id="demo_pattern",
            name="Demo Pattern",
            description="A sample pattern for demonstration",
            complexity_level=2,
            domain_tags=["demo"],
            core_concept=CoreConcept(
                simple_definition="A sample concept for demonstration",
                key_components=["component1", "component2"],
                examples=["example1", "example2"]
            ),
            prerequisites=[],
            evolution_paths=[],
            forces=ForceEvolutionMap(
                applicable_forces=[],
                force_evolution_map={}
            ),
            learning_indicators=LearningIndicators(
                mastery_signals=[],
                struggle_signals=[],
                readiness_criteria=[]
            )
        )
        
        # Create sample learner state
        from constructivistlearning.core.schemas import LearnerState
        sample_learner_state = LearnerState(
            learner_id="demo_user",
            current_pattern="demo_pattern",
            pattern_history=[],
            force_exposure={},
            readiness_indicators={},
            learning_preferences={"learning_style": "visual", "preferred_difficulty": "medium"},
            session_data={}
        )
        
        # Create prompt context
        context = PromptContext(
            learner_state=sample_learner_state,
            current_pattern=sample_pattern,
            applied_force=None,
            interaction_history=[],
            domain="demo",
            learning_style="visual",
            difficulty_preference="medium"
        )
        
        # Generate sample prompts
        templates = ConstructivistPromptTemplates()
        
        print("🔧 System Prompt:")
        print("-" * 20)
        system_prompt = templates.get_system_prompt()
        print(system_prompt[:200] + "...")
        
        print("\n📚 Pattern Introduction Prompt:")
        print("-" * 30)
        intro_prompt = templates.get_pattern_introduction_prompt(context)
        print(intro_prompt[:300] + "...")
        
        print("\n🔍 Interaction Analysis Prompt:")
        print("-" * 30)
        analysis_prompt = templates.get_interaction_analysis_prompt(context, "I understand this concept")
        print(analysis_prompt[:300] + "...")
        
        print("\n✅ Prompt templates working correctly!")
        
    except ImportError:
        print("❌ LLM module not available for prompt template demo")
    except Exception as e:
        print(f"❌ Error with prompt templates: {e}")


def main():
    """Main demo function."""
    
    print("🎓 Constructivist Learning System - LLM Integration Demo")
    print("=" * 60)
    
    # Check what's available
    print(f"🔧 LLM Integration Available: {LLM_AVAILABLE}")
    
    if LLM_AVAILABLE:
        print("✅ OpenAI integration ready")
        demo_llm_enhanced_system()
    else:
        print("⚠️  LLM integration not available")
        demo_basic_system()
    
    # Always show prompt templates demo
    demo_prompt_templates()
    
    print("\n🎉 Demo Complete!")
    print("\n💡 Next Steps:")
    print("   • Set OPENAI_API_KEY environment variable for full LLM integration")
    print("   • Install openai package: pip install openai")
    print("   • Explore the prompt templates for customization")
    print("   • Add more patterns and forces to the database")


if __name__ == "__main__":
    main() 