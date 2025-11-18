# MERE: Minimal Evidence for Reproducibility

An implementation that determines which evidence items help improve **reproducibility of outcomes** in LLM responses. By systematically testing all combinations of available evidence, this tool identifies the minimal set of evidence that ensures consistent, reliable results while minimizing hallucination risk.

## Core Purpose

When working with language models, the choice of evidence provided can significantly impact the reproducibility and consistency of outputs. This tool addresses the critical question: **Which evidence items are essential for achieving reproducible outcomes?**

Through combinatorial testing of evidence subsets, MERE (Minimal Evidence for Reproducibility):
- Identifies evidence combinations that lead to consistent, reproducible results
- Minimizes hallucination risk by selecting evidence that the model can reliably use
- Determines the minimal evidence set needed for optimal reproducibility
- Provides quantitative metrics (RoH bounds, ISR, etc.) to assess evidence quality

## Attribution

**This implementation uses code co-opted from the [HallBayes](https://github.com/leochlon/hallbayes) package** by [leochlon](https://github.com/leochlon). The HallBayes code is located in the `credence/` directory of this repository and provides the core hallucination detection framework based on the EDFL (Expected Disagreement from First Look) methodology described in the paper ["Predictable Compression Failures: Why Language Models Actually Hallucinate"](https://arxiv.org/abs/2509.11208).

The HallBayes package is licensed under the MIT License. This implementation extends HallBayes functionality to optimize evidence selection for reproducibility through combinatorial testing.

## Overview

Given a prompt/question and a list of available evidence items, this tool:
1. Tests **all combinations** (not permutations) of evidence subsets
2. Evaluates each combination using HallBayes' EDFL framework to assess reproducibility and hallucination risk
3. Identifies the optimal evidence subset that maximizes outcome reproducibility while minimizing hallucination risk
4. Saves results to YAML files for easy inspection and reuse

## Features

- **Reproducibility Focus**: Identifies evidence that leads to consistent, reproducible LLM outcomes
- **Comprehensive Testing**: Tests all possible combinations of evidence subsets to find optimal configurations
- **Risk Assessment**: Uses HallBayes' EDFL framework to quantify hallucination risk for each evidence combination
- **Optimization Strategies**: Optimize for lowest hallucination risk (`roh_bound`) or prefer ANSWER decisions that indicate reliable outcomes
- **YAML-based**: Simple YAML format for input (evidence) and output (results)
- **Multiple Backends**: Supports OpenAI, Anthropic, Ollama, and other HallBayes backends
- **Minimal Set Preference**: Can prefer smaller evidence sets when metrics are equal, reducing complexity while maintaining reproducibility

## Installation

Ensure you have the required dependencies:

```bash
pip install pyyaml
```

You'll also need API keys for your chosen backend:
- **OpenAI**: Set `OPENAI_API_KEY` environment variable
- **Anthropic**: Set `ANTHROPIC_API_KEY` environment variable
- **Ollama**: Ensure Ollama is running locally

## Quick Start

### 1. Create an input YAML file

Create a file (e.g., `evidence_input.yaml`) with your prompt and evidence:

```yaml
prompt: "Who won the 2019 Nobel Prize in Physics?"

evidence:
  - "The 2019 Nobel Prize in Physics was awarded to James Peebles, Michel Mayor, and Didier Queloz"
  - "James Peebles received half the prize for theoretical discoveries in physical cosmology"
  - "Michel Mayor and Didier Queloz shared the other half for discovering an exoplanet"
  - "The prize was announced on October 8, 2019"
  - "The Nobel Prize in Physics is awarded by the Royal Swedish Academy of Sciences"
```

### 2. Run the optimizer

**Option A: Using the example script**
```bash
python example_optimize_evidence.py
```

**Option B: Using the command-line interface**
```bash
python evidence_optimizer.py --input evidence_input.yaml --output evidence_output.yaml
```

**Option C: Using Python directly**
```python
from evidence_optimizer import EvidenceOptimizer

# Create MERE optimizer
optimizer = EvidenceOptimizer(model="gpt-4o-mini")
prompt, evidence_list = optimizer.load_evidence_from_yaml("evidence_input.yaml")

result = optimizer.optimize(
    prompt=prompt,
    evidence_list=evidence_list,
    min_evidence=1,
    optimize_for="roh_bound",
)

optimizer.save_results_to_yaml(result, "evidence_output.yaml")
```

### 3. Check the results

The output YAML file will contain:
- The optimal evidence subset (indices and items)
- Metrics (RoH bound, decision, ISR, etc.)
- Evaluation configuration

## API Reference

### `EvidenceOptimizer`

Main class for the MERE (Minimal Evidence for Reproducibility) optimizer. This class handles the combinatorial testing and optimization of evidence subsets.

#### Initialization

```python
optimizer = EvidenceOptimizer(
    backend=None,              # Pre-configured backend (optional)
    model="gpt-4o-mini",      # Model name (if backend is None)
    temperature=0.3,          # LLM temperature
    n_samples=5,              # Samples per evaluation
    m=6,                      # Skeleton variants
    h_star=0.05,             # Target hallucination rate
    skeleton_policy="auto",  # "auto" | "evidence_erase" | "closed_book"
)
```

#### Methods

**`optimize(prompt, evidence_list, ...)`**
- Tests all combinations and returns the optimal subset
- Parameters:
  - `prompt`: The question/prompt to evaluate
  - `evidence_list`: List of evidence strings
  - `min_evidence`: Minimum evidence items per combination (default: 1)
  - `max_evidence`: Maximum evidence items (default: None = all)
  - `optimize_for`: "roh_bound" or "decision_answer"
  - `prefer_minimal`: Prefer smaller sets when metrics are equal

**`load_evidence_from_yaml(yaml_path)`**
- Loads prompt and evidence from YAML file
- Returns: `(prompt, evidence_list)`

**`save_results_to_yaml(result, yaml_path, include_all_results=False)`**
- Saves optimization results to YAML

## Output Format

The output YAML file structure:

```yaml
prompt: "Your question here"
optimization_summary:
  total_evidence_count: 5
  best_evidence_count: 3
  best_roh_bound: 0.0234
  best_decision: "ANSWER"
best_evidence:
  indices: [0, 2, 4]
  items:
    - "Evidence item 1"
    - "Evidence item 3"
    - "Evidence item 5"
  metrics:
    roh_bound: 0.0234
    decision_answer: true
    delta_bar: 2.456
    isr: 1.234
    rationale: "Explanation..."
evaluation_config:
  n_samples: 5
  m: 6
  h_star: 0.05
  skeleton_policy: "auto"
  temperature: 0.3
```

## Performance Considerations

- **Number of combinations**: For `n` evidence items, testing all combinations from size 1 to `n` results in `2^n - 1` combinations
- **Evaluation time**: Each combination requires `n_samples * m` LLM calls
- **Recommendations**:
  - For large evidence sets (>10 items), consider using `max_evidence` to limit subset sizes
  - Reduce `n_samples` for faster (but less accurate) evaluation
  - Use `min_evidence` to skip testing very small subsets

## Example Use Cases

1. **RAG System Optimization**: Find the minimal context needed for reproducible, accurate answers across multiple queries
2. **Knowledge Base Curation**: Identify which facts are most critical for ensuring consistent, reliable outcomes
3. **Prompt Engineering**: Determine the optimal evidence to include in prompts for maximum reproducibility
4. **Quality Assurance**: Validate that evidence sets meet reproducibility and hallucination thresholds
5. **Production Systems**: Ensure LLM applications produce consistent results by selecting evidence that maximizes outcome stability

## Implementation Details

### Architecture

The MERE (Minimal Evidence for Reproducibility) implementation consists of several key components:

1. **EvidenceOptimizer Class** (`evidence_optimizer.py`):
   - Main class for the MERE optimizer
   - Orchestrates the optimization process
   - Handles evidence combination generation, evaluation, and result tracking
   - Provides YAML-based I/O for evidence and results

2. **HallBayes Integration** (`credence/` directory):
   - Contains the co-opted HallBayes codebase
   - Provides core classes: `OpenAIBackend`, `OpenAIItem`, `OpenAIPlanner`
   - Implements the EDFL framework for hallucination risk calculation
   - Supports multiple backends (OpenAI, Anthropic, Ollama, HuggingFace, OpenRouter)

3. **Example Scripts**:
   - `example_optimize_evidence.py`: Simple usage example
   - `main.py`: Basic hallucination check demonstration

### How It Works

The optimization process follows these steps:

1. **Evidence Loading**: 
   - Reads prompt and evidence list from YAML file
   - Validates input format and structure

2. **Combination Generation**:
   - Generates all possible combinations (not permutations) of evidence subsets
   - Uses `itertools.combinations` to create subsets of size `min_evidence` to `max_evidence`
   - For `n` evidence items, this creates `2^n - 1` total combinations (if testing all sizes)

3. **Evaluation Loop**:
   - For each evidence combination:
     - Formats the prompt with the evidence subset using the `Evidence:` section format
     - Creates an `OpenAIItem` with the formatted prompt
     - Calls `OpenAIPlanner.evaluate_item()` which:
       - Generates skeleton variants of the prompt (with evidence masked)
       - Samples LLM responses to estimate prior probabilities
       - Calculates information-theoretic metrics:
         - **Δ̄ (delta_bar)**: Information budget in nats
         - **q_lo (q_conservative)**: Worst-case prior probability
         - **q̄ (q_avg)**: Average prior probability
         - **B2T (bits-to-trust)**: Information sufficiency requirement
         - **ISR (Information Sufficiency Ratio)**: Ratio of available to required information
         - **RoH (Risk of Hallucination)**: Upper bound on hallucination probability
       - Makes a decision (ANSWER or ABSTAIN) based on the metrics and `h_star` threshold

4. **Optimization**:
   - Collects all evaluation results
   - Sorts by optimization criteria:
     - `optimize_for="roh_bound"`: Minimizes hallucination risk bound
     - `optimize_for="decision_answer"`: Prefers combinations that result in ANSWER decisions
   - If `prefer_minimal=True`, breaks ties by selecting smaller evidence sets

5. **Result Export**:
   - Saves the optimal evidence subset and metrics to YAML
   - Optionally includes all tested combinations for analysis

### Evidence Format

The wrapper formats evidence in the prompt using HallBayes' expected format:

```
Your question here?

Evidence:
- Evidence item 1
- Evidence item 2
- Evidence item 3
```

HallBayes automatically detects the `Evidence:` section and uses it for evidence-based evaluation. When creating skeleton variants, HallBayes masks the evidence section to estimate how much the model relies on the provided evidence versus its internal knowledge.

### Metrics Explained

- **RoH Bound (Risk of Hallucination)**: The upper bound on the probability that the model will hallucinate. Lower is better. This is the primary metric for optimization.

- **Decision (ANSWER/ABSTAIN)**: Whether the model should answer the question based on the available information. ANSWER means the information is sufficient and risk is acceptable.

- **Δ̄ (Information Budget)**: Measures the information content in nats. Higher values indicate more information is available.

- **ISR (Information Sufficiency Ratio)**: Ratio of available information to required information. Values > 1.0 indicate sufficient information.

- **q_lo (Conservative Prior)**: Worst-case estimate of the model's prior knowledge. Lower values mean the model relies more on provided evidence.

### Backend Support

MERE (Minimal Evidence for Reproducibility) supports all HallBayes backends through the `credence` module:

- **OpenAI**: Requires `OPENAI_API_KEY` environment variable
- **Anthropic**: Requires `ANTHROPIC_API_KEY` environment variable  
- **Ollama**: Requires local Ollama server running
- **HuggingFace**: Supports local models, TGI servers, or HF Inference API
- **OpenRouter**: Requires `OPENROUTER_API_KEY` environment variable

The optimizer automatically tries to initialize backends in order (OpenAI → Anthropic → Ollama) if no backend is explicitly provided.

## Integration with HallBayes

MERE (Minimal Evidence for Reproducibility) uses HallBayes' core functionality from the `credence/` directory:

- **`OpenAIItem`**: Represents evaluation items with evidence. The `skeleton_policy` parameter controls how evidence is handled:
  - `"auto"`: Automatically detects evidence and uses appropriate mode
  - `"evidence_erase"`: Explicitly uses evidence-erase skeletons
  - `"closed_book"`: Uses closed-book mode (no evidence)

- **`OpenAIPlanner`**: Runs the EDFL evaluation framework:
  - Generates skeleton variants by masking evidence
  - Samples LLM responses to estimate priors
  - Calculates information-theoretic metrics
  - Makes ANSWER/ABSTAIN decisions based on risk thresholds

- **Evidence Formatting**: Evidence is formatted as `Evidence:` sections in prompts, which HallBayes automatically detects and processes. The skeleton generation masks this section to measure the model's dependence on provided evidence.

- **Backend Abstraction**: All backends implement the same interface (`chat_create`, `multi_choice`), allowing seamless switching between providers.

## License

MERE (Minimal Evidence for Reproducibility) and the co-opted HallBayes code are both licensed under the MIT License. See the original HallBayes repository for full license details.

