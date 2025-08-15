# Voice Agent Network

A Python 3.11 project for building/experimenting with voice-agent components.

## Requirements
- Python **3.11** (3.12 not supported)
- Git

## Install Poetry
Recommended (pipx):
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry
```

Alternative:
```bash
python3 -m pip install --user poetry
```

Verify:
```bash
poetry --version
```

## Setup
```bash
git clone <YOUR_REPO_URL>.git
cd voice_agent_network
poetry install
```

This creates a virtualenv and installs all dependencies from `pyproject.toml`.

## Usage
Activate the environment:
```bash
poetry shell
```

## Model Files
You have to add the necessary llm vector folders into the corresponding folders in: src/llm/llm_models/model_files/gemma


## Project Structure

This is a modular and scalable layout for building an agentic voice assistant using [LangGraph](https://github.com/langchain-ai/langgraph), with **Poetry** for dependency and environment management.

```
voice-agent-network/
├── 📁 src/                         # All main application code
│   ├── 📁 stt/                     # Speech-to-Text (ASR) models and processing
│   │
│   ├── 📁 tts/                     # Text-to-Speech synthesis
│   │
│   ├── 📁 agentic_network/        # LangGraph agent structure
│   │   ├── graph_builder.py       # Builds and defines the LangGraph DAG
│   │   ├── 📁 agents/
│   │   │   ├── topic_manager_agent.py   # Agent handling the topic operations
│   │   │   ├── diagnosis_agent.py # Agent handling medical Q&A (Modül 1)
│   │   │   ├── appointment_agent.py # Agent for booking appointments (Modül 2)
│   │   └── 📁 core/
│   │       ├── agent_state.py         # Shared state object passed between nodes
│   │       └── topic_manager.py   # Implements the "Topic Stack" routing logic
│   │
│   ├── 📁 external/               # Integrations with third-party systems
│   │   └── server.py     # Server system
│   │
├── 📁 tests/                     # Unit and integration tests
│   ├── test_stt.py
│   ├── test_tts.py
│   ├── test_agents.py
│   └── test_graph.py
│
├── .env                          # Secrets like API keys (never commit this!)
├── .gitignore                   # Ignore venv, .env, logs, __pycache__, etc.
├── pyproject.toml               # 🧠 Poetry config: dependencies, metadata, etc.
├── poetry.lock                  # 🔒 Locked dependency versions
└── README.md                    # Project overview and quickstart
```

---

## 🧠 Notes on Using Poetry

- To install dependencies:
  ```bash
  poetry install
  ```

- To enter the environment shell:
  ```bash
  poetry shell
  ```

- To add a new package:
  ```bash
  poetry add some-library
  ```

- To run a script in env:
  ```bash
  poetry run python scripts/run_server.py
  ```

- To list dependencies:
  ```bash
  poetry show
  ```
