"""
RAG (Retrieval-Augmented Generation) Service.

This module provides the core RAG functionality including document ingestion,
chunking, embedding, and semantic retrieval using ChromaDB.
"""

import uuid
from typing import Any, List

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import Settings
from app.core.interfaces import EmbeddingProvider


class RAGService:
    """
    RAG Service for managing document ingestion and retrieval.

    This service handles:
    - Document chunking
    - Embedding generation via EmbeddingProvider
    - Vector storage in ChromaDB
    - Semantic search and retrieval
    """

    def __init__(self, settings: Settings, embedding_provider: EmbeddingProvider) -> None:
        """
        Initialize the RAG service.

        Args:
            settings: Application settings containing ChromaDB configuration.
            embedding_provider: Provider for generating text embeddings.
        """
        self.settings = settings
        self.embedding_provider = embedding_provider

        # Initialize ChromaDB client with persistent storage
        chroma_path = settings.get_chroma_db_path()
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding.

        Uses simple character-based chunking with overlap for context preservation.

        Args:
            text: The input text to chunk.

        Returns:
            List of text chunks.
        """
        chunk_size = self.settings.rag_chunk_size
        chunk_overlap = self.settings.rag_chunk_overlap

        # Handle empty or very short text
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk from start to start + chunk_size
            end = start + chunk_size
            chunk = text[start:end]

            # Only add non-empty chunks
            if chunk.strip():
                chunks.append(chunk)

            # Move start position with overlap
            start += chunk_size - chunk_overlap

        return chunks

    async def ingest_note(
        self,
        note_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Ingest a note into the RAG system.

        This function:
        1. Chunks the note text
        2. Generates embeddings for each chunk
        3. Stores chunks and embeddings in ChromaDB

        Args:
            note_text: The text content of the note.
            metadata: Optional metadata to attach to the note chunks.

        Returns:
            A dictionary containing ingestion statistics and the note ID.

        Raises:
            Exception: If ingestion fails.
        """
        if not note_text or not note_text.strip():
            raise ValueError("Note text cannot be empty")

        # Generate a unique ID for this note
        note_id = str(uuid.uuid4())

        # Prepare metadata
        base_metadata = metadata or {}
        base_metadata["note_id"] = note_id

        # Chunk the text
        chunks = self.chunk_text(note_text)

        if not chunks:
            raise ValueError("Text chunking resulted in no chunks")

        # Generate embeddings for all chunks
        embeddings = await self.embedding_provider.get_embeddings_batch(chunks)

        # Prepare data for ChromaDB
        ids = [f"{note_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                **base_metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        # Add to ChromaDB collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        return {
            "note_id": note_id,
            "chunks_created": len(chunks),
            "total_characters": len(note_text),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
        }

    async def query_notes(
        self,
        query: str,
        k: int = 3,
        filter_metadata: dict[str, Any] | None = None,
    ) -> List[dict[str, Any]]:
        """
        Query the RAG system for relevant note chunks.

        This function:
        1. Generates an embedding for the query
        2. Performs semantic search in ChromaDB
        3. Returns the top k most similar chunks

        Args:
            query: The search query text.
            k: Number of results to return (default: 3, max: 100).
            filter_metadata: Optional metadata filters for the search.

        Returns:
            List of dictionaries containing:
            - id: Chunk ID
            - text: Chunk text content
            - metadata: Chunk metadata
            - distance: Similarity distance (lower = more similar)

        Raises:
            Exception: If query fails.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Limit k to reasonable bounds
        k = max(1, min(k, 100))

        # Generate embedding for the query
        query_embedding = await self.embedding_provider.get_embedding(query)

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                    }
                )

        return formatted_results

    async def delete_note(self, note_id: str) -> dict[str, Any]:
        """
        Delete all chunks associated with a note.

        Args:
            note_id: The ID of the note to delete.

        Returns:
            A dictionary with deletion statistics.
        """
        # Query to find all chunks with this note_id
        results = self.collection.get(
            where={"note_id": note_id},
            include=["metadatas"],
        )

        if not results["ids"]:
            return {
                "note_id": note_id,
                "chunks_deleted": 0,
                "found": False,
            }

        # Delete all chunks
        self.collection.delete(ids=results["ids"])

        return {
            "note_id": note_id,
            "chunks_deleted": len(results["ids"]),
            "found": True,
        }

    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the ChromaDB collection.

        Returns:
            Dictionary containing collection statistics.
        """
        count = self.collection.count()

        return {
            "collection_name": self.settings.chroma_collection_name,
            "total_chunks": count,
            "embedding_dimension": self.embedding_provider.get_embedding_dimension(),
        }

    def list_notes(self, limit: int = 100) -> List[dict[str, Any]]:
        """
        List all unique notes in the collection.

        Args:
            limit: Maximum number of notes to return.

        Returns:
            List of note summaries with metadata.
        """
        # Get all items from collection
        results = self.collection.get(
            limit=limit * 10,  # Get more to account for multiple chunks per note
            include=["metadatas"],
        )

        # Group by note_id
        notes_map: dict[str, dict[str, Any]] = {}
        for metadata in results.get("metadatas", []):
            note_id = metadata.get("note_id")
            if note_id and note_id not in notes_map:
                notes_map[note_id] = {
                    "note_id": note_id,
                    "metadata": {
                        k: v for k, v in metadata.items() if k not in ["note_id", "chunk_index", "total_chunks"]
                    },
                    "total_chunks": metadata.get("total_chunks", 1),
                }

        # Return limited list
        return list(notes_map.values())[:limit]

    def reset_collection(self) -> dict[str, str]:
        """
        Delete all data from the collection.

        WARNING: This is irreversible!

        Returns:
            Confirmation message.
        """
        self.client.delete_collection(name=self.settings.chroma_collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        return {
            "status": "success",
            "message": f"Collection '{self.settings.chroma_collection_name}' has been reset",
        }
