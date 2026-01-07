# Chat API Guide

Complete guide to using the RAG-augmented chat endpoints to ask questions about your notes.

## Overview

The chat system combines:
- **Semantic Search (RAG)** - Finds relevant context from your notes
- **LLM Generation** - Generates answers based ONLY on the retrieved context
- **Prompt Engineering** - Ensures the LLM stays grounded in your notes

## API Endpoints

### 1. POST /api/notes/

Create a new note with title and text.

**Request:**
```bash
curl -X POST http://localhost:8000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Basics",
    "text": "Python is a high-level programming language..."
  }'
```

**Response:**
```json
{
  "note_id": "uuid-here",
  "chunks_created": 2,
  "total_characters": 150,
  "embedding_dimension": 768
}
```

### 2. POST /api/chat/chat

Ask questions about your notes and get answers based on retrieved context.

**Request:**
```bash
curl -X POST http://localhost:8000/api/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key features of Python?",
    "k": 3,
    "include_sources": true
  }'
```

**Parameters:**
- `query` (required): Your question
- `k` (optional, default: 3): Number of context chunks to retrieve (1-10)
- `filter_metadata` (optional): Filter by metadata (e.g., `{"category": "programming"}`)
- `include_sources` (optional, default: true): Include source chunks in response

**Response:**
```json
{
  "query": "What are the key features of Python?",
  "answer": "Based on the provided context, the key features of Python are:\n1. Simple and easy to learn syntax\n2. Extensive standard library\n3. Dynamic typing...",
  "context_used": [
    {
      "text": "Python is a high-level programming language...",
      "metadata": {"title": "Python Basics", "note_id": "..."},
      "distance": 0.3594
    }
  ],
  "num_chunks": 3,
  "has_context": true
}
```

### 3. POST /api/chat/stream

Same as `/chat` but streams the response as it's generated.

**Request:**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain machine learning",
    "k": 3
  }'
```

**Response:** Streaming text response (not JSON)

### 4. POST /api/chat/simple

Simplified chat endpoint for quick testing.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/chat/simple?query=What%20is%20Python&k=3"
```

**Response:**
```json
{
  "query": "What is Python?",
  "answer": "Python is a high-level programming language...",
  "num_chunks_used": 3
}
```

## How It Works

### The RAG Pipeline

```
1. User Query
   ↓
2. Semantic Search (Retrieve top k chunks)
   ↓
3. Prompt Construction
   ↓
4. LLM Generation (Answer based ONLY on context)
   ↓
5. Response
```

### Prompt Template

The system uses this prompt structure:

```
You are a helpful assistant that answers questions based ONLY on the provided context from the user's notes.

IMPORTANT INSTRUCTIONS:
1. Answer the question using ONLY the information in the context below
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Do not make up information or use knowledge outside the provided context
4. If relevant, cite which context section(s) you're using
5. Be concise but complete in your answer

CONTEXT FROM NOTES:
[Retrieved chunks here]

USER QUERY: [User's question]

ANSWER (based only on the context above):
```

This ensures the LLM:
- ✅ Stays grounded in your notes
- ✅ Doesn't hallucinate information
- ✅ Admits when it doesn't have enough context
- ✅ Cites sources when possible

## Usage Examples

### Example 1: Basic Question

```python
import httpx
import asyncio

async def ask_question():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat/chat",
            json={
                "query": "What are the types of machine learning?",
                "k": 3
            }
        )
        data = response.json()
        print(f"Question: {data['query']}")
        print(f"Answer: {data['answer']}")
        print(f"Used {data['num_chunks']} context chunks")

asyncio.run(ask_question())
```

### Example 2: With Metadata Filtering

```python
# Only search in notes tagged as "programming"
response = await client.post(
    "http://localhost:8000/api/chat/chat",
    json={
        "query": "What is FastAPI?",
        "k": 5,
        "filter_metadata": {"category": "programming"}
    }
)
```

### Example 3: Streaming Response

```python
async def stream_answer():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/chat/stream",
            json={"query": "Explain neural networks", "k": 3}
        ) as response:
            async for chunk in response.aiter_text():
                print(chunk, end="", flush=True)

asyncio.run(stream_answer())
```

### Example 4: Checking Sources

```python
response = await client.post(
    "http://localhost:8000/api/chat/chat",
    json={
        "query": "What is Python used for?",
        "k": 3,
        "include_sources": true
    }
)

data = response.json()
print(f"Answer: {data['answer']}\n")
print("Sources:")
for i, chunk in enumerate(data['context_used'], 1):
    print(f"{i}. {chunk['metadata']['title']} (distance: {chunk['distance']:.4f})")
    print(f"   {chunk['text'][:100]}...\n")
```

## Test Results

From `test_chat.py`:

### ✅ Question with Good Context
```
Query: "What are the key features of Python?"
Context Retrieved: 3 chunks (distances: 0.3594, 0.3959, 0.4138)
Answer: Correctly listed all 5 key features from the notes
```

### ✅ Question Requiring Multiple Chunks
```
Query: "What are the three main types of machine learning?"
Context Retrieved: 3 chunks from ML notes
Answer: Correctly identified supervised and unsupervised learning from context
       (Note: Only 2 were in the provided context, LLM correctly stated this)
```

### ✅ Question with No Relevant Context
```
Query: "What is quantum computing?"
Context Retrieved: 2 chunks (not relevant)
Answer: LLM correctly stated it doesn't have information in the knowledge base
        and suggested the user add relevant notes
```

## Best Practices

### 1. Choosing k (Number of Chunks)

- **k=1-2**: Precise, focused answers
- **k=3-5**: Balanced (recommended default)
- **k=5-10**: Comprehensive answers with more context

### 2. Writing Good Queries

**Good:**
- "What are the key features of Python?"
- "Explain the three types of machine learning"
- "How does FastAPI handle async requests?"

**Less Effective:**
- "Tell me everything about Python" (too broad)
- "Python?" (too vague)

### 3. Organizing Notes

Add rich metadata to enable filtering:

```json
{
  "title": "Python OOP Concepts",
  "text": "...",
  "metadata": {
    "category": "programming",
    "subcategory": "python",
    "difficulty": "intermediate",
    "tags": ["oop", "classes", "inheritance"]
  }
}
```

### 4. Handling Edge Cases

**No Context Found:**
```json
{
  "query": "What is quantum physics?",
  "answer": "I don't have information about quantum physics in the current knowledge base...",
  "context_used": [],
  "num_chunks": 0,
  "has_context": false
}
```

**Partial Context:**
The LLM will answer based on what's available and indicate if more information is needed.

## Interactive Testing

### Using Swagger UI

1. Start the server: `python main.py`
2. Visit `http://localhost:8000/docs`
3. Find the "Chat" section
4. Try the `/api/chat/chat` endpoint:
   - Click "Try it out"
   - Enter your query
   - Click "Execute"
   - View the response

### Using curl

```bash
# Create a note
curl -X POST http://localhost:8000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Machine Learning",
    "text": "Machine learning is a subset of AI that enables systems to learn from data..."
  }'

# Ask a question
curl -X POST http://localhost:8000/api/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "k": 3
  }'
```

## Architecture

### Request Flow

```
POST /api/chat/chat
   ↓
ChatRequest (Pydantic validation)
   ↓
RAG Service (query_notes)
   ↓
ChromaDB (semantic search)
   ↓
Context Chunks Retrieved
   ↓
Prompt Construction
   ↓
LLM Provider (generate_response)
   ↓
ChatResponse (with answer + sources)
```

### Dependencies

The chat endpoint uses:
- `RAGDep` - For semantic search and context retrieval
- `LLMDep` - For answer generation
- Automatic dependency injection via FastAPI

## Troubleshooting

### "No relevant context found"

**Solution:** Add more notes about the topic or rephrase your query

### LLM response is too generic

**Solution:** Increase `k` to provide more context

### LLM uses information not in notes

**Solution:** Check the prompt template - should be enforcing "ONLY" use of context

### Slow response time

**Solution:**
- Reduce `k` to retrieve fewer chunks
- Use `/chat/stream` for better perceived performance
- Ensure Ollama is running efficiently

## Next Steps

Now that you have chat working, you can:
1. Build a Streamlit frontend for the chat interface
2. Add conversation history/memory
3. Implement multi-turn conversations
4. Add citation links to specific notes
5. Create a "chat with your notes" mobile app

See `README.md` for overall project documentation and `RAG_GUIDE.md` for RAG system details.
