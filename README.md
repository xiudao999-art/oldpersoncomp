# Wan Qing - Elderly Care Agent

An AI agent designed to provide psychological care for the elderly, specializing in Validation Therapy and Person-Centered Therapy.

## Features

- **Role**: "Wan Qing", a senior psychological care expert.
- **Core Philosophy**: Empathy, validation, and non-judgmental acceptance.
- **Cognitive Process**: Uses an `<inner_thought>` chain to diagnose the user's stage (confusion, time confusion, etc.) and select appropriate therapy techniques before responding.
- **Tech Stack**: LangChain, LangGraph, Doubao (via Volcengine/OpenAI compatible API).

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Create a `.env` file in the root directory (copy from `.env.example`):
    ```bash
    cp .env.example .env
    ```
    Fill in your API keys:
    ```env
    OPENAI_API_KEY=your_doubao_or_openai_api_key
    OPENAI_API_BASE=https://ark.cn-beijing.volces.com/api/v3  # Or your provider's endpoint
    MODEL_NAME=doubao-pro-32k # Optional, defaults to doubao-pro-32k
    ```

## Usage

Run the CLI chat interface:

```bash
python main.py
```

## Structure

- `graph.py`: Defines the LangGraph workflow.
- `nodes.py`: Contains the agent node logic and LLM initialization.
- `state.py`: Defines the agent state (message history).
- `prompts.py`: Contains the detailed system prompt and persona definitions.
- `main.py`: Entry point for the CLI.
