# Constructivist Learning System

A domain-agnostic constructivist learning system that uses pattern language principles to guide learners through progressive complexity by applying forces that drive pattern evolution.

## Overview

This system implements a novel approach to personalized learning that combines:

- **Constructivist Learning Theory**: Learners actively construct knowledge through experience
- **Pattern Language Principles**: Concepts evolve through the application of contextual forces
- **Domain-Agnostic Design**: The same learning framework works across programming, math, language, and other domains
- **Adaptive Personalization**: System adapts to individual learning styles and paces

## Core Concepts

### Patterns
A pattern represents a fundamental concept or idea that can be learned and applied. Patterns have:
- **Core Concept**: Simple definition and key components
- **Complexity Level**: 1-10 scale indicating difficulty
- **Evolution Paths**: Possible next patterns to learn
- **Learning Indicators**: Signals for mastery and readiness

### Forces
Forces are contextual pressures that drive pattern evolution:
- **Constraints**: Limitations that require adaptation
- **Requirements**: Necessary conditions that must be met
- **Context**: Environmental factors that change application
- **Edge Cases**: Boundary conditions that test understanding
- **Pressures**: External demands that push for change

### Evolution
Patterns evolve when learners master the current concept and are ready for increased complexity. The system:
- **Detects Readiness**: Monitors mastery signals and learning progress
- **Selects Forces**: Chooses appropriate forces based on learner characteristics
- **Guides Evolution**: Helps learners understand how patterns transform
- **Provides Support**: Offers scaffolding and intervention when needed

## Architecture

```
constructivistlearning/
├── core/
│   ├── schemas.py              # Data structures and type definitions
│   ├── pattern_database.py     # Pattern and force definitions
│   ├── evolution_detector.py   # Mastery assessment and evolution logic
│   └── learning_system.py      # Main system orchestration
├── demo.py                     # Demonstration script
└── README.md                   # This file
```

### Key Components

#### PatternDatabase
- Stores patterns and forces across multiple domains
- Manages pattern relationships and evolution paths
- Provides domain-agnostic pattern definitions

#### EvolutionDetector
- Assesses learner mastery using multiple indicators
- Detects learning struggles and intervention needs
- Determines optimal evolution timing and paths

#### ConstructivistLearningSystem
- Orchestrates the complete learning experience
- Manages learner state and progress tracking
- Generates personalized responses and guidance

## Usage

### Basic Setup

```python
from constructivistlearning import ConstructivistLearningSystem

# Initialize the system
system = ConstructivistLearningSystem()

# Create a new learner
learner_id = "user_123"
learner_state = system.initialize_learner(
    learner_id, 
    domain="programming",
    starting_pattern="var_basic"
)
```

### Processing Interactions

```python
# Process learner input
response = system.process_interaction(
    learner_id, 
    "I understand that variables store data with names"
)

print(response.message)
print(f"Next action: {response.next_action}")
print(f"Confidence: {response.confidence}")
```

### Applying Forces

```python
# Apply a force to introduce complexity
response = system.apply_force(learner_id, "type_safety")
print(response.message)
```

### Checking Progress

```python
# Get comprehensive progress information
progress = system.get_learner_progress(learner_id)

print(f"Current pattern: {progress['current_pattern']['name']}")
print(f"Mastery level: {progress['mastery_assessment']['overall_mastery']}")
print(f"Ready to evolve: {progress['evolution_status']['should_evolve']}")
```

## Running the Demo

```bash
cd constructivistlearning
python demo.py
```

The demo shows:
- Basic learner interactions
- Force application and pattern evolution
- Cross-domain pattern similarities
- Struggle detection and intervention

## Example Learning Flow

### Programming Domain

1. **Start**: Variable Storage pattern
   - Core concept: "A named container that holds one value"
   - Examples: `age = 25`, `name = 'Alice'`

2. **Apply Force**: Type Safety Requirement
   - Pressure: "Data must be validated to prevent errors"
   - Evolution: Variables become typed

3. **Evolve**: Typed Variables pattern
   - Core concept: "A variable that can only hold values of a specific type"
   - Examples: `int age = 25`, `string name = 'Alice'`

4. **Continue**: Apply more forces (Scope Context, Reliability Requirement)
   - Patterns continue to evolve in complexity

### Mathematics Domain

1. **Start**: Number Representation pattern
   - Core concept: "A symbol that represents a specific quantity"
   - Examples: `5`, `42`, `1000`

2. **Apply Force**: Negative Context
   - Pressure: "Real-world situations require values below zero"
   - Evolution: Numbers become signed

3. **Evolve**: Signed Numbers pattern
   - Core concept: "A number that can represent values above or below zero"
   - Examples: `+5`, `-3`, `0`

## Extending the System

### Adding New Patterns

```python
from constructivistlearning.core.schemas import Pattern, CoreConcept, LearningIndicators

new_pattern = Pattern(
    pattern_id="my_new_pattern",
    name="My New Pattern",
    description="Description of the pattern",
    complexity_level=3,
    domain_tags=["my_domain"],
    core_concept=CoreConcept(
        simple_definition="Simple definition",
        key_components=["component1", "component2"],
        examples=["example1", "example2"]
    ),
    prerequisites=["prerequisite_pattern"],
    evolution_paths=["next_pattern"],
    forces=ForceEvolutionMap(
        applicable_forces=["force1", "force2"],
        force_evolution_map={"force1": "evolved_pattern"}
    ),
    learning_indicators=LearningIndicators(
        mastery_signals=["signal1", "signal2"],
        struggle_signals=["struggle1", "struggle2"],
        readiness_criteria=["criteria1", "criteria2"]
    )
)
```

### Adding New Forces

```python
from constructivistlearning.core.schemas import Force, ForceCategory

new_force = Force(
    force_id="my_new_force",
    name="My New Force",
    description="Description of the force",
    category=ForceCategory.REQUIREMENT,
    intensity=3,
    domain_agnostic=True,
    force_definition=ForceDefinition(
        core_pressure="The pressure this force applies",
        evolution_direction="How it pushes patterns to change",
        universal_examples=["example1", "example2"]
    ),
    application_conditions=ApplicationConditions(
        pattern_compatibility=["pattern1", "pattern2"],
        prerequisite_forces=[],
        timing_considerations="When to introduce this force"
    ),
    evolution_outcomes=EvolutionOutcomes(
        pattern_transformations={"pattern1": "evolved_pattern"},
        complexity_increase=2,
        new_capabilities=["capability1", "capability2"]
    )
)
```

## Research Applications

This system is designed for educational research experiments that test:

1. **Constructivist vs. Traditional Learning**: Compare pattern-based evolution with linear instruction
2. **Personalization Effectiveness**: Measure impact of adaptive force selection
3. **Cross-Domain Transfer**: Study how patterns transfer between subjects
4. **Learning Analytics**: Analyze evolution patterns and mastery indicators

## Future Enhancements

- **LLM Integration**: Connect with GPT-4 or Claude for natural language responses
- **Advanced Analytics**: Machine learning for better mastery prediction
- **Visual Interface**: Web-based learning environment
- **Collaborative Learning**: Multi-learner pattern evolution
- **Real-time Assessment**: Continuous learning progress monitoring

## Contributing

This is an experimental system for educational research. Contributions are welcome for:

- Additional patterns and forces
- Improved evolution detection algorithms
- Better personalization strategies
- Enhanced analytics and reporting
- User interface development

## License

This project is for educational research purposes. Please cite appropriately if used in academic work. 

# Stage 3: Personalization & Adaptation - Complete!

I've successfully created the core personalization components for **Stage 3**. Here's what we've built:

## **Stage 3 Complete: Personalization & Adaptation**

### **What We've Created:**

1. **Learner Profiler** (`personalization/learner_profiler.py`)
   - Comprehensive learner profiling with 5 key dimensions:
     - **Learning Preferences**: Style, difficulty, domains, contexts
     - **Cognitive Profile**: Memory, processing speed, attention, pattern recognition
     - **Behavioral Profile**: Persistence, risk tolerance, error handling, exploration
     - **Performance Profile**: Mastery rate, retention, transfer ability, learning curve
     - **Engagement Profile**: Motivation, interests, frustration tolerance, challenge preference

2. **Adaptive Force Selector** (`personalization/adaptive_force_selector.py`)
   - Intelligent force selection based on 6 criteria:
     - Learner preference matching
     - Cognitive fit assessment
     - Behavioral compatibility
     - Performance optimization
     - Engagement enhancement
     - Contextual relevance
   - Force sequence recommendations
   - Expected impact calculations

### **Key Features Implemented:**

✅ **Multi-Dimensional Profiling**: Tracks 20+ learner characteristics
✅ **Real-Time Adaptation**: Updates profiles based on interactions and performance
✅ **Intelligent Force Selection**: Scores forces across multiple criteria
✅ **Personalized Recommendations**: Adapts pacing, scaffolding, and interaction style
✅ **Performance Optimization**: Avoids error patterns, reinforces success patterns
✅ **Engagement Enhancement**: Matches forces to motivation and interest levels

### **How It Works:**

1. **Profile Creation**: Initial profile with default values
2. **Continuous Learning**: Updates profile based on every interaction
3. **Force Scoring**: Each force scored across 6 dimensions
4. **Optimal Selection**: Chooses forces that best match learner characteristics
5. **Adaptive Recommendations**: Adjusts learning experience in real-time

### **Personalization Examples:**

```python
# Visual learner with low working memory
profile.preferences.learning_style = LearningStyle.VISUAL
profile.cognitive.working_memory_capacity = 0.3
# System recommends: Low-intensity forces, high scaffolding, visual aids

# High-performing kinesthetic learner
profile.preferences.learning_style = LearningStyle.KINESTHETIC
profile.performance.mastery_rate = 0.8
# System recommends: High-intensity forces, hands-on examples, rapid pacing

# Struggling learner with low motivation
profile.performance.mastery_rate = 0.2
profile.engagement.intrinsic_motivation = 0.3
# System recommends: Simple forces, frequent feedback, real-world contexts
```

