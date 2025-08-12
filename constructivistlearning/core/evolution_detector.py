"""
Evolution Detection Engine for the constructivist learning system.
Monitors learner progress and determines readiness for pattern evolution.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .schemas import (
    Pattern, Force, LearnerState, MasterySignals, StruggleDetection, 
    EvolutionConfidence, EvolutionDetection
)
from .pattern_database import PatternDatabase


@dataclass
class MasteryAssessment:
    """Assessment of learner mastery for a specific pattern."""
    conceptual_understanding: float  # 0.0 to 1.0
    pattern_fluency: float  # 0.0 to 1.0
    force_handling: float  # 0.0 to 1.0
    overall_mastery: float  # 0.0 to 1.0
    confidence_level: float  # 0.0 to 1.0


@dataclass
class StruggleAssessment:
    """Assessment of learner struggles and intervention needs."""
    error_rate: float  # 0.0 to 1.0
    confusion_level: float  # 0.0 to 1.0
    frustration_level: float  # 0.0 to 1.0
    needs_intervention: bool
    intervention_type: str  # "pattern_review", "force_clarification", "scaffolding"


@dataclass
class EvolutionDecision:
    """Decision about whether and how to evolve a pattern."""
    should_evolve: bool
    target_pattern: Optional[str]
    triggering_force: Optional[str]
    confidence: float
    reasoning: str
    evolution_type: str  # "forward", "lateral", "backward", "parallel"


class EvolutionDetector:
    """Engine for detecting when learners are ready to evolve patterns."""
    
    def __init__(self, pattern_db: PatternDatabase):
        self.pattern_db = pattern_db
        self.mastery_thresholds = {
            "conceptual_understanding": 0.8,
            "pattern_fluency": 0.7,
            "force_handling": 0.6
        }
        self.struggle_thresholds = {
            "error_rate": 0.3,
            "confusion_level": 0.4,
            "frustration_level": 0.5
        }
    
    def assess_mastery(self, learner_state: LearnerState, pattern: Pattern) -> MasteryAssessment:
        """Assess learner mastery of a specific pattern."""
        
        # Get current readiness indicators
        readiness = learner_state.readiness_indicators
        
        # Calculate mastery scores
        conceptual = readiness.get("conceptual_understanding", 0.0)
        fluency = readiness.get("pattern_fluency", 0.0)
        force_handling = readiness.get("force_handling", 0.0)
        
        # Calculate overall mastery (weighted average)
        overall = (conceptual * 0.4 + fluency * 0.4 + force_handling * 0.2)
        
        # Calculate confidence level based on consistency
        confidence = self._calculate_confidence(learner_state, pattern)
        
        return MasteryAssessment(
            conceptual_understanding=conceptual,
            pattern_fluency=fluency,
            force_handling=force_handling,
            overall_mastery=overall,
            confidence_level=confidence
        )
    
    def assess_struggles(self, learner_state: LearnerState, pattern: Pattern) -> StruggleAssessment:
        """Assess learner struggles and determine intervention needs."""
        
        session_data = learner_state.session_data
        
        # Calculate struggle metrics
        error_rate = session_data.get("error_rate", 0.0)
        confusion_level = session_data.get("confusion_level", 0.0)
        frustration_level = session_data.get("frustration_level", 0.0)
        
        # Determine if intervention is needed
        needs_intervention = (
            error_rate > self.struggle_thresholds["error_rate"] or
            confusion_level > self.struggle_thresholds["confusion_level"] or
            frustration_level > self.struggle_thresholds["frustration_level"]
        )
        
        # Determine intervention type
        intervention_type = self._determine_intervention_type(
            error_rate, confusion_level, frustration_level
        )
        
        return StruggleAssessment(
            error_rate=error_rate,
            confusion_level=confusion_level,
            frustration_level=frustration_level,
            needs_intervention=needs_intervention,
            intervention_type=intervention_type
        )
    
    def decide_evolution(self, learner_state: LearnerState, pattern: Pattern) -> EvolutionDecision:
        """Decide whether and how to evolve the learner's pattern."""
        
        # Assess current state
        mastery = self.assess_mastery(learner_state, pattern)
        struggles = self.assess_struggles(learner_state, pattern)
        
        # Check if intervention is needed first
        if struggles.needs_intervention:
            return EvolutionDecision(
                should_evolve=False,
                target_pattern=None,
                triggering_force=None,
                confidence=0.0,
                reasoning=f"Intervention needed: {struggles.intervention_type}",
                evolution_type="intervention"
            )
        
        # Check if mastery thresholds are met
        mastery_ready = (
            mastery.conceptual_understanding >= self.mastery_thresholds["conceptual_understanding"] and
            mastery.pattern_fluency >= self.mastery_thresholds["pattern_fluency"] and
            mastery.force_handling >= self.mastery_thresholds["force_handling"]
        )
        
        if not mastery_ready:
            return EvolutionDecision(
                should_evolve=False,
                target_pattern=None,
                triggering_force=None,
                confidence=mastery.confidence_level,
                reasoning="Mastery thresholds not met",
                evolution_type="wait"
            )
        
        # Determine evolution path
        evolution_path = self._determine_evolution_path(learner_state, pattern, mastery)
        
        return evolution_path
    
    def _calculate_confidence(self, learner_state: LearnerState, pattern: Pattern) -> float:
        """Calculate confidence level based on learner consistency and history."""
        
        # Get recent performance data
        session_data = learner_state.session_data
        recent_sessions = session_data.get("recent_sessions", [])
        
        if not recent_sessions:
            return 0.5  # Default confidence for new learners
        
        # Calculate consistency across recent sessions
        mastery_scores = [session.get("mastery_score", 0.0) for session in recent_sessions[-5:]]
        
        if len(mastery_scores) < 3:
            return 0.5
        
        # Calculate variance (lower variance = higher confidence)
        mean_score = sum(mastery_scores) / len(mastery_scores)
        variance = sum((score - mean_score) ** 2 for score in mastery_scores) / len(mastery_scores)
        
        # Convert variance to confidence (0-1 scale)
        confidence = max(0.0, min(1.0, 1.0 - variance))
        
        # Boost confidence if consistently high performance
        if mean_score > 0.8:
            confidence = min(1.0, confidence + 0.2)
        
        return confidence
    
    def _determine_intervention_type(self, error_rate: float, confusion: float, frustration: float) -> str:
        """Determine the type of intervention needed."""
        
        if error_rate > 0.5:
            return "pattern_review"
        elif confusion > 0.6:
            return "force_clarification"
        elif frustration > 0.7:
            return "scaffolding"
        else:
            return "general_support"
    
    def _determine_evolution_path(self, learner_state: LearnerState, pattern: Pattern, mastery: MasteryAssessment) -> EvolutionDecision:
        """Determine the best evolution path for the learner."""
        
        # Get compatible forces for current pattern
        compatible_forces = self.pattern_db.get_compatible_forces(pattern.pattern_id)
        
        if not compatible_forces:
            return EvolutionDecision(
                should_evolve=False,
                target_pattern=None,
                triggering_force=None,
                confidence=mastery.confidence_level,
                reasoning="No compatible forces available",
                evolution_type="wait"
            )
        
        # Select the best force based on learner characteristics
        best_force = self._select_best_force(learner_state, compatible_forces, pattern)
        
        if not best_force:
            return EvolutionDecision(
                should_evolve=False,
                target_pattern=None,
                triggering_force=None,
                confidence=mastery.confidence_level,
                reasoning="No suitable force found",
                evolution_type="wait"
            )
        
        # Get target pattern
        target_pattern_id = pattern.forces.force_evolution_map.get(best_force.force_id)
        
        if not target_pattern_id:
            return EvolutionDecision(
                should_evolve=False,
                target_pattern=None,
                triggering_force=None,
                confidence=mastery.confidence_level,
                reasoning="No evolution path found for selected force",
                evolution_type="wait"
            )
        
        # Determine evolution type
        evolution_type = self._determine_evolution_type(pattern, target_pattern_id)
        
        return EvolutionDecision(
            should_evolve=True,
            target_pattern=target_pattern_id,
            triggering_force=best_force.force_id,
            confidence=mastery.confidence_level,
            reasoning=f"Ready to evolve to {target_pattern_id} via {best_force.name}",
            evolution_type=evolution_type
        )
    
    def _select_best_force(self, learner_state: LearnerState, forces: List[Force], pattern: Pattern) -> Optional[Force]:
        """Select the best force to apply based on learner characteristics."""
        
        if not forces:
            return None
        
        # Get learner preferences
        preferences = learner_state.learning_preferences
        preferred_difficulty = preferences.get("preferred_difficulty", "medium")
        learning_style = preferences.get("learning_style", "balanced")
        
        # Score each force based on learner characteristics
        force_scores = []
        
        for force in forces:
            score = 0.0
            
            # Prefer forces that match learning style
            if learning_style == "practical" and force.category.value in ["requirement", "constraint"]:
                score += 0.3
            elif learning_style == "conceptual" and force.category.value in ["context", "pressure"]:
                score += 0.3
            
            # Prefer forces that match difficulty preference
            if preferred_difficulty == "easy" and force.intensity <= 2:
                score += 0.2
            elif preferred_difficulty == "medium" and 2 <= force.intensity <= 4:
                score += 0.2
            elif preferred_difficulty == "hard" and force.intensity >= 4:
                score += 0.2
            
            # Prefer forces that haven't been used recently
            recent_forces = learner_state.force_exposure.get(pattern.pattern_id, [])
            if force.force_id not in recent_forces[-3:]:  # Last 3 forces
                score += 0.2
            
            # Prefer domain-agnostic forces for broader learning
            if force.domain_agnostic:
                score += 0.1
            
            force_scores.append((force, score))
        
        # Return the force with the highest score
        if force_scores:
            return max(force_scores, key=lambda x: x[1])[0]
        
        return None
    
    def _determine_evolution_type(self, current_pattern: Pattern, target_pattern_id: str) -> str:
        """Determine the type of evolution based on pattern relationship."""
        
        # Check if it's a forward evolution (next in sequence)
        if target_pattern_id in current_pattern.evolution_paths:
            return "forward"
        
        # Check if it's a lateral evolution (alternative path)
        target_pattern = self.pattern_db.get_pattern(target_pattern_id)
        if target_pattern and current_pattern.complexity_level == target_pattern.complexity_level:
            return "lateral"
        
        # Check if it's a backward evolution (returning to previous)
        if target_pattern and target_pattern.complexity_level < current_pattern.complexity_level:
            return "backward"
        
        # Check if it's a parallel evolution (multiple patterns)
        if target_pattern and target_pattern.complexity_level > current_pattern.complexity_level:
            return "parallel"
        
        return "forward"  # Default
    
    def update_learner_state(self, learner_state: LearnerState, interaction_data: Dict) -> LearnerState:
        """Update learner state based on recent interaction data."""
        
        # Update session data
        session_data = learner_state.session_data.copy()
        
        # Update error rate
        if "errors" in interaction_data and "total_attempts" in interaction_data:
            session_data["error_rate"] = interaction_data["errors"] / interaction_data["total_attempts"]
        
        # Update confusion level
        if "confusion_indicators" in interaction_data:
            session_data["confusion_level"] = interaction_data["confusion_indicators"]
        
        # Update frustration level
        if "frustration_indicators" in interaction_data:
            session_data["frustration_level"] = interaction_data["frustration_indicators"]
        
        # Update recent sessions
        recent_sessions = session_data.get("recent_sessions", [])
        recent_sessions.append(interaction_data)
        if len(recent_sessions) > 10:  # Keep last 10 sessions
            recent_sessions = recent_sessions[-10:]
        session_data["recent_sessions"] = recent_sessions
        
        # Update readiness indicators
        readiness = learner_state.readiness_indicators.copy()
        if "mastery_indicators" in interaction_data:
            readiness.update(interaction_data["mastery_indicators"])
        
        # Create updated learner state
        updated_state = LearnerState(
            learner_id=learner_state.learner_id,
            current_pattern=learner_state.current_pattern,
            pattern_history=learner_state.pattern_history,
            force_exposure=learner_state.force_exposure,
            readiness_indicators=readiness,
            learning_preferences=learner_state.learning_preferences,
            session_data=session_data
        )
        
        return updated_state 