"""Test LLM output to ChangeSet validation."""

import json
from instruction_sdk_compiler.parser.ir import ChangeSet, AddClassChange, AddMethodChange, ModelSpec, FieldSpec
from instruction_sdk_compiler.parser.validate import validate_changeset


def test_valid_changeset():
    """Test that a valid ChangeSet JSON validates correctly."""
    valid_json = json.dumps({
        "changes": [
            {
                "kind": "ADD_CLASS",
                "class_name": "UserService",
                "doc": "Service for managing users"
            },
            {
                "kind": "ADD_METHOD",
                "class_name": "UserService",
                "method_name": "create_user",
                "inputs": {
                    "name": "CreateUserInput",
                    "fields": [
                        {
                            "name": "email",
                            "type": "str",
                            "optional": False
                        }
                    ]
                },
                "outputs": {
                    "name": "User",
                    "fields": [
                        {
                            "name": "id",
                            "type": "str",
                            "optional": False
                        }
                    ]
                },
                "doc": "Create a new user"
            }
        ]
    })
    
    changeset, error = validate_changeset(valid_json)
    assert changeset is not None, f"Validation failed: {error}"
    assert len(changeset.changes) == 2
    assert changeset.changes[0].kind == "ADD_CLASS"
    assert changeset.changes[0].class_name == "UserService"
    assert changeset.changes[1].kind == "ADD_METHOD"
    assert changeset.changes[1].method_name == "create_user"


def test_invalid_changeset_missing_field():
    """Test that invalid JSON is rejected."""
    invalid_json = json.dumps({
        "changes": [
            {
                "kind": "ADD_CLASS"
                # Missing class_name
            }
        ]
    })
    
    changeset, error = validate_changeset(invalid_json)
    assert changeset is None
    assert error is not None
    assert "class_name" in error.lower() or "validation" in error.lower()


def test_invalid_identifier():
    """Test that invalid Python identifiers are rejected."""
    invalid_json = json.dumps({
        "changes": [
            {
                "kind": "ADD_CLASS",
                "class_name": "123Invalid"  # Starts with digit
            }
        ]
    })
    
    changeset, error = validate_changeset(invalid_json)
    assert changeset is None
    assert error is not None
