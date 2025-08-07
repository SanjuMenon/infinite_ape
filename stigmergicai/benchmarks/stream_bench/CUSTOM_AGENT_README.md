# Custom Agent Implementation for StreamBench

This document explains how to use and customize the custom agent implementation for StreamBench benchmarking.

## Overview

The custom agent (`CustomAgent`) is a template implementation that demonstrates how to create your own agent for StreamBench. It includes:

- **Memory-based learning**: Stores past interactions to improve performance over time
- **Performance tracking**: Monitors accuracy and learning progress
- **Flexible configuration**: Easy to customize via YAML configuration files
- **Standard interface**: Implements the required StreamBench agent interface

## Files Created

1. **`stream_bench/agents/custom_agent.py`** - The main custom agent implementation
2. **`configs/agent/custom.yml`** - Configuration file for the custom agent
3. **`run_custom_agent.sh`** - Example script to run the custom agent
4. **`CUSTOM_AGENT_README.md`** - This documentation file

## How to Use

### 1. Basic Usage

Run the custom agent on a dataset:

```bash
python -m stream_bench.pipelines.run_bench \
    --agent_cfg "configs/agent/custom.yml" \
    --bench_cfg "configs/bench/ddxplus.yml" \
    --entity "your_entity" \
    --use_wandb
```

### 2. Using the Shell Script

```bash
# Make the script executable
chmod +x run_custom_agent.sh

# Run the script
./run_custom_agent.sh
```

## Customization Options

### 1. Modify the Agent Logic

Edit `stream_bench/agents/custom_agent.py` to implement your own logic:

#### Key Methods to Override:

- **`__call__(self, prompt, label_set, **kwargs)`**: Main inference method
- **`update(self, has_feedback, **feedbacks)`**: Learning from feedback
- **`_parse_response(self, response_text, label_set)`**: Parse LLM responses
- **`_build_memory_context(self)`**: Build context from memory

#### Example Customization:

```python
def __call__(self, prompt: str, label_set: list[str], **kwargs) -> str:
    # Your custom inference logic here
    # For example, implement chain-of-thought reasoning:
    
    # Step 1: Generate reasoning
    reasoning_prompt = f"Let's think step by step about this:\n{prompt}"
    reasoning, _ = self.llm(reasoning_prompt)
    
    # Step 2: Generate final answer
    answer_prompt = f"Based on the reasoning: {reasoning}\n\nWhat's the answer?"
    response_text, response_info = self.llm(answer_prompt)
    
    return self._parse_response(response_text, label_set)
```

### 2. Modify Configuration

Edit `configs/agent/custom.yml` to change parameters:

```yaml
agent_name: "custom"
llm:
  series: "openai"
  model_name: "gpt-4o-mini-2024-07-18"
  temperature: 0.0
  max_tokens: 512

# Custom parameters
learning_rate: 0.1
max_memory_size: 100
prompt_template: "Your custom prompt template here"
```

### 3. Add New Features

You can extend the custom agent with additional features:

```python
class CustomAgent(Agent):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        
        # Add new features
        self.use_chain_of_thought = config.get("use_chain_of_thought", False)
        self.use_rag = config.get("use_rag", False)
        self.rag_retriever = None
        
        if self.use_rag:
            self._setup_rag()
    
    def _setup_rag(self):
        # Initialize RAG components
        pass
```

## Key Features of the Custom Agent

### 1. Memory-Based Learning

The agent maintains a memory of past interactions:

```python
memory_entry = {
    "input": input_text,
    "prediction": prediction,
    "correct_answer": correct_answer,
    "is_correct": is_correct,
    "time_step": time_step
}
```

### 2. Performance Tracking

Track accuracy and learning progress:

```python
def get_performance_stats(self) -> Dict[str, Any]:
    accuracy = sum(self.performance_history) / len(self.performance_history)
    return {
        "accuracy": accuracy,
        "total_predictions": len(self.performance_history),
        "memory_size": len(self.memory)
    }
```

### 3. Flexible Response Parsing

Robust parsing of LLM responses to extract correct labels:

```python
def _parse_response(self, response_text: str, label_set: List[str]) -> str:
    # Multiple parsing strategies
    # 1. Exact match
    # 2. Partial match
    # 3. Default fallback
```

## Available Datasets

You can run your custom agent on these StreamBench datasets:

1. **DDXPlus** - Medical diagnosis reasoning
2. **DS-1000** - Data science code generation
3. **Spider** - Text-to-SQL generation
4. **CoSQL** - Conversational SQL generation
5. **BIRD** - Text-to-SQL with domain knowledge
6. **ToolBench** - Tool use and reasoning

## Environment Setup

Make sure you have the required API keys:

```bash
export OAI_KEY=<your_openai_api_key>
export GOOGLE_API_KEY=<your_google_ai_studio_api_key>
export ANTHROPIC_KEY=<your_anthropic_api_key>
```

## Advanced Customization

### 1. Multi-Model Support

You can configure multiple LLMs:

```yaml
llm:
  series: "openai"
  model_name: "gpt-4o-mini-2024-07-18"
  # Or use multiple models:
  # models:
  #   - "gpt-4o-mini-2024-07-18"
  #   - "gpt-4-turbo-2024-04-09"
```

### 2. Custom Learning Strategies

Implement sophisticated learning algorithms:

```python
def update(self, has_feedback: bool, **feedbacks) -> bool:
    if not has_feedback:
        return False
    
    # Implement your learning strategy
    if not feedbacks.get("is_correct", True):
        # Learn from mistakes
        self._adapt_strategy(feedbacks)
    
    return True
```

### 3. Integration with External Tools

Add RAG, external APIs, or other tools:

```python
def _setup_external_tools(self):
    # Initialize external tools
    self.vector_db = ChromaDB()
    self.external_api = ExternalAPIClient()
```

## Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure your custom agent is properly registered in `__init__.py`
2. **Configuration Errors**: Check that your YAML configuration is valid
3. **API Key Issues**: Verify your environment variables are set correctly
4. **Memory Issues**: Adjust `max_memory_size` if you encounter memory problems

### Debug Mode:

Add debug logging to your agent:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

def __call__(self, prompt: str, label_set: list[str], **kwargs) -> str:
    logging.debug(f"Processing prompt: {prompt[:100]}...")
    # Your logic here
```

## Next Steps

1. **Test your agent** on a small dataset first
2. **Monitor performance** using the built-in metrics
3. **Iterate and improve** based on results
4. **Share your findings** with the StreamBench community

## Contributing

To contribute your custom agent:

1. Fork the StreamBench repository
2. Add your agent implementation
3. Create comprehensive tests
4. Submit a pull request

## Support

For questions or issues:

1. Check the main StreamBench documentation
2. Review the example implementations in `stream_bench/agents/`
3. Open an issue on the StreamBench GitHub repository

---

**Happy benchmarking! 🚀** 