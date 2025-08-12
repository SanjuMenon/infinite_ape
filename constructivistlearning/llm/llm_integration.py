"""
LLM Integration Layer for the Constructivist Learning System.

This module provides the interface between the learning system and OpenAI's API,
enabling natural language processing and dynamic response generation.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
from ..core.schemas import Pattern, Force, LearnerState
from .prompt_templates import ConstructivistPromptTemplates, PromptContext


@dataclass
class LLMResponse:
    """Structured response from the LLM."""
    content: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]


@dataclass
class InteractionAnalysis:
    """Analysis of a learner interaction."""
    understanding_level: float
    mastery_signals: List[str]
    struggle_signals: List[str]
    readiness_signals: List[str]
    recommended_action: str
    confidence: float
    reasoning: str


class LLMIntegration:
    """Integration layer for OpenAI API in the constructivist learning system."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.7):
        """
        Initialize the LLM integration.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
            temperature: Response creativity (0.0-1.0)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.templates = ConstructivistPromptTemplates()
        self.logger = logging.getLogger(__name__)
        
        # Cache for system prompts to avoid repeated API calls
        self._system_prompt_cache = None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for constructivist learning."""
        if self._system_prompt_cache is None:
            self._system_prompt_cache = self.templates.get_system_prompt()
        return self._system_prompt_cache
    
    def analyze_interaction(self, context: PromptContext, user_input: str) -> InteractionAnalysis:
        """
        Analyze a learner interaction to assess understanding and needs.
        
        Args:
            context: Current learning context
            user_input: Learner's input text
            
        Returns:
            Structured analysis of the interaction
        """
        try:
            # Generate analysis prompt
            analysis_prompt = self.templates.get_interaction_analysis_prompt(context, user_input)
            
            # Get LLM response
            response = self._call_llm(analysis_prompt, response_format="json")
            
            # Parse structured response
            analysis_data = json.loads(response.content)
            
            return InteractionAnalysis(
                understanding_level=analysis_data.get("understanding_level", 0.0),
                mastery_signals=analysis_data.get("mastery_signals", []),
                struggle_signals=analysis_data.get("struggle_signals", []),
                readiness_signals=analysis_data.get("readiness_signals", []),
                recommended_action=analysis_data.get("recommended_action", "continue"),
                confidence=analysis_data.get("confidence", 0.5),
                reasoning=analysis_data.get("reasoning", "")
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing interaction: {e}")
            # Fallback to basic analysis
            return InteractionAnalysis(
                understanding_level=0.5,
                mastery_signals=[],
                struggle_signals=[],
                readiness_signals=[],
                recommended_action="continue",
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}"
            )
    
    def generate_pattern_introduction(self, context: PromptContext) -> LLMResponse:
        """
        Generate an introduction for a new pattern.
        
        Args:
            context: Current learning context
            
        Returns:
            LLM response for pattern introduction
        """
        try:
            prompt = self.templates.get_pattern_introduction_prompt(context)
            return self._call_llm(prompt)
        except Exception as e:
            self.logger.error(f"Error generating pattern introduction: {e}")
            return self._fallback_response("pattern_introduction", context)
    
    def generate_force_application(self, context: PromptContext) -> LLMResponse:
        """
        Generate a response for applying a force to evolve a pattern.
        
        Args:
            context: Current learning context with applied force
            
        Returns:
            LLM response for force application
        """
        try:
            prompt = self.templates.get_force_application_prompt(context)
            return self._call_llm(prompt)
        except Exception as e:
            self.logger.error(f"Error generating force application: {e}")
            return self._fallback_response("force_application", context)
    
    def generate_evolution_guidance(self, context: PromptContext, target_pattern: Pattern) -> LLMResponse:
        """
        Generate guidance for pattern evolution.
        
        Args:
            context: Current learning context
            target_pattern: Pattern to evolve to
            
        Returns:
            LLM response for evolution guidance
        """
        try:
            prompt = self.templates.get_evolution_guidance_prompt(context, target_pattern)
            return self._call_llm(prompt)
        except Exception as e:
            self.logger.error(f"Error generating evolution guidance: {e}")
            return self._fallback_response("evolution_guidance", context)
    
    def generate_scaffolding(self, context: PromptContext, intervention_type: str) -> LLMResponse:
        """
        Generate scaffolding and support response.
        
        Args:
            context: Current learning context
            intervention_type: Type of intervention needed
            
        Returns:
            LLM response for scaffolding
        """
        try:
            prompt = self.templates.get_scaffolding_prompt(context, intervention_type)
            return self._call_llm(prompt)
        except Exception as e:
            self.logger.error(f"Error generating scaffolding: {e}")
            return self._fallback_response("scaffolding", context)
    
    def generate_metacognitive_reflection(self, context: PromptContext) -> LLMResponse:
        """
        Generate prompts for metacognitive reflection.
        
        Args:
            context: Current learning context
            
        Returns:
            LLM response for reflection guidance
        """
        try:
            prompt = self.templates.get_metacognitive_reflection_prompt(context)
            return self._call_llm(prompt)
        except Exception as e:
            self.logger.error(f"Error generating reflection: {e}")
            return self._fallback_response("reflection", context)
    
    def generate_domain_adaptation(self, context: PromptContext, target_domain: str) -> LLMResponse:
        """
        Generate guidance for adapting patterns across domains.
        
        Args:
            context: Current learning context
            target_domain: Domain to adapt to
            
        Returns:
            LLM response for domain adaptation
        """
        try:
            prompt = self.templates.get_domain_adaptation_prompt(context, target_domain)
            return self._call_llm(prompt)
        except Exception as e:
            self.logger.error(f"Error generating domain adaptation: {e}")
            return self._fallback_response("domain_adaptation", context)
    
    def _call_llm(self, prompt: str, response_format: str = "text") -> LLMResponse:
        """
        Make a call to the OpenAI API.
        
        Args:
            prompt: The prompt to send
            response_format: Expected response format ("text" or "json")
            
        Returns:
            LLM response
        """
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            # Prepare parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 1000
            }
            
            # Add response format if JSON is requested
            if response_format == "json":
                params["response_format"] = {"type": "json_object"}
            
            # Make API call
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            confidence = self._extract_confidence(response)
            
            return LLMResponse(
                content=content,
                confidence=confidence,
                reasoning="Generated by LLM",
                metadata={
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens,
                    "response_format": response_format
                }
            )
            
        except Exception as e:
            self.logger.error(f"LLM API call failed: {e}")
            raise
    
    def _extract_confidence(self, response) -> float:
        """Extract confidence from LLM response metadata."""
        # This is a simplified confidence extraction
        # In a real implementation, you might analyze response quality, token usage, etc.
        return 0.8  # Default confidence
    
    def _fallback_response(self, response_type: str, context: PromptContext) -> LLMResponse:
        """
        Generate fallback responses when LLM calls fail.
        
        Args:
            response_type: Type of response needed
            context: Current learning context
            
        Returns:
            Fallback response
        """
        pattern = context.current_pattern
        
        fallback_responses = {
            "pattern_introduction": f"Let's explore the concept of {pattern.name}. This pattern represents {pattern.core_concept.simple_definition}. What questions do you have about this?",
            "force_application": "I'm here to help you explore this concept further. What aspects would you like to understand better?",
            "evolution_guidance": "Great progress! You're ready to explore more advanced concepts. What interests you most?",
            "scaffolding": f"I'm here to support your learning of {pattern.name}. Let's break this down step by step. What part would you like to focus on first?",
            "reflection": "Take a moment to reflect on what you've learned. What insights have you gained?",
            "domain_adaptation": "This concept can be applied in many different areas. How do you think it might work in other domains?"
        }
        
        content = fallback_responses.get(response_type, "I'm here to help you learn. What would you like to explore?")
        
        return LLMResponse(
            content=content,
            confidence=0.5,
            reasoning="Fallback response due to LLM failure",
            metadata={"response_type": "fallback", "original_type": response_type}
        )


class LLMEnhancedLearningSystem:
    """
    Enhanced learning system with LLM integration.
    
    This class extends the basic learning system with LLM capabilities
    for natural language processing and dynamic response generation.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize the LLM-enhanced learning system.
        
        Args:
            api_key: OpenAI API key
            model: LLM model to use
        """
        from ..core.learning_system import ConstructivistLearningSystem
        
        self.base_system = ConstructivistLearningSystem()
        self.llm = LLMIntegration(api_key, model)
        self.logger = logging.getLogger(__name__)
    
    def initialize_learner(self, learner_id: str, domain: str = "programming", 
                          starting_pattern: str = "var_basic") -> LearnerState:
        """Initialize a new learner with LLM-enhanced capabilities."""
        return self.base_system.initialize_learner(learner_id, domain, starting_pattern)
    
    def process_interaction(self, learner_id: str, user_input: str) -> Dict:
        """
        Process a learner interaction with LLM-enhanced analysis and response generation.
        
        Args:
            learner_id: ID of the learner
            user_input: Learner's input text
            
        Returns:
            Enhanced response with LLM-generated content
        """
        # Get current learner state and pattern
        learner_state = self.base_system.learner_states.get(learner_id)
        if not learner_state:
            raise ValueError(f"Learner {learner_id} not found")
        
        current_pattern = self.base_system.pattern_db.get_pattern(learner_state.current_pattern)
        
        # Create prompt context
        context = PromptContext(
            learner_state=learner_state,
            current_pattern=current_pattern,
            applied_force=None,  # Will be set if a force is active
            interaction_history=[],  # Could be enhanced with actual history
            domain=learner_state.learning_preferences.get("domain_interest", "general"),
            learning_style=learner_state.learning_preferences.get("learning_style", "balanced"),
            difficulty_preference=learner_state.learning_preferences.get("preferred_difficulty", "medium")
        )
        
        # Analyze the interaction
        analysis = self.llm.analyze_interaction(context, user_input)
        
        # Generate appropriate response based on analysis
        if analysis.recommended_action == "scaffold":
            llm_response = self.llm.generate_scaffolding(context, "general_support")
        elif analysis.recommended_action == "evolve":
            # Get evolution decision from base system
            evolution_decision = self.base_system.evolution_detector.decide_evolution(learner_state, current_pattern)
            if evolution_decision.should_evolve and evolution_decision.target_pattern:
                target_pattern = self.base_system.pattern_db.get_pattern(evolution_decision.target_pattern)
                llm_response = self.llm.generate_evolution_guidance(context, target_pattern)
            else:
                llm_response = self.llm.generate_pattern_introduction(context)
        else:
            llm_response = self.llm.generate_pattern_introduction(context)
        
        # Update learner state (using base system logic)
        interaction_data = self._extract_interaction_data(analysis)
        updated_state = self.base_system.evolution_detector.update_learner_state(learner_state, interaction_data)
        self.base_system.learner_states[learner_id] = updated_state
        
        # Return enhanced response
        return {
            "message": llm_response.content,
            "pattern_context": current_pattern.core_concept.simple_definition,
            "force_context": None,
            "next_action": analysis.recommended_action,
            "confidence": llm_response.confidence,
            "reasoning": analysis.reasoning,
            "llm_analysis": {
                "understanding_level": analysis.understanding_level,
                "mastery_signals": analysis.mastery_signals,
                "struggle_signals": analysis.struggle_signals,
                "readiness_signals": analysis.readiness_signals
            },
            "metadata": llm_response.metadata
        }
    
    def _extract_interaction_data(self, analysis: InteractionAnalysis) -> Dict:
        """Extract interaction data from LLM analysis for state updates."""
        return {
            "mastery_indicators": {
                "conceptual_understanding": analysis.understanding_level,
                "pattern_fluency": analysis.understanding_level,
                "force_handling": analysis.understanding_level
            },
            "confusion_indicators": len(analysis.struggle_signals) * 0.2,
            "frustration_indicators": len(analysis.struggle_signals) * 0.1,
            "mastery_score": analysis.understanding_level
        }
    
    def get_learner_progress(self, learner_id: str) -> Dict:
        """Get learner progress with LLM-enhanced insights."""
        progress = self.base_system.get_learner_progress(learner_id)
        
        # Add LLM-specific insights if available
        learner_state = self.base_system.learner_states.get(learner_id)
        if learner_state:
            context = PromptContext(
                learner_state=learner_state,
                current_pattern=self.base_system.pattern_db.get_pattern(learner_state.current_pattern),
                applied_force=None,
                interaction_history=[],
                domain=learner_state.learning_preferences.get("domain_interest", "general"),
                learning_style=learner_state.learning_preferences.get("learning_style", "balanced"),
                difficulty_preference=learner_state.learning_preferences.get("preferred_difficulty", "medium")
            )
            
            # Generate reflection prompt
            reflection_response = self.llm.generate_metacognitive_reflection(context)
            
            progress["llm_insights"] = {
                "reflection_prompt": reflection_response.content,
                "learning_style_recommendations": self._generate_style_recommendations(context),
                "next_steps_suggestions": self._generate_next_steps(context)
            }
        
        return progress
    
    def _generate_style_recommendations(self, context: PromptContext) -> List[str]:
        """Generate learning style recommendations based on context."""
        # This could be enhanced with more sophisticated analysis
        style = context.learning_style
        recommendations = {
            "visual": ["Use diagrams and visual examples", "Create mind maps", "Watch demonstration videos"],
            "kinesthetic": ["Try hands-on exercises", "Build physical models", "Practice with real examples"],
            "auditory": ["Discuss concepts with others", "Listen to explanations", "Use verbal mnemonics"],
            "balanced": ["Mix different learning approaches", "Experiment with various methods", "Find what works best for you"]
        }
        return recommendations.get(style, recommendations["balanced"])
    
    def _generate_next_steps(self, context: PromptContext) -> List[str]:
        """Generate suggestions for next learning steps."""
        pattern = context.current_pattern
        domain = context.domain
        
        return [
            f"Explore more examples of {pattern.name} in {domain}",
            f"Practice applying {pattern.name} to real problems",
            f"Connect {pattern.name} to other concepts you know",
            f"Try explaining {pattern.name} to someone else",
            f"Look for {pattern.name} in everyday situations"
        ] 