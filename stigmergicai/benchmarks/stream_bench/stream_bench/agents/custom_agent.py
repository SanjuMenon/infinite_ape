import json
import textwrap
from typing import Dict, Any, List

from .base import Agent


class CustomAgent(Agent):
    """
    A custom agent implementation for StreamBench.
    
    This agent demonstrates how to implement a custom agent that can:
    1. Process prompts and generate responses
    2. Learn from feedback to improve over time
    3. Track performance metrics
    """
    
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        
        # Initialize agent-specific attributes
        self.memory = []  # Store past interactions for learning
        self.performance_history = []  # Track performance over time
        self.learning_rate = config.get("learning_rate", 0.1)
        self.max_memory_size = config.get("max_memory_size", 100)
        
        # Custom prompt template for this agent
        self.prompt_template = config.get("prompt_template", 
            "Task: {task_description}\n\nInput: {input}\n\nOptions:\n{options}\n\nAnswer:")
    
    def __call__(self, prompt: str, label_set: list[str], **kwargs) -> str:
        """
        Generate response text using the prompt.
        The response should be parsed to a label in the label_set.
        
        Args:
            prompt: The input prompt
            label_set: List of possible labels/options
            **kwargs: Additional context (e.g., task description, time_step)
        
        Returns:
            str: The predicted label from label_set
        """
        # Extract context from kwargs
        task_description = kwargs.get("desc", "Answer the question based on the given options.")
        input_text = kwargs.get("input", prompt)
        time_step = kwargs.get("time_step", 0)
        
        # Build the full prompt
        options_text = self.get_options_text(set(label_set))
        full_prompt = self.prompt_template.format(
            task_description=task_description,
            input=input_text,
            options=options_text
        )
        
        # Add memory context if available
        if self.memory and len(self.memory) > 0:
            memory_context = self._build_memory_context()
            full_prompt = f"Previous examples:\n{memory_context}\n\n{full_prompt}"
        
        # Call the LLM
        response_text, response_info = self.llm(full_prompt)
        
        # Update logging information
        self.update_log_info({
            "num_inference_call": 1,
            "num_success_call": 1 if response_text else 0,
            "num_input_tokens": response_info.get("input_tokens", 0),
            "num_output_tokens": response_info.get("output_tokens", 0),
        })
        
        # Parse the response to get the predicted label
        predicted_label = self._parse_response(response_text, label_set)
        
        return predicted_label
    
    def update(self, has_feedback: bool, **feedbacks) -> bool:
        """
        Update the agent based on feedback.
        
        Args:
            has_feedback: Whether feedback is available
            **feedbacks: Feedback information including correct answer, prediction, etc.
        
        Returns:
            bool: True if the agent was updated, False otherwise
        """
        if not has_feedback:
            return False
        
        # Extract feedback information
        correct_answer = feedbacks.get("y", "")
        prediction = feedbacks.get("prediction", "")
        input_text = feedbacks.get("input", "")
        time_step = feedbacks.get("time_step", 0)
        
        # Calculate if prediction was correct
        is_correct = prediction == correct_answer
        
        # Store the interaction in memory
        memory_entry = {
            "input": input_text,
            "prediction": prediction,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "time_step": time_step
        }
        
        self.memory.append(memory_entry)
        
        # Keep memory size within limits
        if len(self.memory) > self.max_memory_size:
            self.memory.pop(0)  # Remove oldest entry
        
        # Update performance history
        self.performance_history.append(is_correct)
        
        # Simple learning strategy: if wrong, try to learn from the mistake
        if not is_correct:
            # You could implement more sophisticated learning here
            # For example, adjusting prompt templates, learning patterns, etc.
            pass
        
        return True  # Agent was updated
    
    def _parse_response(self, response_text: str, label_set: List[str]) -> str:
        """
        Parse the LLM response to extract the predicted label.
        
        Args:
            response_text: Raw response from the LLM
            label_set: List of valid labels
        
        Returns:
            str: The predicted label
        """
        if not response_text:
            return label_set[0] if label_set else ""
        
        # Clean the response text
        response_text = response_text.strip().lower()
        
        # Try to find an exact match in the label set
        for label in label_set:
            if label.lower() in response_text or response_text in label.lower():
                return label
        
        # If no exact match, try to find the best match
        # This is a simple implementation - you might want to use more sophisticated matching
        for label in label_set:
            if any(word in response_text for word in label.lower().split()):
                return label
        
        # Default to first label if no match found
        return label_set[0] if label_set else ""
    
    def _build_memory_context(self) -> str:
        """
        Build context from memory for few-shot learning.
        
        Returns:
            str: Formatted memory context
        """
        if not self.memory:
            return ""
        
        # Use recent memory entries (last 5)
        recent_memory = self.memory[-5:]
        
        context_parts = []
        for entry in recent_memory:
            context_parts.append(
                f"Input: {entry['input']}\n"
                f"Prediction: {entry['prediction']}\n"
                f"Correct: {entry['correct_answer']}\n"
                f"Correct: {'Yes' if entry['is_correct'] else 'No'}\n"
            )
        
        return "\n".join(context_parts)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the agent.
        
        Returns:
            Dict containing performance metrics
        """
        if not self.performance_history:
            return {"accuracy": 0.0, "total_predictions": 0}
        
        accuracy = sum(self.performance_history) / len(self.performance_history)
        return {
            "accuracy": accuracy,
            "total_predictions": len(self.performance_history),
            "memory_size": len(self.memory)
        }
    
    def reset_memory(self) -> None:
        """Reset the agent's memory."""
        self.memory = []
        self.performance_history = [] 