"""OpenAI LLM client implementation."""

import os
from openai import OpenAI
from instruction_sdk_compiler.llm.base import LLMClient


class OpenAIClient(LLMClient):
    """OpenAI-based LLM client."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize OpenAI client.
        
        Args:
            model: Model name (default: gpt-4o-mini)
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
            base_url: Base URL for API (default: OpenAI official)
        """
        self.model = model
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate response from OpenAI.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            
        Returns:
            Raw response string
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for deterministic JSON
        )
        return response.choices[0].message.content or ""
