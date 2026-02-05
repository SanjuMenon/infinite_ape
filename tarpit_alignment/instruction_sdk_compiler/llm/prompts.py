"""Prompt templates for LLM instruction-to-ChangeSet conversion."""

SYSTEM_PROMPT = """You are a compiler that converts natural language instructions into structured JSON edits for an SDK specification.

CRITICAL RULES:
1. You MUST output ONLY valid JSON. No markdown, no code blocks, no explanations.
2. The output MUST be a JSON object with a "changes" array: {"changes": [...]}
3. You MUST NOT generate Python code. Only JSON that validates against the ChangeSet schema.
4. Produce minimal edits: only change what the instruction explicitly requests.
5. Do not refactor unrelated classes or methods.
6. Preserve existing documentation unless explicitly asked to replace it.
7. Use doc_note fields to describe modifications concisely.

CHANGE TYPES:
1. ADD_CLASS: {"kind": "ADD_CLASS", "class_name": "ServiceName", "doc": "optional description"}
2. ADD_METHOD: {"kind": "ADD_METHOD", "class_name": "ServiceName", "method_name": "method_name", "inputs": ModelSpec, "outputs": ModelSpec, "doc": "optional"}
3. MODIFY_METHOD_SIGNATURE: {"kind": "MODIFY_METHOD_SIGNATURE", "class_name": "...", "method_name": "...", "add_params": [...], "remove_params": [...], "change_return": ModelSpec, "doc_note": "..."}
4. ADD_CONSTRAINT: {"kind": "ADD_CONSTRAINT", "class_name": "...", "method_name": "...", "constraint": ConstraintSpec, "doc_note": "..."}
5. RENAME: {"kind": "RENAME", "target_type": "class"|"method", "from": "OldName", "to": "NewName", "alias_old": true, "doc_note": "..."}
6. DEPRECATE: {"kind": "DEPRECATE", "target_type": "class"|"method", "target": "ClassName"|"ClassName.method_name", "message": "...", "doc_note": "..."}

FIELD SPECS:
- FieldSpec: {"name": "field_name", "type": "str"|"int"|"float"|"bool"|"ModelName", "optional": false, "default": null, "description": "optional"}
- ModelSpec: {"name": "ModelName", "fields": [FieldSpec, ...]}  (fields is an ARRAY, not a dict)
- ConstraintSpec: {"kind": "precondition"|"postcondition"|"policy", "expression": "rule text", "message": "optional"}

CRITICAL: For ADD_METHOD, inputs and outputs MUST be ModelSpec objects with "name" and "fields" (array):
  "inputs": {"name": "CreateUserInput", "fields": [{"name": "email", "type": "str", "optional": false, "default": null, "description": "..."}]}
  "outputs": {"name": "User", "fields": [{"name": "user", "type": "User", "optional": false, "default": null, "description": "..."}]}
  
DO NOT generate: "inputs": {"email": {...}}  (WRONG - this is a dict, not a ModelSpec)
DO generate: "inputs": {"name": "InputModelName", "fields": [{"name": "email", ...}]}  (CORRECT)

VALIDATION:
- All names must be valid Python identifiers (alphanumeric + underscore, not starting with digit)
- Types are strings: "str", "int", "float", "bool", or custom model names
- For renames, set alias_old=true to preserve backward compatibility
- Prefer alias+deprecate over breaking changes

OUTPUT FORMAT:
Return ONLY the JSON object, nothing else. 

Example ADD_CLASS:
{"changes": [{"kind": "ADD_CLASS", "class_name": "UserService", "doc": "Manages users"}]}

Example ADD_METHOD:
{"changes": [{"kind": "ADD_METHOD", "class_name": "UserService", "method_name": "create_user", "inputs": {"name": "CreateUserInput", "fields": [{"name": "email", "type": "str", "optional": false, "default": null, "description": "User email"}]}, "outputs": {"name": "User", "fields": [{"name": "user", "type": "User", "optional": false, "default": null, "description": "Created user"}]}, "doc": "Creates a new user"}]}
"""


def build_user_prompt(instruction: str, spec_summary: str) -> str:
    """
    Build user prompt with instruction and current spec summary.
    
    Args:
        instruction: Natural language instruction
        spec_summary: Compact summary of current SDK spec
        
    Returns:
        Formatted user prompt
    """
    return f"""Convert this instruction into a ChangeSet JSON:

INSTRUCTION:
{instruction}

CURRENT SDK SPECIFICATION:
{spec_summary}

RULES:
- Produce minimal edits matching the instruction exactly
- For renames, use alias_old=true to maintain backward compatibility
- Avoid deleting anything unless explicitly requested
- Use doc_note to describe changes concisely
- Preserve existing documentation unless replace_doc_summary=true

Return ONLY the JSON object with "changes" array, no other text."""


def build_repair_prompt(original_instruction: str, invalid_json: str, validation_errors: str) -> str:
    """
    Build repair prompt for fixing invalid JSON.
    
    Args:
        original_instruction: Original instruction text
        invalid_json: The invalid JSON that was produced
        validation_errors: Validation error messages
        
    Returns:
        Repair prompt
    """
    return f"""The previous JSON output failed validation. Fix it to satisfy the schema.

ORIGINAL INSTRUCTION:
{original_instruction}

INVALID JSON:
{invalid_json}

VALIDATION ERRORS:
{validation_errors}

Return ONLY the corrected JSON object with "changes" array, no other text."""
