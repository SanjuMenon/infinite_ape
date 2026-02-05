# Quick Start Guide

## Step 1: Install Dependencies

**Option 1: Using requirements.txt (Recommended)**
```bash
cd tarpit_alignment
pip install -r requirements.txt
```

**Option 2: Manual installation**
```bash
cd tarpit_alignment
pip install pyglove pydantic openai python-dotenv
```

**Option 3: Install package in development mode**
```bash
cd tarpit_alignment/instruction_sdk_compiler
pip install -e .
```

## Step 2: Set Up OpenAI API Key

You need an OpenAI API key to use the LLM. Set it as an environment variable:

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your-api-key-here
```

Or create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

## Step 3: Run the Demo

From the `tarpit_alignment` directory:

```bash
python -m instruction_sdk_compiler.examples.demo_end_to_end
```

Or if you're in the `instruction_sdk_compiler` directory:

```bash
python examples/demo_end_to_end.py
```

## Step 4: Use the Generated SDK

After running the demo, you can use the generated SDK:

```python
import sys
from pathlib import Path

# Add the demo_output directory to Python path
sys.path.insert(0, str(Path("demo_output").absolute()))

from generated_sdk import Client

# Create client
sdk = Client()

# Use attribute access
user = sdk.user_service.create_user(email="test@example.com", name="Test User")

# List capabilities
print(sdk.list_capabilities())
```

## Basic Usage in Your Own Code

```python
from instruction_sdk_compiler import CompilerClient

# Create compiler
c = CompilerClient(project_dir="my_project")

# Add instructions
c.ingest_instruction("Create a UserService with method create_user(email: str) -> User")
c.ingest_instruction("Add InvoiceService with method create_invoice(user_id: str, amount: float) -> Invoice")

# Build the SDK
result = c.build()

if result.success:
    print(f"SDK generated to {result.output_dir}")
    
    # Use the generated SDK
    import sys
    sys.path.insert(0, result.output_dir)
    from generated_sdk import Client
    
    sdk = Client()
    user = sdk.user_service.create_user(email="a@b.com")
```

## Running Tests

```bash
# Install pytest if needed
pip install pytest

# Run tests
python -m pytest instruction_sdk_compiler/tests/
```

## Troubleshooting

1. **Import errors**: Make sure you're running from the correct directory and the package is in your Python path
2. **API key errors**: Verify your OPENAI_API_KEY is set correctly
3. **Module not found**: Install dependencies with `pip install pyglove pydantic openai python-dotenv`
