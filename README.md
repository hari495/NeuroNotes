# RAG Notes App

A local-first Retrieval-Augmented Generation (RAG) Notes application built with FastAPI, Ollama, and ChromaDB.

## Project Overview

This application allows you to store notes locally and query them using natural language powered by RAG technology. The architecture is designed for easy migration from local Ollama models to cloud-based APIs (like Anthropic) in the future.

### Key Features

- **Local-First**: All data and AI processing happens on your machine
- **RAG-Powered**: Semantic search and context-aware responses with source citations
- **Chat Interface**: Beautiful Streamlit web UI for chatting with your notes
- **REST API**: Full FastAPI backend with OpenAPI documentation
- **Modular Architecture**: Strategy pattern for easy provider switching
- **Type-Safe**: Full type hints and Pydantic validation
- **Async-First**: Asynchronous FastAPI for high performance

## Project Structure

```
rag-study-app/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic settings management
│   │   └── interfaces.py       # Abstract base classes for AI layer
│   ├── services/               # Business logic & AI service implementations
│   │   └── __init__.py
│   ├── api/                    # FastAPI route handlers
│   │   └── __init__.py
│   └── models/                 # Pydantic models for request/response
│       └── __init__.py
├── tests/                      # Unit and integration tests
│   └── __init__.py
├── data/                       # Local data storage
│   └── chroma/                 # ChromaDB persistent storage
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Modern Python project configuration
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.ai/) installed and running locally

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd rag-study-app
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using pip with pyproject.toml:
```bash
pip install -e .
pip install -e ".[dev]"  # Include development dependencies
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` file with your configuration (defaults should work for local Ollama setup).

### 5. Install Ollama models

```bash
# Install the LLM model (3B parameter model, good for local use)
ollama pull llama3.2:3b

# Install the embedding model
ollama pull nomic-embed-text:latest
```

## Running the Application

### Start the FastAPI backend

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Start the Streamlit Web Interface

**Make sure the FastAPI backend is running first!**

```bash
# Option 1: Using the launch script
./run_streamlit.sh

# Option 2: Direct command
streamlit run app/frontend.py
```

The web interface will open automatically at `http://localhost:8501`

**Features:**
- 📝 Create and manage notes via sidebar
- 💬 Chat with your notes using RAG
- 📚 View sources and citations for each answer
- ⚙️ Adjust search parameters (k chunks, show sources)
- 📊 Real-time collection statistics

See `STREAMLIT_GUIDE.md` for detailed usage instructions.

## Architecture

### Strategy Pattern for AI Providers

The application uses abstract base classes (`LLMProvider` and `EmbeddingProvider`) defined in `app/core/interfaces.py`. This allows you to:

1. **Currently**: Use Ollama for local AI processing
2. **Future**: Easily swap to Anthropic API without rewriting core logic

### Key Components

- **`app/core/interfaces.py`**: Abstract interfaces for LLM and Embedding providers
- **`app/core/config.py`**: Centralized configuration using Pydantic Settings
- **`main.py`**: FastAPI application with CORS, health checks, and lifespan management

## Configuration

All configuration is managed through environment variables or the `.env` file. See `.env.example` for all available options.

Key configurations:
- `OLLAMA_BASE_URL`: Ollama API endpoint (default: `http://localhost:11434`)
- `OLLAMA_LLM_MODEL`: Model for text generation (default: `llama3.2:3b`)
- `OLLAMA_EMBEDDING_MODEL`: Model for embeddings (default: `nomic-embed-text:latest`)
- `CHROMA_DB_PATH`: Local storage path for ChromaDB (default: `./data/chroma`)

## Development

### Code Quality Tools

The project includes configuration for:
- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **Pytest**: Testing framework

### Run tests

```bash
pytest
```

### Format code

```bash
black .
```

### Lint code

```bash
ruff check .
```

### Type checking

```bash
mypy app/
```

## What You Can Do Now

The RAG Notes App is fully functional! Here's what you can build with it:

### Current Features (Complete ✅)
1. ✅ Create and manage notes via API or Streamlit UI
2. ✅ Chat with your notes using RAG-augmented LLM
3. ✅ View sources and citations for each answer
4. ✅ Semantic search across all your notes
5. ✅ Persistent storage with ChromaDB
6. ✅ Full REST API with OpenAPI docs
7. ✅ Beautiful web interface with Streamlit

### Possible Enhancements
1. **Multi-user support** - Add authentication and user isolation
2. **Advanced chunking** - Implement smart paragraph/sentence splitting
3. **Hybrid search** - Combine semantic + keyword search
4. **Conversation memory** - Multi-turn dialogs with context
5. **Export/Import** - Backup and restore notes
6. **Mobile app** - Build React Native or Flutter frontend
7. **Cloud deployment** - Deploy to AWS/GCP/Azure
8. **Provider migration** - Switch to Anthropic API for LLM/embeddings

## License

[Specify your license]

## Contributing

[Specify contribution guidelines]
