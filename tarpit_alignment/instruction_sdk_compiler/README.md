# Instruction SDK Compiler

A Python package that compiles freeform natural-language instructions into an object-oriented SDK (Python classes + methods). The system supports incremental evolution: new instructions may add new classes/methods, or modify/deprecate/rename existing ones.

## Architecture

The compiler uses an LLM **only** to convert instructions into structured edits (ChangeSets) that validate against strict Pydantic schemas. All downstream steps are deterministic:

```
Instruction → LLM → ChangeSet (JSON) → Validate → Apply (PyGlove patch) → Codegen → Generated SDK
```

### Key Principles

1. **LLM outputs JSON only** - The LLM never generates Python code directly. It only produces JSON that validates against the ChangeSet schema.
2. **Deterministic pipeline** - Once a ChangeSet is validated, all subsequent steps (patching, codegen) are deterministic.
3. **In-place spec mutation** - The SDK specification is maintained as a single in-memory PyGlove object that is mutated in-place using `rebind()` operations.
4. **Repair loop** - If LLM output fails validation, the system automatically feeds errors back and requests corrected JSON (up to 2 retries).
5. **No code execution** - The system never executes arbitrary code from LLM output. Only validated schema edits are applied.

## Installation

```bash
pip install pyglove pydantic openai python-dotenv
```

## Quick Start

```python
from instruction_sdk_compiler import CompilerClient

# Create compiler client
c = CompilerClient(project_dir="out_project")

# Ingest instructions
c.ingest_instruction("Create a UserService with method create_user(email: str) -> User")
c.ingest_instruction("Modify UserService.create_user to also accept name: str")
c.ingest_instruction("Add InvoiceService with method create_invoice(user_id: str, amount: float) -> Invoice")

# Build generated SDK
build_result = c.build()  # emits to out_project/generated_sdk

# Use the generated SDK
from out_project.generated_sdk import Client
sdk = Client()
user = sdk.user_service.create_user(email="a@b.com", name="Ada")
```

## Usage API

### CompilerClient

The main interface for the compiler:

```python
c = CompilerClient(project_dir="out_project", llm_client=OpenAIClient())

# Ingest natural language instruction
receipt = c.ingest_instruction("Create a UserService class")

# Ingest pre-validated ChangeSet (bypasses LLM)
receipt = c.ingest_changeset(changeset, source_text="Optional instruction text")

# Get current specification
spec = c.current_spec()

# Get patch history
history = c.history()

# Build generated SDK
result = c.build(output_dir=None)  # Uses project_dir/generated_sdk by default

# Persistence
c.save()  # Save spec + patch log to disk
c.load()  # Load from disk

# Rollback
c.rollback(n=1)  # Rollback last n patches
```

## ChangeSet Schema

The LLM must output JSON matching this schema:

```json
{
  "changes": [
    {
      "kind": "ADD_CLASS",
      "class_name": "UserService",
      "doc": "optional description"
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
            "optional": false,
            "default": null,
            "description": "optional"
          }
        ]
      },
      "outputs": {
        "name": "User",
        "fields": [...]
      },
      "doc": "optional method description"
    },
    {
      "kind": "MODIFY_METHOD_SIGNATURE",
      "class_name": "UserService",
      "method_name": "create_user",
      "add_params": [...],
      "remove_params": [...],
      "change_return": {...},
      "doc_note": "optional note"
    },
    {
      "kind": "RENAME",
      "target_type": "class",
      "from": "OldName",
      "to": "NewName",
      "alias_old": true,
      "doc_note": "optional note"
    },
    {
      "kind": "DEPRECATE",
      "target_type": "method",
      "target": "UserService.old_method",
      "message": "optional deprecation message"
    }
  ]
}
```

## Repair Loop

If the LLM output fails validation:

1. Validation errors are extracted
2. A repair prompt is sent to the LLM with the errors and original instruction
3. The LLM attempts to fix the JSON
4. This repeats up to 2 times (configurable)
5. If still invalid after max attempts, a `ValueError` is raised

## In-Place Spec Mutation

The SDK specification is maintained as a single `SdkSpec` PyGlove object that is mutated in-place:

- Changes are applied using `spec.rebind({...})` for direct updates
- The same object ID is preserved (verified in tests)
- Patch history is maintained separately as a log of `PatchRecord` objects
- Rollback rebuilds the spec by replaying patches from an initial empty spec

## Docstring Evolution Policy

- **New classes/methods**: Use `doc` from ChangeSet if provided, else fallback description
- **Modifications**: Preserve existing `doc_summary` unless `replace_doc_summary=true`
- **Change notes**: Append `doc_note` to `doc_notes` list (bounded to last 10 entries)
- **Timestamps**: Doc notes include ISO timestamps
- **Generated code**: All classes and methods have Python docstrings with Args/Returns/Notes sections

## Generated SDK Structure

```
generated_sdk/
  __init__.py          # Exports Client
  client.py            # Client front door
  models.py            # Pydantic models for inputs/outputs
  registry.py          # Capability registry
  services/
    userservice.py     # One file per service class
    invoiceservice.py
  runtime/
    base.py            # BaseService
    registry.py        # CapabilityRegistry
```

### Client API

```python
from generated_sdk import Client

sdk = Client()

# Attribute access
user = sdk.user_service.create_user(email="test@example.com", name="Test")

# String dispatch
user = sdk.call("UserService.create_user", email="test@example.com", name="Test")

# List capabilities
caps = sdk.list_capabilities()  # ["UserService.create_user", ...]

# Describe capability
desc = sdk.describe("UserService.create_user")
```

## Storage and Replay

The compiler persists:

- `spec.json` - Serialized PyGlove spec
- `patch_log.json` - List of PatchRecord objects

You can:

- **Save/Load**: `c.save()` and `c.load()` persist/restore state
- **Replay**: Rebuild spec from initial state + patch log
- **Rollback**: `c.rollback(n)` replays patches up to `len(log) - n`

## Examples

See `examples/` directory:

- `demo_end_to_end.py` - Full pipeline demo
- `demo_use_generated_sdk.py` - Using generated SDK

## Tests

Run tests:

```bash
python -m pytest instruction_sdk_compiler/tests/
```

Test coverage:

- `test_llm_to_changeset.py` - ChangeSet validation
- `test_repair_loop.py` - Repair loop behavior
- `test_patching_in_place.py` - In-place mutation verification
- `test_codegen_import.py` - Generated code importability
- `test_generated_client_calls.py` - Client method calls, aliases, deprecation

## Requirements

- Python 3.8+
- pyglove
- pydantic
- openai (for LLM client)
- python-dotenv (for environment variables)

## License

MIT
