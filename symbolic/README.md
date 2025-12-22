# Agentica Sample Program

This folder contains a sample program demonstrating the [Agentica Python SDK](https://github.com/symbolica-ai/agentica-python-sdk).

## What is Agentica?

Agentica is a type-safe AI framework that lets LLM agents integrate with your code—functions, classes, live objects, even entire SDKs. Instead of building MCP wrappers or brittle schemas, you pass references directly; the framework enforces your types at runtime, constrains return types, and manages agent lifecycle.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your API key:**
   - Create a `.env` file in this directory
   - Add your Agentica API key:
     ```
     AGENTICA_API_KEY=your_actual_api_key_here
     ```
   - You can use `env.example` as a template

3. **Get your API key:**
   - Visit [docs.symbolica.ai](https://docs.symbolica.ai) to get your API key

## Running the Sample

```bash
python sample_agentica.py
```

## Example Usage

The sample program demonstrates three use cases:

1. **Sentiment Analysis** - Classify text as positive, neutral, or negative
2. **Keyword Extraction** - Extract important keywords from text
3. **Text Summarization** - Generate concise summaries of longer text

## Requirements

- Python 3.12 or 3.13
- `uv` (recommended package manager)
- Agentica API key

## Documentation

Full documentation: https://docs.symbolica.ai

