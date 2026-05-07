# Friday AI Smart Assistant

A real-time AI voice assistant built for intelligent conversations, automation workflows, and modular tool execution.

## Features

- Voice interaction
- Real-time responses
- Web search tools
- System utilities
- Modular AI architecture
- Extensible tool framework
- Automation-ready backend

---

## Project Structure

```text
Friday---AI-Smart-Assistant/
│
├── server.py
├── agent_friday.py
├── pyproject.toml
├── .env.example
│
├── friday/
│   ├── config.py
│   ├── tools/
│   ├── prompts/
│   └── resources/
```

---

## Setup

### Install dependencies

```bash
uv sync
```

### Create environment file

```bash
copy .env.example .env
```

### Run backend server

```bash
uv run friday
```

### Run voice assistant

```bash
uv run friday_voice
```

---

## Tech Stack

- Python
- FastMCP
- LiveKit Agents
- Modular AI Tooling

---

## Future Improvements

- Local LLM support
- Desktop automation
- Offline execution
- AI workflow agents
- Advanced voice pipeline

---
