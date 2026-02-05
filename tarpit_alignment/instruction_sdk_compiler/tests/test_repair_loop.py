"""Test repair loop for invalid LLM output."""

import json
from unittest.mock import Mock
from instruction_sdk_compiler.llm.base import LLMClient
from instruction_sdk_compiler.compiler import compile_instruction
from instruction_sdk_compiler.spec.model import SdkSpec


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response


def test_repair_loop_success():
    """Test that repair loop fixes invalid JSON."""
    # First response is invalid, second is valid
    invalid_json = json.dumps({
        "changes": [
            {
                "kind": "ADD_CLASS"
                # Missing class_name
            }
        ]
    })
    
    valid_json = json.dumps({
        "changes": [
            {
                "kind": "ADD_CLASS",
                "class_name": "UserService",
                "doc": "Service for users"
            }
        ]
    })
    
    llm_client = MockLLMClient([invalid_json, valid_json])
    spec = SdkSpec(version="1.0.0")
    spec.rebind(classes={}, metadata={})
    
    receipt = compile_instruction(
        "Create a UserService class",
        spec,
        llm_client,
        max_repair_attempts=2
    )
    
    assert receipt.changeset is not None
    assert len(receipt.changeset.changes) == 1
    assert receipt.changeset.changes[0].kind == "ADD_CLASS"
    assert receipt.repair_attempts == 1


def test_repair_loop_failure():
    """Test that repair loop raises error after max attempts."""
    invalid_json = json.dumps({
        "changes": [
            {
                "kind": "ADD_CLASS"
                # Missing class_name
            }
        ]
    })
    
    llm_client = MockLLMClient([invalid_json, invalid_json, invalid_json])
    spec = SdkSpec(version="1.0.0")
    spec.rebind(classes={}, metadata={})
    
    try:
        compile_instruction(
            "Create a UserService class",
            spec,
            llm_client,
            max_repair_attempts=2
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Failed to generate valid ChangeSet" in str(e)
        assert llm_client.call_count == 3  # Initial + 2 repair attempts
