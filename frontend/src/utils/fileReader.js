/**
 * File Reader Utility.
 *
 * Utilities for reading file contents in the browser.
 */

/**
 * Read a text file and return its contents as a string.
 *
 * @param {File} file - The file object to read
 * @returns {Promise<string>} The file contents as text
 */
export async function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      resolve(event.target.result);
    };

    reader.onerror = (error) => {
      reject(new Error(`Failed to read file: ${error}`));
    };

    reader.readAsText(file);
  });
}

/**
 * Read a file and return its contents as a data URL.
 *
 * @param {File} file - The file object to read
 * @returns {Promise<string>} The file contents as a data URL
 */
export async function readFileAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      resolve(event.target.result);
    };

    reader.onerror = (error) => {
      reject(new Error(`Failed to read file: ${error}`));
    };

    reader.readAsDataURL(file);
  });
}

/**
 * Generate a unique ID for a note.
 *
 * @returns {string} A unique ID
 */
export function generateNoteId() {
  return `note_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Extract title from filename.
 *
 * @param {string} filename - The filename
 * @returns {string} The title (filename without extension)
 */
export function extractTitleFromFilename(filename) {
  return filename.replace(/\.[^/.]+$/, '');
}

/**
 * Format timestamp to readable date string.
 *
 * @param {number} timestamp - Unix timestamp in milliseconds
 * @returns {string} Formatted date string
 */
export function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Truncate text to a specified length.
 *
 * @param {string} text - The text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text with ellipsis
 */
export function truncateText(text, maxLength = 100) {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + '...';
}
