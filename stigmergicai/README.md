# Stigmergic AI

A research project exploring stigmergic (indirect coordination through environment) approaches to multi-agent AI systems. This project implements hierarchical agent architectures and evolvable AI components using systematic inventive thinking (SIT) principles.

## Architecture Overview

The system is built around a **Stable Agency** that orchestrates coordination between multiple components:

![Stigmergic AI UML](stigmergic%20ai%20uml.png)

### Core Architecture Components

- **Stable Agency** (Red) - Central orchestrator that manages the overall system
- **Substrate** (Yellow) - Environmental layer with stable sheets and selection/extension rules
- **Persona** (Blue) - Identity and memory components for agents
- **Tacit Instructions (TI)** (Blue) - Implicit knowledge and instructions
- **Agent** (Green) - Individual agents with identity descriptions and constraints
- **Fitness Function (FF)** (Blue) - Evaluation mechanism with stability scoring
- **MarkovPlanner** (Yellow) - Planning component with plan steps
- **PlanStep** (Yellow) - Individual planning steps coupled to agents

### Key Relationships

- **Stable Agency** acts as the central hub, managing multiple agents and planners
- **Substrate** provides the environmental context with stable sheets and coordination rules
- **Persona and TI** components initialize and provide identity/memory for the system
- **Fitness Function** evaluates system stability and provides go/no-go decisions
- **MarkovPlanner** manages planning with multiple plan steps, each coupled to specific agents
- Users can send multiple instructions to the Stable Agency, which coordinates responses through the agent network

## Overview

This project explores how AI agents can coordinate through environmental modifications rather than direct communication, inspired by stigmergy in nature (like ant colonies using pheromone trails). The system implements hierarchical organizational structures and evolvable components that can adapt and transform themselves.

## Project Structure

### Core Components

- **`planner_and_assigner.py`** - Implements a multi-agent system with specialized roles (planner, sales, product, engineering, AI) that coordinate through message passing
- **`hierarchical_structure.py`** - Creates organizational hierarchies (CEO → CMO/CTO → Department Heads) with delegation patterns
- **`gradio_patch.py`** - Web interface for interacting with the agent systems

### Evolvable AI (`evolvable/`)

- **`model.py`** - Implements SIT (Systematic Inventive Thinking) operations for class transformation:
  - Subtraction: Removing components to achieve improvement
  - Division: Splitting classes by methods or attributes
  - Task Unification: Combining unrelated functions
  - Attribute Dependency: Creating conditional relationships
- **`pyglove_sit.py`** - PyGlove integration for symbolic programming and class manipulation

### Substrates (`substrates/`)

- **`active_inference_tt.py`** - Active inference implementations
- **`global_lcmc.py`** - Global LCMC (Local Causal Markov Condition) components
- **`planning.py`** - Planning substrate implementations
- **`searchable_components/`** - Searchable component architecture

### Benchmarks (`benchmarks/`)

- **`stream_bench_for_stigmergic/`** - Benchmarking tools for stigmergic systems

### Tools (`tools/`)

- Various utility tools and helper functions

### Fitness Functions (`fitness_functions/`)

- Evaluation metrics and fitness functions for evolutionary processes

## Key Concepts

### Stigmergy
Agents coordinate indirectly by modifying their shared environment rather than communicating directly. This creates emergent coordination patterns.

### Hierarchical Organization
The system implements organizational hierarchies where higher-level agents delegate to specialized lower-level agents, creating structured coordination patterns.

### Evolvable Components
Using SIT principles, components can transform themselves through systematic operations like subtraction, division, and task unification.

## Usage

### Running the Hierarchical System
```python
from hierarchical_structure import agency
# The agency is configured with CEO → CMO/CTO → Department Heads structure
```

### Running the Planner-Assigner System
```python
from planner_and_assigner import planner, teams
# Creates a planner that assigns tasks to specialized team agents
```

### Using Evolvable Components
```python
from evolvable.model import SITOperationsManager

manager = SITOperationsManager()
# Apply SIT transformations to classes
transformed_class = manager.apply_sit_operation('subtraction', MyClass, 
                                              methods_to_remove=['method1'])
```

## Research Goals

1. **Stigmergic Coordination**: Explore how agents can coordinate through environmental modifications
2. **Hierarchical Delegation**: Study how organizational structures emerge in AI systems
3. **Evolvable Architecture**: Develop systems that can transform and adapt their own structure
4. **Systematic Innovation**: Apply SIT principles to AI system design

## Dependencies

- `agency_swarm` - Multi-agent framework
- `pyglove` - Symbolic programming
- `openai` - LLM integration
- `gradio` - Web interface
- `pydantic` - Data validation

## Status

This is experimental research code. The project is actively being developed and refined as part of ongoing research into stigmergic AI systems.

## Related Work

For more information about the broader research program, see: https://github.com/SanjuMenon/OrchestrableAI/ (currently private repo) 