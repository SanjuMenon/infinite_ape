from __future__ import annotations

from typing import Final

COLLATERAL_PROMPT_V1: str = (
    "Summarize the collateral JSON payload.\n"
    "Use only the provided fields; do not infer or invent.\n"
    "Return only the summary text."
)

BUSINESS_MODEL_PROMPT_V1: str = (
    "You are given a JSON payload for the 'business_model' section.\n"
    "Write a concise, accurate summary of the business model.\n"
    "Only use information explicitly present in the payload. Do not infer or invent.\n"
    "Return only the summary text (no headings)."
)

PROMPT_NONE: Final[str] = "__NONE__"

def get_prompt_for_section(section_name: str) -> str:
    """Return the prompt for a section, or PROMPT_NONE to enable passthrough behavior."""
    key = (section_name or "").strip().lower()
    if key == "collateral":
        return PROMPT_NONE
    if key == "business_model":
        return BUSINESS_MODEL_PROMPT_V1
    return PROMPT_NONE

