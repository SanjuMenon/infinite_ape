"""SGI (Semantic Grounding Index) metric implementation."""

__version__ = "0.1.0"

from semantic_grounding_index.core import sgi, Embedder
from semantic_grounding_index.openai_embedder import (
    AzureOpenAIEmbedder,
    OpenAIEmbedder,
    get_embedder,
)

__all__ = [
    "sgi",
    "Embedder",
    "AzureOpenAIEmbedder",
    "OpenAIEmbedder",
    "get_embedder",
]
