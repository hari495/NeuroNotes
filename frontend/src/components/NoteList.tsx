/**
 * NoteList Component.
 *
 * Displays a list of notes from IndexedDB with file upload functionality.
 */

import { useState, useEffect } from 'react';
import { getAllNotes, addNote, deleteNote } from '../services/noteStore';
import { uploadFileToBackend } from '../services/api';
import {
  readFileAsText,
  generateNoteId,
  extractTitleFromFilename,
  formatTimestamp,
  truncateText,
} from '../utils/fileReader';
import type { Note, UploadStatus } from '../types/note';
import './NoteList.css';

interface NoteListProps {
  onNoteSelect?: (note: Note | null) => void;
}

function NoteList({ onNoteSelect }: NoteListProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load notes from IndexedDB on mount
  useEffect(() => {
    loadNotes();
  }, []);

  const loadNotes = async () => {
    try {
      const loadedNotes = await getAllNotes();
      setNotes(loadedNotes);
    } catch (err) {
      console.error('Failed to load notes:', err);
      setError('Failed to load notes from local storage');
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus(null);
    setError(null);

    try {
      // Step 1: Read file content for local display
      const content = await readFileAsText(file);
      const title = extractTitleFromFilename(file.name);
      const noteId = generateNoteId();

      // Step 2: Upload raw file to FastAPI backend for RAG indexing
      console.log('Uploading file to backend:', file.name);
      const backendResponse = await uploadFileToBackend(file);
      console.log('Backend response:', backendResponse);

      // Step 3: Save to IndexedDB
      const note: Note = {
        id: noteId,
        title: title,
        content: content,
        timestamp: Date.now(),
        backendNoteId: backendResponse.note_id,
        filename: file.name,
        chunksCreated: backendResponse.chunks_created,
      };

      await addNote(note);

      // Step 4: Reload notes list
      await loadNotes();

      setUploadStatus({
        success: true,
        message: `✅ Uploaded "${file.name}" - ${backendResponse.chunks_created} chunks created`,
      });

      // Clear the file input
      event.target.value = '';
    } catch (err: any) {
      console.error('File upload failed:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to upload file');
      setUploadStatus({
        success: false,
        message: `❌ Upload failed: ${err.response?.data?.detail || err.message}`,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleNoteClick = (note: Note) => {
    setSelectedNoteId(note.id);
    if (onNoteSelect) {
      onNoteSelect(note);
    }
  };

  const handleDeleteNote = async (noteId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent note selection when deleting

    if (!confirm('Are you sure you want to delete this note from local storage?')) {
      return;
    }

    try {
      await deleteNote(noteId);
      await loadNotes();

      if (selectedNoteId === noteId) {
        setSelectedNoteId(null);
        if (onNoteSelect) {
          onNoteSelect(null);
        }
      }
    } catch (err) {
      console.error('Failed to delete note:', err);
      setError('Failed to delete note');
    }
  };

  return (
    <div className="note-list-container">
      <div className="note-list-header">
        <h2>📚 Local Notes</h2>
        <p className="note-count">{notes.length} note{notes.length !== 1 ? 's' : ''}</p>
      </div>

      {/* File Upload Section */}
      <div className="upload-section">
        <label htmlFor="file-upload" className="upload-button">
          📤 Upload File
        </label>
        <input
          id="file-upload"
          type="file"
          accept=".txt,.md,.pdf"
          onChange={handleFileUpload}
          disabled={isUploading}
          style={{ display: 'none' }}
        />

        {isUploading && (
          <div className="upload-status uploading">
            <div className="spinner"></div>
            <span>Uploading...</span>
          </div>
        )}

        {uploadStatus && (
          <div className={`upload-status ${uploadStatus.success ? 'success' : 'error'}`}>
            {uploadStatus.message}
          </div>
        )}

        {error && (
          <div className="upload-status error">
            ❌ {error}
          </div>
        )}
      </div>

      {/* Notes List */}
      <div className="notes-list">
        {notes.length === 0 ? (
          <div className="empty-state">
            <p>No notes yet</p>
            <p className="empty-hint">Upload a file to get started</p>
          </div>
        ) : (
          notes.map((note) => (
            <div
              key={note.id}
              className={`note-item ${selectedNoteId === note.id ? 'selected' : ''}`}
              onClick={() => handleNoteClick(note)}
            >
              <div className="note-item-header">
                <h3 className="note-title">{note.title}</h3>
                <button
                  className="delete-button"
                  onClick={(e) => handleDeleteNote(note.id, e)}
                  title="Delete note"
                >
                  🗑️
                </button>
              </div>
              <p className="note-preview">{truncateText(note.content, 80)}</p>
              <div className="note-meta">
                <span className="note-date">{formatTimestamp(note.timestamp)}</span>
                {note.chunksCreated && (
                  <span className="note-chunks">{note.chunksCreated} chunks</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info Section */}
      <div className="info-section">
        <p className="info-text">
          💡 Notes are stored locally in your browser and indexed in the backend for AI chat.
        </p>
        <p className="info-text">
          📁 Supported formats: .txt, .md, .pdf
        </p>
      </div>
    </div>
  );
}

export default NoteList;
