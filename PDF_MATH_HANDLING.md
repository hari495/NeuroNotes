# PDF Math Character Handling

## Problem

PDFs, especially those with mathematical notation, often get parsed incorrectly:

**Common Issues:**
- Vectors: `#v`, `#»v`, `# »v` instead of proper $\vec{v}$
- Subscripts: `e1`, `x1` instead of $e_1$, $x_1$
- Greek letters: Raw Unicode or garbled text
- Equations: Completely mangled formatting

**Example of Bad Parse:**
```
The span of vectors {#v1, #v2, ..., #vk} in R2...
```

**Should be:**
```
The span of vectors {$\vec{v_1}, \vec{v_2}, ..., \vec{v_k}$} in $\mathbb{R}^2$...
```

## Solution

The RAG system now automatically converts PDF artifacts to proper LaTeX notation.

### How It Works

1. **PDF is parsed** and stored in ChromaDB (artifacts included)
2. **AI retrieves** the context with artifacts
3. **AI automatically converts** artifacts to proper LaTeX before responding
4. **Frontend renders** the LaTeX beautifully with KaTeX

### AI Conversion Rules

The AI has been instructed to convert common PDF artifacts:

| PDF Artifact | LaTeX Output | Rendered |
|--------------|--------------|----------|
| `#v`, `#»v`, `# »v` | `$\vec{v}$` | $\vec{v}$ |
| `#e1`, `#»e1` | `$\vec{e_1}$` | $\vec{e_1}$ |
| `#x1` (vector) | `$\vec{x_1}$` | $\vec{x_1}$ |
| `x1` (subscript) | `$x_1$` | $x_1$ |
| `R`, `R2`, `R3` | `$\mathbb{R}$, $\mathbb{R}^2$, $\mathbb{R}^3$` | $\mathbb{R}$, $\mathbb{R}^2$, $\mathbb{R}^3$ |
| `in`, `∈` | `$\in$` | $\in$ |
| Malformed equations | Proper LaTeX equations | Rendered math |

## Testing

### Before Fix
Ask: "What is a span of vectors?"

Response:
```
The span of vectors {#v1, #v2, ..., #vk} is...
```

### After Fix
Ask: "What is a span of vectors?"

Response:
```
The span of vectors $\{\vec{v_1}, \vec{v_2}, ..., \vec{v_k}\}$ is...
```

## If You Still See Artifacts

If the AI misses some artifacts, you can explicitly ask:

**Prompt Examples:**
- "Can you rewrite that with proper LaTeX notation?"
- "Please use LaTeX for the math symbols"
- "Format the vectors and equations properly"

The AI will then reprocess its response with more aggressive LaTeX conversion.

## Better Source Citations

Sources are now cited by note title instead of "Context 1, Context 2":

**Before:**
```
According to Context 1, Section 2.4, and Context 2:
```

**After:**
```
According to the Linear Algebra notes, Section 2.4:
```

This makes it much clearer which notes the information came from.

## In the UI

The source citations at the bottom of each AI response now show:

```
📚 Sources (3 chunks used)

  Linear Algebra Notes               85.3% match
  The span of vectors is defined as...

  Calculus Review                    78.9% match
  For any set of vectors...
```

## Best Practices

### When Uploading PDFs

1. **Preview the text**: If possible, check if math is parsing correctly
2. **Use high-quality PDFs**: Better formatted PDFs parse better
3. **Consider alternatives**: If a PDF parses poorly, you might:
   - Export as LaTeX source and upload that
   - Manually create a .txt or .md file with proper LaTeX
   - Use OCR with math recognition

### When Chatting

1. **Trust the AI**: It will automatically fix most artifacts
2. **Ask for corrections**: If math looks wrong, ask to reformat
3. **Check sources**: The expandable sources show the raw text, so you can see what was actually stored

## Technical Details

### Backend Changes (app/api/chat_routes.py)

The prompt now includes:

```python
7. CRITICAL - Convert malformed PDF characters to proper LaTeX:
   The context may contain poorly parsed PDF characters. You MUST convert them to proper LaTeX:

   Common PDF artifacts to fix:
   - "#v", "#»v", "# »v" → $\vec{v}$
   - "#e1", "#»e1" → $\vec{e_1}$
   ...
```

And sources are cited with titles:

```python
f"[From: {chunk.get('metadata', {}).get('title', f'Note {i+1}')}]\n{chunk['text']}"
```

### Frontend Changes (frontend/src/components/Chat.jsx)

Source display shows note titles prominently:

```jsx
<strong className="source-note-title">
  {source.metadata?.title || 'Untitled Note'}
</strong>
```

## Limitations

1. **Not Perfect**: Very badly mangled PDFs might still have issues
2. **Context Dependent**: The AI guesses based on context (e.g., is "x1" a subscript or vector?)
3. **Manual Review**: For critical documents, consider manual LaTeX conversion

## Future Improvements

Potential enhancements:

1. **Preprocessing**: Clean artifacts before storing in ChromaDB
2. **Better PDF Parser**: Use specialized math-aware PDF parsers
3. **Manual Corrections**: Allow users to edit stored text
4. **LaTeX Source Upload**: Direct LaTeX file support

## Examples

### Example 1: Linear Algebra

**Raw PDF Parse (stored in DB):**
```
The span of {#»v1, ..., #»vk} in Rn is the set of all linear combinations.
```

**AI Response:**
```markdown
The **span** of vectors $\{\vec{v_1}, ..., \vec{v_k}\}$ in $\mathbb{R}^n$ is
the set of all linear combinations of those vectors.

According to the Linear Algebra notes, this can be expressed as:

$$
\text{span}(\vec{v_1}, ..., \vec{v_k}) = \{c_1\vec{v_1} + ... + c_k\vec{v_k} : c_i \in \mathbb{R}\}
$$
```

### Example 2: Calculus

**Raw PDF Parse:**
```
The limit as x→∞ of f(x) is...
```

**AI Response:**
```markdown
According to the Calculus Review notes, the limit as $x \to \infty$ of $f(x)$ is:

$$
\lim_{x \to \infty} f(x) = L
$$
```

## Summary

- ✅ AI automatically converts PDF artifacts to LaTeX
- ✅ Sources cited by note title, not "Context 1"
- ✅ Frontend renders LaTeX beautifully
- ✅ Manual corrections available via chat prompts
- ✅ Works for most common mathematical notation

The system now handles poorly parsed PDFs gracefully, converting artifacts to proper mathematical notation automatically.
