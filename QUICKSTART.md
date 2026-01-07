# Quick Start Guide

This guide will help you get the RAG Notes App up and running quickly.

## Prerequisites

1. **Python 3.10+** installed
2. **Ollama** installed and running ([Download here](https://ollama.ai/))

## Setup Steps

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# (Optional) Edit .env if you need custom settings
# The defaults should work for most local setups
```

### 3. Install Ollama Models

```bash
# Install the LLM model (3B parameter model, ~2GB download)
ollama pull llama3.2:3b

# Install the embedding model (~275MB download)
ollama pull nomic-embed-text:latest
```

### 4. Test Ollama Connection

```bash
# Run the test script to verify everything works
python test_ollama.py
```

You should see output like:
```
======================================================================
  Testing Ollama LLM Service
======================================================================

✅ Model 'llama3.2:3b' is available
✅ Generation successful!
✅ Streaming successful!

======================================================================
  Testing Ollama Embedding Service
======================================================================

✅ Model 'nomic-embed-text:latest' is available
✅ Embedding generation successful!
   Dimension: 768
...

🎉 All tests passed! Your Ollama setup is working correctly.
```

### 5. Start the Application

```bash
# Start the FastAPI server
python main.py
```

The server will start at `http://localhost:8000`

## Testing the API

### Using the Interactive Docs

Visit `http://localhost:8000/docs` to access the Swagger UI where you can test all endpoints interactively.

### Using curl

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. AI Services Health Check
```bash
curl http://localhost:8000/api/ai/health
```

#### 3. Generate Text
```bash
curl -X POST http://localhost:8000/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'
```

#### 4. Generate Text (Streaming)
```bash
curl -X POST http://localhost:8000/api/ai/generate/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a short poem about coding."}'
```

#### 5. Generate Embedding
```bash
curl -X POST http://localhost:8000/api/ai/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test sentence."}'
```

#### 6. Generate Embeddings (Batch)
```bash
curl -X POST http://localhost:8000/api/ai/embed/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "First sentence",
      "Second sentence",
      "Third sentence"
    ]
  }'
```

### Using Python

```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Generate text
        response = await client.post(
            "http://localhost:8000/api/ai/generate",
            json={"prompt": "What is Python?"}
        )
        print(response.json())

        # Generate embedding
        response = await client.post(
            "http://localhost:8000/api/ai/embed",
            json={"text": "Hello, world!"}
        )
        data = response.json()
        print(f"Embedding dimension: {data['dimension']}")

asyncio.run(test_api())
```

## Project Structure

```
rag-study-app/
├── app/
│   ├── core/
│   │   ├── config.py           # Settings management
│   │   └── interfaces.py       # Abstract base classes
│   ├── services/
│   │   └── ollama_service.py   # Ollama implementations
│   ├── api/
│   │   └── ai_routes.py        # API endpoints
│   └── dependencies.py         # Dependency injection
├── main.py                     # FastAPI app
└── test_ollama.py             # Connection test script
```

## Architecture Highlights

### Strategy Pattern
The application uses abstract interfaces (`LLMProvider`, `EmbeddingProvider`) making it easy to swap AI providers in the future:

```python
# Current: Ollama (local)
from app.services.ollama_service import OllamaLLM, OllamaEmbedding

# Future: Just implement the interfaces for new providers
from app.services.anthropic_service import AnthropicLLM, AnthropicEmbedding
```

### Dependency Injection
FastAPI's DI system makes it clean to use services:

```python
from app.dependencies import LLMDep, EmbeddingDep

@app.post("/chat")
async def chat(llm: LLMDep):
    response = await llm.generate_response("Hello!")
    return {"response": response}
```

## Troubleshooting

### Ollama Not Running
```bash
# Start Ollama service
ollama serve
```

### Model Not Found
```bash
# List installed models
ollama list

# Pull missing model
ollama pull llama3.2:3b
ollama pull nomic-embed-text:latest
```

### Port Already in Use
Edit `.env` and change `API_PORT`:
```bash
API_PORT=8001
```

### Connection Refused
Check your `.env` file:
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

Make sure Ollama is running on that port.

## Next Steps

1. Implement ChromaDB integration for vector storage
2. Create note CRUD endpoints
3. Build RAG retrieval logic
4. Add Streamlit frontend
5. Implement chat interface with context

Refer to the main `README.md` for detailed documentation.
