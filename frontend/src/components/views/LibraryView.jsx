import { useState, useEffect } from 'react'
import { Upload, FileText, Trash2, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { uploadFileToBackend } from '@/services/api'
import { getAllNotes, addNote, deleteNote } from '@/services/noteStore'

export default function LibraryView({ onNoteSelect }) {
  const [notes, setNotes] = useState([])
  const [uploading, setUploading] = useState(false)
  const [selectedNoteId, setSelectedNoteId] = useState(null)

  useEffect(() => {
    loadNotes()
  }, [])

  const loadNotes = async () => {
    const loadedNotes = await getAllNotes()
    setNotes(loadedNotes)
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      const response = await uploadFileToBackend(file)

      const note = {
        id: `note_${Date.now()}`,
        title: file.name,
        content: '', // Not stored locally
        timestamp: Date.now(),
        backendNoteId: response.note_id,
        filename: file.name,
        chunksCreated: response.chunks_created,
      }

      await addNote(note)
      await loadNotes()
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (noteId) => {
    if (!confirm('Delete this note?')) return
    await deleteNote(noteId)
    await loadNotes()
    if (selectedNoteId === noteId) {
      setSelectedNoteId(null)
      onNoteSelect?.(null)
    }
  }

  const handleSelect = (note) => {
    setSelectedNoteId(note.id)
    onNoteSelect?.(note)
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-card p-4">
        <h2 className="text-lg font-semibold tracking-tight">Library</h2>
        <p className="text-sm text-muted-foreground">Upload and manage your notes</p>
      </div>

      {/* Upload */}
      <div className="border-b bg-card p-4">
        <label htmlFor="file-upload" className="block">
          <Button className="w-full" disabled={uploading} asChild>
            <span>
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload File
                </>
              )}
            </span>
          </Button>
          <input
            id="file-upload"
            type="file"
            accept=".txt,.md,.pdf"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>
      </div>

      {/* Notes List */}
      <ScrollArea className="flex-1">
        <div className="space-y-2 p-4">
          {notes.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
              <p className="mt-4 text-sm text-muted-foreground">
                No notes yet. Upload a file to get started.
              </p>
            </div>
          ) : (
            notes.map((note) => (
              <Card
                key={note.id}
                className={`cursor-pointer p-4 transition-colors hover:bg-accent ${
                  selectedNoteId === note.id ? 'bg-accent' : ''
                }`}
                onClick={() => handleSelect(note)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <p className="truncate font-medium text-sm">{note.title}</p>
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{new Date(note.timestamp).toLocaleDateString()}</span>
                      {note.chunksCreated && (
                        <>
                          <Separator orientation="vertical" className="h-4" />
                          <Badge variant="secondary" className="text-xs">
                            {note.chunksCreated} chunks
                          </Badge>
                        </>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(note.id)
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
