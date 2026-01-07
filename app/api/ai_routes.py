"""
AI API Routes.

This module provides example API endpoints demonstrating how to use
the LLM and Embedding services with FastAPI dependency injection.
"""

from typing import List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.dependencies import EmbeddingDep, LLMDep


router = APIRouter()


# Request/Response Models
class GenerateRequest(BaseModel):
    """Request model for text generation."""

    prompt: str = Field(
        ...,
        description="The prompt to send to the LLM",
        min_length=1,
        max_length=4000,
    )


class GenerateResponse(BaseModel):
    """Response model for text generation."""

    response: str = Field(..., description="The generated text from the LLM")
    model: str = Field(..., description="The model used for generation")


class EmbedRequest(BaseModel):
    """Request model for embedding generation."""

    text: str = Field(
        ...,
        description="The text to generate embeddings for",
        min_length=1,
        max_length=8000,
    )


class EmbedBatchRequest(BaseModel):
    """Request model for batch embedding generation."""

    texts: List[str] = Field(
        ...,
        description="List of texts to generate embeddings for",
        min_length=1,
        max_length=100,
    )


class EmbedResponse(BaseModel):
    """Response model for embedding generation."""

    embedding: List[float] = Field(..., description="The embedding vector")
    dimension: int = Field(..., description="Dimension of the embedding vector")
    model: str = Field(..., description="The model used for embeddings")


class EmbedBatchResponse(BaseModel):
    """Response model for batch embedding generation."""

    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimension: int = Field(..., description="Dimension of the embedding vectors")
    count: int = Field(..., description="Number of embeddings generated")
    model: str = Field(..., description="The model used for embeddings")


# API Endpoints
@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest, llm: LLMDep) -> GenerateResponse:
    """
    Generate text using the LLM.

    This endpoint demonstrates how to use the LLM provider with
    FastAPI dependency injection.
    """
    response = await llm.generate_response(request.prompt)

    return GenerateResponse(
        response=response,
        model=llm.model,  # type: ignore
    )


@router.post("/generate/stream")
async def generate_text_stream(request: GenerateRequest, llm: LLMDep) -> StreamingResponse:
    """
    Generate text using the LLM with streaming.

    This endpoint demonstrates streaming responses, which is useful
    for long-form content generation.
    """

    async def stream_generator():
        """Generate streaming response chunks."""
        async for chunk in llm.generate_response_stream(request.prompt):
            yield chunk

    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",
    )


@router.post("/embed", response_model=EmbedResponse)
async def generate_embedding(
    request: EmbedRequest, embedding: EmbeddingDep
) -> EmbedResponse:
    """
    Generate an embedding vector for text.

    This endpoint demonstrates how to use the embedding provider
    to convert text into vector representations.
    """
    vector = await embedding.get_embedding(request.text)
    dimension = embedding.get_embedding_dimension()

    return EmbedResponse(
        embedding=vector,
        dimension=dimension,
        model=embedding.model,  # type: ignore
    )


@router.post("/embed/batch", response_model=EmbedBatchResponse)
async def generate_embeddings_batch(
    request: EmbedBatchRequest, embedding: EmbeddingDep
) -> EmbedBatchResponse:
    """
    Generate embedding vectors for multiple texts.

    This endpoint is more efficient than calling /embed multiple times
    as it processes texts concurrently.
    """
    vectors = await embedding.get_embeddings_batch(request.texts)
    dimension = embedding.get_embedding_dimension()

    return EmbedBatchResponse(
        embeddings=vectors,
        dimension=dimension,
        count=len(vectors),
        model=embedding.model,  # type: ignore
    )


@router.get("/health")
async def health_check(llm: LLMDep, embedding: EmbeddingDep) -> dict[str, bool]:
    """
    Check the health of AI services.

    Returns the status of both LLM and embedding services.
    """
    llm_healthy = await llm.health_check()  # type: ignore
    embedding_healthy = await embedding.health_check()  # type: ignore

    return {
        "llm_healthy": llm_healthy,
        "embedding_healthy": embedding_healthy,
        "overall_healthy": llm_healthy and embedding_healthy,
    }
