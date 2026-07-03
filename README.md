# AI Repository Analysis Agent

An AI-powered agent that analyzes software repositories using **Retrieval-Augmented Generation (RAG)**, **LangChain**, and **LangGraph**. Ask natural-language questions about a codebase and get answers grounded in actual source code — with file references.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.x-green.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.1xx-teal.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![FAISS](https://img.shields.io/badge/FAISS-vector%20search-orange.svg)](https://github.com/facebookresearch/faiss)

---

## The Problem

Understanding an unfamiliar codebase is slow and painful:

- **Where is authentication handled?**
- **How does the database layer work?**
- **Which files use JWT?**

Traditional keyword search fails when you don't know the exact function or file names. Reading every file manually doesn't scale.

This project solves that by combining **semantic code search** with an **AI agent** that can explore, read, and reason about your repository — then answer in plain language with source references.

---

## What It Does

1. **Indexes** a local codebase into a FAISS vector store using OpenAI embeddings
2. **Searches** semantically — find relevant code by meaning, not just exact text
3. **Analyzes** via a LangGraph agent with tools for search, file reading, grep, and listing
4. **Answers** questions like *"Where is authentication handled?"* with cited files and explanations
5. **Exposes** everything through a FastAPI REST API and Docker for easy deployment

---

## Features

| Feature | Description |
|---------|-------------|
| **RAG pipeline** | Load → chunk → embed → store in FAISS |
| **Language-aware splitting** | LangChain splitters tuned for Python, JS, TS, Go, Rust, and more |
| **Semantic search** | Natural-language queries over indexed code |
| **LangGraph agent** | Structured flow: plan → search → read → answer |
| **Agent tools** | `search_codebase`, `read_file`, `grep_code`, `list_files` |
| **REST API** | `POST /ask`, `POST /index`, `GET /health` |
| **Docker support** | One-command setup with `docker compose up` |
| **Drop-in repo folder** | Place any codebase in `repo/` and go |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.12 |
| **LLM orchestration** | LangChain, LangGraph |
| **Embeddings** | OpenAI `text-embedding-3-small` |
| **Vector database** | FAISS (local, persisted to disk) |
| **API** | FastAPI + Uvicorn |
| **Containerization** | Docker, Docker Compose |
| **Config** | python-dotenv |

---

## Architecture

## Arkitektur

```mermaid
flowchart TB
    Input[repo/ — din kodbas] --> Indexing
    
    subgraph Indexing
        L[loader.py] --> S[splitter.py]
        S --> E[OpenAI Embeddings]
        E --> F[(FAISS Index)]
    end

    subgraph Agent
        P[Plan] --> SE[Search]
        SE --> RE[Read Files]
        RE --> AN[Answer]
    end

    subgraph Tools
        T1[search_codebase]
        T2[read_file]
        T3[grep_code]
        T4[list_files]
    end

    API[FastAPI]

    F --> T1
    T1 & T2 & T3 & T4 --> Agent
    Agent --> API

## Quick Start

### Prerequisites

- Python 3.12+
- [OpenAI API key](https://platform.openai.com/api-keys)
- Docker *(optional)*

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/ai-repo-analysis-agent.git
cd ai-repo-analysis-agent

python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

### 3. Add a codebase

Place your source files in `repo/`, or try the included demo:

```bash
# Windows (PowerShell)
Copy-Item -Recurse test_project\* repo\

# macOS / Linux
cp -r test_project/. repo/
```

### 4. Build the index

```bash
python scripts/build_index.py
```

### 5. Ask a question

```bash
python scripts/ask.py "Where is authentication handled?"
```

---

## Usage

### CLI

| Command | Description |
|---------|-------------|
| `python scripts/build_index.py` | Index the codebase in `repo/` |
| `python scripts/search.py "query"` | Raw semantic search (no LLM) |
| `python scripts/ask.py "query"` | Ask the agent (graph mode) |
| `python scripts/ask.py "query" --mode react` | Ask with all tools (flexible) |
| `python scripts/run_api.py` | Start the FastAPI server |

### API

Start the server:

```bash
python scripts/run_api.py
```

Open interactive docs at **http://127.0.0.1:8000/docs**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/ask` | Ask a question about the codebase |
| `POST` | `/index` | Re-index a codebase |

**Example — ask a question:**

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Where is authentication handled?"}'
```

**Example — re-index:**

```bash
curl -X POST http://127.0.0.1:8000/index \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "repo"}'
```

### Docker

```bash
# 1. Add your code to repo/
# 2. Set OPENAI_API_KEY in .env
docker compose up --build
```

| Volume | Purpose |
|--------|---------|
| `./repo` | Your codebase (mount point) |
| `./data` | Persisted FAISS index |

If `repo/` is empty, the API starts but indexing must be triggered manually via `POST /index` after adding files.

---

## Project Structure

```
ai-repo-analysis-agent/
├── repo/                  # ← Put your codebase here
├── test_project/          # Optional demo project
├── data/                  # FAISS index (generated)
├── src/
│   ├── loader.py          # Load source files
│   ├── splitter.py        # Language-aware chunking
│   ├── indexer.py         # Build FAISS index
│   ├── search.py          # Semantic search
│   ├── agent.py           # Agent entry point
│   ├── repo.py            # File ops: read, grep, list
│   ├── graph/
│   │   └── agent_graph.py # LangGraph: plan → search → read → answer
│   ├── tools/             # LangChain tools
│   └── api/
│       ├── app.py         # FastAPI application
│       └── schemas.py     # Request/response models
├── scripts/
│   ├── build_index.py
│   ├── search.py
│   ├── ask.py
│   └── run_api.py
├── docker/
│   └── entrypoint.sh
├── Dockerfile
└── docker-compose.yml
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required. Your OpenAI API key |
| `REPO_PATH` | `repo` | Codebase directory (Docker) |
| `INDEX_PATH` | `data/faiss_index` | FAISS index location (Docker) |

---

## Supported File Types

`.py` · `.js` · `.ts` · `.tsx` · `.jsx` · `.java` · `.go` · `.rs` · `.md`

---

## Example Output

**Question:** `Where is authentication handled?`

**Answer:**
> Authentication is primarily handled in `app/auth.py` and `app/main.py`.
>
> - `authenticate_user()` validates email and password
> - `create_access_token()` generates JWT tokens
> - `/auth/login` and `/auth/register` endpoints in `app/main.py`
> - JWT config (`JWT_SECRET`, `JWT_ALGORITHM`) in `config.py`

---

## Roadmap

- [ ] Support for additional embedding providers (local models)
- [ ] Git repository cloning as input
- [ ] Streaming responses in API
- [ ] Web UI for querying

---

## License

This project is open source. Add a license before publishing (e.g. MIT).

---

## Author

Built as a learning project exploring **RAG**, **AI agents**, and **codebase analysis** with modern LLM tooling.
