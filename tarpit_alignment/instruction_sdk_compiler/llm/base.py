"""Base LLM client interface."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            system_prompt: System prompt describing the task
            user_prompt: User prompt with instruction and context
            
        Returns:
            Raw response string (should contain JSON)
        """
        pass
