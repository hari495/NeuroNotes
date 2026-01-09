/**
 * API Service for FastAPI Backend Communication.
 *
 * Handles all HTTP requests to the FastAPI backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload a file to the backend for RAG indexing.
 *
 * @param {File} file - The file object to upload
 * @returns {Promise<Object>} The API response data
 */
export async function uploadFileToBackend(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(
    `${API_BASE_URL}/api/notes/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 second timeout
    }
  );

  return response.data;
}

/**
 * Create a note on the backend.
 *
 * @param {string} title - Note title
 * @param {string} text - Note content
 * @returns {Promise<Object>} The API response data
 */
export async function createNoteOnBackend(title, text) {
  const response = await axios.post(
    `${API_BASE_URL}/api/notes/`,
    {
      title,
      text,
    },
    {
      timeout: 30000,
    }
  );

  return response.data;
}

/**
 * Send a chat message to the backend.
 *
 * @param {string} query - The user's question
 * @param {number} k - Number of context chunks to retrieve (default: 3)
 * @param {boolean} includeSources - Whether to include sources (default: true)
 * @param {string|null} noteId - Filter by specific note ID (null = search all notes)
 * @returns {Promise<Object>} The API response data
 */
export async function sendChatMessage(query, k = 3, includeSources = true, noteId = null) {
  const response = await axios.post(
    `${API_BASE_URL}/api/chat/chat`,
    {
      query,
      k,
      include_sources: includeSources,
      note_id: noteId,
    },
    {
      timeout: 120000, // 2 minute timeout for LLM generation
    }
  );

  return response.data;
}

/**
 * Get collection statistics from the backend.
 *
 * @returns {Promise<Object>} Collection stats
 */
export async function getCollectionStats() {
  const response = await axios.get(
    `${API_BASE_URL}/api/notes/stats`,
    {
      timeout: 10000,
    }
  );

  return response.data;
}

/**
 * List all notes from the backend.
 *
 * @param {number} limit - Maximum number of notes to return
 * @returns {Promise<Object>} List of notes
 */
export async function listBackendNotes(limit = 100) {
  const response = await axios.get(
    `${API_BASE_URL}/api/notes/list`,
    {
      params: { limit },
      timeout: 10000,
    }
  );

  return response.data;
}

/**
 * Query notes from the backend (semantic search).
 *
 * @param {string} query - Search query
 * @param {number} k - Number of results to return
 * @returns {Promise<Object>} Query results
 */
export async function queryNotes(query, k = 3) {
  const response = await axios.post(
    `${API_BASE_URL}/api/notes/query`,
    {
      query,
      k,
    },
    {
      timeout: 30000,
    }
  );

  return response.data;
}

/**
 * Generate flashcards for a topic using RAG + LLM.
 *
 * @param {string} topic - Topic to generate flashcards for
 * @param {number} count - Number of flashcards to generate (1-10, default: 5)
 * @returns {Promise<Object>} Flashcard response with cards and sources
 */
export async function generateFlashcards(topic, count = 5) {
  const response = await axios.post(
    `${API_BASE_URL}/api/study/flashcards`,
    null,
    {
      params: { topic, count },
      timeout: 60000, // 60 second timeout for LLM generation
    }
  );

  return response.data;
}

/**
 * Generate a quiz question for a topic using RAG + LLM.
 *
 * @param {string} topic - Topic for the quiz question
 * @param {string} difficulty - Difficulty level: "easy", "medium", or "hard" (default: "medium")
 * @returns {Promise<Object>} Quiz response with question, options, and sources
 */
export async function generateQuiz(topic, difficulty = 'medium') {
  const response = await axios.post(
    `${API_BASE_URL}/api/study/quiz`,
    null,
    {
      params: { topic, difficulty },
      timeout: 60000, // 60 second timeout for LLM generation
    }
  );

  return response.data;
}

/**
 * Health check for the API.
 *
 * @returns {Promise<boolean>} True if API is reachable
 */
export async function checkApiHealth() {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`, {
      timeout: 5000,
    });
    return response.status === 200;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
}
