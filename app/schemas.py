"""
Pydantic schemas for API request/response models.

This module centralizes all Pydantic models used across the application,
including Study Mode (flashcards, quizzes) and existing API models.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal


# ==================== STUDY MODE MODELS ====================

class Flashcard(BaseModel):
    """Single flashcard with front and back."""

    front: str = Field(..., min_length=1, description="Concept, term, or question")
    back: str = Field(..., min_length=1, max_length=500, description="Concise answer (max 2 sentences)")


class FlashcardResponse(BaseModel):
    """Response containing generated flashcards."""

    topic: str
    count: int
    cards: List[Flashcard]
    context_sources: List[str] = Field(default_factory=list, description="Titles of notes used")


class MCQOption(BaseModel):
    """Single multiple-choice option."""

    text: str = Field(..., min_length=1, description="Option text")
    is_correct: bool = Field(..., description="True if this is the correct answer")


class QuizQuestion(BaseModel):
    """Single multiple-choice question."""

    question: str = Field(..., min_length=1, description="The question text")
    options: List[MCQOption] = Field(..., min_items=4, max_items=4, description="Exactly 4 options")
    explanation: str = Field(..., min_length=1, description="Explanation of correct answer")

    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        """Ensure exactly 1 correct answer."""
        correct_count = sum(1 for opt in v if opt.is_correct)
        if correct_count != 1:
            raise ValueError(f"Must have exactly 1 correct answer, found {correct_count}")
        return v


class QuizResponse(BaseModel):
    """Response containing generated quiz question."""

    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    question: QuizQuestion
    context_sources: List[str] = Field(default_factory=list, description="Titles of notes used")


# ==================== EXISTING API MODELS ====================
# These models are used by existing endpoints (chat, notes, etc.)

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    query: str = Field(
        ...,
        description="The user's question or query",
        min_length=1,
        max_length=2000,
    )
    k: int = Field(
        default=5,
        description="Number of context chunks to retrieve from notes (after re-ranking)",
        ge=1,
        le=10,
    )
    note_id: str | None = Field(
        default=None,
        description="Filter by specific note ID (searches only that note)",
    )
    filter_metadata: dict | None = Field(
        default=None,
        description="Optional metadata filters for context retrieval",
    )
    include_sources: bool = Field(
        default=True,
        description="Whether to include source information in the response",
    )


class ContextChunk(BaseModel):
    """Model for a context chunk used in the response."""

    text: str = Field(..., description="The text content of the chunk")
    metadata: dict = Field(..., description="Metadata about the chunk")
    distance: float = Field(..., description="Similarity distance (lower = more relevant)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    query: str = Field(..., description="The user's original query")
    answer: str = Field(..., description="The LLM-generated answer")
    context_used: List[ContextChunk] = Field(
        ...,
        description="The context chunks used to generate the answer",
    )
    num_chunks: int = Field(..., description="Number of context chunks used")
    has_context: bool = Field(
        ...,
        description="Whether any relevant context was found",
    )
