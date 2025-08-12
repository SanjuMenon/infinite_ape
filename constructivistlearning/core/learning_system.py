"""
Main Learning System for the constructivist learning experiment.
Orchestrates pattern evolution, force application, and learner state management.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .schemas import Pattern, Force, LearnerState
from .pattern_database import PatternDatabase
from .evolution_detector import EvolutionDetector, EvolutionDecision, MasteryAssessment, StruggleAssessment


@dataclass
class LearningSession:
    """Represents a learning session with the system."""
    session_id: str
    learner_id: str
    current_pattern: Pattern
    applied_force: Optional[Force]
    interaction_history: List[Dict]
    session_metrics: Dict


@dataclass
class LearningResponse:
    """Response from the learning system to a learner interaction."""
    message: str
    pattern_context: str
    force_context: Optional[str]
    next_action: str  # "continue", "evolve", "intervene", "complete"
    confidence: float
    reasoning: str


class ConstructivistLearningSystem:
    """Main system for constructivist learning using pattern language principles."""
    
    def __init__(self):
        self.pattern_db = PatternDatabase()
        self.evolution_detector = EvolutionDetector(self.pattern_db)
        self.learner_states: Dict[str, LearnerState] = {}
        self.session_history: Dict[str, List[LearningSession]] = {}
    
    def initialize_learner(self, learner_id: str, domain: str = "programming", 
                          starting_pattern: str = "var_basic") -> LearnerState:
        """Initialize a new learner in the system."""
        
        # Get the starting pattern
        pattern = self.pattern_db.get_pattern(starting_pattern)
        if not pattern:
            raise ValueError(f"Starting pattern {starting_pattern} not found")
        
        # Create initial learner state
        learner_state = LearnerState(
            learner_id=learner_id,
            current_pattern=starting_pattern,
            pattern_history=[],
            force_exposure={},
            readiness_indicators={
                "conceptual_understanding": 0.0,
                "pattern_fluency": 0.0,
                "force_handling": 0.0
            },
            learning_preferences={
                "preferred_difficulty": "medium",
                "learning_style": "balanced",
                "domain_interest": domain
            },
            session_data={
                "error_rate": 0.0,
                "confusion_level": 0.0,
                "frustration_level": 0.0,
                "recent_sessions": []
            }
        )
        
        self.learner_states[learner_id] = learner_state
        self.session_history[learner_id] = []
        
        return learner_state
    
    def process_interaction(self, learner_id: str, user_input: str, 
                          interaction_type: str = "conversation") -> LearningResponse:
        """Process a learner interaction and return an appropriate response."""
        
        # Get current learner state
        learner_state = self.learner_states.get(learner_id)
        if not learner_state:
            raise ValueError(f"Learner {learner_id} not found")
        
        # Get current pattern
        current_pattern = self.pattern_db.get_pattern(learner_state.current_pattern)
        if not current_pattern:
            raise ValueError(f"Current pattern {learner_state.current_pattern} not found")
        
        # Analyze the interaction
        interaction_data = self._analyze_interaction(user_input, interaction_type)
        
        # Update learner state
        updated_state = self.evolution_detector.update_learner_state(learner_state, interaction_data)
        self.learner_states[learner_id] = updated_state
        
        # Check for evolution opportunities
        evolution_decision = self.evolution_detector.decide_evolution(updated_state, current_pattern)
        
        # Generate response based on evolution decision
        response = self._generate_response(updated_state, current_pattern, evolution_decision, user_input)
        
        return response
    
    def apply_force(self, learner_id: str, force_id: str) -> LearningResponse:
        """Apply a specific force to the learner's current pattern."""
        
        learner_state = self.learner_states.get(learner_id)
        if not learner_state:
            raise ValueError(f"Learner {learner_id} not found")
        
        current_pattern = self.pattern_db.get_pattern(learner_state.current_pattern)
        force = self.pattern_db.get_force(force_id)
        
        if not force:
            raise ValueError(f"Force {force_id} not found")
        
        # Check if force is compatible with current pattern
        compatible_forces = self.pattern_db.get_compatible_forces(learner_state.current_pattern)
        if force not in compatible_forces:
            return LearningResponse(
                message=f"The force '{force.name}' is not compatible with your current pattern '{current_pattern.name}'.",
                pattern_context=current_pattern.core_concept.simple_definition,
                force_context=None,
                next_action="continue",
                confidence=0.0,
                reasoning="Incompatible force application"
            )
        
        # Update force exposure
        force_exposure = learner_state.force_exposure.copy()
        if learner_state.current_pattern not in force_exposure:
            force_exposure[learner_state.current_pattern] = []
        force_exposure[learner_state.current_pattern].append(force_id)
        
        # Update learner state
        updated_state = LearnerState(
            learner_id=learner_state.learner_id,
            current_pattern=learner_state.current_pattern,
            pattern_history=learner_state.pattern_history,
            force_exposure=force_exposure,
            readiness_indicators=learner_state.readiness_indicators,
            learning_preferences=learner_state.learning_preferences,
            session_data=learner_state.session_data
        )
        
        self.learner_states[learner_id] = updated_state
        
        # Generate force application response
        response = self._generate_force_response(current_pattern, force)
        
        return response
    
    def evolve_pattern(self, learner_id: str, target_pattern_id: str) -> LearningResponse:
        """Evolve the learner to a new pattern."""
        
        learner_state = self.learner_states.get(learner_id)
        if not learner_state:
            raise ValueError(f"Learner {learner_id} not found")
        
        current_pattern = self.pattern_db.get_pattern(learner_state.current_pattern)
        target_pattern = self.pattern_db.get_pattern(target_pattern_id)
        
        if not target_pattern:
            raise ValueError(f"Target pattern {target_pattern_id} not found")
        
        # Check if evolution is valid
        if target_pattern_id not in current_pattern.evolution_paths:
            return LearningResponse(
                message=f"Cannot evolve from '{current_pattern.name}' to '{target_pattern.name}'. This evolution path is not available.",
                pattern_context=current_pattern.core_concept.simple_definition,
                force_context=None,
                next_action="continue",
                confidence=0.0,
                reasoning="Invalid evolution path"
            )
        
        # Update learner state with new pattern
        pattern_history = learner_state.pattern_history.copy()
        pattern_history.append(learner_state.current_pattern)
        
        updated_state = LearnerState(
            learner_id=learner_state.learner_id,
            current_pattern=target_pattern_id,
            pattern_history=pattern_history,
            force_exposure=learner_state.force_exposure,
            readiness_indicators={
                "conceptual_understanding": 0.0,
                "pattern_fluency": 0.0,
                "force_handling": 0.0
            },
            learning_preferences=learner_state.learning_preferences,
            session_data={
                "error_rate": 0.0,
                "confusion_level": 0.0,
                "frustration_level": 0.0,
                "recent_sessions": []
            }
        )
        
        self.learner_states[learner_id] = updated_state
        
        # Generate evolution response
        response = self._generate_evolution_response(current_pattern, target_pattern)
        
        return response
    
    def get_learner_progress(self, learner_id: str) -> Dict:
        """Get comprehensive progress information for a learner."""
        
        learner_state = self.learner_states.get(learner_id)
        if not learner_state:
            raise ValueError(f"Learner {learner_id} not found")
        
        current_pattern = self.pattern_db.get_pattern(learner_state.current_pattern)
        
        # Get mastery assessment
        mastery = self.evolution_detector.assess_mastery(learner_state, current_pattern)
        struggles = self.evolution_detector.assess_struggles(learner_state, current_pattern)
        
        # Get available evolution paths
        evolution_decision = self.evolution_detector.decide_evolution(learner_state, current_pattern)
        
        return {
            "learner_id": learner_id,
            "current_pattern": {
                "id": current_pattern.pattern_id,
                "name": current_pattern.name,
                "description": current_pattern.description,
                "complexity_level": current_pattern.complexity_level
            },
            "pattern_history": learner_state.pattern_history,
            "mastery_assessment": {
                "conceptual_understanding": mastery.conceptual_understanding,
                "pattern_fluency": mastery.pattern_fluency,
                "force_handling": mastery.force_handling,
                "overall_mastery": mastery.overall_mastery,
                "confidence_level": mastery.confidence_level
            },
            "struggle_assessment": {
                "error_rate": struggles.error_rate,
                "confusion_level": struggles.confusion_level,
                "frustration_level": struggles.frustration_level,
                "needs_intervention": struggles.needs_intervention,
                "intervention_type": struggles.intervention_type
            },
            "evolution_status": {
                "should_evolve": evolution_decision.should_evolve,
                "target_pattern": evolution_decision.target_pattern,
                "triggering_force": evolution_decision.triggering_force,
                "confidence": evolution_decision.confidence,
                "reasoning": evolution_decision.reasoning,
                "evolution_type": evolution_decision.evolution_type
            },
            "available_forces": [
                {
                    "id": force.force_id,
                    "name": force.name,
                    "description": force.description,
                    "category": force.category.value,
                    "intensity": force.intensity
                }
                for force in self.pattern_db.get_compatible_forces(learner_state.current_pattern)
            ]
        }
    
    def _analyze_interaction(self, user_input: str, interaction_type: str) -> Dict:
        """Analyze a user interaction to extract learning indicators."""
        
        # This is a simplified analysis - in a real system, this would use
        # NLP and more sophisticated analysis
        interaction_data = {
            "input": user_input,
            "type": interaction_type,
            "timestamp": "2024-01-01T00:00:00Z"  # In real system, use actual timestamp
        }
        
        # Simple keyword-based analysis for demonstration
        user_input_lower = user_input.lower()
        
        # Check for confusion indicators
        confusion_indicators = ["confused", "don't understand", "unclear", "what do you mean", "?"]
        confusion_count = sum(1 for indicator in confusion_indicators if indicator in user_input_lower)
        interaction_data["confusion_indicators"] = min(1.0, confusion_count * 0.2)
        
        # Check for frustration indicators
        frustration_indicators = ["frustrated", "annoyed", "difficult", "hard", "struggling"]
        frustration_count = sum(1 for indicator in frustration_indicators if indicator in user_input_lower)
        interaction_data["frustration_indicators"] = min(1.0, frustration_count * 0.2)
        
        # Check for mastery indicators
        mastery_indicators = ["understand", "got it", "clear", "makes sense", "I can"]
        mastery_count = sum(1 for indicator in mastery_indicators if indicator in user_input_lower)
        
        # Estimate mastery score (simplified)
        if mastery_count > 0:
            interaction_data["mastery_indicators"] = {
                "conceptual_understanding": min(1.0, mastery_count * 0.1),
                "pattern_fluency": min(1.0, mastery_count * 0.1),
                "force_handling": min(1.0, mastery_count * 0.1)
            }
        
        # Set default values
        interaction_data.setdefault("confusion_indicators", 0.0)
        interaction_data.setdefault("frustration_indicators", 0.0)
        interaction_data.setdefault("mastery_indicators", {
            "conceptual_understanding": 0.0,
            "pattern_fluency": 0.0,
            "force_handling": 0.0
        })
        
        return interaction_data
    
    def _generate_response(self, learner_state: LearnerState, current_pattern: Pattern, 
                          evolution_decision: EvolutionDecision, user_input: str) -> LearningResponse:
        """Generate an appropriate response based on the current state and evolution decision."""
        
        if evolution_decision.should_evolve:
            # Suggest evolution
            target_pattern = self.pattern_db.get_pattern(evolution_decision.target_pattern)
            return LearningResponse(
                message=f"Great progress! You've mastered the concept of '{current_pattern.name}'. "
                       f"Would you like to explore how this evolves into '{target_pattern.name}' "
                       f"when we introduce the force of '{evolution_decision.triggering_force}'?",
                pattern_context=current_pattern.core_concept.simple_definition,
                force_context=f"Ready to introduce: {evolution_decision.triggering_force}",
                next_action="evolve",
                confidence=evolution_decision.confidence,
                reasoning=evolution_decision.reasoning
            )
        
        elif evolution_decision.evolution_type == "intervention":
            # Provide intervention
            return LearningResponse(
                message=f"I notice you might be having some difficulty with '{current_pattern.name}'. "
                       f"Let me help clarify this concept: {current_pattern.core_concept.simple_definition}. "
                       f"Can you tell me what specific part is unclear?",
                pattern_context=current_pattern.core_concept.simple_definition,
                force_context=None,
                next_action="intervene",
                confidence=0.0,
                reasoning=evolution_decision.reasoning
            )
        
        else:
            # Continue with current pattern
            return LearningResponse(
                message=f"You're working with the concept of '{current_pattern.name}': "
                       f"{current_pattern.core_concept.simple_definition}. "
                       f"Keep exploring this pattern - you're making good progress!",
                pattern_context=current_pattern.core_concept.simple_definition,
                force_context=None,
                next_action="continue",
                confidence=evolution_decision.confidence,
                reasoning=evolution_decision.reasoning
            )
    
    def _generate_force_response(self, current_pattern: Pattern, force: Force) -> LearningResponse:
        """Generate a response when a force is applied."""
        
        return LearningResponse(
            message=f"Now let's explore how the force of '{force.name}' affects the pattern of '{current_pattern.name}'. "
                   f"This force represents: {force.force_definition.core_pressure}. "
                   f"How do you think this might change how we use {current_pattern.name}?",
            pattern_context=current_pattern.core_concept.simple_definition,
            force_context=force.force_definition.core_pressure,
            next_action="continue",
            confidence=0.8,
            reasoning=f"Force {force.force_id} applied to pattern {current_pattern.pattern_id}"
        )
    
    def _generate_evolution_response(self, current_pattern: Pattern, target_pattern: Pattern) -> LearningResponse:
        """Generate a response when evolving to a new pattern."""
        
        return LearningResponse(
            message=f"Excellent! You've evolved from '{current_pattern.name}' to '{target_pattern.name}'. "
                   f"This new pattern represents: {target_pattern.core_concept.simple_definition}. "
                   f"Notice how it builds upon what you learned before, but now handles more complex situations.",
            pattern_context=target_pattern.core_concept.simple_definition,
            force_context="Pattern evolution completed",
            next_action="continue",
            confidence=1.0,
            reasoning=f"Evolved from {current_pattern.pattern_id} to {target_pattern.pattern_id}"
        ) 