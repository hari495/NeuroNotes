#!/usr/bin/env python3
"""
Ollama Connection Test Script.

This script verifies that:
1. Ollama is running locally
2. Required models are installed
3. LLM generation works
4. Embedding generation works
5. Services are properly configured

Run this before starting the main application to ensure everything is set up correctly.
"""

import asyncio
import sys
from typing import List

from app.core.config import get_settings
from app.services.ollama_service import OllamaEmbedding, OllamaLLM


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"✅ {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"❌ {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"ℹ️  {text}")


async def test_llm_service() -> bool:
    """
    Test the Ollama LLM service.

    Returns:
        True if all tests pass, False otherwise.
    """
    print_header("Testing Ollama LLM Service")

    try:
        settings = get_settings()
        print_info(f"Using LLM model: {settings.ollama_llm_model}")
        print_info(f"Ollama URL: {settings.ollama_base_url}")

        llm = OllamaLLM(settings)

        # Test 1: Health check
        print("\n1. Checking if LLM model is available...")
        is_healthy = await llm.health_check()
        if is_healthy:
            print_success(f"Model '{settings.ollama_llm_model}' is available")
        else:
            print_error(
                f"Model '{settings.ollama_llm_model}' not found. "
                f"Install it with: ollama pull {settings.ollama_llm_model}"
            )
            return False

        # Test 2: Simple generation
        print("\n2. Testing text generation...")
        prompt = "What is 2+2? Answer in one short sentence."
        print_info(f"Prompt: {prompt}")

        response = await llm.generate_response(prompt)
        print_success("Generation successful!")
        print(f"   Response: {response.strip()[:100]}...")

        # Test 3: Streaming generation
        print("\n3. Testing streaming generation...")
        prompt = "Count from 1 to 5."
        print_info(f"Prompt: {prompt}")

        chunks: List[str] = []
        async for chunk in llm.generate_response_stream(prompt):
            chunks.append(chunk)

        full_response = "".join(chunks)
        print_success("Streaming successful!")
        print(f"   Response: {full_response.strip()[:100]}...")

        return True

    except Exception as e:
        print_error(f"LLM test failed: {e}")
        return False


async def test_embedding_service() -> bool:
    """
    Test the Ollama Embedding service.

    Returns:
        True if all tests pass, False otherwise.
    """
    print_header("Testing Ollama Embedding Service")

    try:
        settings = get_settings()
        print_info(f"Using embedding model: {settings.ollama_embedding_model}")
        print_info(f"Ollama URL: {settings.ollama_base_url}")

        embedding = OllamaEmbedding(settings)

        # Test 1: Health check
        print("\n1. Checking if embedding model is available...")
        is_healthy = await embedding.health_check()
        if is_healthy:
            print_success(f"Model '{settings.ollama_embedding_model}' is available")
        else:
            print_error(
                f"Model '{settings.ollama_embedding_model}' not found. "
                f"Install it with: ollama pull {settings.ollama_embedding_model}"
            )
            return False

        # Test 2: Single embedding
        print("\n2. Testing single embedding generation...")
        text = "This is a test sentence for embedding."
        print_info(f"Text: {text}")

        vector = await embedding.get_embedding(text)
        dimension = len(vector)

        print_success("Embedding generation successful!")
        print(f"   Dimension: {dimension}")
        print(f"   First 5 values: {vector[:5]}")
        print(f"   Last 5 values: {vector[-5:]}")

        # Test 3: Dimension method
        print("\n3. Testing get_embedding_dimension()...")
        reported_dimension = embedding.get_embedding_dimension()
        if reported_dimension == dimension:
            print_success(f"Dimension method works: {reported_dimension}")
        else:
            print_error(
                f"Dimension mismatch: reported {reported_dimension}, "
                f"actual {dimension}"
            )
            return False

        # Test 4: Batch embeddings
        print("\n4. Testing batch embedding generation...")
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence.",
        ]
        print_info(f"Generating embeddings for {len(texts)} texts...")

        vectors = await embedding.get_embeddings_batch(texts)
        print_success(f"Batch embedding successful! Generated {len(vectors)} vectors")

        # Verify all vectors have the same dimension
        all_same_dim = all(len(v) == dimension for v in vectors)
        if all_same_dim:
            print_success(f"All vectors have dimension {dimension}")
        else:
            print_error("Vectors have inconsistent dimensions!")
            return False

        return True

    except Exception as e:
        print_error(f"Embedding test failed: {e}")
        return False


async def main() -> int:
    """
    Run all tests.

    Returns:
        Exit code: 0 if all tests pass, 1 otherwise.
    """
    print_header("Ollama Service Verification")

    settings = get_settings()
    print_info(f"Configuration loaded from: {settings.model_config.get('env_file', 'environment variables')}")

    # Run tests
    llm_ok = await test_llm_service()
    embedding_ok = await test_embedding_service()

    # Print summary
    print_header("Test Summary")
    if llm_ok:
        print_success("LLM Service: All tests passed")
    else:
        print_error("LLM Service: Tests failed")

    if embedding_ok:
        print_success("Embedding Service: All tests passed")
    else:
        print_error("Embedding Service: Tests failed")

    print("\n" + "=" * 70)

    if llm_ok and embedding_ok:
        print("\n🎉 All tests passed! Your Ollama setup is working correctly.")
        print("\nYou can now start the FastAPI application:")
        print("   python main.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon fixes:")
        print("   1. Ensure Ollama is running: ollama serve")
        print(f"   2. Install LLM model: ollama pull {settings.ollama_llm_model}")
        print(f"   3. Install embedding model: ollama pull {settings.ollama_embedding_model}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
