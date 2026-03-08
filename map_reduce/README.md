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
- ✅ **Flexible Schemas**: Configurable bundle types and output report structure via `bundle_config.yaml`
- ✅ **Agent Selection**: Automatic selection between freeform and table-based summarization
- ✅ **Evaluation**: Sequential LLM-based evaluation of summaries and overall report (optional)
- ✅ **Integration**: Direct integration with `declarative_fsm` module for end-to-end pipeline

## Installation

```bash
pip install -r map_reduce/requirements.txt
```

### Dependencies

- `langgraph>=0.2.0` - Graph-based workflow orchestration
- `pydantic>=2.0.0` - Data validation and schemas
- `openai>=1.35.0` - OpenAI/Azure OpenAI client (optional, for LLM features)
- `python-dotenv>=1.0.0` - Environment variable management (optional)
- `pyyaml>=6.0.0` - YAML configuration file support

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

**Note:** The demo automatically runs `declarative_fsm.demo.main()` to generate bundles, then processes them through the map-reduce pipeline.

## Architecture

### Execution Flow

```
Declarative FSM (optional)
    ↓
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
[evaluate] (conditional) → Evaluate summaries and report (if eval_type/metrics present)
    ├─ Step 1: Evaluate individual summaries
    ├─ Step 2: Evaluate overall report
    └─ Step 3: Regenerate report with scores
    ↓
Output Report (with evaluation scores if applicable)

















```

### Key Components

#### 1. **Graph** (`graph.py`)
- `build_map_reduce_graph()`: Creates the LangGraph pipeline
- Uses `Send` API for parallel fan-out
- Automatic result merging with `operator.add`

#### 2. **Agents** (`agents.py`)
- `summarize_freeform()`: Freeform text summarization
- `summarize_table()`: Table-based summarization (markdown)
- Auto-selects based on `bundle.format` field
- LLM-powered with deterministic fallback

#### 3. **LLM Client** (`llm_client.py`)
- Auto-detects provider (Azure OpenAI or OpenAI)
- Lazy initialization
- Graceful fallback when credentials unavailable

#### 4. **Schemas** (`schemas.py`)
- `Bundle`: Input data structure
- `OutputSchema`: Report structure definition
- `BundleConfig`: Bundle ordering and section configuration
- `BundleTypeConfig`: Individual bundle configuration (field_name, section_title, order, display_name)

#### 5. **Evaluator** (`evaluator.py`)
- `evaluate_summary()`: Evaluates individual summaries against metrics
- `evaluate_report()`: Evaluates overall report quality
- LLM-powered scoring (0-10 scale)
- Sequential execution after map-reduce completes

#### 6. **Config** (`config.py`)
- `load_bundle_config()`: Loads bundle configuration from YAML or JSON
- `load_output_schema()`: Loads output schema from JSON

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
        field_name="collateral",
        format="table",
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
- `field_name`: Used for matching bundles to configuration (e.g., "collateral", "financials_debt")
- `format`: Either `"freeform"` or `"table"` (selects summarizer type). **Required field.**
- `most_current_data`: **Required** dictionary containing the data to be summarized by the LLM.

Optional fields:
- `eval_type`: Optional string (e.g., "llm") - triggers evaluation if not None
- `metrics`: Optional list of metric names (e.g., ["readability", "completeness"]) - used for evaluation
- Additional fields: Flexible payload (e.g., `field_data`, `canonical_data`, etc.)

Example:
```json
{
  "field_name": "collateral",
  "format": "table",
  "most_current_data": {
    "canonical_value_type": "Real Estate Property",
    "canonical_amount": "2500000"
  },
  "eval_type": "llm",
  "metrics": [
    "score how readable it is",
    "score how complete the information is",
    "score how accurate the data appears"
  ]
}
```

**Note:** The `most_current_data` field is always used for LLM summarization (both freeform and table modes). This ensures the LLM only processes the current data and excludes metadata fields.

### Bundle Configuration (`bundle_config.yaml`)

The `bundle_config.yaml` file defines the ordering and section grouping of bundles in the final report:

```yaml
bundle_order:
  - field_name: collateral
    section_title: Collateral
    order: 0
  - field_name: real estate assets
    section_title: Real Estate Assets
    order: 1
  - field_name: Financials
    section_title: Financials
    order: 2
  - field_name: financials_debt
    section_title: Financials
    order: 3
    display_name: Financials_Debt
```

**Fields:**
- `field_name`: Must match the `field_name` in the bundle (used for matching)
- `section_title`: Section heading under which this bundle appears (e.g., "Financials")
- `order`: Numeric order within the section (0 = first)
- `display_name`: Optional display name for the report heading (defaults to `field_name`)

Bundles with the same `section_title` are grouped together. The `order` field determines the sequence within each section.

### Output Schema (`output_schema.json`)

The `output_schema.json` defines the report title (section structure is now handled by `bundle_config.yaml`):

```json
{
  "title": "Bundle Report",
  "sections": []
}
```

**Note:** The `sections` field in `output_schema.json` is currently not used. Section structure and ordering are defined in `bundle_config.yaml`.

## API Reference

### Main Functions

#### `build_map_reduce_graph() -> CompiledGraph`
Builds and compiles the LangGraph map-reduce pipeline.

**Returns:** Compiled graph ready for execution

**Input State:**
- `bundles: List[Bundle]` - Input bundles to process
- `bundle_config: BundleConfig` - Bundle ordering and section configuration
- `output_schema: OutputSchema` - Report title definition

**Output State:**
- `report: str` - Final aggregated report (with evaluation scores if applicable)
- `evaluation_scores: Dict[str, Any]` - Evaluation scores (if evaluation was performed)
  - `summary_scores`: Dict mapping field_name to metric scores
  - `report_scores`: Dict mapping metric to overall report score

#### `load_output_schema(path: Path) -> OutputSchema`
Loads output schema from JSON file.

#### `load_bundle_config(path: Path) -> BundleConfig`
Loads bundle configuration from YAML or JSON file (auto-detects by file extension).

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
5. **Evaluate Node** (conditional): Runs sequentially after reduce if bundles have `eval_type` and `metrics`

See `graph.py` for the implementation.

## Evaluation

The map-reduce pipeline supports optional LLM-based evaluation of summaries and the overall report.

### How Evaluation Works

1. **Automatic Trigger**: Evaluation runs if any bundle has `eval_type` and `metrics` fields (both not None)
2. **Sequential Execution**: Evaluation runs **after** the map-reduce completes (not in parallel)
3. **Two-Step Process**:
   - **Step 1**: Evaluate individual summaries for bundles that have `eval_type`/`metrics`
   - **Step 2**: Evaluate the overall aggregated report
4. **Score Integration**: Evaluation scores are automatically included in the final report

### Evaluation Scores

Scores are displayed in the report:
- **Individual Summary Scores**: Shown under each bundle section
  - Overall score (average of all metrics)
  - Detailed scores per metric
- **Overall Report Score**: Shown at the end of the report

Example:
```
### collateral

[summary content]

**Evaluation Score: 7.0/10**
*Detailed: score how readable it is: 7.0/10, score how complete the information is: 6.0/10, score how accurate the data appears: 8.0/10*
```

### Evaluation Metrics

Metrics are defined per bundle in the `metrics` field:
```json
{
  "field_name": "collateral",
  "eval_type": "llm",
  "metrics": [
    "score how readable it is",
    "score how complete the information is",
    "score how accurate the data appears"
  ]
}
```

Each metric is scored on a 0-10 scale by the LLM.

## Examples

### Example 1: Using with Declarative FSM (Recommended)

The demo automatically integrates with `declarative_fsm`:

```python
from declarative_fsm import demo as fsm_demo
from map_reduce import build_map_reduce_graph, load_bundle_config, load_output_schema
from map_reduce.schemas import Bundle

# Step 1: Run declarative_fsm to generate bundles
most_current_data_list = fsm_demo.main()

# Step 2: Convert to Bundle objects and run map-reduce
bundle_config = load_bundle_config("bundle_config.yaml")
output_schema = load_output_schema("output_schema.json")
bundles = [Bundle.model_validate(item) for item in most_current_data_list]

# Step 3: Execute map-reduce pipeline
graph = build_map_reduce_graph()
result = graph.invoke({
    "bundles": bundles,
    "bundle_config": bundle_config,
    "output_schema": output_schema
})
print(result["report"])
```

### Example 2: Processing Bundles Directly

```python
import json
from pathlib import Path
from map_reduce import build_map_reduce_graph, load_bundle_config, load_output_schema
from map_reduce.schemas import Bundle

# Load configuration
here = Path(__file__).parent
bundle_config = load_bundle_config(here / "bundle_config.yaml")
output_schema = load_output_schema(here / "output_schema.json")

# Load bundles
bundles_raw = json.loads((here / "sample_bundles.json").read_text())
bundles = [Bundle.model_validate(b) for b in bundles_raw]

# Execute
graph = build_map_reduce_graph()
result = graph.invoke({
    "bundles": bundles,
    "bundle_config": bundle_config,
    "output_schema": output_schema
})
print(result["report"])
```

### Example 3: Custom Bundle Processing

```python
from map_reduce import build_map_reduce_graph, load_bundle_config
from map_reduce.schemas import Bundle, BundleConfig, BundleTypeConfig, OutputSchema

bundles = [
    Bundle(
        field_name="custom_data",
        format="freeform",
        most_current_data={"key1": "value1", "key2": "value2"}
    )
]

# Create bundle config
bundle_config = BundleConfig(
    bundle_order=[
        BundleTypeConfig(
            field_name="custom_data",
            section_title="Custom Section",
            order=0
        )
    ]
)

output_schema = OutputSchema(title="Custom Report")

graph = build_map_reduce_graph()
result = graph.invoke({
    "bundles": bundles,
    "bundle_config": bundle_config,
    "output_schema": output_schema
})
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
