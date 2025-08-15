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