"""OpenAI and Azure OpenAI embedding backends for SGI."""

import os
import time
import numpy as np
from typing import Optional

try:
    from openai import OpenAI, AzureOpenAI
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


class OpenAIEmbedder:
    """OpenAI embedding client with retry logic."""

    DEFAULT_MODEL = "text-embedding-3-small"

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize OpenAI embedder.

        Args:
            model: Model name (default: text-embedding-3-small)
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
        """
        self.model = model or os.getenv("OPENAI_MODEL") or self.DEFAULT_MODEL
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it in your environment or .env file."
            )
        
        self.client = OpenAI(api_key=api_key)

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
                    model=self.model,
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
                        f"OpenAI API call failed after {max_retries + 1} attempts: {e}"
                    ) from e


def get_embedder(provider: Optional[str] = None) -> AzureOpenAIEmbedder | OpenAIEmbedder:
    """
    Get an embedder instance, auto-detecting provider if not specified.

    Args:
        provider: "azure" or "openai" (default: auto-detect from env vars)

    Returns:
        AzureOpenAIEmbedder or OpenAIEmbedder instance

    Raises:
        ValueError: If provider cannot be determined or credentials are missing
    """
    if provider is None:
        # Auto-detect: check for Azure credentials first, then OpenAI
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if azure_key and azure_endpoint:
            return AzureOpenAIEmbedder()
        elif openai_key:
            return OpenAIEmbedder()
        else:
            raise ValueError(
                "Could not auto-detect provider. Set either:\n"
                "  - AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT (for Azure)\n"
                "  - OPENAI_API_KEY (for OpenAI)\n"
                "Or specify provider='azure' or provider='openai'"
            )
    
    provider = provider.lower()
    if provider == "azure":
        return AzureOpenAIEmbedder()
    elif provider == "openai":
        return OpenAIEmbedder()
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'azure' or 'openai'")

