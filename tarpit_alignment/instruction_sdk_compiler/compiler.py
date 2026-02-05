"""Orchestrates: summarize spec -> LLM -> validate -> apply -> log."""

from typing import Optional
from instruction_sdk_compiler.llm.base import LLMClient
from instruction_sdk_compiler.llm.prompts import SYSTEM_PROMPT, build_user_prompt, build_repair_prompt
from instruction_sdk_compiler.parser.ir import ChangeSet
from instruction_sdk_compiler.parser.validate import validate_changeset, extract_changeset_from_response
from instruction_sdk_compiler.spec.model import SdkSpec


class InstructionReceipt:
    """Receipt for an ingested instruction."""

    def __init__(
        self,
        instruction_text: str,
        changeset: ChangeSet,
        validation_errors: Optional[str] = None,
        repair_attempts: int = 0,
    ):
        self.instruction_text = instruction_text
        self.changeset = changeset
        self.validation_errors = validation_errors
        self.repair_attempts = repair_attempts


def summarize_spec(spec: SdkSpec) -> str:
    """
    Generate a compact summary of the current SDK spec.
    
    Args:
        spec: The SDK specification
        
    Returns:
        Compact text summary
    """
    if not spec.classes or spec.classes is None:
        return "Empty SDK (no classes defined yet)."
    
    lines = ["Current SDK Specification:"]
    if not spec.classes:
        lines.append("\n(No classes defined)")
        return "\n".join(lines)
    for class_name, class_spec in spec.classes.items():
        lines.append(f"\n{class_name}:")
        if class_spec.doc_summary:
            lines.append(f"  Doc: {class_spec.doc_summary}")
        if class_spec.deprecated:
            lines.append("  [DEPRECATED]")
        
        if class_spec.methods:
            lines.append("  Methods:")
            for method_name, method_spec in class_spec.methods.items():
                # Build signature summary
                input_fields = []
                if method_spec.inputs.fields:
                    for field_name, field_spec in method_spec.inputs.fields.items():
                        optional_str = "?" if field_spec.optional else ""
                        input_fields.append(f"{field_name}: {field_spec.type}{optional_str}")
                
                sig = f"    {method_name}({', '.join(input_fields)}) -> {method_spec.outputs.name}"
                if method_spec.deprecated:
                    sig += " [DEPRECATED]"
                lines.append(sig)
        else:
            lines.append("  Methods: (none)")
    
    return "\n".join(lines)


def compile_instruction(
    instruction: str,
    spec: SdkSpec,
    llm_client: LLMClient,
    max_repair_attempts: int = 2,
) -> InstructionReceipt:
    """
    Compile a natural language instruction into a ChangeSet.
    
    This orchestrates the full pipeline:
    1. Summarize current spec
    2. Call LLM to produce JSON
    3. Validate JSON against ChangeSet schema
    4. If invalid, run repair loop (up to max_repair_attempts)
    
    Args:
        instruction: Natural language instruction
        spec: Current SDK specification
        llm_client: LLM client to use
        max_repair_attempts: Maximum number of repair attempts
        
    Returns:
        InstructionReceipt with changeset
        
    Raises:
        ValueError: If validation fails after all repair attempts
    """
    # Step 1: Summarize spec
    spec_summary = summarize_spec(spec)
    
    # Step 2: Call LLM
    user_prompt = build_user_prompt(instruction, spec_summary)
    response = llm_client.generate(SYSTEM_PROMPT, user_prompt)
    
    # Step 3: Extract and validate JSON
    json_str = extract_changeset_from_response(response)
    if json_str is None:
        json_str = response  # Fallback to raw response
    
    changeset, error = validate_changeset(json_str)
    repair_attempts = 0
    
    # Step 4: Repair loop if needed
    while changeset is None and repair_attempts < max_repair_attempts:
        repair_attempts += 1
        repair_prompt = build_repair_prompt(instruction, json_str, error or "Unknown error")
        repair_response = llm_client.generate(SYSTEM_PROMPT, repair_prompt)
        
        json_str = extract_changeset_from_response(repair_response)
        if json_str is None:
            json_str = repair_response
        
        changeset, error = validate_changeset(json_str)
    
    if changeset is None:
        raise ValueError(
            f"Failed to generate valid ChangeSet after {repair_attempts} repair attempts. "
            f"Last validation errors: {error}\nLast JSON: {json_str}"
        )
    
    return InstructionReceipt(
        instruction_text=instruction,
        changeset=changeset,
        validation_errors=None,
        repair_attempts=repair_attempts,
    )
