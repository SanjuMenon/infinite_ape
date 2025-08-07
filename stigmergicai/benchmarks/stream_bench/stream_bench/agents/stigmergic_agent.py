import json
import textwrap
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
import random

from .base import Agent


class InstructionType(Enum):
    NORMATIVE = "normative"
    PRESCRIPTIVE = "prescriptive"


@dataclass
class Persona:
    """Represents a specific identity or role within the system."""
    id: int
    description: str
    memory: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.memory is None:
            self.memory = {}


@dataclass
class TacitInstruction:
    """Represents implicit or unstated instructions."""
    id: int
    name: str
    description: str
    instruction_type: InstructionType
    memory: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.memory is None:
            self.memory = {}


@dataclass
class PlanStep:
    """Represents a single step within a plan."""
    step: str
    coupled_agent: str
    confidence: float = 0.0


class Substrate:
    """The environment or shared medium where agents interact."""
    
    def __init__(self, id: int):
        self.id = id
        self.stable_sheet = {}  # Generative function results
        self.rules_of_selection = []
        self.rules_of_extension = []
        self.memory = {}
        self.shared_state = {}
        self.traces = []  # Stigmergic traces left by agents
    
    def add_trace(self, agent_id: str, trace: Dict[str, Any]):
        """Add a stigmergic trace to the substrate."""
        self.traces.append({
            "agent_id": agent_id,
            "trace": trace,
            "timestamp": len(self.traces)
        })
    
    def get_relevant_traces(self, context: str, limit: int = 5) -> List[Dict]:
        """Get relevant traces based on context."""
        # Simple relevance scoring - could be enhanced with embeddings
        relevant_traces = []
        for trace in self.traces[-limit:]:
            if context.lower() in str(trace["trace"]).lower():
                relevant_traces.append(trace)
        return relevant_traces
    
    def update_shared_state(self, key: str, value: Any):
        """Update the shared state."""
        self.shared_state[key] = value


class FitnessFunction:
    """Evaluates the fitness or stability of the system."""
    
    def __init__(self, id: int, threshold: float = 0.7):
        self.id = id
        self.stability_score = 0.0
        self.threshold = threshold
        self.history = []
    
    def calculate_stability(self, substrate: Substrate, planned_agents: Set[str]) -> float:
        """Calculate stability based on substrate and planned agents."""
        # Calculate stability based on:
        # 1. Consistency of traces
        # 2. Agent coordination
        # 3. Task completion rate
        
        trace_consistency = self._calculate_trace_consistency(substrate)
        agent_coordination = self._calculate_agent_coordination(substrate, planned_agents)
        task_completion = self._calculate_task_completion(substrate)
        
        self.stability_score = (trace_consistency + agent_coordination + task_completion) / 3
        self.history.append(self.stability_score)
        
        return self.stability_score
    
    def _calculate_trace_consistency(self, substrate: Substrate) -> float:
        """Calculate consistency of stigmergic traces."""
        if not substrate.traces:
            return 0.5
        
        # Simple consistency metric
        recent_traces = substrate.traces[-10:]
        if len(recent_traces) < 2:
            return 0.5
        
        # Check if traces follow similar patterns
        patterns = [trace["trace"].get("pattern", "default") for trace in recent_traces]
        unique_patterns = len(set(patterns))
        consistency = 1.0 - (unique_patterns / len(patterns))
        
        return max(0.0, min(1.0, consistency))
    
    def _calculate_agent_coordination(self, substrate: Substrate, planned_agents: Set[str]) -> float:
        """Calculate coordination among agents."""
        if not planned_agents:
            return 0.5
        
        # Check if agents are building on each other's traces
        coordination_score = 0.0
        trace_count = len(substrate.traces)
        
        if trace_count > 1:
            # Check if recent traces reference previous ones
            recent_traces = substrate.traces[-5:]
            for i, trace in enumerate(recent_traces[1:], 1):
                if self._traces_reference_each_other(trace, recent_traces[i-1]):
                    coordination_score += 1.0
        
        return min(1.0, coordination_score / max(1, len(planned_agents)))
    
    def _calculate_task_completion(self, substrate: Substrate) -> float:
        """Calculate task completion rate."""
        if not substrate.traces:
            return 0.5
        
        # Count completed vs attempted tasks
        completed = sum(1 for trace in substrate.traces if trace["trace"].get("status") == "completed")
        total = len(substrate.traces)
        
        return completed / max(1, total)
    
    def _traces_reference_each_other(self, trace1: Dict, trace2: Dict) -> bool:
        """Check if two traces reference each other."""
        # Simple reference check - could be enhanced
        content1 = str(trace1["trace"]).lower()
        content2 = str(trace2["trace"]).lower()
        
        # Check for common keywords or patterns
        common_words = set(content1.split()) & set(content2.split())
        return len(common_words) > 2
    
    def go_or_nogo(self) -> bool:
        """Decision-making operation based on stability score and threshold."""
        return self.stability_score >= self.threshold


class MarkovPlanner:
    """Responsible for planning sequences of actions."""
    
    def __init__(self):
        self.plan = set()
        self.memory = {}
        self.transaction_fee = 0.0
    
    def add_plan_step(self, step: PlanStep):
        """Add a plan step."""
        self.plan.add(step)
    
    def get_next_steps(self, context: str, num_steps: int = 3) -> List[PlanStep]:
        """Get next planned steps based on context."""
        # Simple planning - could be enhanced with more sophisticated algorithms
        relevant_steps = []
        for step in self.plan:
            if context.lower() in step.step.lower():
                relevant_steps.append(step)
        
        # Sort by confidence and return top steps
        relevant_steps.sort(key=lambda x: x.confidence, reverse=True)
        return relevant_steps[:num_steps]
    
    def get_transaction_fee(self) -> float:
        return self.transaction_fee
    
    def set_transaction_fee(self, fee: float):
        self.transaction_fee = fee


class StigmergicAgent(Agent):
    """
    A Stigmergic AI agent implementation for StreamBench.
    
    This agent implements the Stigmergic AI architecture with:
    - Substrate for shared environment
    - Stable Agency for orchestration
    - Persona for identity
    - TacitInstructions for implicit guidance
    - Fitness Function for evaluation
    - MarkovPlanner for sequential planning
    """
    
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        
        # Initialize Stigmergic AI components
        self.substrate = Substrate(id=1)
        self.fitness_function = FitnessFunction(
            id=1, 
            threshold=config.get("stability_threshold", 0.7)
        )
        self.markov_planner = MarkovPlanner()
        
        # Initialize personas
        self.personas = self._initialize_personas(config)
        
        # Initialize tacit instructions
        self.normative_instructions = self._initialize_normative_instructions(config)
        self.prescriptive_instructions = self._initialize_prescriptive_instructions(config)
        
        # Agent registry
        self.planned_agents = set()
        self.agent_memory = {}
        
        # Configuration
        self.use_stigmergic_learning = config.get("use_stigmergic_learning", True)
        self.trace_decay_rate = config.get("trace_decay_rate", 0.1)
        self.max_traces = config.get("max_traces", 50)
    
    def _initialize_personas(self, config: dict) -> List[Persona]:
        """Initialize personas based on configuration."""
        personas = []
        
        # Default personas
        default_personas = [
            Persona(id=1, description="Analytical thinker who breaks down complex problems"),
            Persona(id=2, description="Creative problem solver who explores multiple solutions"),
            Persona(id=3, description="Systematic planner who follows structured approaches")
        ]
        
        # Add custom personas from config
        custom_personas = config.get("personas", [])
        for i, persona_desc in enumerate(custom_personas):
            personas.append(Persona(id=len(personas) + 1, description=persona_desc))
        
        return personas + default_personas
    
    def _initialize_normative_instructions(self, config: dict) -> TacitInstruction:
        """Initialize normative (should) instructions."""
        return TacitInstruction(
            id=1,
            name="Normative Guidance",
            description="Follow established patterns and maintain consistency",
            instruction_type=InstructionType.NORMATIVE
        )
    
    def _initialize_prescriptive_instructions(self, config: dict) -> TacitInstruction:
        """Initialize prescriptive (must) instructions."""
        return TacitInstruction(
            id=2,
            name="Prescriptive Guidance", 
            description="Achieve specific outcomes and meet performance targets",
            instruction_type=InstructionType.PRESCRIPTIVE
        )
    
    def __call__(self, prompt: str, label_set: list[str], **kwargs) -> str:
        """
        Generate response using Stigmergic AI approach.
        """
        # Extract context
        task_description = kwargs.get("desc", "Answer the question based on the given options.")
        input_text = kwargs.get("input", prompt)
        time_step = kwargs.get("time_step", 0)
        
        # Update substrate with current context
        self.substrate.update_shared_state("current_task", {
            "description": task_description,
            "input": input_text,
            "time_step": time_step
        })
        
        # Get relevant traces from substrate
        relevant_traces = self.substrate.get_relevant_traces(input_text)
        
        # Build stigmergic context
        stigmergic_context = self._build_stigmergic_context(relevant_traces, input_text)
        
        # Generate response using stigmergic approach
        response_text, response_info = self._generate_stigmergic_response(
            input_text, label_set, stigmergic_context, task_description
        )
        
        # Update logging
        self.update_log_info({
            "num_inference_call": 1,
            "num_success_call": 1 if response_text else 0,
            "num_input_tokens": response_info.get("input_tokens", 0),
            "num_output_tokens": response_info.get("output_tokens", 0),
        })
        
        # Parse response
        predicted_label = self._parse_response(response_text, label_set)
        
        # Leave trace in substrate
        self._leave_trace(input_text, predicted_label, response_text, time_step)
        
        return predicted_label
    
    def _build_stigmergic_context(self, traces: List[Dict], current_input: str) -> str:
        """Build context from stigmergic traces."""
        if not traces:
            return ""
        
        context_parts = ["Previous successful patterns:"]
        
        for trace in traces[-3:]:  # Use last 3 traces
            trace_data = trace["trace"]
            context_parts.append(
                f"Input: {trace_data.get('input', 'N/A')}\n"
                f"Response: {trace_data.get('response', 'N/A')}\n"
                f"Pattern: {trace_data.get('pattern', 'N/A')}\n"
            )
        
        return "\n".join(context_parts)
    
    def _generate_stigmergic_response(self, input_text: str, label_set: List[str], 
                                    stigmergic_context: str, task_description: str) -> tuple:
        """Generate response using stigmergic approach."""
        
        # Build prompt with stigmergic context
        options_text = self.get_options_text(set(label_set))
        
        prompt = f"""Task: {task_description}

{stigmergic_context}

Current Input: {input_text}

Options:
{options_text}

Based on the patterns from previous successful interactions, provide the most appropriate answer:"""

        # Call LLM
        response_text, response_info = self.llm(prompt)
        
        return response_text, response_info
    
    def _leave_trace(self, input_text: str, prediction: str, response_text: str, time_step: int):
        """Leave a stigmergic trace in the substrate."""
        trace = {
            "input": input_text,
            "prediction": prediction,
            "response": response_text,
            "pattern": self._extract_pattern(input_text, prediction),
            "status": "completed",
            "time_step": time_step
        }
        
        self.substrate.add_trace("stigmergic_agent", trace)
        
        # Maintain trace limit
        if len(self.substrate.traces) > self.max_traces:
            self.substrate.traces.pop(0)
    
    def _extract_pattern(self, input_text: str, prediction: str) -> str:
        """Extract pattern from input and prediction."""
        # Simple pattern extraction - could be enhanced
        words = input_text.lower().split()
        if len(words) > 3:
            return f"pattern_{words[0]}_{words[-1]}"
        return "default_pattern"
    
    def update(self, has_feedback: bool, **feedbacks) -> bool:
        """
        Update the agent based on feedback using stigmergic learning.
        """
        if not has_feedback:
            return False
        
        # Extract feedback
        correct_answer = feedbacks.get("y", "")
        prediction = feedbacks.get("prediction", "")
        input_text = feedbacks.get("input", "")
        time_step = feedbacks.get("time_step", 0)
        
        # Calculate if prediction was correct
        is_correct = prediction == correct_answer
        
        # Update substrate with feedback
        feedback_trace = {
            "input": input_text,
            "prediction": prediction,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "time_step": time_step,
            "pattern": self._extract_pattern(input_text, prediction)
        }
        
        self.substrate.add_trace("feedback", feedback_trace)
        
        # Update fitness function
        stability_score = self.fitness_function.calculate_stability(
            self.substrate, self.planned_agents
        )
        
        # Update tacit instructions based on performance
        if is_correct:
            self._reinforce_successful_patterns(input_text, prediction)
        else:
            self._adapt_from_mistake(input_text, prediction, correct_answer)
        
        # Update planning based on stability
        if self.fitness_function.go_or_nogo():
            self._update_planning_strategy()
        
        return True
    
    def _reinforce_successful_patterns(self, input_text: str, prediction: str):
        """Reinforce patterns that led to successful predictions."""
        pattern = self._extract_pattern(input_text, prediction)
        
        # Update normative instructions to reinforce good patterns
        if pattern not in self.normative_instructions.memory:
            self.normative_instructions.memory[pattern] = 0
        self.normative_instructions.memory[pattern] += 1
    
    def _adapt_from_mistake(self, input_text: str, prediction: str, correct_answer: str):
        """Adapt from mistakes to improve future performance."""
        pattern = self._extract_pattern(input_text, prediction)
        
        # Update prescriptive instructions to avoid similar mistakes
        if pattern not in self.prescriptive_instructions.memory:
            self.prescriptive_instructions.memory[pattern] = 0
        self.prescriptive_instructions.memory[pattern] -= 1
    
    def _update_planning_strategy(self):
        """Update planning strategy based on current stability."""
        # Add new plan steps based on successful patterns
        successful_patterns = [
            pattern for pattern, count in self.normative_instructions.memory.items()
            if count > 0
        ]
        
        for pattern in successful_patterns[-3:]:  # Last 3 successful patterns
            plan_step = PlanStep(
                step=f"Apply pattern: {pattern}",
                coupled_agent="stigmergic_agent",
                confidence=0.8
            )
            self.markov_planner.add_plan_step(plan_step)
    
    def get_stigmergic_stats(self) -> Dict[str, Any]:
        """Get statistics about the stigmergic system."""
        return {
            "stability_score": self.fitness_function.stability_score,
            "trace_count": len(self.substrate.traces),
            "successful_patterns": len([
                pattern for pattern, count in self.normative_instructions.memory.items()
                if count > 0
            ]),
            "plan_steps": len(self.markov_planner.plan),
            "personas": len(self.personas)
        }
    
    def _parse_response(self, response_text: str, label_set: List[str]) -> str:
        """Parse the LLM response to extract the predicted label."""
        if not response_text:
            return label_set[0] if label_set else ""
        
        # Clean the response text
        response_text = response_text.strip().lower()
        
        # Try to find an exact match in the label set
        for label in label_set:
            if label.lower() in response_text or response_text in label.lower():
                return label
        
        # If no exact match, try to find the best match
        for label in label_set:
            if any(word in response_text for word in label.lower().split()):
                return label
        
        # Default to first label if no match found
        return label_set[0] if label_set else "" 