# Agents Implementation Documentation

This document records the implementation details of the summarization agents used in the map-reduce pipeline.

## Overview

The map-reduce module uses three types of summarization agents:
1. **Freeform Agent** - Produces narrative text summaries (LLM-powered)
2. **Table Agent** - Produces markdown table summaries (LLM-powered with deterministic fallback)
3. **Template Fill Agent** - Produces structured text summaries (deterministic, no LLM required)

Freeform and Table agents support:
- LLM-powered summarization (OpenAI or Azure OpenAI)
- Deterministic fallback when LLM is unavailable
- Automatic provider detection (Azure OpenAI or OpenAI)

Template Fill agent:
- Deterministic template-based formatting (no LLM required)
- Always available regardless of LLM configuration

## Agent Selection

Agent selection is determined by the `format` field in each bundle:
- `format: "freeform"` → Uses `summarize_freeform()`
- `format: "table"` → Uses `summarize_table()`
- `format: "fill_template"` → Uses `summarize_template_fill()`
- Default: `"freeform"` if `format` is not specified

**Location:** `graph.py` lines 188-194

```python
if bundle.format == "table":
    text = summarize_table(bundle)
elif bundle.format == "fill_template":
    text = summarize_template_fill(bundle)
else:
    text = summarize_freeform(bundle)
```

## Data Source

**All agents always use `most_current_data` for summarization.**

- `most_current_data` is a **required field** in the Bundle schema
- When LLM is available, only `bundle.most_current_data` is sent to the LLM
- Template Fill agent also uses `bundle.most_current_data` for consistency
- This ensures metadata fields (like `format_validated`, `length_validated`) are excluded from summarization

**Location:** `agents.py` lines 47, 157, and 23

```python
# Freeform agent
bundle_json = _as_compact_json(bundle.most_current_data)

# Table agent  
bundle_json = _as_compact_json(bundle.most_current_data)

# Template Fill agent
if bundle.most_current_data:
    # Uses most_current_data directly
```

## Freeform Agent (`summarize_freeform`)

### LLM Mode (when API key available)

**Function:** `summarize_freeform(bundle: Bundle) -> str`

**Behavior:**
1. Checks if LLM client is available
2. If available, sends `bundle.most_current_data` to LLM with a freeform summarization prompt
3. Returns LLM-generated narrative summary
4. Falls back to deterministic mode on any error

**Prompt Structure:**
```
Summarize the following bundle data in a clear, freeform narrative format.
Focus on the key information and provide context about what this bundle represents.

Bundle Name: {bundle.field_name}
Bundle Data:
{JSON of most_current_data}

Provide a concise, readable summary that highlights the important fields and their values.
```

**LLM Parameters:**
- Model: `gpt-4o-mini` (configurable via `OPENAI_MODEL` or `AZURE_OPENAI_DEPLOYMENT_NAME`)
- Temperature: `0.3` (for consistent output)
- Max Tokens: `500`

**Location:** `agents.py` lines 49-95

### Deterministic Fallback Mode

**Function:** `_summarize_freeform_deterministic(bundle: Bundle) -> str`

**Behavior:**
1. Creates a structured text summary with:
   - Bundle name as heading
   - List of required fields found
   - Field data as nested list
   - Validation metadata (format_validated, length_validated, etc.)
2. Falls back to showing entire payload if no structured data available

**Output Format:**
```
Bundle: {field_name}
- required_fields_found: field1, field2
- field_data:
  - key1: value1
  - key2: value2
- checks: format_validated=true, length_validated=true
```

**Location:** `agents.py` lines 30-46

## Table Agent (`summarize_table`)

### LLM Mode (when API key available)

**Function:** `summarize_table(bundle: Bundle) -> str`

**Behavior:**
1. Checks if LLM client is available
2. If available, sends `bundle.most_current_data` to LLM with a table formatting prompt
3. Returns LLM-generated markdown table
4. Falls back to deterministic mode on any error

**Prompt Structure:**
```
Summarize the following bundle data as a well-formatted markdown table.
The table should have clear column headers and organize the key information from the bundle.

Bundle Name: {bundle.field_name}
Bundle Data:
{JSON of most_current_data}

Create a markdown table that presents the important fields and their values in a structured, readable format.
Use appropriate column headers based on the data structure.
```

**LLM Parameters:**
- Model: `gpt-4o-mini` (configurable via `OPENAI_MODEL` or `AZURE_OPENAI_DEPLOYMENT_NAME`)
- Temperature: `0.2` (lower for more structured output)
- Max Tokens: `500`

**Location:** `agents.py` lines 137-187

### Deterministic Fallback Mode

**Function:** `_summarize_table_deterministic(bundle: Bundle) -> str`

**Behavior:**
1. Priority order for data source:
   - **Primary:** `field_data` → 2-column table (key | value)
   - **Secondary:** `canonical_data` → 2-column table (key | value)
   - **Fallback:** Entire bundle → 2-column table of all top-level keys
2. Uses `_markdown_table()` helper to format as markdown

**Output Format:**
```
Bundle: {field_name}

| key | value |
|---|---|
| field1 | value1 |
| field2 | value2 |
```

**Location:** `agents.py` lines 117-135

## Template Fill Agent (`summarize_template_fill`)

The Template Fill agent provides deterministic, template-based summarization without requiring an LLM.

**Function:** `summarize_template_fill(bundle: Bundle) -> str`

**Behavior:**
1. Always uses `most_current_data` for consistency with other agents
2. Formats data as a structured list with indentation
3. No LLM required - always deterministic
4. Fallback to entire bundle if `most_current_data` is empty

**Output Format:**
```
- data:
  - field1: value1
  - field2: value2
  - field3: value3
```

**Use Cases:**
- When LLM is unavailable or not desired
- When structured, deterministic output is preferred
- For debugging or testing scenarios
- When cost or latency is a concern

**Advantages:**
- Always available (no API dependencies)
- Fast and predictable
- No API costs
- Consistent formatting

**Limitations:**
- Less flexible than LLM-powered agents
- No natural language generation
- Simple key-value formatting only

**Location:** `agents.py` lines 15-32

**Example:**
```python
bundle = Bundle(
    field_name="example",
    format="fill_template",
    most_current_data={"key1": "value1", "key2": "value2"}
)
summary = summarize_template_fill(bundle)
# Returns:
# "- data:\n  - key1: value1\n  - key2: value2"
```

## Helper Functions

### `_markdown_table(rows, columns)`

Creates a markdown table from a list of dictionaries.

**Parameters:**
- `rows: List[Dict[str, Any]]` - Data rows
- `columns: Optional[List[str]]` - Column names (auto-detected if None)

**Returns:** Markdown table string

**Location:** `agents.py` lines 100-114

### `_as_compact_json(obj)`

Converts Python object to compact JSON string.

**Returns:** JSON string with 2-space indentation

**Location:** `agents.py` line 11-12

## LLM Client Integration

### Provider Detection

The agents use `llm_client.py` for LLM access:

- `get_openai_client()` - Returns OpenAI or AzureOpenAI client
- `get_provider()` - Returns "azure" or "openai"
- `get_deployment_name()` - Returns Azure deployment name if using Azure
- `is_llm_available()` - Checks if credentials are available

**Auto-detection priority:**
1. Azure OpenAI (if `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` are set)
2. OpenAI (if `OPENAI_API_KEY` is set)

### Model/Deployment Selection

**For Azure OpenAI:**
- Uses `AZURE_OPENAI_DEPLOYMENT_NAME` environment variable
- Defaults to `"gpt-4o-mini"` if not specified

**For OpenAI:**
- Uses `OPENAI_MODEL` environment variable
- Defaults to `"gpt-4o-mini"` if not specified

**Location:** `agents.py` lines 70-74 and 160-164

## Error Handling

Both agents implement consistent error handling:

1. **No LLM credentials:** Automatically falls back to deterministic mode
2. **API call failure:** Catches exception and falls back to deterministic mode
3. **Empty LLM response:** Falls back to deterministic mode
4. **Any other error:** Catches exception and falls back to deterministic mode

This ensures the pipeline always produces output, even when LLM is unavailable or fails.

**Location:** `agents.py` lines 93-95 and 185-187

## State Management

### Input State

Each agent receives a `SummarizeOneState` containing:
```python
class SummarizeOneState(TypedDict):
    bundle: Bundle
```

### Output State

Each agent returns:
```python
{
    "partials": [
        {
            "field_name": str,
            "text": str  # The summary text
        }
    ]
}
```

The `partials` list is automatically merged across parallel executions using `operator.add` in the graph state.

**Location:** `graph.py` lines 188-196

### Final Report State

The final report in `MapReduceState` is a `CreditSummaryGenAIResponse` Pydantic model:

```python
class MapReduceState(TypedDict, total=False):
    bundles: List[Bundle]
    bundle_config: BundleConfig
    output_schema: OutputSchema
    metadata: Optional[Dict[str, Any]]  # From sample_data.json
    
    # populated during execution
    subtasks: List[Bundle]
    partials: Annotated[List[Dict[str, str]], operator.add]
    report: CreditSummaryGenAIResponse  # Pydantic model (not string)
    evaluation_scores: Dict[str, Any]
```

**Location:** `graph.py` lines 16-35

## Parallel Execution

Agents are executed in parallel via LangGraph's `Send` API:

1. `_dispatch_node` creates one `Send` per bundle
2. Each `Send` triggers `_summarize_one_node` with a different bundle
3. All agents run concurrently
4. Results are automatically merged into the `partials` list

**Location:** `graph.py` lines 80-84 and 121

## Report Structure (Pydantic Model)

The final report is now structured as a Pydantic model (`CreditSummaryGenAIResponse`) instead of a plain markdown string. This provides:

- **Structured, validated output** - Type-safe report structure
- **Easy JSON serialization** - Can export to JSON via `model_dump(by_alias=True)`
- **Flexible rendering** - Can render to markdown, HTML, or other formats
- **Metadata integration** - Includes request metadata, evaluation scores, and debug information

### Report Aggregation Strategy (Option B)

Bundles are grouped by `section_title` from `bundle_config.yaml`:

- **One `SummarySection` per `section_title`** - Groups bundles that share the same section title
- **Each bundle becomes a `SummarySubSection`** - Individual bundles appear as subsections within their section
- **Ordering preserved** - Bundles maintain their order within each section based on `bundle_config.yaml`

**Example Structure:**
```
SummarySection (heading: "Financials")
  ├─ SummarySubSection (identifier: "Financials", heading: "Financials")
  └─ SummarySubSection (identifier: "financials_debt", heading: "Financials_Debt")
```

**Location:** `graph.py` lines 54-220 (`_aggregate_report_pydantic`)

### Content Format Mapping

Bundle formats are mapped to content format strings:

- `format: "table"` → `content_format: "MD"` (Markdown)
- `format: "freeform"` → `content_format: "TEXT"` (Plain text)
- `format: "fill_template"` → `content_format: "TEXT"` (Plain text)

**Location:** `graph.py` lines 47-51 (`_determine_content_format`)

### Metadata Flow

Metadata flows from `sample_data.json` (top-level fields) through the pipeline:

1. **Source:** Top-level fields in `declarative_fsm/sample_data.json`:
   - `requestId` - Request identifier
   - `language` - Report language (default: "en")
   - `generatedBy` - System/user that generated the report (default: "map_reduce")
   - `generatedAt` - Timestamp (auto-generated if not provided)

2. **Extraction:** `declarative_fsm/demo.py` extracts metadata from parsed `SampleData` model

3. **Flow:** Metadata passed to `MapReduceState` and used in `_aggregate_report_pydantic()`

4. **Usage:** Included in `CreditSummaryGenAIResponse.summary_meta_data` and top-level fields

**Location:** 
- `declarative_fsm/models.py` - `SampleData` model with metadata fields
- `declarative_fsm/demo.py` - Metadata extraction
- `map_reduce/graph.py` - Metadata usage in report generation

### Report Renderer

A renderer function (`render_to_markdown()`) converts the Pydantic model to markdown for backward compatibility:

**Function:** `render_to_markdown(response: CreditSummaryGenAIResponse) -> str`

**Behavior:**
- Converts `CreditSummaryGenAIResponse` to markdown string
- Preserves section hierarchy and formatting
- Includes evaluation scores and metadata
- Used by `run_summarizer.py` for console output

**Usage:**
```python
from map_reduce import build_map_reduce_graph, render_to_markdown

graph = build_map_reduce_graph()
result = graph.invoke({...})
report = result["report"]  # CreditSummaryGenAIResponse

# Render to markdown
markdown = render_to_markdown(report)
print(markdown)

# Or serialize to JSON
json_output = report.model_dump(by_alias=True)
```

**Location:** `graph.py` lines 222-250

### Report Schema

The report structure follows the `CreditSummaryGenAIResponse` schema:

```python
CreditSummaryGenAIResponse
├─ schema_ ($schema) - JSON schema reference
├─ id_ ($id) - Schema identifier
├─ request_id (requestId) - From metadata
├─ language - From metadata
├─ generated_by (generatedBy) - From metadata
├─ generated_at (generatedAt) - From metadata
├─ summary_sections - List[SummarySection]
│   └─ SummarySection
│       ├─ identifier - Section identifier (from section_title)
│       ├─ heading - Section title
│       ├─ sub_heading - Optional subsection heading
│       ├─ content - Section-level content (usually empty)
│       ├─ content_format - "TEXT" or "MD"
│       └─ summary_sub_sections - List[SummarySubSection]
│           └─ SummarySubSection
│               ├─ identifier - Bundle field_name
│               ├─ heading - Display name or field_name
│               ├─ content_format - "TEXT" or "MD"
│               └─ content - Summary text (with evaluation scores if available)
└─ summary_meta_data
    ├─ overall_evaluation_report
    │   ├─ content - Overall evaluation text
    │   └─ content_format - "TEXT"
    └─ debug_log - LLM availability and other debug information
```

**Location:** `report_schemas.py`

### Evaluation Scores Integration

Evaluation scores are integrated into the report structure:

- **Individual summary scores:** Added to each `SummarySubSection.content` as markdown text
- **Overall report scores:** Included in `summary_meta_data.overall_evaluation_report.content`
- **Format:** Scores displayed as "Evaluation Score: X.X/10" with detailed breakdown

**Location:** `graph.py` lines 129-137, 178-185

## Configuration

### Environment Variables

**OpenAI:**
- `OPENAI_API_KEY` - Required for OpenAI
- `OPENAI_MODEL` - Optional, defaults to "gpt-4o-mini"

**Azure OpenAI:**
- `AZURE_OPENAI_API_KEY` - Required for Azure
- `AZURE_OPENAI_ENDPOINT` - Required for Azure
- `AZURE_OPENAI_API_VERSION` - Optional, defaults to "2024-02-15-preview"
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Optional, defaults to "gpt-4o-mini"

### Bundle Schema Requirements

**Required fields:**
- `field_name: str` - Used for report headings
- `most_current_data: Dict[str, Any]` - Always used for LLM summarization

**Optional fields:**
- `format: Literal["freeform", "table", "fill_template"]` - Defaults to "freeform"
- `field_data: Dict[str, Any]` - Used by deterministic table fallback
- `canonical_data: Dict[str, Any]` - Used by deterministic table fallback
- Other metadata fields (format_validated, length_validated, etc.)

**Location:** `schemas.py` lines 11-37

## Testing Considerations

When testing agents:

1. **Without LLM credentials:** Agents will use deterministic fallback
2. **With LLM credentials:** Agents will call LLM API (ensure API key is set)
3. **Error scenarios:** Agents gracefully fall back to deterministic mode

To test LLM mode:
```bash
export OPENAI_API_KEY=your_key
# or
export AZURE_OPENAI_API_KEY=your_key
export AZURE_OPENAI_ENDPOINT=your_endpoint
```

## Future Enhancements

Potential improvements:
1. Configurable temperature per agent type
2. Configurable max_tokens per agent type
3. Support for other LLM providers (Anthropic, etc.)
4. Custom prompt templates per bundle type
5. Retry logic with exponential backoff for API failures
6. Streaming responses for long summaries
