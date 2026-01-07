# RAG System Guide

This guide explains how to use the RAG (Retrieval-Augmented Generation) system that's now integrated into your application.

## Overview

The RAG system provides semantic search capabilities for your notes using:
- **ChromaDB** for persistent vector storage
- **Ollama** embeddings (nomic-embed-text) for semantic understanding
- **Cosine similarity** for finding relevant content

## Architecture

```
User Input → Text Chunking → Embedding Generation → ChromaDB Storage
                                                            ↓
User Query → Query Embedding → Similarity Search ← ChromaDB Retrieval
```

## Key Components

### 1. RAG Service (`app/services/rag_service.py`)

The core service that handles:
- **Text Chunking**: Splits long texts into manageable chunks with overlap
- **Embedding Generation**: Uses OllamaEmbedding to create vector representations
- **Vector Storage**: Stores embeddings in ChromaDB with metadata
- **Semantic Search**: Finds similar chunks based on query embeddings

### 2. API Routes (`app/api/notes_routes.py`)

REST endpoints for RAG operations:
- `POST /api/notes/ingest` - Add notes to the system
- `POST /api/notes/query` - Search for relevant notes
- `DELETE /api/notes/{note_id}` - Remove a note
- `GET /api/notes/stats` - Collection statistics
- `GET /api/notes/list` - List all notes
- `POST /api/notes/reset` - Clear all data (⚠️ DANGER)

## Configuration

The RAG system uses settings from your `.env` file:

```env
# ChromaDB Settings
CHROMA_DB_PATH=./data/chroma
CHROMA_COLLECTION_NAME=notes_collection

# RAG Settings
RAG_TOP_K=5                      # Default number of results
RAG_SIMILARITY_THRESHOLD=0.7     # Minimum similarity score
RAG_CHUNK_SIZE=512              # Characters per chunk
RAG_CHUNK_OVERLAP=50            # Overlap between chunks
```

## Usage Examples

### Using the API

#### 1. Ingest a Note

```bash
curl -X POST http://localhost:8000/api/notes/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning is a subset of AI...",
    "metadata": {
      "title": "ML Basics",
      "author": "John Doe",
      "tags": ["ai", "ml"]
    }
  }'
```

Response:
```json
{
  "note_id": "uuid-here",
  "chunks_created": 2,
  "total_characters": 500,
  "embedding_dimension": 768
}
```

#### 2. Query Notes

```bash
curl -X POST http://localhost:8000/api/notes/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "k": 3
  }'
```

Response:
```json
{
  "query": "What is machine learning?",
  "results": [
    {
      "id": "note_id_chunk_0",
      "text": "Machine learning is a subset of AI...",
      "metadata": {
        "title": "ML Basics",
        "note_id": "uuid-here",
        "chunk_index": 0
      },
      "distance": 0.2178
    }
  ],
  "count": 3
}
```

#### 3. Get Collection Stats

```bash
curl http://localhost:8000/api/notes/stats
```

Response:
```json
{
  "collection_name": "notes_collection",
  "total_chunks": 42,
  "embedding_dimension": 768
}
```

#### 4. List All Notes

```bash
curl http://localhost:8000/api/notes/list?limit=10
```

#### 5. Delete a Note

```bash
curl -X DELETE http://localhost:8000/api/notes/{note_id}
```

### Using Python

```python
import asyncio
from app.core.config import get_settings
from app.services.ollama_service import OllamaEmbedding
from app.services.rag_service import RAGService

async def main():
    settings = get_settings()
    embedding = OllamaEmbedding(settings)
    rag = RAGService(settings, embedding)

    # Ingest a note
    result = await rag.ingest_note(
        note_text="Your note content here...",
        metadata={"title": "My Note"}
    )
    print(f"Ingested note: {result['note_id']}")

    # Query notes
    results = await rag.query_notes(
        query="What is this about?",
        k=3
    )

    for r in results:
        print(f"Distance: {r['distance']:.4f}")
        print(f"Text: {r['text'][:100]}...")

asyncio.run(main())
```

## How It Works

### Text Chunking

Notes are split into overlapping chunks to preserve context:

```
Original: "ABCDEFGHIJ" (chunk_size=5, overlap=2)
Chunks:   ["ABCDE", "DEFGH", "GHIJ"]
           ↑----↑  ↑----↑
          overlap overlap
```

This ensures that information spanning chunk boundaries isn't lost.

### Embedding Generation

Each chunk is converted to a 768-dimensional vector using Ollama's `nomic-embed-text` model:

```python
text = "Machine learning is..."
embedding = [0.489, 0.885, -3.176, ...]  # 768 numbers
```

### Similarity Search

Queries are embedded the same way, then ChromaDB finds the closest vectors using cosine similarity:

```
Query: "What is ML?" → [0.512, 0.891, -3.201, ...]
                              ↓
                    Cosine Similarity
                              ↓
Results: [0.2178, 0.2202, 0.3045]  # Lower = more similar
```

## Metadata Filtering

You can filter search results by metadata:

```bash
curl -X POST http://localhost:8000/api/notes/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "k": 5,
    "filter_metadata": {
      "author": "John Doe",
      "category": "AI/ML"
    }
  }'
```

This only returns chunks where metadata matches the filter.

## Testing

Run the test script to verify everything works:

```bash
python test_rag.py
```

Expected output:
```
✅ RAG service initialized successfully
✅ Note ingested successfully!
✅ Found 3 relevant chunks!
✅ Deleted note successfully
🎉 All RAG tests passed!
```

## Persistence

ChromaDB data is stored in `./data/chroma/` and persists across restarts:
- Notes and embeddings are automatically saved
- Restarting the app reloads existing data
- Delete the `data/` directory to completely reset

## Performance Tips

1. **Chunk Size**: Smaller chunks (256-512) = more precise, larger chunks (1024+) = more context
2. **Top K**: Start with k=3-5, adjust based on your needs
3. **Metadata**: Add rich metadata for better filtering
4. **Batch Operations**: Ingest multiple notes in sequence for efficiency

## Common Use Cases

### 1. Study Notes Search

```python
# Ingest study notes
await rag.ingest_note(
    note_text=biology_notes,
    metadata={"subject": "biology", "chapter": "cell biology"}
)

# Search for specific topics
results = await rag.query_notes(
    query="What is mitochondria?",
    k=3,
    filter_metadata={"subject": "biology"}
)
```

### 2. Personal Knowledge Base

```python
# Add articles
await rag.ingest_note(
    note_text=article_text,
    metadata={
        "source": "research_paper",
        "date": "2024-01-01",
        "tags": ["ai", "deep-learning"]
    }
)

# Find related content
results = await rag.query_notes(
    query="latest developments in AI",
    k=5
)
```

### 3. Meeting Notes

```python
# Store meeting notes
await rag.ingest_note(
    note_text=meeting_transcript,
    metadata={
        "type": "meeting",
        "date": "2024-01-06",
        "attendees": ["Alice", "Bob"]
    }
)

# Retrieve action items
results = await rag.query_notes(
    query="action items from last meeting",
    filter_metadata={"type": "meeting"}
)
```

## API Documentation

For interactive API documentation, start the server and visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### "Collection not found" error
- ChromaDB will auto-create the collection on first use
- Check that `CHROMA_DB_PATH` directory is writable

### "Embedding dimension mismatch" error
- Ensure you're using the same embedding model consistently
- Reset the collection if you changed models

### Poor search results
- Try adjusting `RAG_CHUNK_SIZE` (smaller = more precise)
- Increase `k` to get more results
- Add more notes to improve coverage

### Slow performance
- ChromaDB loads all data into memory on first query
- First query may be slow, subsequent queries are fast
- Consider adding an index for large collections (10k+ chunks)

## Next Steps

Now that you have RAG working, you can:
1. Build a chat interface that uses RAG for context
2. Add a Streamlit frontend for easy note management
3. Implement a "chat with your notes" feature using LLM + RAG
4. Add more sophisticated chunking strategies
5. Implement hybrid search (semantic + keyword)

See `QUICKSTART.md` for general setup and `README.md` for the full project overview.
