# infinite_ape
Experiments with Agents that I'm testing in public 

This repository contains early code for experiments I am running across different AI agent approaches. Each folder represents a separate project:

- **Causal Agent** - See `causalagent/` for an LLM-Modulo framework that brings causal inference to LLMs through a Generate-Test-Critique loop. It combines the generative power of LLMs with external verifiers (statistical tests, domain validators) to suggest and validate causal graphs, structural causal models, and counterfactual scenarios. Includes a web-based Streamlit interface for interactive causal analysis of educational data.
- **Stigmergic AI** - See `stigmergicai/` for a research project exploring stigmergic (indirect coordination through environment) approaches to multi-agent AI systems. Inspired by ant colonies using pheromone trails, agents coordinate through environmental modifications rather than direct communication. Implements hierarchical organizational structures and evolvable AI components using systematic inventive thinking (SIT) principles for self-transformation.
- **Partial Prompt Bias Probe** - See `partial_prompt_bias/` for a quantitative, model-agnostic methodology to detect whether a partial prompt is steering an LLM toward certain options over others. Uses Bayesian teaching and Distribution Non-Uniformity Index (DNUI) to measure prompt-induced bias by treating model choices as probability distributions and measuring drift from uniform, enabling systematic comparison and identification of biased wording.
- **Semantic Grounding Index (SGI)** - See `semantic_grounding_index/` for a Python implementation of the SGI metric for evaluating RAG-style systems. SGI measures how well a generated response is grounded in retrieved context versus how aligned it is with the user's question using geometric bounds on context engagement.
- **Symbolic (Agentica)** - See `symbolic/` for a sample program demonstrating the Agentica Python SDK, a type-safe AI framework that lets LLM agents integrate with your code—functions, classes, live objects, and entire SDKs.
- **MERE (Minimal Evidence for Reproducibility)** - See `mere/` for a tool that determines which evidence items help improve reproducibility of outcomes in LLM responses. Through combinatorial testing, it identifies the minimal set of evidence that ensures consistent, reliable results while minimizing hallucination risk.

Building Evolvable AI (or formerly Stigmergic AI) here : https://github.com/SanjuMenon/OrchestrableAI/ (currently private repo)




