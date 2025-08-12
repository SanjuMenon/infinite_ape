"""
LLM Integration Module for Constructivist Learning System.

This module provides OpenAI API integration for natural language processing
and dynamic response generation in the constructivist learning system.
"""

from .prompt_templates import ConstructivistPromptTemplates, PromptContext
from .llm_integration import LLMIntegration, LLMEnhancedLearningSystem, LLMResponse, InteractionAnalysis

__all__ = [
    "ConstructivistPromptTemplates",
    "PromptContext",
    "LLMIntegration", 
    "LLMEnhancedLearningSystem",
    "LLMResponse",
    "InteractionAnalysis"
] 