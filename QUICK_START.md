# Quick Start Guide - RAG Notes App

## Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 20.19+** (for frontend)
- **Ollama** (for local LLM & embeddings)

---

## 1. Start Ollama

```bash
# Install Ollama if not already installed
# https://ollama.ai

# Pull the required models
ollama pull llama3.2:3b
ollama pull nomic-embed-text

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

---

## 2. Setup & Start Backend

```bash
# Navigate to project root
cd /Users/harikolla/workspace/rag-study-app

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend
python main.py
```

**Backend runs at:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs`

---

## 3. Setup & Start Frontend

```bash
# Open a new terminal tab/window

# Navigate to frontend directory
cd /Users/harikolla/workspace/rag-study-app/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Frontend runs at:** `http://localhost:5173`

---

## 4. Test the Application

### Upload a File

1. Open http://localhost:5173 in your browser
2. Click **"📤 Upload File"** in the sidebar
3. Select a `.txt`, `.md`, or `.pdf` file
4. Watch the spinner while backend processes the file
5. Success message will show: "✅ Uploaded [filename] - X chunks created"

### Chat with Your Notes

1. Type a question in the chat input box (bottom of right panel)
2. Press **Enter** or click **Send**
3. Wait for AI response (shows loading spinner)
4. Response appears with markdown formatting and math support

### Example Queries

- "What are the main topics covered in this document?"
- "Explain the concept of [topic from your document]"
- "Summarize the key points about [specific section]"

---

## 5. Verify Everything Works

### Backend Health Check

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Check ChromaDB Collection

```bash
curl http://localhost:8000/api/notes/stats
# Should return collection statistics
```

### Frontend Console (Browser DevTools)

- Open browser DevTools (F12)
- Check **Console** tab for errors (should be none)
- Check **Application** > **IndexedDB** > `rag-notes-db` > `notes`
- Should see your uploaded notes

---

## 6. Understanding the Workflow

### File Upload Process

```
1. Select file → 2. Read locally → 3. Upload to backend
                                           ↓
4. Save to IndexedDB ← Backend chunks & indexes document
                                           ↓
5. Display in sidebar     Store in ChromaDB (vector database)
```

**Backend Processing (for 500-page document):**
- Chunking: ~750 chunks (1000 chars each, 200 overlap)
- Batch processing: 15 batches (50 chunks per batch)
- Time: 30-60 seconds
- Progress shown in terminal logs

### Chat Query Process

```
1. User question → 2. Generate embedding → 3. Search ChromaDB
                                                    ↓
6. Display response ← 5. Generate answer ← 4. Re-rank results (FlashRank)
```

**Retrieval Strategy:**
- Initial retrieval: 10 chunks
- Re-ranking: Top 5 chunks (using FlashRank)
- LLM generation: Uses top 5 chunks as context

---

## 7. Project Structure Overview

```
rag-study-app/
├── app/                          # Backend (Python/FastAPI)
│   ├── api/
│   │   ├── notes_routes.py      # File upload & notes API
│   │   └── chat_routes.py       # Chat API
│   ├── services/
│   │   ├── rag_service.py       # RAG logic (chunking, indexing, retrieval)
│   │   └── ollama_service.py    # Ollama LLM & embeddings
│   └── core/
│       └── config.py            # Configuration
├── frontend/                     # Frontend (React/Vite)
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── services/            # API & IndexedDB services
│   │   └── App.jsx              # Main app (2-column layout)
│   └── package.json
├── data/
│   └── chroma/                  # ChromaDB persistent storage
├── requirements.txt             # Python dependencies
└── main.py                      # Backend entry point
```

---

## 8. Configuration

### Backend Environment Variables

Create `.env` in project root (optional):

```bash
# LLM Settings
LLM_MODEL=llama3.2:3b
EMBEDDING_MODEL=nomic-embed-text

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# ChromaDB
CHROMA_DB_PATH=./data/chroma
```

### Frontend Environment Variables

Edit `frontend/.env`:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000
```

---

## 9. Common Issues & Solutions

### Issue: "Connection refused" when uploading file

**Cause:** Backend not running

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start backend
python main.py
```

### Issue: "Ollama connection failed"

**Cause:** Ollama not running or models not pulled

**Solution:**
```bash
# Check Ollama
ollama list

# Pull models if missing
ollama pull llama3.2:3b
ollama pull nomic-embed-text

# Restart Ollama service
# (Method depends on OS - see Ollama docs)
```

### Issue: Upload hangs or times out

**Cause:** Large file taking too long

**Solution:**
- Check backend terminal for batch processing logs
- Wait up to 60 seconds for large files
- If still fails, check backend logs for errors

### Issue: Chat says "No context found"

**Cause:** No documents uploaded or query doesn't match content

**Solution:**
- Ensure at least one file is uploaded
- Check backend ChromaDB stats: `curl http://localhost:8000/api/notes/stats`
- Try a more general question about your document

---

## 10. Testing with Sample Data

### Test Large Document Processing

```bash
# Run the test script
python test_large_document.py
```

**Expected output:**
- Creates simulated 500-page textbook
- Shows batch processing progress
- Displays final statistics (750 chunks, 100% success)
- Tests querying the document

### Test with Real PDF

1. Find a PDF textbook (e.g., math, computer science)
2. Upload via the frontend
3. Wait for processing (watch backend terminal for progress)
4. Try queries like:
   - "What chapters are covered?"
   - "Explain [specific concept]"
   - "What are the main formulas?"

---

## 11. Stopping the Application

### Stop Frontend

```bash
# In frontend terminal, press:
Ctrl + C
```

### Stop Backend

```bash
# In backend terminal, press:
Ctrl + C

# Deactivate virtual environment
deactivate
```

### Stop Ollama (Optional)

```bash
# If you want to stop Ollama
# Method depends on OS:

# macOS/Linux
killall ollama

# Or use system service manager
```

---

## 12. Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- **Frontend:** Vite auto-reloads on file changes
- **Backend:** uvicorn reloads on Python file changes

### Debugging

**Frontend:**
- Open browser DevTools (F12)
- Check Console for JavaScript errors
- Check Network tab for API calls
- Check Application > IndexedDB for stored notes

**Backend:**
- Check terminal for error logs
- Visit http://localhost:8000/docs for interactive API docs
- Use `print()` or `logging` for debugging

### Database Management

**View ChromaDB data:**
```python
# In Python REPL
from app.services.rag_service import RAGService
from app.core.config import get_settings

settings = get_settings()
# ... initialize RAGService and query collection
```

**Clear all notes:**
```bash
# Delete ChromaDB directory
rm -rf data/chroma

# Restart backend (will recreate collection)
```

---

## 13. Next Steps

Once the basic app is working:

1. **Upload multiple documents** - Test with different file types
2. **Experiment with queries** - Try different question styles
3. **Monitor performance** - Watch backend logs during processing
4. **Explore the code** - Read `FRONTEND_ARCHITECTURE.md` and `REFACTORING_SUMMARY.md`
5. **Customize** - Adjust chunk size, retrieval count, or LLM model

---

## Summary

**You now have a fully functional RAG Notes App!**

- ✅ Local-first note storage (IndexedDB)
- ✅ AI-powered document chat (Ollama + ChromaDB)
- ✅ Clean 2-column UI (React + Vite)
- ✅ Batch processing for large documents (500+ pages)
- ✅ Markdown & math rendering

**Enjoy building your knowledge base!** 📚✨
