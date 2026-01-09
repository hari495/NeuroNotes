/**
 * Main App Component.
 *
 * Linear-style UI with AppShell layout:
 * - Sidebar navigation (Chat, Flashcards, Library)
 * - View components with shadcn/ui styling
 */

import { useState } from 'react'
import AppShell from './components/layout/AppShell'
import ChatView from './components/views/ChatView'
import FlashcardsView from './components/views/FlashcardsView'
import LibraryView from './components/views/LibraryView'

export default function App() {
  const [activeView, setActiveView] = useState('chat')
  const [selectedNote, setSelectedNote] = useState(null)

  const renderView = () => {
    switch (activeView) {
      case 'chat':
        return <ChatView selectedNote={selectedNote} />
      case 'flashcards':
        return <FlashcardsView />
      case 'library':
        return <LibraryView onNoteSelect={setSelectedNote} />
      default:
        return <ChatView selectedNote={selectedNote} />
    }
  }

  return (
    <AppShell activeView={activeView} onViewChange={setActiveView}>
      {renderView()}
    </AppShell>
  )
}
