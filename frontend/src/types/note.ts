/**
 * Type definitions for the Notes system.
 */

export interface Note {
  id: string;
  title: string;
  content: string;
  timestamp: number;
  backendNoteId?: string;
  filename?: string;
  chunksCreated?: number;
}

export interface UploadStatus {
  success: boolean;
  message: string;
}
