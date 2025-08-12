"""
Learner Profiling System for the Constructivist Learning System.

This module provides comprehensive learner profiling capabilities to enable
personalized adaptation of the learning experience.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from ..core.schemas import LearnerState, Pattern, Force


class LearningStyle(Enum):
    """Learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    BALANCED = "balanced"


class DifficultyPreference(Enum):
    """Difficulty level preferences."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADAPTIVE = "adaptive"


class EngagementLevel(Enum):
    """Learner engagement levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VARIABLE = "variable"


@dataclass
class LearningPreferences:
    """Comprehensive learning preferences profile."""
    learning_style: LearningStyle = LearningStyle.BALANCED
    difficulty_preference: DifficultyPreference = DifficultyPreference.MEDIUM
    preferred_domains: List[str] = field(default_factory=list)
    preferred_contexts: List[str] = field(default_factory=list)  # real-world, abstract, etc.
    interaction_frequency: str = "medium"  # low, medium, high
    feedback_preference: str = "immediate"  # immediate, delayed, minimal
    collaboration_preference: str = "individual"  # individual, collaborative, mixed


@dataclass
class CognitiveProfile:
    """Cognitive characteristics and capabilities."""
    working_memory_capacity: float = 0.5  # 0.0 to 1.0
    processing_speed: float = 0.5  # 0.0 to 1.0
    attention_span: float = 0.5  # 0.0 to 1.0
    pattern_recognition: float = 0.5  # 0.0 to 1.0
    abstract_thinking: float = 0.5  # 0.0 to 1.0
    metacognitive_awareness: float = 0.5  # 0.0 to 1.0


@dataclass
class BehavioralProfile:
    """Behavioral patterns and tendencies."""
    persistence_level: float = 0.5  # 0.0 to 1.0
    risk_tolerance: float = 0.5  # 0.0 to 1.0
    error_handling: str = "adaptive"  # avoidant, adaptive, experimental
    exploration_tendency: float = 0.5  # 0.0 to 1.0
    reflection_frequency: float = 0.5  # 0.0 to 1.0
    help_seeking_behavior: str = "balanced"  # independent, dependent, balanced


@dataclass
class PerformanceProfile:
    """Performance characteristics and patterns."""
    mastery_rate: float = 0.5  # 0.0 to 1.0
    retention_rate: float = 0.5  # 0.0 to 1.0
    transfer_ability: float = 0.5  # 0.0 to 1.0
    error_patterns: Dict[str, float] = field(default_factory=dict)
    success_patterns: Dict[str, float] = field(default_factory=dict)
    learning_curve: List[Tuple[float, float]] = field(default_factory=list)  # (time, mastery)


@dataclass
class EngagementProfile:
    """Engagement and motivation characteristics."""
    intrinsic_motivation: float = 0.5  # 0.0 to 1.0
    extrinsic_motivation: float = 0.5  # 0.0 to 1.0
    interest_areas: List[str] = field(default_factory=list)
    frustration_tolerance: float = 0.5  # 0.0 to 1.0
    boredom_threshold: float = 0.5  # 0.0 to 1.0
    challenge_preference: str = "optimal"  # easy, optimal, difficult


@dataclass
class LearnerProfile:
    """Comprehensive learner profile combining all aspects."""
    learner_id: str
    preferences: LearningPreferences
    cognitive: CognitiveProfile
    behavioral: BehavioralProfile
    performance: PerformanceProfile
    engagement: EngagementProfile
    profile_version: str = "1.0"
    last_updated: float = field(default_factory=time.time)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class LearnerProfiler:
    """System for analyzing and updating learner profiles."""
    
    def __init__(self):
        self.profiles: Dict[str, LearnerProfile] = {}
        self.analysis_weights = {
            "interaction_analysis": 0.3,
            "performance_analysis": 0.3,
            "behavioral_analysis": 0.2,
            "engagement_analysis": 0.2
        }
    
    def create_initial_profile(self, learner_id: str, domain: str = "general") -> LearnerProfile:
        """Create an initial learner profile with default values."""
        
        profile = LearnerProfile(
            learner_id=learner_id,
            preferences=LearningPreferences(
                preferred_domains=[domain],
                preferred_contexts=["real-world", "practical"]
            ),
            cognitive=CognitiveProfile(),
            behavioral=BehavioralProfile(),
            performance=PerformanceProfile(),
            engagement=EngagementProfile(
                interest_areas=[domain]
            )
        )
        
        self.profiles[learner_id] = profile
        return profile
    
    def update_profile_from_interaction(self, learner_id: str, interaction_data: Dict) -> LearnerProfile:
        """Update learner profile based on interaction data."""
        
        profile = self.profiles.get(learner_id)
        if not profile:
            profile = self.create_initial_profile(learner_id)
        
        # Update based on interaction type and content
        self._update_preferences_from_interaction(profile, interaction_data)
        self._update_cognitive_from_interaction(profile, interaction_data)
        self._update_behavioral_from_interaction(profile, interaction_data)
        self._update_engagement_from_interaction(profile, interaction_data)
        
        # Update timestamp and confidence
        profile.last_updated = time.time()
        self._update_confidence_scores(profile, interaction_data)
        
        return profile
    
    def update_profile_from_performance(self, learner_id: str, performance_data: Dict) -> LearnerProfile:
        """Update learner profile based on performance data."""
        
        profile = self.profiles.get(learner_id)
        if not profile:
            profile = self.create_initial_profile(learner_id)
        
        # Update performance characteristics
        self._update_performance_profile(profile, performance_data)
        
        # Update cognitive profile based on performance patterns
        self._update_cognitive_from_performance(profile, performance_data)
        
        # Update behavioral profile based on performance
        self._update_behavioral_from_performance(profile, performance_data)
        
        profile.last_updated = time.time()
        return profile
    
    def get_personalization_recommendations(self, learner_id: str, context: Dict) -> Dict:
        """Get personalized recommendations for the current learning context."""
        
        profile = self.profiles.get(learner_id)
        if not profile:
            return self._get_default_recommendations()
        
        recommendations = {
            "force_selection": self._recommend_forces(profile, context),
            "pattern_pacing": self._recommend_pacing(profile, context),
            "scaffolding_level": self._recommend_scaffolding(profile, context),
            "interaction_style": self._recommend_interaction_style(profile, context),
            "content_adaptation": self._recommend_content_adaptation(profile, context),
            "motivation_strategies": self._recommend_motivation_strategies(profile, context)
        }
        
        return recommendations
    
    def _update_preferences_from_interaction(self, profile: LearnerProfile, interaction_data: Dict):
        """Update learning preferences based on interaction data."""
        
        # Analyze interaction patterns
        interaction_text = interaction_data.get("input", "").lower()
        
        # Detect learning style preferences
        visual_indicators = ["see", "visual", "picture", "diagram", "show me"]
        auditory_indicators = ["hear", "tell me", "explain", "discuss"]
        kinesthetic_indicators = ["try", "practice", "hands-on", "do it myself"]
        
        visual_score = sum(1 for indicator in visual_indicators if indicator in interaction_text)
        auditory_score = sum(1 for indicator in auditory_indicators if indicator in interaction_text)
        kinesthetic_score = sum(1 for indicator in kinesthetic_indicators if indicator in interaction_text)
        
        # Update learning style preference
        if visual_score > auditory_score and visual_score > kinesthetic_score:
            profile.preferences.learning_style = LearningStyle.VISUAL
        elif auditory_score > visual_score and auditory_score > kinesthetic_score:
            profile.preferences.learning_style = LearningStyle.AUDITORY
        elif kinesthetic_score > visual_score and kinesthetic_score > auditory_score:
            profile.preferences.learning_style = LearningStyle.KINESTHETIC
        
        # Detect difficulty preference
        if "easy" in interaction_text or "simple" in interaction_text:
            profile.preferences.difficulty_preference = DifficultyPreference.EASY
        elif "challenging" in interaction_text or "hard" in interaction_text:
            profile.preferences.difficulty_preference = DifficultyPreference.HARD
        
        # Detect context preferences
        if any(word in interaction_text for word in ["real", "practical", "use", "apply"]):
            if "real-world" not in profile.preferences.preferred_contexts:
                profile.preferences.preferred_contexts.append("real-world")
    
    def _update_cognitive_from_interaction(self, profile: LearnerProfile, interaction_data: Dict):
        """Update cognitive profile based on interaction data."""
        
        # Analyze response time and complexity
        response_time = interaction_data.get("response_time", 0)
        input_length = len(interaction_data.get("input", ""))
        
        # Update processing speed based on response time
        if response_time > 0:
            # Normalize response time (shorter = faster processing)
            normalized_speed = max(0.1, min(1.0, 10.0 / response_time))
            profile.cognitive.processing_speed = (
                profile.cognitive.processing_speed * 0.9 + normalized_speed * 0.1
            )
        
        # Update attention span based on input length and engagement
        engagement_level = interaction_data.get("engagement_level", 0.5)
        profile.cognitive.attention_span = (
            profile.cognitive.attention_span * 0.9 + engagement_level * 0.1
        )
        
        # Update pattern recognition based on interaction quality
        if interaction_data.get("pattern_recognized", False):
            profile.cognitive.pattern_recognition = min(1.0, profile.cognitive.pattern_recognition + 0.1)
    
    def _update_behavioral_from_interaction(self, profile: LearnerProfile, interaction_data: Dict):
        """Update behavioral profile based on interaction data."""
        
        # Analyze error handling behavior
        error_count = interaction_data.get("errors", 0)
        if error_count > 0:
            if error_count < 3:
                profile.behavioral.error_handling = "adaptive"
            else:
                profile.behavioral.error_handling = "avoidant"
        
        # Update persistence based on interaction frequency
        interaction_frequency = interaction_data.get("interaction_frequency", 1)
        profile.behavioral.persistence_level = min(1.0, profile.behavioral.persistence_level + interaction_frequency * 0.1)
        
        # Update exploration tendency
        if interaction_data.get("explored_new_concepts", False):
            profile.behavioral.exploration_tendency = min(1.0, profile.behavioral.exploration_tendency + 0.1)
    
    def _update_engagement_from_interaction(self, profile: LearnerProfile, interaction_data: Dict):
        """Update engagement profile based on interaction data."""
        
        # Update intrinsic motivation
        positive_indicators = ["interesting", "enjoy", "like", "want to learn"]
        negative_indicators = ["boring", "difficult", "confusing", "frustrated"]
        
        interaction_text = interaction_data.get("input", "").lower()
        positive_score = sum(1 for indicator in positive_indicators if indicator in interaction_text)
        negative_score = sum(1 for indicator in negative_indicators if indicator in interaction_text)
        
        if positive_score > negative_score:
            profile.engagement.intrinsic_motivation = min(1.0, profile.engagement.intrinsic_motivation + 0.1)
        elif negative_score > positive_score:
            profile.engagement.intrinsic_motivation = max(0.0, profile.engagement.intrinsic_motivation - 0.1)
        
        # Update frustration tolerance
        frustration_level = interaction_data.get("frustration_level", 0.0)
        profile.engagement.frustration_tolerance = max(0.0, profile.engagement.frustration_tolerance - frustration_level * 0.1)
    
    def _update_performance_profile(self, profile: LearnerProfile, performance_data: Dict):
        """Update performance profile based on performance data."""
        
        # Update mastery rate
        current_mastery = performance_data.get("mastery_level", 0.0)
        time_spent = performance_data.get("time_spent", 1.0)
        
        if time_spent > 0:
            mastery_rate = current_mastery / time_spent
            profile.performance.mastery_rate = (
                profile.performance.mastery_rate * 0.9 + mastery_rate * 0.1
            )
        
        # Update learning curve
        profile.performance.learning_curve.append((time.time(), current_mastery))
        if len(profile.performance.learning_curve) > 100:  # Keep last 100 points
            profile.performance.learning_curve = profile.performance.learning_curve[-100:]
        
        # Update error patterns
        error_type = performance_data.get("error_type")
        if error_type:
            profile.performance.error_patterns[error_type] = (
                profile.performance.error_patterns.get(error_type, 0.0) * 0.9 + 0.1
            )
        
        # Update success patterns
        success_type = performance_data.get("success_type")
        if success_type:
            profile.performance.success_patterns[success_type] = (
                profile.performance.success_patterns.get(success_type, 0.0) * 0.9 + 0.1
            )
    
    def _update_cognitive_from_performance(self, profile: LearnerProfile, performance_data: Dict):
        """Update cognitive profile based on performance data."""
        
        # Update working memory capacity based on complexity handling
        complexity_level = performance_data.get("complexity_level", 1)
        if complexity_level > 3:
            profile.cognitive.working_memory_capacity = min(1.0, profile.cognitive.working_memory_capacity + 0.1)
        
        # Update abstract thinking based on transfer performance
        transfer_score = performance_data.get("transfer_score", 0.0)
        profile.cognitive.abstract_thinking = (
            profile.cognitive.abstract_thinking * 0.9 + transfer_score * 0.1
        )
    
    def _update_behavioral_from_performance(self, profile: LearnerProfile, performance_data: Dict):
        """Update behavioral profile based on performance data."""
        
        # Update risk tolerance based on experimentation
        experiments_tried = performance_data.get("experiments_tried", 0)
        if experiments_tried > 0:
            profile.behavioral.risk_tolerance = min(1.0, profile.behavioral.risk_tolerance + experiments_tried * 0.1)
        
        # Update help seeking behavior
        help_requests = performance_data.get("help_requests", 0)
        if help_requests > 5:
            profile.behavioral.help_seeking_behavior = "dependent"
        elif help_requests < 2:
            profile.behavioral.help_seeking_behavior = "independent"
        else:
            profile.behavioral.help_seeking_behavior = "balanced"
    
    def _update_confidence_scores(self, profile: LearnerProfile, data: Dict):
        """Update confidence scores for different profile aspects."""
        
        # Calculate confidence based on data consistency and amount
        data_points = data.get("data_points", 1)
        consistency_score = data.get("consistency_score", 0.5)
        
        confidence = min(1.0, (data_points / 10.0) * consistency_score)
        
        profile.confidence_scores["overall"] = confidence
        profile.confidence_scores["preferences"] = confidence * 0.8
        profile.confidence_scores["cognitive"] = confidence * 0.7
        profile.confidence_scores["behavioral"] = confidence * 0.6
        profile.confidence_scores["performance"] = confidence * 0.9
        profile.confidence_scores["engagement"] = confidence * 0.8
    
    def _recommend_forces(self, profile: LearnerProfile, context: Dict) -> Dict:
        """Recommend forces based on learner profile."""
        
        recommendations = {
            "preferred_categories": [],
            "intensity_range": (1, 3),
            "application_timing": "gradual",
            "context_preferences": []
        }
        
        # Adjust based on cognitive profile
        if profile.cognitive.working_memory_capacity < 0.3:
            recommendations["intensity_range"] = (1, 2)
            recommendations["application_timing"] = "very_gradual"
        elif profile.cognitive.working_memory_capacity > 0.7:
            recommendations["intensity_range"] = (2, 5)
            recommendations["application_timing"] = "rapid"
        
        # Adjust based on behavioral profile
        if profile.behavioral.risk_tolerance < 0.3:
            recommendations["preferred_categories"] = ["requirement", "constraint"]
        elif profile.behavioral.risk_tolerance > 0.7:
            recommendations["preferred_categories"] = ["pressure", "edge_case"]
        
        # Adjust based on engagement
        if profile.engagement.intrinsic_motivation < 0.3:
            recommendations["context_preferences"] = ["real-world", "practical"]
        
        return recommendations
    
    def _recommend_pacing(self, profile: LearnerProfile, context: Dict) -> Dict:
        """Recommend learning pacing based on learner profile."""
        
        base_pacing = 1.0  # Normal pace
        
        # Adjust based on cognitive profile
        if profile.cognitive.processing_speed < 0.3:
            base_pacing *= 0.5  # Slower pace
        elif profile.cognitive.processing_speed > 0.7:
            base_pacing *= 1.5  # Faster pace
        
        # Adjust based on performance
        if profile.performance.mastery_rate < 0.3:
            base_pacing *= 0.7  # Slower for struggling learners
        elif profile.performance.mastery_rate > 0.7:
            base_pacing *= 1.3  # Faster for quick learners
        
        # Adjust based on engagement
        if profile.engagement.intrinsic_motivation < 0.3:
            base_pacing *= 0.8  # Slower for less motivated learners
        
        return {
            "pace_multiplier": base_pacing,
            "session_duration": max(10, min(60, 30 * base_pacing)),
            "break_frequency": max(1, min(5, 3 / base_pacing)),
            "review_frequency": max(1, min(5, 3 * base_pacing))
        }
    
    def _recommend_scaffolding(self, profile: LearnerProfile, context: Dict) -> Dict:
        """Recommend scaffolding level based on learner profile."""
        
        base_scaffolding = 0.5  # Medium scaffolding
        
        # Increase scaffolding for struggling learners
        if profile.performance.mastery_rate < 0.3:
            base_scaffolding = 0.8
        elif profile.cognitive.working_memory_capacity < 0.3:
            base_scaffolding = 0.7
        elif profile.behavioral.help_seeking_behavior == "dependent":
            base_scaffolding = 0.6
        
        # Decrease scaffolding for independent learners
        if profile.behavioral.help_seeking_behavior == "independent":
            base_scaffolding = 0.3
        elif profile.performance.mastery_rate > 0.7:
            base_scaffolding = 0.4
        
        return {
            "scaffolding_level": base_scaffolding,
            "hint_frequency": "high" if base_scaffolding > 0.6 else "medium" if base_scaffolding > 0.4 else "low",
            "step_by_step_guidance": base_scaffolding > 0.7,
            "visual_aids": profile.preferences.learning_style == LearningStyle.VISUAL,
            "practice_opportunities": "frequent" if base_scaffolding > 0.6 else "moderate"
        }
    
    def _recommend_interaction_style(self, profile: LearnerProfile, context: Dict) -> Dict:
        """Recommend interaction style based on learner profile."""
        
        return {
            "response_length": "detailed" if profile.cognitive.attention_span > 0.7 else "concise",
            "question_style": "open_ended" if profile.behavioral.exploration_tendency > 0.6 else "guided",
            "feedback_style": "immediate" if profile.preferences.feedback_preference == "immediate" else "delayed",
            "encouragement_level": "high" if profile.engagement.intrinsic_motivation < 0.4 else "moderate",
            "challenge_level": "high" if profile.engagement.challenge_preference == "difficult" else "optimal"
        }
    
    def _recommend_content_adaptation(self, profile: LearnerProfile, context: Dict) -> Dict:
        """Recommend content adaptation based on learner profile."""
        
        adaptations = {
            "examples": "real_world" if "real-world" in profile.preferences.preferred_contexts else "abstract",
            "complexity": "simple" if profile.cognitive.working_memory_capacity < 0.4 else "standard",
            "visualization": "high" if profile.preferences.learning_style == LearningStyle.VISUAL else "low",
            "interactivity": "high" if profile.preferences.learning_style == LearningStyle.KINESTHETIC else "medium",
            "domain_context": profile.preferences.preferred_domains[0] if profile.preferences.preferred_domains else "general"
        }
        
        return adaptations
    
    def _recommend_motivation_strategies(self, profile: LearnerProfile, context: Dict) -> Dict:
        """Recommend motivation strategies based on learner profile."""
        
        strategies = {
            "primary_strategy": "intrinsic" if profile.engagement.intrinsic_motivation > 0.6 else "extrinsic",
            "reward_type": "achievement" if profile.engagement.intrinsic_motivation > 0.5 else "external",
            "challenge_level": "optimal" if profile.engagement.challenge_preference == "optimal" else "easy",
            "social_elements": profile.preferences.collaboration_preference != "individual",
            "progress_visibility": "high" if profile.engagement.extrinsic_motivation > 0.5 else "low"
        }
        
        return strategies
    
    def _get_default_recommendations(self) -> Dict:
        """Get default recommendations when no profile is available."""
        
        return {
            "force_selection": {
                "preferred_categories": ["requirement", "constraint"],
                "intensity_range": (1, 3),
                "application_timing": "gradual",
                "context_preferences": ["real-world"]
            },
            "pattern_pacing": {
                "pace_multiplier": 1.0,
                "session_duration": 30,
                "break_frequency": 3,
                "review_frequency": 3
            },
            "scaffolding_level": {
                "scaffolding_level": 0.5,
                "hint_frequency": "medium",
                "step_by_step_guidance": False,
                "visual_aids": True,
                "practice_opportunities": "moderate"
            },
            "interaction_style": {
                "response_length": "concise",
                "question_style": "guided",
                "feedback_style": "immediate",
                "encouragement_level": "moderate",
                "challenge_level": "optimal"
            },
            "content_adaptation": {
                "examples": "real_world",
                "complexity": "standard",
                "visualization": "medium",
                "interactivity": "medium",
                "domain_context": "general"
            },
            "motivation_strategies": {
                "primary_strategy": "intrinsic",
                "reward_type": "achievement",
                "challenge_level": "optimal",
                "social_elements": False,
                "progress_visibility": "medium"
            }
        }
    
    def export_profile(self, learner_id: str) -> str:
        """Export learner profile as JSON string."""
        
        profile = self.profiles.get(learner_id)
        if not profile:
            return "{}"
        
        # Convert to dict for JSON serialization
        profile_dict = {
            "learner_id": profile.learner_id,
            "preferences": {
                "learning_style": profile.preferences.learning_style.value,
                "difficulty_preference": profile.preferences.difficulty_preference.value,
                "preferred_domains": profile.preferences.preferred_domains,
                "preferred_contexts": profile.preferences.preferred_contexts,
                "interaction_frequency": profile.preferences.interaction_frequency,
                "feedback_preference": profile.preferences.feedback_preference,
                "collaboration_preference": profile.preferences.collaboration_preference
            },
            "cognitive": {
                "working_memory_capacity": profile.cognitive.working_memory_capacity,
                "processing_speed": profile.cognitive.processing_speed,
                "attention_span": profile.cognitive.attention_span,
                "pattern_recognition": profile.cognitive.pattern_recognition,
                "abstract_thinking": profile.cognitive.abstract_thinking,
                "metacognitive_awareness": profile.cognitive.metacognitive_awareness
            },
            "behavioral": {
                "persistence_level": profile.behavioral.persistence_level,
                "risk_tolerance": profile.behavioral.risk_tolerance,
                "error_handling": profile.behavioral.error_handling,
                "exploration_tendency": profile.behavioral.exploration_tendency,
                "reflection_frequency": profile.behavioral.reflection_frequency,
                "help_seeking_behavior": profile.behavioral.help_seeking_behavior
            },
            "performance": {
                "mastery_rate": profile.performance.mastery_rate,
                "retention_rate": profile.performance.retention_rate,
                "transfer_ability": profile.performance.transfer_ability,
                "error_patterns": profile.performance.error_patterns,
                "success_patterns": profile.performance.success_patterns,
                "learning_curve": profile.performance.learning_curve
            },
            "engagement": {
                "intrinsic_motivation": profile.engagement.intrinsic_motivation,
                "extrinsic_motivation": profile.engagement.extrinsic_motivation,
                "interest_areas": profile.engagement.interest_areas,
                "frustration_tolerance": profile.engagement.frustration_tolerance,
                "boredom_threshold": profile.engagement.boredom_threshold,
                "challenge_preference": profile.engagement.challenge_preference
            },
            "profile_version": profile.profile_version,
            "last_updated": profile.last_updated,
            "confidence_scores": profile.confidence_scores
        }
        
        return json.dumps(profile_dict, indent=2)
    
    def import_profile(self, learner_id: str, profile_json: str) -> LearnerProfile:
        """Import learner profile from JSON string."""
        
        try:
            profile_dict = json.loads(profile_json)
            
            # Reconstruct profile object
            profile = LearnerProfile(
                learner_id=learner_id,
                preferences=LearningPreferences(
                    learning_style=LearningStyle(profile_dict["preferences"]["learning_style"]),
                    difficulty_preference=DifficultyPreference(profile_dict["preferences"]["difficulty_preference"]),
                    preferred_domains=profile_dict["preferences"]["preferred_domains"],
                    preferred_contexts=profile_dict["preferences"]["preferred_contexts"],
                    interaction_frequency=profile_dict["preferences"]["interaction_frequency"],
                    feedback_preference=profile_dict["preferences"]["feedback_preference"],
                    collaboration_preference=profile_dict["preferences"]["collaboration_preference"]
                ),
                cognitive=CognitiveProfile(**profile_dict["cognitive"]),
                behavioral=BehavioralProfile(**profile_dict["behavioral"]),
                performance=PerformanceProfile(**profile_dict["performance"]),
                engagement=EngagementProfile(**profile_dict["engagement"]),
                profile_version=profile_dict.get("profile_version", "1.0"),
                last_updated=profile_dict.get("last_updated", time.time()),
                confidence_scores=profile_dict.get("confidence_scores", {})
            )
            
            self.profiles[learner_id] = profile
            return profile
            
        except Exception as e:
            # Return default profile if import fails
            return self.create_initial_profile(learner_id) 