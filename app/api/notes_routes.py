"""
Notes API Routes.

This module provides REST API endpoints for managing notes in the RAG system,
including ingestion, querying, and deletion.
"""

from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import RAGDep


router = APIRouter()


# Request/Response Models
class IngestNoteRequest(BaseModel):
    """Request model for ingesting a note."""

    text: str = Field(
        ...,
        description="The text content of the note",
        min_length=1,
        max_length=100000,
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata to attach to the note (e.g., title, author, tags)",
    )


class IngestNoteResponse(BaseModel):
    """Response model for note ingestion."""

    note_id: str = Field(..., description="Unique ID of the ingested note")
    chunks_created: int = Field(..., description="Number of chunks created from the note")
    total_characters: int = Field(..., description="Total character count of the note")
    embedding_dimension: int = Field(..., description="Dimension of the embedding vectors")


class QueryNotesRequest(BaseModel):
    """Request model for querying notes."""

    query: str = Field(
        ...,
        description="The search query text",
        min_length=1,
        max_length=1000,
    )
    k: int = Field(
        default=3,
        description="Number of results to return",
        ge=1,
        le=20,
    )
    filter_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata filters (e.g., {'author': 'John'})",
    )


class QueryResult(BaseModel):
    """Model for a single query result."""

    id: str = Field(..., description="Chunk ID")
    text: str = Field(..., description="Chunk text content")
    metadata: dict[str, Any] = Field(..., description="Chunk metadata")
    distance: float = Field(
        ...,
        description="Similarity distance (lower = more similar)",
    )


class QueryNotesResponse(BaseModel):
    """Response model for note queries."""

    query: str = Field(..., description="The search query that was executed")
    results: List[QueryResult] = Field(..., description="List of matching chunks")
    count: int = Field(..., description="Number of results returned")


class DeleteNoteResponse(BaseModel):
    """Response model for note deletion."""

    note_id: str = Field(..., description="ID of the note that was deleted")
    chunks_deleted: int = Field(..., description="Number of chunks deleted")
    found: bool = Field(..., description="Whether the note was found")


class CollectionStatsResponse(BaseModel):
    """Response model for collection statistics."""

    collection_name: str = Field(..., description="Name of the ChromaDB collection")
    total_chunks: int = Field(..., description="Total number of chunks in the collection")
    embedding_dimension: int = Field(..., description="Dimension of embedding vectors")


class NoteInfo(BaseModel):
    """Model for note information."""

    note_id: str = Field(..., description="Unique note ID")
    metadata: dict[str, Any] = Field(..., description="Note metadata")
    total_chunks: int = Field(..., description="Number of chunks for this note")


class ListNotesResponse(BaseModel):
    """Response model for listing notes."""

    notes: List[NoteInfo] = Field(..., description="List of notes")
    count: int = Field(..., description="Number of notes returned")


class CreateNoteRequest(BaseModel):
    """Simplified request model for creating a note."""

    title: str = Field(
        ...,
        description="The title of the note",
        min_length=1,
        max_length=500,
    )
    text: str = Field(
        ...,
        description="The text content of the note",
        min_length=1,
        max_length=100000,
    )


# API Endpoints
@router.post("/", response_model=IngestNoteResponse)
async def create_note(request: CreateNoteRequest, rag: RAGDep) -> IngestNoteResponse:
    """
    Create a new note (simplified endpoint).

    This is a simplified version of /ingest that accepts title and text.
    The title is automatically added to metadata.

    Args:
        request: Note creation request with title and text.

    Returns:
        Information about the created note and chunks.
    """
    try:
        result = await rag.ingest_note(
            note_text=request.text,
            metadata={"title": request.title},
        )
        return IngestNoteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create note: {str(e)}",
        )


@router.post("/ingest", response_model=IngestNoteResponse)
async def ingest_note(request: IngestNoteRequest, rag: RAGDep) -> IngestNoteResponse:
    """
    Ingest a note into the RAG system.

    This endpoint:
    1. Chunks the note text
    2. Generates embeddings for each chunk
    3. Stores chunks in ChromaDB for semantic search

    Example metadata:
    ```json
    {
        "title": "My Research Notes",
        "author": "John Doe",
        "tags": ["machine-learning", "research"],
        "created_at": "2024-01-01"
    }
    ```
    """
    try:
        result = await rag.ingest_note(
            note_text=request.text,
            metadata=request.metadata,
        )
        return IngestNoteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest note: {str(e)}",
        )


@router.post("/query", response_model=QueryNotesResponse)
async def query_notes(request: QueryNotesRequest, rag: RAGDep) -> QueryNotesResponse:
    """
    Query the RAG system for relevant note chunks.

    This endpoint performs semantic search to find the most relevant
    note chunks based on the query text.

    The results are sorted by similarity (lowest distance = most similar).
    """
    try:
        results = await rag.query_notes(
            query=request.query,
            k=request.k,
            filter_metadata=request.filter_metadata,
        )

        return QueryNotesResponse(
            query=request.query,
            results=[QueryResult(**r) for r in results],
            count=len(results),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query notes: {str(e)}",
        )


@router.delete("/{note_id}", response_model=DeleteNoteResponse)
async def delete_note(note_id: str, rag: RAGDep) -> DeleteNoteResponse:
    """
    Delete a note and all its chunks from the RAG system.

    Args:
        note_id: The unique ID of the note to delete.

    Returns:
        Information about the deletion operation.
    """
    try:
        result = await rag.delete_note(note_id)
        return DeleteNoteResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete note: {str(e)}",
        )


@router.get("/stats", response_model=CollectionStatsResponse)
async def get_collection_stats(rag: RAGDep) -> CollectionStatsResponse:
    """
    Get statistics about the note collection.

    Returns information about the total number of chunks, collection name,
    and embedding dimensions.
    """
    try:
        stats = rag.get_collection_stats()
        return CollectionStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.get("/list", response_model=ListNotesResponse)
async def list_notes(limit: int = 100, rag: RAGDep = RAGDep) -> ListNotesResponse:
    """
    List all notes in the collection.

    Args:
        limit: Maximum number of notes to return (default: 100, max: 1000).

    Returns:
        List of notes with their metadata and chunk counts.
    """
    try:
        # Limit to reasonable bounds
        limit = max(1, min(limit, 1000))

        notes = rag.list_notes(limit=limit)
        return ListNotesResponse(
            notes=[NoteInfo(**n) for n in notes],
            count=len(notes),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list notes: {str(e)}",
        )


@router.post("/reset")
async def reset_collection(rag: RAGDep) -> dict[str, str]:
    """
    Reset the entire collection.

    WARNING: This deletes ALL notes and chunks! This action is irreversible!

    Use with caution - typically only for development/testing.
    """
    try:
        result = rag.reset_collection()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset collection: {str(e)}",
        )
