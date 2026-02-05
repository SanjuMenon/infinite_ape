"""Validation and repair helpers for ChangeSet."""

import json
from typing import Optional
from instruction_sdk_compiler.parser.ir import ChangeSet
from pydantic import ValidationError


def validate_changeset(json_str: str) -> tuple[Optional[ChangeSet], Optional[str]]:
    """
    Validate a JSON string against the ChangeSet schema.
    
    Returns:
        Tuple of (ChangeSet if valid, error message if invalid)
    """
    try:
        data = json.loads(json_str)
        changeset = ChangeSet.model_validate(data)
        return changeset, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            path = " -> ".join(str(p) for p in error.get("loc", []))
            msg = error.get("msg", "Validation error")
            error_details.append(f"{path}: {msg}")
        return None, "Validation errors:\n" + "\n".join(error_details)
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def extract_changeset_from_response(response: str) -> Optional[str]:
    """
    Extract JSON from LLM response, handling markdown code blocks.
    
    Returns:
        JSON string if found, None otherwise
    """
    # Remove markdown code blocks if present
    response = response.strip()
    if response.startswith("```"):
        # Find the first newline after ```
        start_idx = response.find("\n")
        if start_idx != -1:
            response = response[start_idx + 1 :]
        # Remove trailing ```
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
    
    # Try to find JSON object
    start_brace = response.find("{")
    end_brace = response.rfind("}")
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        return response[start_brace : end_brace + 1]
    
    return response if response.startswith("{") else None
