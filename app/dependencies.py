"""
Dependency Injection Factories.

This module provides factory functions for creating service instances
used throughout the application. These can be used with FastAPI's
dependency injection system.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.interfaces import EmbeddingProvider, LLMProvider
from app.services.ollama_service import OllamaEmbedding, OllamaLLM
from app.services.rag_service import RAGService
from app.services.study_service import StudyService


# Singleton instances for service reuse
_llm_provider: LLMProvider | None = None
_embedding_provider: EmbeddingProvider | None = None
_rag_service: RAGService | None = None
_study_service: StudyService | None = None


def get_llm_provider(
    settings: Annotated[Settings, Depends(get_settings)]
) -> LLMProvider:
    """
    Get or create the LLM provider instance.

    This factory creates a singleton instance of the LLM provider based on
    the application settings. Currently returns OllamaLLM, but can be
    extended to support other providers (e.g., Anthropic) in the future.

    Args:
        settings: Application settings injected by FastAPI.

    Returns:
        An instance of LLMProvider (currently OllamaLLM).

    Example:
        ```python
        @app.get("/generate")
        async def generate(llm: Annotated[LLMProvider, Depends(get_llm_provider)]):
            response = await llm.generate_response("Hello, world!")
            return {"response": response}
        ```
    """
    global _llm_provider

    if _llm_provider is None:
        # Future: Add logic to switch providers based on settings
        # if settings.provider_type == "anthropic":
        #     _llm_provider = AnthropicLLM(settings)
        # else:
        #     _llm_provider = OllamaLLM(settings)

        _llm_provider = OllamaLLM(settings)

    return _llm_provider


def get_embedding_provider(
    settings: Annotated[Settings, Depends(get_settings)]
) -> EmbeddingProvider:
    """
    Get or create the Embedding provider instance.

    This factory creates a singleton instance of the embedding provider based on
    the application settings. Currently returns OllamaEmbedding, but can be
    extended to support other providers (e.g., Anthropic, OpenAI) in the future.

    Args:
        settings: Application settings injected by FastAPI.

    Returns:
        An instance of EmbeddingProvider (currently OllamaEmbedding).

    Example:
        ```python
        @app.post("/embed")
        async def embed(
            text: str,
            embedding: Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
        ):
            vector = await embedding.get_embedding(text)
            return {"embedding": vector}
        ```
    """
    global _embedding_provider

    if _embedding_provider is None:
        # Future: Add logic to switch providers based on settings
        # if settings.provider_type == "anthropic":
        #     _embedding_provider = AnthropicEmbedding(settings)
        # else:
        #     _embedding_provider = OllamaEmbedding(settings)

        _embedding_provider = OllamaEmbedding(settings)

    return _embedding_provider


def get_rag_service(
    settings: Annotated[Settings, Depends(get_settings)],
    embedding: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> RAGService:
    """
    Get or create the RAG service instance.

    This factory creates a singleton instance of the RAG service with
    ChromaDB persistence and embedding capabilities.

    Args:
        settings: Application settings injected by FastAPI.
        embedding: Embedding provider for generating vectors.

    Returns:
        An instance of RAGService.

    Example:
        ```python
        @app.post("/ingest")
        async def ingest(
            note: str,
            rag: Annotated[RAGService, Depends(get_rag_service)]
        ):
            result = await rag.ingest_note(note)
            return result
        ```
    """
    global _rag_service

    if _rag_service is None:
        _rag_service = RAGService(settings, embedding)

    return _rag_service


def get_study_service(
    rag: Annotated[RAGService, Depends(get_rag_service)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> StudyService:
    """
    Get or create the Study Service instance.

    This factory creates a singleton instance of the Study Service for
    generating flashcards and quiz questions from user notes.

    Args:
        rag: RAG service for retrieving relevant context.
        llm: LLM provider for generating study materials.

    Returns:
        An instance of StudyService.

    Example:
        ```python
        @app.post("/flashcards")
        async def flashcards(
            topic: str,
            study: Annotated[StudyService, Depends(get_study_service)]
        ):
            result = await study.generate_flashcards(topic, count=5)
            return result
        ```
    """
    global _study_service

    if _study_service is None:
        _study_service = StudyService(rag_service=rag, llm_provider=llm)

    return _study_service


def reset_providers() -> None:
    """
    Reset all provider singletons.

    This is useful for testing or when you need to reinitialize
    providers with new settings.
    """
    global _llm_provider, _embedding_provider, _rag_service, _study_service
    _llm_provider = None
    _embedding_provider = None
    _rag_service = None
    _study_service = None


# Type aliases for cleaner dependency injection
LLMDep = Annotated[LLMProvider, Depends(get_llm_provider)]
EmbeddingDep = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
RAGDep = Annotated[RAGService, Depends(get_rag_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
