# OpenAI Agents for Causal Analysis

This module implements an intelligent agent system for causal analysis and counterfactual reasoning using OpenAI's language models. The system is particularly focused on analyzing educational data and generating insights about causal relationships.

## Overview

The module provides a framework for:
- Causal analysis of educational data
- Counterfactual reasoning and scenario generation
- Structured conversation handling using LLM-FSM (Finite State Machine)
- Automated form filling and data processing

## Key Components

### Core Modules

- `causal_agent.py`: Main implementation of the causal analysis agent using LLM-FSM
- `counterfactual_models.py`: Models and functions for generating counterfactual scenarios
- `definitions.py`: Data structure definitions and variable mappings
- `causal.py`: Core causal analysis functionality

### Data and Configuration

- `student-por.csv`: Dataset containing student performance data
- `preprocessing_config.yaml`: Configuration for data preprocessing
- `form_filling.json`: FSM definition for structured conversation handling

### Supporting Files

- `saved_models/`: Directory containing trained model artifacts
- `logs/`: Directory for storing execution logs
- `supporting_files/`: Additional resources and utilities

## Features

1. **Causal Analysis**
   - Automated extraction of causal relationships
   - Counterfactual scenario generation
   - Educational data analysis

2. **Conversation Management**
   - Structured dialogue using LLM-FSM
   - Context-aware responses
   - Automated form filling

3. **Data Processing**
   - Preprocessing of educational datasets
   - Variable mapping and standardization
   - Model training and evaluation

## Requirements

The module requires the following dependencies:
- Python 3.10
- OpenAI API access
- fsm-llm (installed from GitHub)
- Additional dependencies listed in requirements.txt

## Setup and Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/SanjuMenon/OrchestrableAI.git
   cd OrchestrableAI/stigmergicai/openai-agents
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install fsm-llm directly from GitHub:
   ```bash
   pip install git+https://github.com/NikolasMarkou/fsm_llm.git
   ```

5. Set up your environment variables:
   ```bash
   # On Windows:
   set OPENAI_API_KEY=your-api-key-here
   # On Unix or MacOS:
   export OPENAI_API_KEY=your-api-key-here
   ```

## Usage

1. After completing the setup steps above, you can run the causal agent:
   ```python
   from causal_agent import main
   main()
   ```

2. Interact with the system through the command-line interface

## Data Structure

The system works with educational data containing various features such as:
- Student demographics
- Academic performance metrics
- Family background
- Study habits and behaviors
- Health and lifestyle factors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that is short and to the point. It lets people do anything they want with your code as long as they provide attribution back to you and don't hold you liable.

### How to Cite

If you use this software in your research or projects, please cite:

```
@software{orchestrableai2024,
  author = {Sanju Menon},
  title = {OrchestrableAI: OpenAI Agents for Causal Analysis},
  year = {2024},
  url = {https://github.com/SanjuMenon/OrchestrableAI}
}
```

## Contact

[Add contact information]
