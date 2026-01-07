/**
 * Local Note Store Service using IndexedDB.
 *
 * This service manages notes in the browser's IndexedDB.
 * Note structure: { id, title, content, timestamp }
 */

import { openDB } from 'idb';

const DB_NAME = 'rag-notes-db';
const STORE_NAME = 'notes';
const DB_VERSION = 1;

/**
 * Initialize the IndexedDB database.
 *
 * @returns {Promise<IDBDatabase>} The opened database instance
 */
async function initDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      // Create the notes object store if it doesn't exist
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, {
          keyPath: 'id',
          autoIncrement: false
        });

        // Create indexes
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('title', 'title', { unique: false });
      }
    },
  });
}

/**
 * Add a new note to the store.
 *
 * @param {Object} note - The note object
 * @param {string} note.id - Unique ID for the note
 * @param {string} note.title - Note title
 * @param {string} note.content - Note content
 * @param {number} [note.timestamp] - Creation timestamp (defaults to now)
 * @returns {Promise<string>} The ID of the added note
 */
export async function addNote(note) {
  const db = await initDB();

  // Ensure timestamp exists
  const noteWithTimestamp = {
    ...note,
    timestamp: note.timestamp || Date.now(),
  };

  await db.add(STORE_NAME, noteWithTimestamp);
  return noteWithTimestamp.id;
}

/**
 * Get all notes from the store, sorted by timestamp (newest first).
 *
 * @returns {Promise<Array>} Array of note objects
 */
export async function getAllNotes() {
  const db = await initDB();
  const notes = await db.getAllFromIndex(STORE_NAME, 'timestamp');

  // Return in reverse order (newest first)
  return notes.reverse();
}

/**
 * Get a single note by ID.
 *
 * @param {string} id - The note ID
 * @returns {Promise<Object|undefined>} The note object or undefined if not found
 */
export async function getNote(id) {
  const db = await initDB();
  return db.get(STORE_NAME, id);
}

/**
 * Update an existing note.
 *
 * @param {string} id - The note ID to update
 * @param {Object} updates - Partial note object with fields to update
 * @returns {Promise<void>}
 */
export async function updateNote(id, updates) {
  const db = await initDB();
  const note = await db.get(STORE_NAME, id);

  if (!note) {
    throw new Error(`Note with id ${id} not found`);
  }

  const updatedNote = {
    ...note,
    ...updates,
    id, // Ensure ID doesn't change
  };

  await db.put(STORE_NAME, updatedNote);
}

/**
 * Delete a note by ID.
 *
 * @param {string} id - The note ID to delete
 * @returns {Promise<void>}
 */
export async function deleteNote(id) {
  const db = await initDB();
  await db.delete(STORE_NAME, id);
}

/**
 * Delete all notes from the store.
 *
 * @returns {Promise<void>}
 */
export async function clearAllNotes() {
  const db = await initDB();
  await db.clear(STORE_NAME);
}

/**
 * Get the count of notes in the store.
 *
 * @returns {Promise<number>} The number of notes
 */
export async function getNotesCount() {
  const db = await initDB();
  return db.count(STORE_NAME);
}

/**
 * Search notes by title (case-insensitive partial match).
 *
 * @param {string} searchTerm - The term to search for
 * @returns {Promise<Array>} Array of matching notes
 */
export async function searchNotesByTitle(searchTerm) {
  const db = await initDB();
  const allNotes = await db.getAllFromIndex(STORE_NAME, 'timestamp');

  const lowerSearchTerm = searchTerm.toLowerCase();
  return allNotes.filter(note =>
    note.title.toLowerCase().includes(lowerSearchTerm)
  ).reverse();
}
