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

    def _extract_response_value(self, response: Any) -> str:
        """
        Extract response string from Ollama response object.

        Args:
            response: Ollama response (object or dict)

        Returns:
            str: Extracted response text

        Raises:
            ValueError: If response format is unrecognized
        """
        if hasattr(response, "response"):
            return response.response
        elif isinstance(response, dict) and "response" in response:
            return response["response"]
        else:
            raise ValueError(f"Unexpected response format from Ollama: {response}")

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
1. **Synthesis over Retrieval:** Do not just list facts. Explain the *implications* of the facts.
2. **Handle Sparsity:** If the context is sparse (like a slide with few words), infer the likely connection between concepts based on standard academic knowledge.
3. **Source Grounding:** When making a claim, briefly reference the source text (e.g., "As seen in the definition of rank..."), then expand on it.
4. **Logical Flow:** Never dump a wall of text. Break complex ideas into their component parts (Definition → Intuition → Application).

FORMATTING STANDARDS:
- **Math:** ALWAYS use LaTeX formatting for mathematical expressions (e.g., $Ax = b$, $\lambda$).
- **Emphasis:** Use **bold** for key terms and core concepts.
- **Lists:** Use bullet points or numbered lists for steps, properties, or conditions.
- **Sub-headers:** Use `###` headers within the analysis to separate distinct sub-topics.

REQUIRED RESPONSE STRUCTURE:
Your response MUST follow this exact structure:

## Core Concept
[Provide a concise 2-3 sentence summary of the fundamental idea. Start with a direct definition, then state its significance.]

## Detailed Analysis
[This section must be logically structured, not a stream of consciousness.]
- **Context & Definitions:** Start by defining the terms found in the text.
- **The "Why" (Intuition):** Explain the logic behind the concept. Why does this theorem hold? Why is this formula constructed this way?
- **The "How" (Mechanics):** If applicable, explain the steps or conditions required to apply this concept.
- **Connections:** Explicitly state how this connects to previous chapters or broader linear algebra concepts (e.g., "This generalizes the concept of...").

## Key Takeaways
[Provide 3-5 bullet points. Each point should be a complete sentence containing a high-value insight.]

Remember:
- Distinguish between what is explicitly stated in the context vs. what you are inferring.
- If the user asks a "How to" question, use numbered steps.
- If the user asks for a comparison, consider using a Markdown table.
"""

        # Construct full prompt with system instruction
        full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            response = await asyncio.wait_for(
                self.client.generate(
                    model=self.model,
                    prompt=full_prompt,
                    options={
                        "num_predict": 2000,  # Increase token limit for longer responses (e.g., flashcards)
                    },
                ),
                timeout=self.timeout,
            )

            # Extract the response text from the response object
            return self._extract_response_value(response)

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
                yield self._extract_response_value(chunk)

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

    async def _get_available_models(self) -> List[str]:
        """
        Get list of available model names from Ollama.

        Returns:
            List of available model names

        Raises:
            Exception: If unable to retrieve model list
        """
        models_response = await self.client.list()

        # Handle both object and dict responses
        if hasattr(models_response, "models"):
            models_list = models_response.models
        elif isinstance(models_response, dict):
            models_list = models_response.get("models", [])
        else:
            raise ValueError("Unexpected models response format")

        # Extract model names
        model_names = []
        for m in models_list:
            if hasattr(m, "model"):
                model_names.append(m.model)
            elif hasattr(m, "name"):
                model_names.append(m.name)
            elif isinstance(m, dict):
                model_names.append(m.get("model", m.get("name", "")))

        return model_names

    async def health_check(self) -> bool:
        """
        Check if the Ollama service is healthy and the model is available.

        Returns:
            True if the service is healthy, False otherwise.
        """
        try:
            model_names = await self._get_available_models()
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

    def _extract_embedding_value(self, response: Any) -> List[float]:
        """
        Extract embedding vector from Ollama response object.

        Args:
            response: Ollama response (object or dict)

        Returns:
            List[float]: Extracted embedding vector

        Raises:
            ValueError: If response format is unrecognized
        """
        if hasattr(response, "embedding"):
            return response.embedding
        elif isinstance(response, dict) and "embedding" in response:
            return response["embedding"]
        else:
            raise ValueError(f"Unexpected response format from Ollama: {response}")

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
            embedding = self._extract_embedding_value(response)

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

    async def _get_available_models(self) -> List[str]:
        """
        Get list of available model names from Ollama.

        Returns:
            List of available model names

        Raises:
            Exception: If unable to retrieve model list
        """
        models_response = await self.client.list()

        # Handle both object and dict responses
        if hasattr(models_response, "models"):
            models_list = models_response.models
        elif isinstance(models_response, dict):
            models_list = models_response.get("models", [])
        else:
            raise ValueError("Unexpected models response format")

        # Extract model names
        model_names = []
        for m in models_list:
            if hasattr(m, "model"):
                model_names.append(m.model)
            elif hasattr(m, "name"):
                model_names.append(m.name)
            elif isinstance(m, dict):
                model_names.append(m.get("model", m.get("name", "")))

        return model_names

    async def health_check(self) -> bool:
        """
        Check if the Ollama embedding service is healthy and the model is available.

        Returns:
            True if the service is healthy, False otherwise.
        """
        try:
            model_names = await self._get_available_models()
            return any(self.model in name for name in model_names)
        except Exception:
            return False
