"""Identifier and docstring sanitization utilities."""

import re
from typing import Any


def sanitize_identifier(name: str) -> str:
    """
    Sanitize a string to be a valid Python identifier.
    
    Args:
        name: Input string
        
    Returns:
        Valid Python identifier
    """
    # Replace invalid characters with underscore
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Ensure it doesn't start with a digit
    if name and name[0].isdigit():
        name = "_" + name
    # Ensure it's not empty
    if not name:
        name = "_unnamed"
    return name


def sanitize_docstring(doc: str) -> str:
    """
    Sanitize a docstring to avoid triple-quote injection.
    
    Args:
        doc: Input docstring
        
    Returns:
        Sanitized docstring
    """
    if not doc:
        return ""
    
    # Escape triple quotes
    doc = doc.replace('"""', '\\"\\"\\"')
    doc = doc.replace("'''", "\\'\\'\\'")
    
    # Remove control characters except newlines and tabs
    doc = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", doc)
    
    return doc


def format_type_string(type_str: str) -> str:
    """
    Format a type string for Python code.
    
    Args:
        type_str: Type string from spec
        
    Returns:
        Formatted type string for Python typing
    """
    # Map common types
    type_map = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "dict": "dict",
        "list": "list",
    }
    
    if type_str in type_map:
        return type_map[type_str]
    
    # Assume it's a custom model name
    return sanitize_identifier(type_str)


def escape_string(value: Any) -> str:
    """
    Escape a value for use in Python code.
    
    Args:
        value: Value to escape
        
    Returns:
        Escaped string representation
    """
    if value is None:
        return "None"
    elif isinstance(value, str):
        return repr(value)
    elif isinstance(value, (int, float, bool)):
        return str(value)
    else:
        return repr(str(value))
