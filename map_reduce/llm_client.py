from __future__ import annotations

import os
from typing import Optional, Union

from dotenv import load_dotenv

try:
    from openai import OpenAI, AzureOpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None

# Load environment variables from .env file if present
load_dotenv()

# Global client instance (lazy initialization)
_client: Optional[Union[OpenAI, AzureOpenAI]] = None
_provider: Optional[str] = None  # "azure" or "openai"
_deployment_name: Optional[str] = None  # For Azure OpenAI


def get_openai_client() -> Optional[Union[OpenAI, AzureOpenAI]]:
    """Get or create OpenAI/Azure OpenAI client instance.
    
    Auto-detects provider:
    - Azure OpenAI if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set
    - OpenAI if OPENAI_API_KEY is set
    
    Returns None if no credentials are available.
    """
    global _client, _provider, _deployment_name
    
    if _client is not None:
        return _client
    
    if OpenAI is None or AzureOpenAI is None:
        return None
    
    # Check for Azure OpenAI first
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if azure_key and azure_endpoint:
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        _deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")  # Store for use in agents
        _client = AzureOpenAI(
            api_key=azure_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        _provider = "azure"
        return _client
    
    # Fall back to OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        _client = OpenAI(api_key=openai_key)
        _provider = "openai"
        return _client
    
    return None


def get_provider() -> Optional[str]:
    """Get the current provider name ('azure' or 'openai'), or None if not available."""
    if get_openai_client() is None:
        return None
    return _provider


def get_deployment_name() -> Optional[str]:
    """Get Azure OpenAI deployment name if using Azure, else None."""
    if _provider == "azure":
        return _deployment_name
    return None


def is_llm_available() -> bool:
    """Check if any LLM provider (OpenAI or Azure OpenAI) is available."""
    return get_openai_client() is not None
