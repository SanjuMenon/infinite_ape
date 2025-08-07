# Stigmergic AI Agent for StreamBench

This document explains the Stigmergic AI agent implementation for StreamBench, based on the UML architecture diagram you provided.

## 🏗️ Architecture Overview

The Stigmergic AI agent implements a sophisticated multi-agent system with the following key components:

### Core Components

1. **Substrate** - The shared environment where agents interact indirectly
2. **Stable Agency** - Central orchestrator that manages the system
3. **Persona** - Specific identities or roles within the system
4. **TacitInstruction** - Implicit guidance (normative and prescriptive)
5. **Fitness Function** - Evaluates system stability and performance
6. **MarkovPlanner** - Plans sequential actions
7. **Agent** - Individual intelligent entities

### Stigmergic Communication

The system uses **stigmergic communication** - agents communicate indirectly by modifying the shared substrate, leaving traces that guide future actions.

## 📁 Files Created

1. **`stream_bench/agents/stigmergic_agent.py`** - Main Stigmergic AI implementation
2. **`configs/agent/stigmergic.yml`** - Configuration file
3. **`STIGMERGIC_AI_README.md`** - This documentation

## 🚀 Key Features

### 1. **Stigmergic Learning**
- Agents leave traces in the substrate
- Future agents build upon these traces
- Indirect communication through environmental modification

### 2. **Multi-Persona System**
- Multiple personas with different characteristics
- Each persona contributes different perspectives
- Adaptive persona selection based on context

### 3. **Tacit Instructions**
- **Normative instructions**: "should" guidelines for consistency
- **Prescriptive instructions**: "must" requirements for outcomes
- Dynamic instruction adaptation based on performance

### 4. **Fitness Function**
- Evaluates system stability
- Measures trace consistency, agent coordination, and task completion
- Provides go/no-go decisions for system adaptation

### 5. **Markov Planning**
- Sequential action planning
- Confidence-based step selection
- Adaptive planning based on stability scores

## 🎯 How to Use

### Basic Usage

```bash
# Set your API key
export OAI_KEY=<your_openai_api_key>

# Run Stigmergic AI agent on DDXPlus dataset
python -m stream_bench.pipelines.run_bench \
    --agent_cfg "configs/agent/stigmergic.yml" \
    --bench_cfg "configs/bench/ddxplus.yml" \
    --entity "your_entity" \
    --use_wandb
```

### Advanced Configuration

Edit `configs/agent/stigmergic.yml` to customize:

```yaml
# Adjust stability threshold
stability_threshold: 0.7

# Configure personas
personas:
  - "Expert analyst who identifies patterns and trends"
  - "Creative problem solver who explores innovative solutions"

# Modify fitness function weights
fitness_function:
  trace_consistency_weight: 0.4
  agent_coordination_weight: 0.3
  task_completion_weight: 0.3
```

## 🔧 Architecture Details

### Substrate Class
```python
class Substrate:
    """The environment or shared medium where agents interact."""
    
    def add_trace(self, agent_id: str, trace: Dict[str, Any]):
        """Add a stigmergic trace to the substrate."""
    
    def get_relevant_traces(self, context: str, limit: int = 5) -> List[Dict]:
        """Get relevant traces based on context."""
```

### Fitness Function
```python
class FitnessFunction:
    """Evaluates the fitness or stability of the system."""
    
    def calculate_stability(self, substrate: Substrate, planned_agents: Set[str]) -> float:
        """Calculate stability based on:
        1. Consistency of traces
        2. Agent coordination  
        3. Task completion rate
        """
```

### Tacit Instructions
```python
@dataclass
class TacitInstruction:
    """Represents implicit or unstated instructions."""
    id: int
    name: str
    description: str
    instruction_type: InstructionType  # NORMATIVE or PRESCRIPTIVE
    memory: Dict[str, Any] = None
```

## 🧠 How It Works

### 1. **Initialization Phase**
- Creates substrate for shared environment
- Initializes personas with different characteristics
- Sets up normative and prescriptive instructions
- Configures fitness function and Markov planner

### 2. **Inference Phase**
- Updates substrate with current task context
- Retrieves relevant traces from substrate
- Builds stigmergic context from previous interactions
- Generates response using LLM with stigmergic context
- Leaves trace in substrate for future agents

### 3. **Learning Phase**
- Receives feedback on predictions
- Updates substrate with feedback traces
- Calculates stability using fitness function
- Reinforces successful patterns in normative instructions
- Adapts from mistakes in prescriptive instructions
- Updates planning strategy based on stability

### 4. **Adaptation Phase**
- Monitors system stability
- Adjusts planning based on fitness scores
- Updates persona selection strategies
- Modifies trace relevance thresholds

## 📊 Performance Metrics

The Stigmergic AI agent tracks:

- **Stability Score**: Overall system stability (0-1)
- **Trace Count**: Number of stigmergic traces
- **Successful Patterns**: Number of reinforced patterns
- **Plan Steps**: Number of planned actions
- **Persona Utilization**: Distribution across personas

## 🔬 Advanced Features

### 1. **Semantic Pattern Extraction**
```yaml
advanced_features:
  use_semantic_patterns: true
  use_embeddings_for_traces: true
```

### 2. **Multi-Persona Planning**
```yaml
advanced_features:
  use_multi_persona_planning: true
```

### 3. **Adaptive Thresholds**
```yaml
advanced_features:
  use_adaptive_thresholds: true
```

## 🎯 Use Cases

### 1. **Complex Problem Solving**
- Multiple personas approach problems differently
- Stigmergic traces build cumulative knowledge
- Fitness function ensures solution quality

### 2. **Continuous Learning**
- Agents learn from each other's traces
- Patterns emerge and get reinforced
- System adapts to changing requirements

### 3. **Multi-Agent Coordination**
- Indirect communication through substrate
- Emergent coordination without direct communication
- Scalable to many agents

## 🔧 Customization Options

### 1. **Add New Personas**
```python
def _initialize_personas(self, config: dict) -> List[Persona]:
    custom_personas = config.get("personas", [])
    for persona_desc in custom_personas:
        personas.append(Persona(id=len(personas) + 1, description=persona_desc))
```

### 2. **Custom Fitness Metrics**
```python
def calculate_stability(self, substrate: Substrate, planned_agents: Set[str]) -> float:
    # Add your custom stability metrics
    custom_metric = self._calculate_custom_metric(substrate)
    return (trace_consistency + agent_coordination + task_completion + custom_metric) / 4
```

### 3. **Enhanced Trace Analysis**
```python
def get_relevant_traces(self, context: str, limit: int = 5) -> List[Dict]:
    # Implement semantic similarity for better trace retrieval
    # Use embeddings to find most relevant traces
```

## 🚀 Comparison with Other Agents

| Feature | Stigmergic AI | Custom Agent | Zero-Shot |
|---------|---------------|--------------|-----------|
| Learning Method | Stigmergic traces | Memory-based | None |
| Communication | Indirect via substrate | Direct | None |
| Personas | Multiple personas | Single agent | None |
| Planning | Markov planning | Simple memory | None |
| Adaptation | Fitness-based | Performance-based | None |

## 🎯 Best Practices

### 1. **Configuration**
- Start with default settings
- Adjust stability threshold based on task complexity
- Monitor trace count to prevent memory overflow

### 2. **Persona Design**
- Create diverse personas for different problem-solving approaches
- Ensure personas complement each other
- Monitor persona utilization patterns

### 3. **Trace Management**
- Set appropriate max_traces limit
- Implement trace decay for old traces
- Use semantic similarity for trace retrieval

### 4. **Fitness Function Tuning**
- Balance trace consistency vs. exploration
- Adjust weights based on task requirements
- Monitor stability trends over time

## 🔍 Troubleshooting

### Common Issues:

1. **Low Stability Scores**
   - Check trace consistency
   - Verify agent coordination
   - Review task completion rates

2. **Memory Issues**
   - Reduce max_traces
   - Implement trace decay
   - Use more efficient trace storage

3. **Poor Performance**
   - Adjust stability threshold
   - Review persona configurations
   - Check tacit instruction memory

## 🎯 Next Steps

1. **Test on different datasets** to understand performance patterns
2. **Experiment with persona configurations** for optimal results
3. **Implement semantic trace analysis** for better pattern recognition
4. **Add multi-agent coordination** for complex tasks
5. **Develop adaptive threshold mechanisms** for dynamic environments

## 📚 References

- **Stigmergy**: Indirect coordination through environmental modification
- **Multi-Agent Systems**: Distributed problem solving
- **Fitness Functions**: Evolutionary algorithm concepts
- **Markov Planning**: Sequential decision making

---

**The Stigmergic AI agent represents a sophisticated approach to continuous learning and adaptation, perfect for benchmarking advanced language agent capabilities! 🚀** 