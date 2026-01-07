# RAG Notes App - Frontend

A modern React frontend for the RAG Notes App with local-first storage using IndexedDB.

## Features

- **Local-First Storage**: Notes are stored in your browser's IndexedDB
- **File Upload**: Upload .txt, .md, and .pdf files
- **Dual Storage**: Files are stored locally AND sent to backend for RAG indexing
- **AI Chat**: Ask questions about your notes using RAG-powered AI
- **Markdown Rendering**: Full markdown support with syntax highlighting, tables, and GitHub Flavored Markdown
- **Math Notation**: LaTeX/KaTeX rendering for mathematical expressions and equations
- **Source Citations**: See which notes were used to generate answers
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **IndexedDB** - Local browser storage (via `idb` library)
- **React Markdown** - Markdown rendering with GitHub Flavored Markdown support
- **KaTeX** - Fast LaTeX math rendering
- **Axios** - HTTP client for API calls
- **CSS3** - Modern styling with flexbox/grid

## Getting Started

### Prerequisites

- Node.js 20+ (recommended) or 18+
- npm or yarn
- FastAPI backend running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment (optional):
```bash
# Edit .env to change API URL
VITE_API_URL=http://localhost:8000
```

3. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
npm run preview  # Preview production build
```

## Usage

### Uploading Files

1. Click the "📤 Upload File" button in the left sidebar
2. Select a .txt, .md, or .pdf file
3. The file will be:
   - Parsed and stored locally in IndexedDB
   - Sent to the backend for RAG indexing
   - Added to your notes list

### Chatting with Notes

1. Type your question in the chat input at the bottom
2. Press Enter or click the send button
3. The AI will:
   - Search your notes for relevant context
   - Generate an answer based on your notes
   - Show source citations (expandable)

### Managing Notes

- Click on a note to select it (highlighted in blue)
- Click the 🗑️ button to delete a note from local storage
- Notes are sorted by newest first

### Markdown & Math Support

The chat interface supports full markdown rendering with LaTeX math notation:

**Markdown Features:**
- **Headers** (# H1, ## H2, ### H3, etc.)
- **Bold** (`**text**`) and *italic* (`*text*`)
- **Lists** (bulleted and numbered)
- **Code blocks** with syntax highlighting (```language```)
- **Inline code** (`code`)
- **Blockquotes** (> quote)
- **Tables** with GitHub Flavored Markdown
- **Links** ([text](url))
- **Horizontal rules** (---)

**Mathematical Notation (LaTeX/KaTeX):**
- **Inline math**: Use `$...$` for inline equations like $x^2 + y^2 = z^2$
- **Display math**: Use `$$...$$` for centered block equations:
  ```
  $$
  \vec{v} = \begin{bmatrix} x \\ y \\ z \end{bmatrix}
  $$
  ```
- **Supported symbols**: Greek letters (α, β, γ), operators (∑, ∫, ∂), vectors, matrices, and more
- **Examples**:
  - Vectors: `$\vec{e_1}, \vec{e_2}$` → $\vec{e_1}, \vec{e_2}$
  - Fractions: `$\frac{a}{b}$` → $\frac{a}{b}$
  - Subscripts/Superscripts: `$x_i^2$` → $x_i^2$
  - Matrices: `$\begin{bmatrix} a & b \\ c & d \end{bmatrix}$`

The AI's responses are automatically rendered with proper formatting, making mathematical explanations, code examples, and structured content easy to read.

**Note**: The AI has been instructed to use proper LaTeX notation for mathematical expressions. If you see weird characters like `# »e1` in the AI's responses (from poorly parsed PDFs), you can ask the AI to "rewrite that with proper LaTeX notation" and it will format it correctly as $\vec{e_1}$.

For a complete guide on LaTeX math notation, see `MATH_NOTATION_GUIDE.md` in the project root.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── NoteList.jsx        # Left column - note list & file upload
│   │   ├── NoteList.css
│   │   ├── Chat.jsx             # Right column - chat interface
│   │   └── Chat.css
│   ├── services/
│   │   ├── noteStore.js         # IndexedDB service
│   │   └── api.js               # FastAPI backend client
│   ├── utils/
│   │   └── fileReader.js        # File reading utilities
│   ├── App.jsx                  # Main app component
│   ├── App.css
│   ├── main.jsx                 # Entry point
│   └── index.css
├── .env                         # Environment configuration
├── package.json
└── vite.config.js
```

## API Integration

The app communicates with these FastAPI endpoints:

### File Upload
- **POST** `/api/notes/upload`
- Uploads raw file for RAG indexing
- Returns: `{ note_id, filename, file_type, chunks_created, total_characters, file_size }`

### Chat
- **POST** `/api/chat/chat`
- Sends chat query with parameters
- Body: `{ query, k, include_sources }`
- Returns: `{ answer, context_used, has_context, num_chunks }`

## IndexedDB Schema

**Database Name**: `rag-notes-db`

**Note Object**:
```javascript
{
  id: string,              // Unique note ID
  title: string,           // Note title (from filename)
  content: string,         // Full note content
  timestamp: number,       // Creation timestamp (milliseconds)
  backendNoteId: string,   // Backend note ID
  filename: string,        // Original filename
  chunksCreated: number    // Chunks created in backend
}
```

## Troubleshooting

### Backend Connection Issues

If you see API errors:
1. Verify FastAPI backend is running: `http://localhost:8000/docs`
2. Check CORS settings in backend (should allow `http://localhost:5173`)
3. Check `.env` file for correct `VITE_API_URL`

### IndexedDB Issues

If notes aren't saving:
1. Check browser console for errors
2. Clear browser data (Storage → IndexedDB)
3. Try a different browser (Chrome/Firefox recommended)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 15+

## Development

```bash
npm run dev      # Start dev server with HMR
npm run build    # Build for production
npm run preview  # Preview production build
```
