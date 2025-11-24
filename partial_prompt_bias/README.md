# Partial Prompt Bias Probe

This methodology provides a quantitative, model-agnostic way to detect whether a partial prompt is quietly steering an LLM toward some options over others, even before the full task is specified. Inspired by “Bayesian Teaching Enables Probabilistic Reasoning in Large Language Models” (Qiu et al., 2025) and Huang’s Distribution Non-Uniformity Index (DNUI), it treats the model’s choices under a partial prompt as a probability distribution and measures how far that distribution drifts from uniform. By repeatedly sampling predictions, updating a simple Bayesian “assistant,” and summarizing the resulting choice frequencies with DNUI, the method turns fuzzy concerns about leading or biased wording into a single scalar score. This lets you directly compare prompts, identify systematically over- or under-selected classes, and study how simple feedback loops amplify initial prompt-induced biases—all without needing ground-truth labels.

This package lets you define a partial prompt, a finite choice set, and a number of trials per choice, then runs an automated loop that:

- Queries an LLM (via the asynchronous OpenAI Chat Completions API) to pick a label.
- Updates a Bayesian assistant that tracks a Dirichlet-like belief over the labels.
- Samples feedback labels from the assistant distribution.
- Reports empirical prediction/feedback distributions and DNUI-based bias scores.



## Installation

From the repository root:

```
pip install -r requirements.txt
```

You will also need credentials:

- **OpenAI**: set `OPENAI_API_KEY`.
- **Azure OpenAI**: set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT`, and `AZURE_OPENAI_KEY` (or provide them via CLI flags shown below).

## CLI Usage

Run the CLI with explicit arguments:

```
python -m partial_prompt_bias.cli ^
  --provider openai ^
  --partial-prompt "Which emoji feels happiest?" ^
  --labels 😀 🙂 😐 😕 ^
  --trials-per-choice 10 ^
  --bayes-increment 0.1 ^
  --temperature 0.7 ^
  --model gpt-4.1-mini
```

Use `--prompt-file` to load the partial prompt from disk, `--seed` for reproducible assistant sampling, `--output` to write JSON to a file, and `--include-table` to embed the full prediction-feedback history.

### Provider selection

- `--provider openai` (default) uses `OpenAIClient` with the standard API key.
- `--provider azure` uses `AzureOpenAIClient`. You may pass `--azure-endpoint`, `--azure-api-version`, `--azure-deployment`, and `--azure-api-key`, or rely on the corresponding environment variables.

Azure example:

```
python -m partial_prompt_bias.cli ^
  --provider azure ^
  --partial-prompt "Which emoji feels happiest?" ^
  --labels 😀 🙂 😐 😕 ^
  --azure-deployment my-deployment ^
  --azure-endpoint https://example.openai.azure.com/ ^
  --azure-api-version 2024-05-01-preview
```

### JSON Config

You can also pass a JSON config file containing the fields of `ExperimentConfig` plus a `labels` field:

```
python -m partial_prompt_bias.cli --config config.json
```

Example `config.json`:

```json
{
  "partial_prompt": "Given this short context, which category fits best?",
  "labels": ["A", "B", "C", "D"],
  "trials_per_choice": 50,
  "bayes_increment": 0.1,
  "temperature": 0.7,
  "max_tokens": 16,
  "model": "my-azure-deployment"
}
```

When using Azure, set `"model"` to your deployment name (the CLI treats this interchangeably). For OpenAI, use the actual OpenAI model ID such as `gpt-4.1-mini`.

