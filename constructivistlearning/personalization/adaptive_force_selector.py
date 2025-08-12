"""
Adaptive Force Selector for the Constructivist Learning System.

This module provides intelligent force selection based on learner profiles,
current context, and learning objectives.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..core.schemas import Pattern, Force, LearnerState
from ..core.pattern_database import PatternDatabase
from .learner_profiler import LearnerProfile, LearningStyle, DifficultyPreference


@dataclass
class ForceSelectionContext:
    """Context for force selection decisions."""
    current_pattern: Pattern
    learner_profile: LearnerProfile
    available_forces: List[Force]
    recent_forces: List[str]
    learning_objectives: List[str]
    session_context: Dict
    time_constraints: Optional[float] = None


@dataclass
class ForceSelectionResult:
    """Result of force selection process."""
    selected_force: Force
    confidence: float
    reasoning: str
    expected_impact: Dict[str, float]
    alternative_forces: List[Force]
    selection_factors: Dict[str, float]


class AdaptiveForceSelector:
    """Intelligent force selection based on learner characteristics and context."""
    
    def __init__(self, pattern_db: PatternDatabase):
        self.pattern_db = pattern_db
        
        # Selection criteria weights
        self.criteria_weights = {
            "learner_preference": 0.25,
            "cognitive_fit": 0.20,
            "behavioral_fit": 0.15,
            "performance_optimization": 0.20,
            "engagement_enhancement": 0.10,
            "contextual_relevance": 0.10
        }
        
        # Force category preferences by learning style
        self.style_force_preferences = {
            LearningStyle.VISUAL: ["context", "requirement"],
            LearningStyle.AUDITORY: ["pressure", "context"],
            LearningStyle.KINESTHETIC: ["constraint", "edge_case"],
            LearningStyle.READING_WRITING: ["requirement", "pressure"],
            LearningStyle.BALANCED: ["requirement", "context", "pressure"]
        }
        
        # Force intensity preferences by difficulty preference
        self.difficulty_intensity_preferences = {
            DifficultyPreference.EASY: (1, 2),
            DifficultyPreference.MEDIUM: (2, 4),
            DifficultyPreference.HARD: (3, 5),
            DifficultyPreference.ADAPTIVE: (1, 5)
        }
    
    def select_optimal_force(self, context: ForceSelectionContext) -> ForceSelectionResult:
        """
        Select the optimal force based on learner profile and context.
        
        Args:
            context: Selection context including learner profile and available forces
            
        Returns:
            Force selection result with reasoning and alternatives
        """
        
        if not context.available_forces:
            raise ValueError("No forces available for selection")
        
        # Score each force based on multiple criteria
        force_scores = []
        
        for force in context.available_forces:
            score = self._calculate_force_score(force, context)
            force_scores.append((force, score))
        
        # Sort by score (highest first)
        force_scores.sort(key=lambda x: x[1]["total_score"], reverse=True)
        
        # Select the best force
        best_force, best_score = force_scores[0]
        
        # Get alternatives (next 2 best options)
        alternatives = [force for force, _ in force_scores[1:3]]
        
        # Calculate expected impact
        expected_impact = self._calculate_expected_impact(best_force, context)
        
        return ForceSelectionResult(
            selected_force=best_force,
            confidence=best_score["total_score"],
            reasoning=self._generate_selection_reasoning(best_force, best_score, context),
            expected_impact=expected_impact,
            alternative_forces=alternatives,
            selection_factors=best_score
        )
    
    def _calculate_force_score(self, force: Force, context: ForceSelectionContext) -> Dict[str, float]:
        """Calculate comprehensive score for a force based on multiple criteria."""
        
        profile = context.learner_profile
        
        scores = {
            "learner_preference": self._score_learner_preference(force, profile),
            "cognitive_fit": self._score_cognitive_fit(force, profile),
            "behavioral_fit": self._score_behavioral_fit(force, profile),
            "performance_optimization": self._score_performance_optimization(force, profile),
            "engagement_enhancement": self._score_engagement_enhancement(force, profile),
            "contextual_relevance": self._score_contextual_relevance(force, context)
        }
        
        # Calculate weighted total score
        total_score = sum(
            scores[criterion] * self.criteria_weights[criterion]
            for criterion in scores
        )
        
        scores["total_score"] = total_score
        return scores
    
    def _score_learner_preference(self, force: Force, profile: LearnerProfile) -> float:
        """Score force based on learner preferences."""
        
        score = 0.0
        
        # Learning style preference
        style_preferences = self.style_force_preferences.get(profile.preferences.learning_style, [])
        if force.category.value in style_preferences:
            score += 0.4
        
        # Difficulty preference
        intensity_range = self.difficulty_intensity_preferences.get(
            profile.preferences.difficulty_preference, (2, 4)
        )
        if intensity_range[0] <= force.intensity <= intensity_range[1]:
            score += 0.3
        
        # Domain preference
        if profile.preferences.preferred_domains and force.domain_agnostic:
            score += 0.2
        
        # Context preference
        if profile.preferences.preferred_contexts and "real-world" in profile.preferences.preferred_contexts:
            if any("real" in example.lower() for example in force.force_definition.universal_examples):
                score += 0.1
        
        return min(1.0, score)
    
    def _score_cognitive_fit(self, force: Force, profile: LearnerProfile) -> float:
        """Score force based on cognitive profile fit."""
        
        score = 0.0
        
        # Working memory capacity
        if force.evolution_outcomes.complexity_increase <= 2:
            if profile.cognitive.working_memory_capacity >= 0.5:
                score += 0.2
        else:
            if profile.cognitive.working_memory_capacity >= 0.7:
                score += 0.2
        
        # Processing speed
        if force.intensity <= 3:
            if profile.cognitive.processing_speed >= 0.4:
                score += 0.2
        else:
            if profile.cognitive.processing_speed >= 0.6:
                score += 0.2
        
        # Pattern recognition
        if profile.cognitive.pattern_recognition >= 0.6:
            score += 0.2
        
        # Abstract thinking
        if profile.cognitive.abstract_thinking >= 0.5:
            score += 0.2
        
        # Metacognitive awareness
        if profile.cognitive.metacognitive_awareness >= 0.5:
            score += 0.2
        
        return min(1.0, score)
    
    def _score_behavioral_fit(self, force: Force, profile: LearnerProfile) -> float:
        """Score force based on behavioral profile fit."""
        
        score = 0.0
        
        # Risk tolerance
        if force.category.value in ["pressure", "edge_case"]:
            if profile.behavioral.risk_tolerance >= 0.6:
                score += 0.3
        else:
            if profile.behavioral.risk_tolerance <= 0.4:
                score += 0.3
        
        # Error handling
        if profile.behavioral.error_handling == "adaptive":
            score += 0.2
        elif profile.behavioral.error_handling == "experimental":
            if force.category.value in ["edge_case", "pressure"]:
                score += 0.2
        
        # Exploration tendency
        if profile.behavioral.exploration_tendency >= 0.6:
            if force.category.value in ["context", "pressure"]:
                score += 0.2
        
        # Help seeking behavior
        if profile.behavioral.help_seeking_behavior == "independent":
            if force.intensity <= 3:
                score += 0.2
        elif profile.behavioral.help_seeking_behavior == "dependent":
            if force.intensity <= 2:
                score += 0.2
        
        # Persistence level
        if profile.behavioral.persistence_level >= 0.6:
            score += 0.1
        
        return min(1.0, score)
    
    def _score_performance_optimization(self, force: Force, profile: LearnerProfile) -> float:
        """Score force based on performance optimization potential."""
        
        score = 0.0
        
        # Mastery rate optimization
        if profile.performance.mastery_rate < 0.3:
            # Struggling learner - prefer simpler forces
            if force.intensity <= 2:
                score += 0.3
        elif profile.performance.mastery_rate > 0.7:
            # High performer - can handle more complex forces
            if force.intensity >= 3:
                score += 0.3
        
        # Error pattern avoidance
        error_patterns = profile.performance.error_patterns
        if error_patterns:
            # Avoid forces that might trigger common errors
            if not any(error_type in force.name.lower() for error_type in error_patterns.keys()):
                score += 0.2
        
        # Success pattern reinforcement
        success_patterns = profile.performance.success_patterns
        if success_patterns:
            # Prefer forces that align with successful patterns
            if any(success_type in force.name.lower() for success_type in success_patterns.keys()):
                score += 0.2
        
        # Transfer ability consideration
        if profile.performance.transfer_ability >= 0.6:
            if force.domain_agnostic:
                score += 0.2
        
        # Retention rate consideration
        if profile.performance.retention_rate >= 0.6:
            score += 0.1
        
        return min(1.0, score)
    
    def _score_engagement_enhancement(self, force: Force, profile: LearnerProfile) -> float:
        """Score force based on engagement enhancement potential."""
        
        score = 0.0
        
        # Intrinsic motivation
        if profile.engagement.intrinsic_motivation < 0.4:
            # Low motivation - prefer engaging forces
            if force.category.value in ["context", "pressure"]:
                score += 0.3
        else:
            # High motivation - can handle any force type
            score += 0.2
        
        # Interest areas
        if profile.engagement.interest_areas:
            # Prefer forces that relate to interest areas
            if any(interest in force.name.lower() for interest in profile.engagement.interest_areas):
                score += 0.2
        
        # Frustration tolerance
        if profile.engagement.frustration_tolerance < 0.4:
            # Low tolerance - prefer gentler forces
            if force.intensity <= 2:
                score += 0.2
        else:
            # High tolerance - can handle challenging forces
            if force.intensity >= 3:
                score += 0.2
        
        # Boredom threshold
        if profile.engagement.boredom_threshold < 0.4:
            # Low boredom threshold - prefer stimulating forces
            if force.intensity >= 3:
                score += 0.2
        else:
            # High boredom threshold - can handle any force
            score += 0.1
        
        # Challenge preference
        if profile.engagement.challenge_preference == "difficult":
            if force.intensity >= 4:
                score += 0.2
        elif profile.engagement.challenge_preference == "easy":
            if force.intensity <= 2:
                score += 0.2
        else:  # optimal
            if 2 <= force.intensity <= 4:
                score += 0.2
        
        return min(1.0, score)
    
    def _score_contextual_relevance(self, force: Force, context: ForceSelectionContext) -> float:
        """Score force based on contextual relevance."""
        
        score = 0.0
        
        # Recent force avoidance
        if force.force_id not in context.recent_forces:
            score += 0.3
        
        # Learning objective alignment
        if context.learning_objectives:
            objective_keywords = [obj.lower() for obj in context.learning_objectives]
            if any(keyword in force.name.lower() or keyword in force.description.lower() 
                   for keyword in objective_keywords):
                score += 0.3
        
        # Session context relevance
        session_context = context.session_context
        if session_context.get("struggling", False):
            # Learner is struggling - prefer supportive forces
            if force.category.value in ["requirement", "constraint"]:
                score += 0.2
        elif session_context.get("bored", False):
            # Learner is bored - prefer stimulating forces
            if force.category.value in ["pressure", "edge_case"]:
                score += 0.2
        
        # Time constraints
        if context.time_constraints and context.time_constraints < 300:  # Less than 5 minutes
            # Short time - prefer simpler forces
            if force.intensity <= 2:
                score += 0.2
        
        return min(1.0, score)
    
    def _calculate_expected_impact(self, force: Force, context: ForceSelectionContext) -> Dict[str, float]:
        """Calculate expected impact of applying the force."""
        
        profile = context.learner_profile
        
        impact = {
            "mastery_increase": 0.0,
            "engagement_change": 0.0,
            "complexity_increase": force.evolution_outcomes.complexity_increase / 3.0,
            "motivation_boost": 0.0,
            "confidence_change": 0.0
        }
        
        # Expected mastery increase
        base_mastery_gain = 0.1
        if profile.performance.mastery_rate < 0.3:
            base_mastery_gain *= 0.5  # Struggling learners gain less
        elif profile.performance.mastery_rate > 0.7:
            base_mastery_gain *= 1.5  # High performers gain more
        
        impact["mastery_increase"] = base_mastery_gain
        
        # Expected engagement change
        if profile.engagement.intrinsic_motivation < 0.4:
            if force.category.value in ["context", "pressure"]:
                impact["engagement_change"] = 0.2
        else:
            impact["engagement_change"] = 0.1
        
        # Expected motivation boost
        if force.category.value in profile.engagement.interest_areas:
            impact["motivation_boost"] = 0.2
        
        # Expected confidence change
        if profile.performance.mastery_rate > 0.6:
            impact["confidence_change"] = 0.1
        elif profile.performance.mastery_rate < 0.3:
            impact["confidence_change"] = -0.1
        
        return impact
    
    def _generate_selection_reasoning(self, force: Force, score: Dict[str, float], 
                                    context: ForceSelectionContext) -> str:
        """Generate human-readable reasoning for force selection."""
        
        profile = context.learner_profile
        reasoning_parts = []
        
        # Top scoring factors
        sorted_factors = sorted(score.items(), key=lambda x: x[1], reverse=True)
        top_factors = [factor for factor, score_val in sorted_factors[:3] if score_val > 0.5]
        
        if "learner_preference" in top_factors:
            reasoning_parts.append(f"matches your {profile.preferences.learning_style.value} learning style")
        
        if "cognitive_fit" in top_factors:
            reasoning_parts.append("aligns well with your cognitive strengths")
        
        if "performance_optimization" in top_factors:
            reasoning_parts.append("builds on your successful learning patterns")
        
        if "engagement_enhancement" in top_factors:
            reasoning_parts.append("should keep you engaged and motivated")
        
        if "contextual_relevance" in top_factors:
            reasoning_parts.append("fits well with your current learning context")
        
        if not reasoning_parts:
            reasoning_parts.append("provides a good balance of challenge and support")
        
        return f"Selected {force.name} because it {', '.join(reasoning_parts)}."
    
    def get_force_sequence_recommendation(self, context: ForceSelectionContext, 
                                        sequence_length: int = 3) -> List[Force]:
        """Recommend a sequence of forces for optimal learning progression."""
        
        if not context.available_forces:
            return []
        
        sequence = []
        remaining_forces = context.available_forces.copy()
        current_context = context
        
        for i in range(sequence_length):
            if not remaining_forces:
                break
            
            # Update context with current sequence
            current_context.available_forces = remaining_forces
            current_context.recent_forces = [f.force_id for f in sequence]
            
            # Select next force
            result = self.select_optimal_force(current_context)
            selected_force = result.selected_force
            
            sequence.append(selected_force)
            remaining_forces.remove(selected_force)
            
            # Update context for next iteration
            current_context = ForceSelectionContext(
                current_pattern=context.current_pattern,
                learner_profile=context.learner_profile,
                available_forces=remaining_forces,
                recent_forces=current_context.recent_forces,
                learning_objectives=context.learning_objectives,
                session_context=context.session_context,
                time_constraints=context.time_constraints
            )
        
        return sequence
    
    def get_adaptive_recommendations(self, context: ForceSelectionContext) -> Dict:
        """Get adaptive recommendations for force application."""
        
        profile = context.learner_profile
        
        recommendations = {
            "force_intensity": "medium",
            "application_pacing": "gradual",
            "scaffolding_level": "medium",
            "feedback_frequency": "moderate",
            "practice_opportunities": "standard"
        }
        
        # Adjust based on cognitive profile
        if profile.cognitive.working_memory_capacity < 0.4:
            recommendations["force_intensity"] = "low"
            recommendations["application_pacing"] = "very_gradual"
            recommendations["scaffolding_level"] = "high"
        elif profile.cognitive.working_memory_capacity > 0.7:
            recommendations["force_intensity"] = "high"
            recommendations["application_pacing"] = "rapid"
            recommendations["scaffolding_level"] = "low"
        
        # Adjust based on performance
        if profile.performance.mastery_rate < 0.3:
            recommendations["force_intensity"] = "low"
            recommendations["feedback_frequency"] = "high"
            recommendations["practice_opportunities"] = "frequent"
        elif profile.performance.mastery_rate > 0.7:
            recommendations["force_intensity"] = "high"
            recommendations["feedback_frequency"] = "low"
            recommendations["practice_opportunities"] = "minimal"
        
        # Adjust based on engagement
        if profile.engagement.intrinsic_motivation < 0.4:
            recommendations["feedback_frequency"] = "high"
            recommendations["practice_opportunities"] = "engaging"
        
        return recommendations 