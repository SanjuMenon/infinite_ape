# Agents Implementation Documentation

This document records the implementation details of the summarization agents used in the map-reduce pipeline.

## Overview

The map-reduce module uses two types of summarization agents:
1. **Freeform Agent** - Produces narrative text summaries
2. **Table Agent** - Produces markdown table summaries

Both agents support:
- LLM-powered summarization (OpenAI or Azure OpenAI)
- Deterministic fallback when LLM is unavailable
- Automatic provider detection (Azure OpenAI or OpenAI)

## Agent Selection

Agent selection is determined by the `format` field in each bundle:
- `format: "freeform"` → Uses `summarize_freeform()`
- `format: "table"` → Uses `summarize_table()`
- Default: `"freeform"` if `format` is not specified

**Location:** `graph.py` line 93-96

```python
if bundle.format == "table":
    text = summarize_table(bundle)
else:
    text = summarize_freeform(bundle)
```

## Data Source

**All agents always use `most_current_data` for LLM summarization.**

- `most_current_data` is a **required field** in the Bundle schema
- When LLM is available, only `bundle.most_current_data` is sent to the LLM
- This ensures metadata fields (like `format_validated`, `length_validated`) are excluded from summarization

**Location:** `agents.py` lines 57 and 145

```python
# Freeform agent
bundle_json = _as_compact_json(bundle.most_current_data)

# Table agent  
bundle_json = _as_compact_json(bundle.most_current_data)
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

**Location:** `graph.py` lines 87-97

## Parallel Execution

Agents are executed in parallel via LangGraph's `Send` API:

1. `_dispatch_node` creates one `Send` per bundle
2. Each `Send` triggers `_summarize_one_node` with a different bundle
3. All agents run concurrently
4. Results are automatically merged into the `partials` list

**Location:** `graph.py` lines 80-84 and 121

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
- `format: Literal["freeform", "table"]` - Defaults to "freeform"
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
