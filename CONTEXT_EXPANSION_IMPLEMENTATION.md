# Context Expansion Implementation

## Overview

Implemented **Context Expansion** in the RAG system to automatically fetch neighboring chunks around each search result, providing richer context to the LLM.

## Problem Solved

**Before:** If a search matched a slide with just a title, the LLM only saw the title without surrounding content.

**After:** The LLM sees the previous chunk + matched chunk + next chunk, ensuring complete context.

---

## Implementation Details

### Strategy

For each top-k search result (e.g., Chunk 10):
1. **Fetch Previous Chunk** (Chunk 9) using `chunk_index - 1`
2. **Fetch Next Chunk** (Chunk 11) using `chunk_index + 1`
3. **Merge:** `[Previous Context] + [Main Match] + [Next Context]`

### Metadata Requirements

The ingestion process already saves the required metadata for each chunk:
- `note_id`: Unique identifier for the document
- `chunk_index`: Index of the chunk within the document (0, 1, 2, ...)
- `total_chunks`: Total number of chunks in the document

**Chunk ID Format:** `{note_id}_chunk_{chunk_index}`

### Code Changes

**File:** `app/services/rag_service.py`

#### 1. New Method: `_expand_context()`

**Location:** Lines 479-576

**Purpose:** Fetches neighboring chunks and merges them with the main match.

**Logic:**
```python
for each chunk in top-k results:
    - Extract: note_id, chunk_index, total_chunks from metadata
    - Build neighbor IDs:
        - Previous: "{note_id}_chunk_{chunk_index - 1}" (if chunk_index > 0)
        - Next: "{note_id}_chunk_{chunk_index + 1}" (if chunk_index < total_chunks - 1)
    - Fetch neighbors from ChromaDB using collection.get(ids=[...])
    - Construct expanded text:
        [Previous Context]
        {previous chunk text}

        [Main Match]
        {main chunk text}

        [Next Context]
        {next chunk text}
    - Return expanded chunk with metadata flag: context_expanded=True
```

**Edge Case Handling:**
- **First chunk** (index 0): No previous context
- **Last chunk** (index = total_chunks - 1): No next context
- **Missing metadata**: Returns chunk as-is without expansion
- **ChromaDB fetch failure**: Logs error and uses original chunk

#### 2. Modified Method: `query_notes()`

**Changes:**
- **Line 470:** Apply context expansion after re-ranking: `expanded_results = self._expand_context(final_results)`
- **Line 476:** Apply context expansion in fallback path: `expanded_results = self._expand_context(candidate_chunks[:k])`
- **Lines 367-402:** Updated docstring to document context expansion

**Retrieval Pipeline:**
```
1. Vector Search (ChromaDB)
    ↓ (50 candidates)
2. Re-ranking (FlashRank)
    ↓ (top 5 chunks)
3. Context Expansion (NEW!)
    ↓ (5 chunks with expanded context)
4. Return to LLM
```

---

## Example Output

### Before Context Expansion

**Search Result (Chunk 10):**
```
Theorem 7.1: Linear Independence

A set of vectors is linearly independent if...
```

**Problem:** The theorem statement might be incomplete. The definition or proof might be in the next chunk.

### After Context Expansion

**Search Result (Chunk 10 with expansion):**
```
[Previous Context]
...end of previous section about vector spaces.

[Main Match]
Theorem 7.1: Linear Independence

A set of vectors is linearly independent if...

[Next Context]
Definition: A set {v₁, v₂, ..., vₙ} is linearly independent if the only solution to
c₁v₁ + c₂v₂ + ... + cₙvₙ = 0 is c₁ = c₂ = ... = cₙ = 0.
```

**Benefit:** The LLM now has the complete definition from the next chunk!

---

## Metadata Structure

### Ingestion (Already Implemented)

**File:** `app/services/rag_service.py` (Lines 284-294)

```python
batch_ids = [
    f"{note_id}_chunk_{i}" for i in range(batch_start, batch_end)
]

batch_metadatas = [
    {
        **base_metadata,
        "chunk_index": i,           # Position in document
        "total_chunks": total_chunks, # Total chunks in document
        "note_id": note_id,         # Document identifier
    }
    for i in range(batch_start, batch_end)
]
```

### Retrieval (New)

**Expanded Chunk Metadata:**
```python
{
    "note_id": "uuid-1234-5678",
    "chunk_index": 10,
    "total_chunks": 524,
    "context_expanded": True,        # NEW: Indicates expansion applied
    "original_text": "Theorem 7.1...", # NEW: Original chunk text before expansion
    "title": "Linear Algebra.pdf",
    # ... other metadata
}
```

---

## Performance Considerations

### Additional Database Queries

**Per Search:**
- Before: 1 query (vector search for 50 chunks)
- After: 1 query + k queries (1 for each top-k chunk to fetch neighbors)

**For k=5:**
- Total queries: 1 (vector search) + 5 (neighbor fetching) = 6 queries
- Each neighbor fetch retrieves 2 chunks (previous + next) using single `get()` call

**Impact:**
- ChromaDB's `get()` by ID is very fast (~1-5ms per query)
- Expected overhead: ~25-50ms for k=5
- Total query time: ~3-7 seconds (unchanged, expansion is negligible)

### Context Size

**Before:**
- 5 chunks × ~1000 chars = ~5000 chars

**After:**
- 5 chunks × 3 neighbors × ~1000 chars = ~15,000 chars
- 3x increase in context size

**Considerations:**
- More context = better LLM understanding
- Still well within LLM context limits (most models support 4K-128K tokens)
- Improved answer quality justifies the increase

---

## Testing

### Test Case 1: Complete Theorem with Definition

**Setup:** Upload Linear Algebra textbook with theorems split across chunks

**Query:** "What is the linear independence theorem?"

**Expected:**
- Match hits chunk with theorem statement
- Previous chunk: Introduction to the section
- Next chunk: Formal definition and proof
- LLM receives complete context

### Test Case 2: Slide with Title Only

**Setup:** Upload PowerPoint slides (one slide = one chunk)

**Slide 10 (Matched):**
```
Chapter 3: Machine Learning
```

**Slide 11 (Next Context):**
```
- Supervised Learning
- Unsupervised Learning
- Reinforcement Learning
```

**Query:** "What types of machine learning are there?"

**Expected:**
- Match hits Slide 10 (just the title)
- Expansion includes Slide 11 with the bullet points
- LLM can answer the question properly

### Test Case 3: Edge Cases

**First Chunk (index=0):**
- No previous context
- Only includes: [Main Match] + [Next Context]

**Last Chunk (index=total_chunks-1):**
- No next context
- Only includes: [Previous Context] + [Main Match]

**Single Chunk Document:**
- No neighbors
- Only includes: [Main Match]

### Manual Testing

1. **Start backend:**
   ```bash
   python main.py
   ```

2. **Upload a document** with clear chunk boundaries (e.g., textbook with sections)

3. **Ask a question** that matches a chunk with incomplete information

4. **Check response sources** in frontend - should show expanded context

5. **Verify backend logs** - should not show expansion errors

---

## Configuration

### Disable Context Expansion (if needed)

To disable context expansion without removing code:

**Option 1: Return original chunks**
```python
# In query_notes(), replace:
expanded_results = self._expand_context(final_results)
# With:
expanded_results = final_results  # Skip expansion
```

**Option 2: Add flag to query_notes**
```python
async def query_notes(
    self,
    query: str,
    k: int = 5,
    filter_metadata: dict[str, Any] | None = None,
    expand_context: bool = True,  # NEW parameter
) -> List[dict[str, Any]]:
    # ...
    if expand_context:
        expanded_results = self._expand_context(final_results)
    else:
        expanded_results = final_results
```

### Adjust Expansion Window

Currently expands ±1 chunk. To expand ±2 chunks:

```python
# In _expand_context(), change:
if chunk_index > 0:
    prev_id = f"{note_id}_chunk_{chunk_index - 1}"
    neighbor_ids.append(prev_id)

# To:
if chunk_index > 1:
    prev_id = f"{note_id}_chunk_{chunk_index - 2}"
    neighbor_ids.append(prev_id)
if chunk_index > 0:
    prev_id = f"{note_id}_chunk_{chunk_index - 1}"
    neighbor_ids.append(prev_id)
```

---

## Benefits

### 1. Complete Context
- No more partial information
- Theorems include definitions
- Titles include content

### 2. Better LLM Understanding
- More context = more accurate answers
- Reduced hallucination risk
- Improved coherence

### 3. Handles Chunking Artifacts
- If a concept is split across chunks, expansion reunites it
- Smooth transitions between chunks

### 4. Automatic
- No user configuration needed
- Works transparently
- No changes to API or frontend

---

## Limitations

### 1. Context Duplication

If consecutive chunks are in top-k results (e.g., Chunk 10 and Chunk 11):
- Chunk 10 expansion includes Chunk 11 as [Next Context]
- Chunk 11 expansion includes Chunk 10 as [Previous Context]
- Chunk 11 appears twice in the final context

**Impact:** Minimal. LLMs handle duplicate information well.

**Mitigation (Future):** Deduplicate overlapping expansions

### 2. Cross-Document Boundaries

Context expansion only works within a single document:
- If Chunk 10 is from Document A, expansion fetches Chunks 9 and 11 from Document A
- Does not fetch chunks from Document B

**Impact:** Not an issue for most use cases

### 3. Fixed Window Size

Currently expands ±1 chunk. Some use cases might benefit from ±2 or ±3.

**Mitigation:** Easy to adjust window size (see Configuration section)

---

## Future Enhancements

### 1. Smart Expansion
- Detect incomplete chunks (e.g., ends mid-sentence)
- Only expand if needed

### 2. Deduplication
- If multiple consecutive chunks in top-k, merge their expansions
- Avoid sending duplicate context to LLM

### 3. Configurable Window
- Allow users to set expansion window (±1, ±2, ±3)
- Add to API parameters

### 4. Expansion Metrics
- Track how often expansion helps
- Log when expansion fetches critical context

---

## Summary

✅ **Implemented:** Context Expansion in `query_notes()`
✅ **Method:** Fetch neighboring chunks using `chunk_index` metadata
✅ **Format:** `[Previous] + [Main] + [Next]`
✅ **Performance:** ~25-50ms overhead for k=5
✅ **Context Size:** ~3x increase (acceptable)
✅ **Edge Cases:** Handled (first/last chunk, missing metadata)
✅ **Backward Compatible:** No API changes required

**The RAG system now provides richer, more complete context to the LLM, improving answer quality especially for documents with fragmented information across chunks!** 🚀
