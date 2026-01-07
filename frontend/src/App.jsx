/**
 * Main App Component.
 *
 * Two-column layout:
 * - Left: Note list with file upload
 * - Right: Chat interface
 */

import { useState } from 'react';
import NoteList from './components/NoteList';
import Chat from './components/Chat';
import './App.css';

function App() {
  const [selectedNote, setSelectedNote] = useState(null);

  return (
    <div className="app">
      <header className="app-header">
        <h1>📚 RAG Notes App</h1>
        <p>Local-first note management with AI-powered chat</p>
      </header>

      <div className="app-layout">
        <aside className="sidebar">
          <NoteList onNoteSelect={setSelectedNote} />
        </aside>

        <main className="main-content">
          <Chat selectedNote={selectedNote} />
        </main>
      </div>
    </div>
  );
}

export default App;
