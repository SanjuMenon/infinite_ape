"""
Pytest configuration and fixtures for declarative FSM tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_config():
    """Fixture providing a sample valid config."""
    return {
        "fields": {
            "test_field": {
                "field_selection_strategy": {
                    "check_completeness": {
                        "description": ["field1"]
                    },
                    "convert_to_canon": {
                        "description": True
                    }
                },
                "extraction_strategy": {
                    "validate_type": {
                        "description": "int"
                    }
                },
                "generation_strategy": {
                    "format": {
                        "description": "table"
                    }
                },
                "validation_strategy": {
                    "llm_eval": {
                        "description": ["score readability"]
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_data():
    """Fixture providing sample test data."""
    return {
        "test_field": {
            "field1": "15",
            "field2": "30"
        }
    }


@pytest.fixture
def canonical_mappings():
    """Fixture providing canonical mappings."""
    return {
        "test_field": {
            "field1": "canonical_field1",
            "field2": "canonical_field2"
        }
    }
