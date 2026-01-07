# Scoped Search Feature

## Overview

The RAG Notes App now supports **scoped search** - the ability to limit chat queries to a specific document or search across all documents.

### How It Works

- **Document Selected:** When you click on a note in the sidebar, all chat queries search **only that document**
- **No Selection:** When no note is selected, chat queries search **all uploaded documents**

---

## User Experience

### Visual Indicator

The chat header shows which scope is active:

**When a note is selected:**
```
💬 Chat with Your Notes
🎯 Searching only: Linear Algebra Notes.pdf
```

**When no note is selected:**
```
💬 Chat with Your Notes
Searching all uploaded notes
```

### Workflow

1. **Upload multiple documents** (e.g., Math notes, Python notes, History notes)
2. **Select a specific note** in the sidebar by clicking on it
3. **Ask questions** - responses will only use that document as context
4. **Click away** or select a different note to change scope
5. **Deselect** to search all documents again

---

## Use Cases

### Single-Document Focus

**Scenario:** You have 10 textbooks uploaded, but you're studying for a Linear Algebra exam.

**Solution:**
1. Click on "Linear Algebra.pdf" in the sidebar
2. Ask: "What is eigenvalue decomposition?"
3. The AI only searches Linear Algebra notes, ignoring other textbooks

**Benefits:**
- More accurate answers from the right context
- Faster search (fewer chunks to scan)
- No confusion from similar topics in other documents

### Multi-Document Search

**Scenario:** You want to find all mentions of "machine learning" across all your notes.

**Solution:**
1. Ensure no note is selected (sidebar has no highlighted item)
2. Ask: "Summarize what I know about machine learning"
3. The AI searches all documents and synthesizes an answer

**Benefits:**
- Comprehensive overview from multiple sources
- Find connections between different documents
- Broader context for general questions

---

## Technical Implementation

### Frontend Changes

**Chat Component (`src/components/Chat.jsx`):**
- Receives `selectedNote` prop from App
- Displays selected note title in header
- Passes `backendNoteId` to API call

**API Service (`src/services/api.js`):**
- `sendChatMessage()` accepts optional `noteId` parameter
- Sends `note_id` field to backend

### Backend Changes

**Chat Routes (`app/api/chat_routes.py`):**
- `ChatRequest` model has new `note_id` field
- Converts `note_id` to `filter_metadata` for ChromaDB
- Passes filter to RAG service

**RAG Service (`app/services/rag_service.py`):**
- `query_notes()` already supports metadata filtering
- ChromaDB `where` clause filters by `note_id`
- Returns only chunks matching the filter

### Data Flow

```
User selects note "Math.pdf" (frontend)
    ↓
selectedNote = { id: "abc", backendNoteId: "uuid-123", ... }
    ↓
User asks: "What is calculus?"
    ↓
Chat component extracts: noteId = "uuid-123"
    ↓
API call: sendChatMessage(query, k=5, includeSources=true, noteId="uuid-123")
    ↓
Backend receives: { query: "...", note_id: "uuid-123", ... }
    ↓
Chat endpoint converts: filter_metadata = { "note_id": "uuid-123" }
    ↓
RAG service queries ChromaDB with where clause
    ↓
ChromaDB returns only chunks where metadata.note_id == "uuid-123"
    ↓
Re-ranker ranks only Math.pdf chunks
    ↓
LLM generates answer using only Math.pdf context
    ↓
Response returned to user
```

---

## Metadata Structure

Each chunk in ChromaDB has metadata:

```python
{
  "note_id": "uuid-4122-...",      # Unique note identifier
  "title": "Linear Algebra.pdf",   # Document title
  "chunk_index": 42,               # Chunk position in document
  "total_chunks": 524,             # Total chunks in document
  # ... other metadata
}
```

The filter works by matching `note_id`:

```python
# Filter for specific document
filter_metadata = {"note_id": "uuid-4122-..."}

# ChromaDB query
results = collection.query(
    query_embeddings=[...],
    where=filter_metadata,  # Only returns matching chunks
    n_results=50
)
```

---

## Examples

### Example 1: Focused Study Session

**Setup:**
- Uploaded: "Physics_Chapter1.pdf", "Physics_Chapter2.pdf", "Chemistry.pdf"

**Task:** Study Physics Chapter 1 only

**Steps:**
1. Click "Physics_Chapter1.pdf" in sidebar
2. Header shows: "🎯 Searching only: Physics_Chapter1.pdf"
3. Ask: "What is Newton's First Law?"
4. Answer uses only Chapter 1 content

**Result:** No confusion with Chapter 2 or Chemistry notes

### Example 2: Cross-Document Research

**Setup:**
- Uploaded: "AI_Basics.pdf", "ML_Algorithms.pdf", "Deep_Learning.pdf"

**Task:** Compare machine learning approaches across all resources

**Steps:**
1. Ensure no note is selected
2. Header shows: "Searching all uploaded notes"
3. Ask: "Compare supervised and unsupervised learning"
4. Answer synthesizes information from all three PDFs

**Result:** Comprehensive answer with multiple perspectives

### Example 3: Quick Topic Check

**Setup:**
- Uploaded: 15 different textbooks

**Task:** Find information about "gradient descent"

**Steps:**
1. No note selected (search all)
2. Ask: "Where is gradient descent explained?"
3. AI searches all 15 books, finds it in "Calculus.pdf" and "ML_Algorithms.pdf"
4. Click on "ML_Algorithms.pdf"
5. Ask: "Explain the gradient descent algorithm"
6. Now answers using only ML_Algorithms.pdf

**Result:** First broad search, then focused deep dive

---

## Performance Considerations

### Scoped Search (Note Selected)

**Advantages:**
- **Faster:** Searches fewer chunks (e.g., 500 instead of 5000)
- **More Accurate:** Context matches query intent
- **Better Re-ranking:** FlashRank compares similar content

**Typical Performance:**
- Document size: 500 pages → 750 chunks
- Initial retrieval: 50 chunks (from 750)
- Re-ranking: Top 5 chunks
- Response time: ~2-5 seconds

### Global Search (No Note Selected)

**Advantages:**
- **Comprehensive:** Finds information anywhere
- **Discovery:** Uncovers unexpected connections

**Typical Performance:**
- Total chunks: 2000-10000 (depending on uploads)
- Initial retrieval: 50 chunks (from all)
- Re-ranking: Top 5 chunks
- Response time: ~3-7 seconds

**Note:** ChromaDB's vector search is optimized, so even searching 10,000 chunks is fast (<1 second for retrieval).

---

## API Reference

### Frontend API

**`sendChatMessage(query, k, includeSources, noteId)`**

Parameters:
- `query` (string): User's question
- `k` (number): Number of chunks to retrieve (default: 5)
- `includeSources` (boolean): Include source chunks in response (default: true)
- `noteId` (string|null): Filter by note ID, or null for all notes

Example:
```javascript
// Search specific note
const response = await sendChatMessage(
  "What is calculus?",
  5,
  true,
  "uuid-1234-5678"
);

// Search all notes
const response = await sendChatMessage(
  "What is calculus?",
  5,
  true,
  null
);
```

### Backend API

**`POST /api/chat/chat`**

Request body:
```json
{
  "query": "What is machine learning?",
  "k": 5,
  "note_id": "uuid-1234-5678",  // Optional: filter by note
  "include_sources": true
}
```

Response:
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is...",
  "context_used": [
    {
      "text": "Machine learning is a subset of AI...",
      "metadata": {
        "note_id": "uuid-1234-5678",
        "title": "AI_Basics.pdf",
        "chunk_index": 42
      },
      "distance": 0.234
    }
  ],
  "num_chunks": 5,
  "has_context": true
}
```

---

## Testing

### Manual Test Steps

**Test 1: Scoped Search**
1. Upload 2 different documents (e.g., "Math.pdf" and "History.pdf")
2. Click on "Math.pdf" in sidebar
3. Verify header shows "🎯 Searching only: Math.pdf"
4. Ask: "What is calculus?"
5. Check response sources - all should be from Math.pdf
6. Click on "History.pdf"
7. Verify header updates to "🎯 Searching only: History.pdf"
8. Ask same question
9. Response should say "no relevant context" (if History.pdf doesn't mention calculus)

**Test 2: Global Search**
1. Click away from any note (or refresh page)
2. Verify header shows "Searching all uploaded notes"
3. Ask: "What topics are covered in my notes?"
4. Response should reference both Math.pdf and History.pdf

**Test 3: Edge Cases**
1. Upload one document
2. Select it → scoped search should work
3. Deselect → global search includes only that one document
4. Upload more documents while one is selected
5. Scoped search should still work for selected document

---

## Limitations & Future Enhancements

### Current Limitations

1. **No Multi-Select:** Can't search across 2-3 specific documents (it's either one or all)
2. **No Saved Filters:** Filter resets on page refresh
3. **No Search History:** Previous queries don't remember which scope was used

### Potential Enhancements

**Multi-Document Selection:**
```
[ ] Math.pdf
[✓] Physics.pdf
[✓] Chemistry.pdf
```
Search only checked documents.

**Tag-Based Filtering:**
```
Tags: [Science] [Textbooks] [2024]
```
Filter by tags instead of individual documents.

**Temporal Filtering:**
```
Filter: Last 7 days | Last 30 days | All time
```
Search only recently uploaded notes.

**Source Weighting:**
```
Prefer: Physics.pdf (80%)
Also search: Math.pdf (20%)
```
Weighted search across documents.

---

## Troubleshooting

### Issue: Selected note doesn't filter search

**Symptoms:** Clicking a note doesn't change search scope

**Possible Causes:**
1. Frontend-backend mismatch (note_id not sent)
2. Metadata missing in ChromaDB
3. Browser console shows errors

**Solutions:**
1. Check browser console for errors
2. Verify API request includes `note_id` field
3. Check backend logs for filter application
4. Verify metadata was stored during upload:
   ```bash
   # Check collection contents
   curl http://localhost:8000/api/notes/stats
   ```

### Issue: "No context found" when note is selected

**Symptoms:** Search returns no results for selected document

**Possible Causes:**
1. Wrong note_id being sent
2. Document not fully indexed
3. Query doesn't match document content

**Solutions:**
1. Verify `backendNoteId` matches ChromaDB metadata
2. Re-upload the document
3. Try broader search terms
4. Deselect note to verify document exists in global search

### Issue: Header doesn't update when selecting notes

**Symptoms:** Scope indicator shows wrong document

**Possible Causes:**
1. React state not updating
2. selectedNote prop not passed correctly

**Solutions:**
1. Refresh page
2. Check React DevTools for component state
3. Verify App.jsx passes selectedNote to Chat

---

## Summary

The **scoped search feature** provides:

✅ **Focused Searching:** Limit queries to specific documents
✅ **Flexible Switching:** Easy toggle between scoped and global search
✅ **Visual Feedback:** Clear indicator of current search scope
✅ **Better Accuracy:** More relevant answers from targeted context
✅ **Improved Performance:** Faster search on large document collections

This feature enhances the RAG Notes App by giving users fine-grained control over their knowledge base queries, making it more powerful for both focused study and broad research.
