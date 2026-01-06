"""
Ollama Service Implementations.

This module provides concrete implementations of LLMProvider and EmbeddingProvider
using Ollama for local AI processing.
"""

import asyncio
from typing import Any, AsyncGenerator, List

import ollama
from ollama import AsyncClient

from app.core.config import Settings
from app.core.interfaces import EmbeddingProvider, LLMProvider


class OllamaLLM(LLMProvider):
    """
    Ollama implementation of the LLM Provider.

    This class uses the Ollama API to generate text responses using local models.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the Ollama LLM service.

        Args:
            settings: Application settings containing Ollama configuration.
        """
        self.settings = settings
        self.client = AsyncClient(host=settings.ollama_base_url)
        self.model = settings.ollama_llm_model
        self.timeout = settings.ollama_timeout

    async def generate_response(self, prompt: str) -> str:
        """
        Generate a text response from the Ollama language model.

        Args:
            prompt: The input prompt/question to send to the LLM.

        Returns:
            The generated text response from the model.

        Raises:
            Exception: If the Ollama service is unavailable or request fails.
        """
        try:
            response = await asyncio.wait_for(
                self.client.generate(
                    model=self.model,
                    prompt=prompt,
                ),
                timeout=self.timeout,
            )

            # Extract the response text
            if isinstance(response, dict) and "response" in response:
                return response["response"]
            else:
                raise ValueError(f"Unexpected response format from Ollama: {response}")

        except asyncio.TimeoutError:
            raise Exception(
                f"Ollama request timed out after {self.timeout} seconds. "
                f"The model '{self.model}' may be too large or the server is slow."
            )
        except ollama.ResponseError as e:
            raise Exception(
                f"Ollama API error: {e}. "
                f"Ensure the model '{self.model}' is installed. "
                f"Run: ollama pull {self.model}"
            )
        except Exception as e:
            raise Exception(
                f"Failed to generate response from Ollama: {e}. "
                f"Check if Ollama is running at {self.settings.ollama_base_url}"
            )

    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming text response from the Ollama language model.

        Args:
            prompt: The input prompt/question to send to the LLM.

        Yields:
            Chunks of the generated text response as they become available.

        Raises:
            Exception: If the Ollama service is unavailable or request fails.
        """
        try:
            stream = await self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
            )

            async for chunk in stream:
                if isinstance(chunk, dict) and "response" in chunk:
                    yield chunk["response"]

        except ollama.ResponseError as e:
            raise Exception(
                f"Ollama API error: {e}. "
                f"Ensure the model '{self.model}' is installed. "
                f"Run: ollama pull {self.model}"
            )
        except Exception as e:
            raise Exception(
                f"Failed to generate streaming response from Ollama: {e}. "
                f"Check if Ollama is running at {self.settings.ollama_base_url}"
            )

    async def health_check(self) -> bool:
        """
        Check if the Ollama service is healthy and the model is available.

        Returns:
            True if the service is healthy, False otherwise.
        """
        try:
            # Try to list models to verify connection
            models = await self.client.list()
            model_names = [m["name"] for m in models.get("models", [])]

            # Check if our configured model is available
            return any(self.model in name for name in model_names)
        except Exception:
            return False


class OllamaEmbedding(EmbeddingProvider):
    """
    Ollama implementation of the Embedding Provider.

    This class uses the Ollama API to generate embeddings using local models.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the Ollama Embedding service.

        Args:
            settings: Application settings containing Ollama configuration.
        """
        self.settings = settings
        self.client = AsyncClient(host=settings.ollama_base_url)
        self.model = settings.ollama_embedding_model
        self.timeout = settings.ollama_timeout
        self._dimension: int | None = None

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
        try:
            response = await asyncio.wait_for(
                self.client.embeddings(
                    model=self.model,
                    prompt=text,
                ),
                timeout=self.timeout,
            )

            # Extract the embedding vector
            if isinstance(response, dict) and "embedding" in response:
                embedding = response["embedding"]

                # Cache the dimension on first call
                if self._dimension is None:
                    self._dimension = len(embedding)

                return embedding
            else:
                raise ValueError(
                    f"Unexpected response format from Ollama: {response}"
                )

        except asyncio.TimeoutError:
            raise Exception(
                f"Ollama embedding request timed out after {self.timeout} seconds."
            )
        except ollama.ResponseError as e:
            raise Exception(
                f"Ollama API error: {e}. "
                f"Ensure the embedding model '{self.model}' is installed. "
                f"Run: ollama pull {self.model}"
            )
        except Exception as e:
            raise Exception(
                f"Failed to generate embedding from Ollama: {e}. "
                f"Check if Ollama is running at {self.settings.ollama_base_url}"
            )

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts in a batch.

        Note: Ollama doesn't have native batch support, so this processes
        texts concurrently for better performance.

        Args:
            texts: A list of input texts to generate embeddings for.

        Returns:
            A list of embedding vectors, one for each input text.

        Raises:
            Exception: If the embedding service is unavailable or request fails.
        """
        # Process embeddings concurrently for better performance
        tasks = [self.get_embedding(text) for text in texts]
        embeddings = await asyncio.gather(*tasks)
        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of the embedding vectors.

        Returns:
            The size of the embedding vector.

        Raises:
            RuntimeError: If called before any embeddings have been generated.
        """
        if self._dimension is None:
            # Common dimensions for popular Ollama embedding models
            dimension_map = {
                "nomic-embed-text": 768,
                "mxbai-embed-large": 1024,
                "all-minilm": 384,
            }

            # Try to infer from model name
            for model_name, dim in dimension_map.items():
                if model_name in self.model:
                    return dim

            raise RuntimeError(
                "Embedding dimension unknown. Call get_embedding() first to "
                "automatically detect the dimension, or check your model documentation."
            )

        return self._dimension

    async def health_check(self) -> bool:
        """
        Check if the Ollama embedding service is healthy and the model is available.

        Returns:
            True if the service is healthy, False otherwise.
        """
        try:
            # Try to list models to verify connection
            models = await self.client.list()
            model_names = [m["name"] for m in models.get("models", [])]

            # Check if our configured embedding model is available
            return any(self.model in name for name in model_names)
        except Exception:
            return False
