# RAG Notes App

A local-first Retrieval-Augmented Generation (RAG) Notes application built with FastAPI, Ollama, and ChromaDB.

## Project Overview

This application allows you to store notes locally and query them using natural language powered by RAG technology. The architecture is designed for easy migration from local Ollama models to cloud-based APIs (like Anthropic) in the future.

### Key Features

- **Local-First**: All data and AI processing happens on your machine
- **RAG-Powered**: Semantic search and context-aware responses with source citations
- **Modern React UI**: Professional two-column interface with IndexedDB storage
- **File Upload**: Support for .txt, .md, and .pdf files
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

### Quick Start (Recommended)

Run both frontend and backend with a single command:

```bash
./run_dev.sh
```

This will start:
- FastAPI backend on `http://localhost:8000`
- React frontend on `http://localhost:5173`

Press `Ctrl+C` to stop both services.

### Manual Start

#### 1. Start the FastAPI Backend

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### 2. Start the React Frontend

**Make sure the FastAPI backend is running first!**

```bash
cd frontend
npm install  # First time only
npm run dev
```

The frontend will be available at `http://localhost:5173`

**Features:**
- 📚 Local-first note storage with IndexedDB
- 📤 File upload (.txt, .md, .pdf)
- 💬 Chat with your notes using RAG
- 📊 Source citations with note titles (not just "Context 1, 2, 3")
- 🎨 Modern, responsive two-column UI
- 🔢 LaTeX math rendering with automatic PDF artifact cleanup
- ✨ AI automatically converts poorly parsed math symbols to proper LaTeX

**Note on PDFs**: The system automatically converts common PDF parsing artifacts (like `#v` or `#e1`) to proper LaTeX notation ($\vec{v}$, $\vec{e_1}$). See `PDF_MATH_HANDLING.md` for details.

See `frontend/README.md` for detailed frontend documentation.

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
1. ✅ Upload and manage notes (.txt, .md, .pdf files)
2. ✅ Local-first storage with IndexedDB in the browser
3. ✅ Chat with your notes using RAG-augmented LLM
4. ✅ View sources and citations for each answer
5. ✅ Semantic search across all your notes
6. ✅ Persistent vector storage with ChromaDB
7. ✅ Full REST API with OpenAPI docs
8. ✅ Modern React UI with two-column layout
9. ✅ File parsing for multiple formats

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
