# SGI (Semantic Grounding Index)

A Python implementation of the SGI (Semantic Grounding Index) metric for evaluating RAG-style systems. SGI measures how well a generated response is grounded in retrieved context versus how aligned it is with the user's question.

## Reference

This implementation is based on the paper:

**Marín, J. (2025). Semantic Grounding Index: Geometric Bounds on Context Engagement in RAG Systems. arXiv preprint arXiv:2512.13771.**

[arXiv:2512.13771](https://arxiv.org/abs/2512.13771)

## Intuition

SGI is a geometry-based metric that compares angular distances on a unit hypersphere:

- **High SGI** (large value): The response is strongly grounded in the retrieved context. The response is "closer" to the context than to the question.

- **Low SGI** (small value): The response is more aligned with the question than the context, indicating weak grounding.

SGI uses **angular distance** (arccos of cosine similarity) rather than raw cosine similarity, ensuring the ratio is in consistent "angle units."

## Formula

Given:
- `q`: question string
- `c`: context string (retrieved evidence)
- `r`: response string (model output)

1. Embed each string: `qv = φ(q)`, `cv = φ(c)`, `rv = φ(r)`
2. L2-normalize each embedding to unit length
3. Compute angular distances:
   - `θ(r,q) = arccos(clip(rv · qv, -1, 1))`
   - `θ(r,c) = arccos(clip(rv · cv, -1, 1))`
4. Compute SGI:
   ```
   SGI = θ(r,q) / (θ(r,c) + ε)
   ```
   where `ε = 1e-8` to avoid division by zero.

## Algorithm Steps

1. **Embedding**: Each string (q, c, r) is embedded using the same embedding model
2. **Normalization**: All embeddings are L2-normalized to unit vectors on a hypersphere
3. **Angular Distance**: Compute `arccos(clip(dot_product, -1, 1))` for each pair
4. **SGI Ratio**: Divide `θ(r,q)` by `(θ(r,c) + ε)`

## Installation

### Prerequisites

- Python 3.11 or higher

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the package in editable mode (optional, for development):
   ```bash
   pip install -e .
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your Azure OpenAI credentials
   ```

   Required environment variables:
   - `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/)
   
   Optional environment variables:
   - `AZURE_OPENAI_DEPLOYMENT_NAME`: Deployment name (default: text-embedding-3-small)
   - `AZURE_OPENAI_API_VERSION`: API version (default: 2024-02-15-preview)

   Or set the environment variables directly:
   ```bash
   export AZURE_OPENAI_API_KEY="your-api-key-here"
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   # On Windows: set AZURE_OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Command Line

First, ensure the package is installed or add the sgi directory to your Python path.

Compute SGI for a question, context, and response:

```bash
python -m sgi.cli compute --q "What is machine learning?" --c "Machine learning is a subset of AI..." --r "Machine learning is a method of data analysis..."
```

You can optionally specify a different deployment:
```bash
python -m sgi.cli compute --q "..." --c "..." --r "..." --deployment "your-deployment-name"
```

Output (default):
```
SGI=1.234567  theta_rq=0.456789  theta_rc=0.370123
```

Output as JSON:
```bash
python -m sgi.cli compute --q "What is machine learning?" --c "Machine learning is a subset of AI..." --r "Machine learning is a method of data analysis..." --json
```

```json
{
  "theta_rq": 0.456789,
  "theta_rc": 0.370123,
  "sgi": 1.234567
}
```

### Python API

```python
from sgi.core import sgi
from sgi.openai_embedder import AzureOpenAIEmbedder

embedder = AzureOpenAIEmbedder()
result = sgi(
    q="What is machine learning?",
    c="Machine learning is a subset of AI...",
    r="Machine learning is a method of data analysis...",
    embedder=embedder
)

print(f"SGI: {result['sgi']}")
print(f"θ(r,q): {result['theta_rq']}")
print(f"θ(r,c): {result['theta_rc']}")
```

## Numerical Stability

The implementation includes several numerical stability measures:

1. **Clipping**: Dot products are clipped to `[-1, 1]` before `arccos` to handle floating-point errors that might push values slightly outside this range.

2. **Epsilon in denominator**: A small constant (`ε = 1e-8`) is added to `θ(r,c)` to prevent division by zero when the response and context are nearly identical.

3. **Normalization safety**: A tiny constant (`1e-12`) is added to the norm denominator during L2 normalization, while still detecting true zero vectors.

## Testing

Install pytest:
```bash
pip install pytest
```

Run tests (no OpenAI API calls required):
```bash
pytest tests/
```

Tests use a `DummyEmbedder` that generates deterministic embeddings based on input text hashes, so no network calls are made.

## Project Structure

```
sgi/
  __init__.py          # Package initialization
  core.py              # Core SGI computation functions
  openai_embedder.py   # OpenAI embedding backend
  cli.py               # Command-line interface
  requirements.txt     # Python dependencies
  README.md            # This file
  .env.example         # Environment variable template

tests/
  test_core.py         # Tests for core functions
  test_cli.py          # Tests for CLI
```

## References

This implementation follows the SGI metric definition from the paper:

**Marín, J. (2025). Semantic Grounding Index: Geometric Bounds on Context Engagement in RAG Systems. arXiv preprint arXiv:2512.13771.**

- [arXiv:2512.13771](https://arxiv.org/abs/2512.13771)

See the paper for theoretical details, geometric foundations, and evaluation methodology.

## License

This implementation follows the SGI metric definition from the referenced paper.

