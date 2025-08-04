# 📁 Project Structure — Voice Agent Network (with Poetry)

This is a modular and scalable layout for building an agentic voice assistant using [LangGraph](https://github.com/langchain-ai/langgraph), with **Poetry** for dependency and environment management.

```
voice-agent-network/
├── 📁 src/                         # All main application code
│   ├── 📁 stt/                     # Speech-to-Text (ASR) models and processing
│   │   ├── __init__.py
│   │   ├── recognizer.py          # Loads STT model (e.g., Whisper) and handles transcription
│   │   └── utils.py               # Audio cleaning, segmentation, format conversion
│   │
│   ├── 📁 tts/                     # Text-to-Speech synthesis
│   │   ├── __init__.py
│   │   ├── synthesizer.py         # TTS model inference (e.g., Tortoise, ElevenLabs)
│   │   └── utils.py
│   │
│   ├── 📁 input_output/           # Audio I/O interface for phone/microphone
│   │   ├── phone_interface.py     # Handles call integration and input capture
│   │   └── audio_io.py            # Streams, records, and manages audio input/output
│   │
│   ├── 📁 agentic_network/        # LangGraph agent structure
│   │   ├── graph_builder.py       # Builds and defines the LangGraph DAG
│   │   ├── 📁 agents/
│   │   │   ├── diagnosis_agent.py # Agent handling medical Q&A (Modül 1)
│   │   │   ├── appointment_agent.py # Agent for booking appointments (Modül 2)
│   │   └── 📁 core/
│   │       ├── context.py         # Shared context object passed between nodes
│   │       ├── topic_manager.py   # Implements the "Topic Stack" routing logic
│   │       └── intent_classifier.py # Classifies user intent (diagnosis/appointment/emergency)
│   │
│   ├── 📁 external/               # Integrations with third-party systems
│   │   ├── appointment_api.py     # External appointment system
│   │
│   └── 📁 output_generator/      # Handles final response generation
│       ├── question_router.py    # Directs clarifying/follow-up questions to agents
│       ├── output_formatter.py   # Formats answers into natural language
│       └── action_executor.py    # Executes suggested actions (e.g., send ambulance)
│
├── 📁 config/                    # Configuration files
│   ├── settings.yaml             # Model paths, service toggles, API keys
│   └── routes.yaml               # Optional: declarative routing between agents
│
├── 📁 tests/                     # Unit and integration tests
│   ├── test_stt.py
│   ├── test_tts.py
│   ├── test_agents.py
│   └── test_graph.py
│
├── 📁 scripts/                   # CLI tools and development utilities
│   ├── run_server.py             # Main entrypoint to run the full system
│   ├── preprocess_audio.py       # Clean and prep audio files
│   └── simulate_call.py          # Mock call behavior for testing
│
├── 📁 notebooks/                 # Prototyping and experiments
│   ├── explore_stt.ipynb
│   └── prototype_graph.ipynb
│
├── 📁 docs/                      # Project documentation
│   ├── architecture.md           # Explanation of the agentic network (with diagrams)
│   └── usage_guide.md            # How to install, run, and develop
│
├── 📁 logs/                      # Runtime and error logs (can be gitignored)
│
├── 📁 data/                      # Sample data, test audio files, etc.
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
