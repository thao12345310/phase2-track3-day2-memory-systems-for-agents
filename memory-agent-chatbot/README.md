# 🧠 Lab 17: Multi-Memory Agent Chatbot with LangGraph

An agent chatbot with a full memory stack (4 types), built using LangGraph for state management, router, and prompt injection.

---

## Architecture

```
┌─────────────┐
│  User Input  │
└──────┬──────┘
       ▼
┌──────────────┐
│  Retrieve     │ ← Gathers from 4 memory backends
│  Memory       │   (short-term, profile, episodic, semantic)
└──────┬───────┘
       ▼
┌──────────────┐
│  Build Prompt │ ← Injects memory sections into system prompt
│  (Router)     │   with token budget management
└──────┬───────┘
       ▼
┌──────────────┐
│  LLM Call     │ ← GPT-4o-mini with memory-augmented prompt
└──────┬───────┘
       ▼
┌──────────────┐
│  Save Memory  │ ← LLM extracts facts, episodes, knowledge
└──────┬───────┘   and saves to appropriate backends
       ▼
┌──────────────┐
│  Response     │
└──────────────┘
```

## Memory Stack

| Memory Type | Backend | Purpose |
|-------------|---------|---------|
| **Short-Term** | Sliding window (list) | Recent conversation context |
| **Long-Term Profile** | JSON/Redis KV store | User facts (name, preferences, allergies) |
| **Episodic** | JSON event log | Past experiences (tasks, outcomes, lessons) |
| **Semantic** | ChromaDB / keyword fallback | Knowledge retrieval (docs, FAQs) |

## Key Features

- ✅ **4 independent memory backends** with clear interfaces
- ✅ **LangGraph state machine** with MemoryState, router, and prompt injection
- ✅ **Conflict handling** — fact corrections update the profile, old values archived
- ✅ **Token budget management** — memory trimming to fit within limits
- ✅ **LLM-based extraction** — automatic fact/episode/knowledge extraction
- ✅ **Benchmark suite** — 10 multi-turn conversations comparing no-memory vs with-memory
- ✅ **Privacy reflection** — PII risks, deletion support, limitations analysis

---

## Quick Start

### 1. Setup

```bash
cd memory-agent-chatbot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Interactive Chat

```bash
python chat.py
```

Commands:
- `/memory` — Show memory status
- `/clear` — Reset all memory
- `/quit` — Exit

### 3. Run Benchmark

```bash
python src/benchmark.py
```

This runs 10 multi-turn conversations comparing no-memory vs with-memory, and generates `BENCHMARK.md`.

---

## Project Structure

```
memory-agent-chatbot/
├── README.md               # This file
├── BENCHMARK.md             # Benchmark results (auto-generated)
├── REFLECTION.md            # Privacy & limitations reflection
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── chat.py                  # Interactive CLI chat
├── src/
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── agent.py             # LangGraph agent (core)
│   ├── extractor.py         # LLM-based memory extraction
│   ├── token_budget.py      # Token estimation & budget allocation
│   ├── benchmark.py         # Benchmark runner
│   └── memory/
│       ├── __init__.py
│       ├── short_term.py    # Sliding window buffer
│       ├── long_term_profile.py  # KV profile store
│       ├── episodic.py      # Event log
│       └── semantic.py      # Vector search (ChromaDB)
├── data/                    # Persisted memory data
│   ├── user_profiles.json
│   ├── episodes.json
│   └── chroma_db/
└── docs/
    └── (additional docs)
```

## Benchmarked Scenarios

| Category | Tests | Description |
|----------|-------|-------------|
| Profile Recall | 2 | Remember name, facts after multiple turns |
| Conflict Update | 2 | Correct allergy, change workplace |
| Episodic Recall | 2 | Remember debugging lesson, completed task |
| Semantic Retrieval | 2 | Retrieve LangGraph docs, RAG explanation |
| Token Budget | 1 | Recall name after 12+ turns |
| Combined | 1 | Profile + episodic + semantic in one response |

---

## Technologies

- **LangGraph** — State machine and workflow orchestration
- **LangChain** — LLM integration (OpenAI GPT-4o-mini)
- **ChromaDB** — Vector search for semantic memory
- **tiktoken** — Accurate token counting
- **Redis** — Optional profile backend
- **Rich** — Terminal UI
