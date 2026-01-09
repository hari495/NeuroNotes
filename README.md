# RAG Study App

A local-first study application that combines note-taking with AI-powered chat using Retrieval-Augmented Generation (RAG). Built with FastAPI, React, Ollama, and ChromaDB.

## Features

- **AI-Powered Chat**: Chat with your notes using local LLMs through Ollama
- **Smart Note Management**: Create, organize, and search your study materials
- **RAG Integration**: Get contextually relevant answers from your notes using vector search
- **Study Mode**: Interactive study sessions with AI assistance
- **Local-First**: All processing happens on your machine - no data leaves your device
- **Math Support**: Render LaTeX equations in notes and chat
- **Markdown Support**: Full markdown rendering with syntax highlighting

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Ollama** - Run LLMs locally
- **ChromaDB** - Vector database for embeddings
- **Pydantic** - Data validation and settings management

### Frontend
- **React 19** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Framer Motion** - Animations
- **KaTeX** - Math rendering
- **React Markdown** - Markdown rendering

## Prerequisites

- Python 3.13+
- Node.js 18+
- [Ollama](https://ollama.ai/) installed and running

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd rag-study-app
```

### 2. Set up the backend

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set up the frontend

```bash
cd frontend
npm install
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
OLLAMA_TIMEOUT=120

# ChromaDB Settings
CHROMA_DB_PATH=./data/chroma
CHROMA_COLLECTION_NAME=notes_collection

# RAG Settings
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=50
```

### 5. Pull Ollama models

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text:latest
```

## Usage

### Start the development servers

#### Option 1: Use the convenience script

```bash
./run_dev.sh
```

#### Option 2: Start services manually

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

### AI Services
- `POST /api/ai/chat` - Chat with AI
- `GET /api/ai/models` - List available models
- `POST /api/ai/embeddings` - Generate text embeddings

### Notes & RAG
- `POST /api/notes` - Create a note
- `GET /api/notes` - List all notes
- `GET /api/notes/{id}` - Get specific note
- `DELETE /api/notes/{id}` - Delete a note
- `POST /api/notes/search` - Search notes with RAG

### Chat
- `POST /api/chat` - Send chat message
- `GET /api/chat/history` - Get chat history
- `DELETE /api/chat/history` - Clear chat history

### Study Mode
- `POST /api/study/session` - Start study session
- `GET /api/study/sessions` - List study sessions

## Development

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Format code
black app/ main.py

# Lint code
ruff check app/ main.py

# Type check
mypy app/ main.py

# Run tests
pytest
```

### Project Structure

```
rag-study-app/
├── app/
│   ├── api/           # API route handlers
│   ├── core/          # Core configuration
│   ├── models/        # Data models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic services
│   └── utils/         # Utility functions
├── frontend/
│   └── src/
│       ├── components/ # React components
│       ├── hooks/      # Custom React hooks
│       ├── services/   # API client services
│       └── utils/      # Frontend utilities
├── data/              # Local data storage
├── main.py            # FastAPI application entry point
└── requirements.txt   # Python dependencies
```

## Configuration

All configuration is managed through environment variables or the `.env` file. Key settings:

- **LLM Model**: Change `OLLAMA_LLM_MODEL` to use different models
- **Embedding Model**: Change `OLLAMA_EMBEDDING_MODEL` for different embeddings
- **RAG Parameters**: Adjust `RAG_TOP_K`, `RAG_SIMILARITY_THRESHOLD` for retrieval behavior
- **Chunk Size**: Modify `RAG_CHUNK_SIZE` and `RAG_CHUNK_OVERLAP` for text processing

## Troubleshooting

### Ollama connection issues
- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_BASE_URL` matches your Ollama instance

### ChromaDB errors
- Delete the ChromaDB directory: `rm -rf data/chroma`
- The database will be recreated on next startup

### Frontend build errors
- Clear node modules: `rm -rf frontend/node_modules`
- Reinstall dependencies: `cd frontend && npm install`

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
