"""
Constructivist Learning System using Pattern Language Principles.

This package implements a domain-agnostic constructivist learning system
that uses pattern language concepts to guide learners through progressive
complexity by applying forces that drive pattern evolution.
"""

from .core.learning_system import ConstructivistLearningSystem, LearningResponse
from .core.pattern_database import PatternDatabase
from .core.evolution_detector import EvolutionDetector
from .core.schemas import Pattern, Force, LearnerState, ForceCategory

# LLM Integration (optional - requires OpenAI API key)
try:
    from .llm.llm_integration import LLMEnhancedLearningSystem, LLMIntegration
    from .llm.prompt_templates import ConstructivistPromptTemplates
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

__version__ = "0.2.0"
__author__ = "Constructivist Learning Team"

__all__ = [
    "ConstructivistLearningSystem",
    "LearningResponse", 
    "PatternDatabase",
    "EvolutionDetector",
    "Pattern",
    "Force", 
    "LearnerState",
    "ForceCategory",
    "LLM_AVAILABLE"
]

# Add LLM components if available
if LLM_AVAILABLE:
    __all__.extend([
        "LLMEnhancedLearningSystem",
        "LLMIntegration", 
        "ConstructivistPromptTemplates"
    ]) 