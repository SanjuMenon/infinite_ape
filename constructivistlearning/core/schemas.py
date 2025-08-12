"""
Core schemas for the constructivist learning system using pattern language principles.
"""

from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ForceCategory(Enum):
    """Categories of forces that drive pattern evolution."""
    CONSTRAINT = "constraint"
    REQUIREMENT = "requirement"
    CONTEXT = "context"
    EDGE_CASE = "edge_case"
    PRESSURE = "pressure"


@dataclass
class CoreConcept:
    """The core concept definition for a pattern."""
    simple_definition: str
    key_components: List[str]
    examples: List[str]


@dataclass
class LearningIndicators:
    """Indicators for learning progress and readiness."""
    mastery_signals: List[str]
    struggle_signals: List[str]
    readiness_criteria: List[str]


@dataclass
class ForceEvolutionMap:
    """Mapping of how forces transform patterns."""
    applicable_forces: List[str]
    force_evolution_map: Dict[str, str]


@dataclass
class Pattern:
    """A learning pattern in the constructivist system."""
    pattern_id: str
    name: str
    description: str
    complexity_level: int  # 1-10
    domain_tags: List[str]
    core_concept: CoreConcept
    prerequisites: List[str]
    evolution_paths: List[str]
    forces: ForceEvolutionMap
    learning_indicators: LearningIndicators


@dataclass
class ForceDefinition:
    """Definition of a force that can be applied to patterns."""
    core_pressure: str
    evolution_direction: str
    universal_examples: List[str]


@dataclass
class ApplicationConditions:
    """Conditions for when and how a force can be applied."""
    pattern_compatibility: List[str]
    prerequisite_forces: List[str]
    timing_considerations: str


@dataclass
class EvolutionOutcomes:
    """Expected outcomes when a force is applied to a pattern."""
    pattern_transformations: Dict[str, str]
    complexity_increase: int  # 1-3
    new_capabilities: List[str]


@dataclass
class Force:
    """A force that drives pattern evolution."""
    force_id: str
    name: str
    description: str
    category: ForceCategory
    intensity: int  # 1-5
    domain_agnostic: bool
    force_definition: ForceDefinition
    application_conditions: ApplicationConditions
    evolution_outcomes: EvolutionOutcomes


@dataclass
class MasterySignals:
    """Signals indicating mastery of a pattern."""
    conceptual_understanding: Dict[str, Union[List[str], float, List[str]]]
    pattern_fluency: Dict[str, Union[List[str], float, List[str]]]
    force_handling: Dict[str, Union[List[str], float, List[str]]]


@dataclass
class StruggleDetection:
    """Detection of learning struggles and intervention needs."""
    warning_signals: List[str]
    intervention_threshold: float
    remediation_strategies: List[str]


@dataclass
class EvolutionConfidence:
    """Confidence metrics for pattern evolution decisions."""
    confidence_factors: List[str]
    minimum_confidence: float
    evolution_trigger: str  # "automatic", "manual", "hybrid"


@dataclass
class EvolutionDetection:
    """System for detecting when learners are ready to evolve patterns."""
    evolution_id: str
    pattern_from: str
    pattern_to: str
    triggering_force: str
    readiness_indicators: MasterySignals
    struggle_detection: StruggleDetection
    evolution_confidence: EvolutionConfidence


@dataclass
class LearnerState:
    """Current state of a learner in the system."""
    learner_id: str
    current_pattern: str
    pattern_history: List[str]
    force_exposure: Dict[str, List[str]]
    readiness_indicators: Dict[str, float]
    learning_preferences: Dict[str, any]
    session_data: Dict[str, any] 