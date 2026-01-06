"""
Abstract Base Classes (Interfaces) for AI Layer Components.

This module defines the strategy pattern interfaces for LLM and Embedding providers,
enabling easy swapping between different implementations (e.g., Ollama, Anthropic).
"""

from abc import ABC, abstractmethod
from typing import List


class LLMProvider(ABC):
    """
    Abstract base class for Language Model providers.

    This interface defines the contract for all LLM implementations,
    allowing seamless switching between providers (Ollama, Anthropic, etc.).
    """

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a text response from the language model.

        Args:
            prompt: The input prompt/question to send to the LLM.

        Returns:
            The generated text response from the model.

        Raises:
            Exception: If the LLM service is unavailable or request fails.
        """
        pass

    @abstractmethod
    async def generate_response_stream(self, prompt: str):
        """
        Generate a streaming text response from the language model.

        Args:
            prompt: The input prompt/question to send to the LLM.

        Yields:
            Chunks of the generated text response as they become available.

        Raises:
            Exception: If the LLM service is unavailable or request fails.
        """
        pass


class EmbeddingProvider(ABC):
    """
    Abstract base class for Embedding providers.

    This interface defines the contract for all embedding implementations,
    allowing seamless switching between providers (Ollama, Anthropic, OpenAI, etc.).
    """

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The input text to generate embeddings for.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            Exception: If the embedding service is unavailable or request fails.
        """
        pass

    @abstractmethod
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts in a single batch.

        This is more efficient than calling get_embedding multiple times.

        Args:
            texts: A list of input texts to generate embeddings for.

        Returns:
            A list of embedding vectors, one for each input text.

        Raises:
            Exception: If the embedding service is unavailable or request fails.
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of the embedding vectors.

        Returns:
            The size of the embedding vector (e.g., 384, 768, 1536).
        """
        pass
