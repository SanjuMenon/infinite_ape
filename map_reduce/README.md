# Map-Reduce with LangGraph

A LangGraph-based map-reduce implementation for processing structured data bundles in parallel and aggregating results into a structured report.

## Overview

This module implements a **map-reduce pattern** using LangGraph to:
1. **Map**: Split bundles into subtasks
2. **Process**: Execute summarization tasks in parallel (with LLM support)
3. **Reduce**: Aggregate results into a structured report based on a configurable output schema

## Features

- ✅ **Parallel Processing**: Automatic parallel execution of bundle summarization using LangGraph's `Send` API
- ✅ **LLM Support**: Works with OpenAI and Azure OpenAI (auto-detects provider)
- ✅ **Fallback Mode**: Deterministic summarization when LLM credentials are unavailable
- ✅ **Flexible Schemas**: Configurable bundle types and output report structure
- ✅ **Agent Selection**: Automatic selection between freeform and table-based summarization

## Installation

```bash
pip install -r map_reduce/requirements.txt
```

### Dependencies

- `langgraph>=0.2.0` - Graph-based workflow orchestration
- `pydantic>=2.0.0` - Data validation and schemas
- `openai>=1.35.0` - OpenAI/Azure OpenAI client (optional, for LLM features)
- `python-dotenv>=1.0.0` - Environment variable management (optional)

## Quick Start

### 1. Set up environment variables (optional, for LLM features)

**For OpenAI:**
```bash
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

**For Azure OpenAI:**
```bash
export AZURE_OPENAI_API_KEY=your_azure_key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_VERSION=2024-02-15-preview  # Optional
export AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment  # Optional, defaults to gpt-4o-mini
```

Or create a `.env` file in the `map_reduce/` directory:
```
OPENAI_API_KEY=your_key_here
```

### 2. Run the demo

```bash
python map_reduce/demo.py
```

## Architecture

### Execution Flow

```
Input Bundles
    ↓
[split] → Split bundles into subtasks
    ↓
[_dispatch_node] → Create Send() events for parallel execution
    ↓
[summarize_one] × N (parallel) → Process each bundle
    ├─ Instance 1: bundle1 → summary1
    ├─ Instance 2: bundle2 → summary2
    └─ Instance 3: bundle3 → summary3
    ↓
LangGraph automatically merges results
    ↓
[reduce] → Aggregate into final report
    ↓
Output Report
```

### Key Components

#### 1. **Graph** (`graph.py`)
- `build_map_reduce_graph()`: Creates the LangGraph pipeline
- Uses `Send` API for parallel fan-out
- Automatic result merging with `operator.add`

#### 2. **Agents** (`agents.py`)
- `summarize_freeform()`: Freeform text summarization
- `summarize_table()`: Table-based summarization (markdown)
- Auto-selects based on `bundle.value` field
- LLM-powered with deterministic fallback

#### 3. **LLM Client** (`llm_client.py`)
- Auto-detects provider (Azure OpenAI or OpenAI)
- Lazy initialization
- Graceful fallback when credentials unavailable

#### 4. **Schemas** (`schemas.py`)
- `Bundle`: Input data structure
- `OutputSchema`: Report structure definition
- `BundleConfig`: Bundle type configurations

## Usage

### Basic Usage

```python
from map_reduce import build_map_reduce_graph, load_output_schema
from map_reduce.schemas import Bundle

# Load configuration
output_schema = load_output_schema("output_schema.json")

# Prepare bundles
bundles = [
    Bundle(
        bundle_name="collateral",
        value="table",
        field_data={"value_type": "Sample", "amount": "1000"}
    ),
    # ... more bundles
]

# Build and run graph
graph = build_map_reduce_graph()
final_state = graph.invoke({
    "bundles": bundles,
    "output_schema": output_schema
})

print(final_state["report"])
```

### Bundle Structure

A bundle must have:
- `bundle_name`: Used for report headings (e.g., "collateral", "financials")
- `value`: Either `"freeform"` or `"table"` (selects summarizer type)
- Additional fields: Flexible payload (e.g., `field_data`, `canonical_data`, etc.)

Example:
```json
{
  "bundle_name": "collateral",
  "value": "table",
  "required_fields_found": ["value_type", "amount"],
  "field_data": {
    "value_type": "Sample value type",
    "amount": "Sample amount"
  },
  "format_validated": true,
  "length_validated": true
}
```

### Output Schema

The `output_schema.json` defines the structure and ordering of the final report:

```json
{
  "title": "Bundle Report",
  "sections": [
    {
      "name": "Financial Information",
      "bundle_names": ["financials", "collateral"],
      "subsections": []
    },
    {
      "name": "Assets",
      "bundle_names": ["real_estate_assets"],
      "subsections": []
    }
  ]
}
```

## Configuration Files

### `bundle_config.json`
Placeholder for future bundle-specific configurations (e.g., splitting rules).

### `output_schema.json`
Defines the final report structure:
- `title`: Report title
- `sections`: Ordered list of sections
  - `name`: Section heading
  - `bundle_names`: Which bundles appear in this section (in order)
  - `subsections`: Nested sections (optional)

## API Reference

### Main Functions

#### `build_map_reduce_graph() -> CompiledGraph`
Builds and compiles the LangGraph map-reduce pipeline.

**Returns:** Compiled graph ready for execution

**Input State:**
- `bundles: List[Bundle]` - Input bundles to process
- `output_schema: OutputSchema` - Report structure definition

**Output State:**
- `report: str` - Final aggregated report

#### `load_output_schema(path: Path) -> OutputSchema`
Loads output schema from JSON file.

#### `load_bundle_config(path: Path) -> BundleConfig`
Loads bundle configuration from JSON file.

### LLM Client Functions

#### `get_openai_client() -> Optional[Union[OpenAI, AzureOpenAI]]`
Returns the initialized LLM client (OpenAI or Azure OpenAI).

#### `is_llm_available() -> bool`
Checks if LLM credentials are available.

#### `get_provider() -> Optional[str]`
Returns the current provider: `"azure"` or `"openai"`.

#### `get_deployment_name() -> Optional[str]`
Returns Azure OpenAI deployment name if using Azure, else `None`.

## How Parallel Execution Works

The parallel execution is implemented using LangGraph's `Send` API:

1. **Dispatch Node** (`_dispatch_node`): Returns `List[Send]` - one `Send` per bundle
2. **Conditional Edge**: When a conditional edge function returns `List[Send]`, LangGraph executes all in parallel
3. **Automatic Merging**: Results are merged using `Annotated[List[Dict], operator.add]` in the state definition
4. **Reduce Node**: Receives all merged results and aggregates into final report

See `graph.py` lines 80-84 and 121 for the implementation.

## Examples

### Example 1: Processing Sample Bundles

```python
import json
from pathlib import Path
from map_reduce import build_map_reduce_graph, load_output_schema
from map_reduce.schemas import Bundle

# Load data
here = Path(__file__).parent
output_schema = load_output_schema(here / "output_schema.json")
bundles_raw = json.loads((here / "sample_bundles.json").read_text())
bundles = [Bundle.model_validate(b) for b in bundles_raw]

# Execute
graph = build_map_reduce_graph()
result = graph.invoke({"bundles": bundles, "output_schema": output_schema})
print(result["report"])
```

### Example 2: Custom Bundle Processing

```python
from map_reduce import build_map_reduce_graph
from map_reduce.schemas import Bundle, OutputSchema

bundles = [
    Bundle(
        bundle_name="custom_data",
        value="freeform",
        field_data={"key1": "value1", "key2": "value2"}
    )
]

output_schema = OutputSchema(
    title="Custom Report",
    sections=[
        {
            "name": "Data",
            "bundle_names": ["custom_data"],
            "subsections": []
        }
    ]
)

graph = build_map_reduce_graph()
result = graph.invoke({"bundles": bundles, "output_schema": output_schema})
```

## Error Handling

- **Missing LLM credentials**: Automatically falls back to deterministic summarization
- **API failures**: Catches exceptions and falls back to deterministic mode
- **Missing bundles**: Empty report is generated
- **Invalid schemas**: Pydantic validation errors are raised

## Extending the Module

### Adding Custom Splitting Logic

Modify `splitter.py`:
```python
def split_bundle(bundle: Bundle) -> List[Bundle]:
    # Your custom splitting logic here
    # Return list of sub-bundles
    pass
```

### Adding Custom Summarizers

Modify `agents.py` to add new summarization functions, then update `_summarize_one_node` in `graph.py` to use them.

### Custom Output Formats

Modify `_aggregate_report()` in `graph.py` to change how results are formatted.

## Requirements

- Python 3.9+ (3.10+ recommended)
- See `requirements.txt` for package dependencies

## License

Part of the `infinite_ape` repository.
