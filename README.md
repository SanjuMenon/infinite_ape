# infinite_ape
Experiments with Agents that I'm testing in public 

This repository contains early code for experiments I am running across different AI agent approaches. Each folder represents a separate project:

- **Causal Agent** - Click on the `causalagent/` folder to find out more about this project
- **Stigmergic AI** - Click on the `stigmergicai/` folder to find out more about this project
- **Partial Prompt Bias Probe** - See `partial_prompt_bias/` for the Bayesian latent-bias probe CLI and library.

Building Evolvable AI (or formerly Stigmergic AI) here : https://github.com/SanjuMenon/OrchestrableAI/ (currently private repo)

## Partial Prompt Bias Probe

Install dependencies:

```
pip install -r requirements.txt
```

Example OpenAI run:

```
python -m partial_prompt_bias.cli ^
  --provider openai ^
  --partial-prompt "Which emoji feels happiest?" ^
  --labels 😀 🙂 😐 😕
```

Example Azure OpenAI run:

```
python -m partial_prompt_bias.cli ^
  --provider azure ^
  --partial-prompt "Which emoji feels happiest?" ^
  --labels 😀 🙂 😐 😕 ^
  --azure-deployment my-deployment ^
  --azure-endpoint https://example.openai.azure.com/ ^
  --azure-api-version 2024-05-01-preview
```

You can also run from a JSON config:

```
python -m partial_prompt_bias.cli --config config.json
```


