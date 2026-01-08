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

        Uses a PhD-level Teaching Assistant system prompt to ensure high-quality,
        structured educational responses.

        Args:
            prompt: The input prompt/question to send to the LLM.

        Returns:
            The generated text response from the model.

        Raises:
            Exception: If the Ollama service is unavailable or request fails.
        """
        # Define PhD-level Teaching Assistant system prompt
        system_prompt = """You are a PhD-level Teaching Assistant. Your goal is not just to answer, but to synthesize information to help the student build a deep mental model.

CRITICAL INSTRUCTIONS:
1. Do not just list facts. Explain the implications of the facts.
2. If the context is sparse (like a slide with few words), infer the likely connection between concepts based on standard academic knowledge, but clearly state what is explicit in the text vs. what is inferred.
3. Connect concepts to build understanding, not just recite information.

REQUIRED RESPONSE STRUCTURE:
Your response MUST follow this exact structure:
Connect the retrieved information... Use specific phrases from the source text to ground your explanation, then expand on them using examples.
## Core Concept
[Provide a concise 2-3 sentence summary of the fundamental idea or main point]

## Detailed Analysis
[Connect the retrieved information, explain relationships between concepts, discuss implications, and build a coherent narrative. This is where you synthesize and explain, not just list.]

## Key Takeaways
[Provide 3-5 bullet points highlighting the most important insights the student should remember]

Remember:
- Distinguish between what is explicitly stated in the context vs. what you are inferring
- Focus on building understanding, not just providing information
- Make connections between concepts
- Explain "why" and "how", not just "what"
"""

        # Construct full prompt with system instruction
        full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            response = await asyncio.wait_for(
                self.client.generate(
                    model=self.model,
                    prompt=full_prompt,
                ),
                timeout=self.timeout,
            )

            # Extract the response text from the response object
            # The Ollama library returns an object with a 'response' attribute
            if hasattr(response, "response"):
                return response.response
            elif isinstance(response, dict) and "response" in response:
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
                if hasattr(chunk, "response"):
                    yield chunk.response
                elif isinstance(chunk, dict) and "response" in chunk:
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
            models_response = await self.client.list()

            # Handle both object and dict responses
            if hasattr(models_response, "models"):
                models_list = models_response.models
            elif isinstance(models_response, dict):
                models_list = models_response.get("models", [])
            else:
                return False

            # Extract model names
            model_names = []
            for m in models_list:
                if hasattr(m, "model"):
                    model_names.append(m.model)
                elif hasattr(m, "name"):
                    model_names.append(m.name)
                elif isinstance(m, dict):
                    model_names.append(m.get("model", m.get("name", "")))

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

            # Extract the embedding vector from the response object
            # The Ollama library returns an object with an 'embedding' attribute
            if hasattr(response, "embedding"):
                embedding = response.embedding
            elif isinstance(response, dict) and "embedding" in response:
                embedding = response["embedding"]
            else:
                raise ValueError(
                    f"Unexpected response format from Ollama: {response}"
                )

            # Cache the dimension on first call
            if self._dimension is None:
                self._dimension = len(embedding)

            return embedding

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
            models_response = await self.client.list()

            # Handle both object and dict responses
            if hasattr(models_response, "models"):
                models_list = models_response.models
            elif isinstance(models_response, dict):
                models_list = models_response.get("models", [])
            else:
                return False

            # Extract model names
            model_names = []
            for m in models_list:
                if hasattr(m, "model"):
                    model_names.append(m.model)
                elif hasattr(m, "name"):
                    model_names.append(m.name)
                elif isinstance(m, dict):
                    model_names.append(m.get("model", m.get("name", "")))

            # Check if our configured embedding model is available
            return any(self.model in name for name in model_names)
        except Exception:
            return False
