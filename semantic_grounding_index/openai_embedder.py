"""Azure OpenAI embedding backend for SGI."""

import os
import time
import numpy as np
from typing import Optional

try:
    from openai import AzureOpenAI
    from dotenv import load_dotenv
except ImportError as e:
    raise ImportError(
        "Missing required dependencies. Install with: pip install openai python-dotenv"
    ) from e

# Load environment variables
load_dotenv()


class AzureOpenAIEmbedder:
    """Azure OpenAI embedding client with retry logic."""

    DEFAULT_DEPLOYMENT = "text-embedding-3-small"

    def __init__(self, deployment: Optional[str] = None, api_version: Optional[str] = None):
        """
        Initialize Azure OpenAI embedder.

        Args:
            deployment: Deployment name (default: text-embedding-3-small)
            api_version: API version (default: 2024-02-15-preview)
        """
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or self.DEFAULT_DEPLOYMENT
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION") or "2024-02-15-preview"
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY environment variable not set. "
                "Set it in your environment or .env file."
            )
        if not endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT environment variable not set. "
                "Set it in your environment or .env file."
            )
        
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=self.api_version,
            azure_endpoint=endpoint,
        )

    def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text string.

        Args:
            text: Input text string

        Returns:
            Embedding vector as float32 numpy array

        Raises:
            Exception: On API failure after retries
        """
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> np.ndarray:
        """
        Embed multiple text strings in a single API call.

        Args:
            texts: List of input text strings

        Returns:
            Array of embedding vectors as float32 numpy array (shape: [len(texts), dim])

        Raises:
            Exception: On API failure after retries
        """
        if not texts:
            raise ValueError("texts list cannot be empty")

        max_retries = 2
        base_delay = 0.5

        for attempt in range(max_retries + 1):
            try:
                response = self.client.embeddings.create(
                    model=self.deployment,
                    input=texts,
                )

                # Extract embeddings
                embeddings = [item.embedding for item in response.data]
                result = np.array(embeddings, dtype=np.float32)

                return result

            except Exception as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise RuntimeError(
                        f"Azure OpenAI API call failed after {max_retries + 1} attempts: {e}"
                    ) from e

