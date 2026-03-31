from __future__ import annotations

from typing import List, Optional

from .llm_client import get_client_and_model, get_openai_client
from .schemas import Bundle


def summarize_with_prompt(bundle: Bundle) -> str:
    """LLM path: send bundle.payload along with bundle.prompt to the LLM."""
    client, model_or_deployment = get_client_and_model()
    if client is None or model_or_deployment is None:
        raise RuntimeError(
            "LLM is required for summarize_with_prompt. "
            "Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT, "
            "or set bundle.prompt=None to use passthrough behavior."
        )

    from .prompts import PROMPT_NONE
    if bundle.prompt == PROMPT_NONE:
        raise RuntimeError("bundle.prompt is PROMPT_NONE; use summarize_passthrough() instead")
    if not bundle.prompt:
        raise RuntimeError("bundle.prompt must be a non-empty string for summarize_with_prompt()")

    combined_prompt = f"""{bundle.prompt}

Payload:
{bundle.payload}
"""

    response = client.chat.completions.create(
        model=model_or_deployment,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that follows the user's prompt exactly and never invents data."},
            {"role": "user", "content": combined_prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    summary = response.choices[0].message.content
    if not summary:
        raise RuntimeError("LLM returned empty response for summarize_freeform")
    
    return summary.strip()


def summarize_passthrough(bundle: Bundle) -> str:
    """Passthrough path: return payload verbatim (used when prompt is None)."""
    return (bundle.payload or "").strip()
