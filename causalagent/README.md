## 🧠 What is This?

**Causal Agent** is an open-source framework that brings the **LLM-Modulo architecture** to **causal inference** tasks. Based on the vision proposed by **Subbarao Kambhampati et al. (2024)**, this framework combines the creative generative power of Large Language Models (LLMs) with the formal correctness guarantees of external verifiers.

It enables LLMs to suggest hypotheses, causal graphs, and estimators — while external modules (statistical tests, domain verifiers, symbolic solvers) validate, critique, and refine those suggestions in a structured loop.

## 🧭 Motivation

> Treat LLMs like an overconfident but helpful know-it-all.  
> Useful for brainstorming, but always double-checked.

LLMs frequently hallucinate, struggle with planning, and can't self-verify their own outputs. However, if we use them within a **Generate-Test-Critique loop**, we can harness their strengths while guarding against their weaknesses.

This project applies that principle to **causal inference**.

## 🧱 Architecture

The system implements a **Generate-Test-Critique** loop, adapted from Kambhampati’s LLM-Modulo Framework:

```text
[1] Input: Causal Query or Dataset
     ↓
[2] LLM-Generated Candidate:
    - DAG
    - SCM (Structural Causal Model)
    - Interventional Query
     ↓
[3] Bank of Critics:
    - DAG validators (e.g., acyclicity, d-separation)
    - Statistical independence tests
    - Do-calculus-based estimators
     ↓
[4] Meta Controller:
    - Aggregates critiques
    - Forms improved prompts
     ↓
[5] LLM revises the causal candidate
     ↓
Repeat until all hard critics approve ✅

## Overview

The module provides a comprehensive framework for:
- **Web-based causal analysis** with an intuitive Streamlit interface
- **Causal analysis** of educational data with automated relationship extraction
- **Counterfactual reasoning** and scenario generation
- **Structured conversation handling** using LLM-FSM (Finite State Machine)
- **Automated form filling** and data processing
- **Real-time chat interface** for interactive causal analysis

## Key Components

### Core Modules

- `app.py`: **Main Streamlit web application** with modern UI and chat interface
- `causal_agent.py`: Implementation of the causal analysis agent using LLM-FSM
- `counterfactual_models.py`: Models and functions for generating counterfactual scenarios
- `definitions.py`: Data structure definitions and variable mappings
- `causal.py`: Core causal analysis functionality

### Web Application Features

- **Modern UI**: Clean, responsive design with custom styling
- **Real-time Chat**: Interactive conversation interface for causal analysis
- **Results Display**: Structured presentation of analysis results and scenarios
- **Session Management**: Persistent conversation state and restart functionality
- **Error Handling**: Graceful error handling and user feedback

### Data and Configuration

- `student-por.csv`: Dataset containing student performance data
- `preprocessing_config.yaml`: Configuration for data preprocessing
- `form_filling.json`: FSM definition for structured conversation handling
- `.streamlit/config.toml`: Streamlit configuration with custom theme

### Supporting Files

- `run_streamlit.py`: Python script to launch the Streamlit app
- `run_app.bat`: Windows batch file for easy app launching
- `saved_models/`: Directory containing trained model artifacts
- `logs/`: Directory for storing execution logs
- `supporting_files/`: Additional resources and utilities

## Features

### 🚀 Web Application
- **Interactive Chat Interface**: Ask what-if questions and get instant causal analysis
- **Modern Design**: Beautiful, responsive UI with custom styling
- **Real-time Processing**: Immediate feedback and scenario generation
- **Session Persistence**: Maintain conversation context across interactions

### 🔍 Causal Analysis
- **Automated Extraction**: Identify causal relationships in educational data
- **Counterfactual Scenarios**: Generate what-if scenarios and their outcomes
- **Educational Focus**: Specialized analysis for student performance data
- **Variable Mapping**: Intelligent mapping of educational variables

### 💬 Conversation Management
- **Structured Dialogue**: LLM-FSM powered conversation flow
- **Context Awareness**: Maintains conversation context and history
- **Automated Classification**: Categorizes user questions and variables
- **Smart Responses**: Contextual and relevant causal insights

### 📊 Data Processing
- **Educational Datasets**: Preprocessing of student performance data
- **Variable Standardization**: Consistent mapping and naming conventions
- **Model Training**: Automated model training and evaluation
- **Performance Metrics**: Comprehensive analysis results

## Requirements

The module requires the following dependencies:
- Python 3.10+
- OpenAI API access
- Streamlit 1.46.0+
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

### 🌐 Web Application (Recommended)

1. **Quick Start (Windows)**:
   ```bash
   run_app.bat
   ```

2. **Quick Start (All Platforms)**:
   ```bash
   python run_streamlit.py
   ```

3. **Manual Launch**:
   ```bash
   streamlit run app.py --server.port 8501 --server.address localhost
   ```

4. Open your browser and navigate to `http://localhost:8501`

### 💻 Command Line Interface

For advanced users who prefer the command line:
```python
from causal_agent import main
main()
```

## Web Application Guide

### Getting Started
1. Launch the application using one of the methods above
2. The app will open in your default browser
3. You'll see a welcome message and can start asking questions immediately

### Asking Questions
- **What-if Questions**: "What if a student studies 2 more hours per day?"
- **Causal Analysis**: "How does family size affect academic performance?"
- **Scenario Generation**: "What would happen if all students had access to tutoring?"

### Understanding Results
The application provides:
- **Question Classification**: How your question was interpreted
- **Target Variables**: What outcomes are being analyzed
- **Input Variables**: What factors are being considered
- **Generated Scenarios**: Multiple counterfactual scenarios with predictions

### Features
- **Chat History**: View your conversation history
- **Restart Conversation**: Start fresh with a new analysis
- **Real-time Processing**: Get immediate feedback and results
- **Error Handling**: Clear error messages and suggestions

## Data Structure

The system works with educational data containing various features such as:
- **Student Demographics**: Age, gender, family background
- **Academic Performance**: Grades, test scores, attendance
- **Family Background**: Parent education, family size, income
- **Study Habits**: Study time, internet access, extra activities
- **Health and Lifestyle**: Alcohol consumption, health status

## Technical Architecture

### Frontend
- **Streamlit**: Modern web framework for data applications
- **Custom CSS**: Responsive design with custom styling
- **Session Management**: Persistent state across interactions

### Backend
- **LLM-FSM**: Finite state machine for conversation management
- **OpenAI API**: GPT-4 integration for intelligent responses
- **Counterfactual Models**: Specialized models for scenario generation

### Data Flow
1. User input → LLM-FSM processing
2. Question classification → Variable extraction
3. Causal analysis → Scenario generation
4. Results formatting → Web display

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the web application locally
5. Submit a pull request

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

## Troubleshooting

### Common Issues

1. **OpenAI API Key Not Set**
   - Ensure your `OPENAI_API_KEY` environment variable is set
   - Restart your terminal/command prompt after setting the key

2. **Port Already in Use**
   - The app uses port 8501 by default
   - Change the port in `run_streamlit.py` or `run_app.bat` if needed

3. **Dependencies Not Found**
   - Ensure you're in the correct virtual environment
   - Run `pip install -r requirements.txt` again

4. **Model Loading Errors**
   - Check that the `saved_models/` directory exists
   - Ensure all required model files are present

## Contact

For questions, issues, or contributions, please open an issue on GitHub or contact the maintainer.

---

**🎉 Ready to explore causal relationships? Launch the web app and start asking what-if questions!**
