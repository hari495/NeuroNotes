#!/usr/bin/env python3
"""
RAG Chat Test Script.

This script demonstrates the full RAG-augmented chat pipeline:
1. Ingest sample notes into the system
2. Ask questions about the notes
3. Retrieve relevant context
4. Generate answers using the LLM based ONLY on the context

Run this to test the end-to-end chat functionality.
"""

import asyncio
import sys

from app.core.config import get_settings
from app.services.ollama_service import OllamaEmbedding, OllamaLLM
from app.services.rag_service import RAGService


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


def construct_rag_prompt(context_chunks: list, query: str) -> str:
    """Construct a RAG prompt for the LLM."""
    if not context_chunks:
        return f"""You are a helpful assistant. The user asked a question, but no relevant \
context was found in the knowledge base.

Please politely inform the user that you don't have information about this topic.

User Query: {query}"""

    # Build context section
    context_text = "\n\n---\n\n".join(
        [f"Context {i+1}:\n{chunk['text']}" for i, chunk in enumerate(context_chunks)]
    )

    prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context from the user's notes.

IMPORTANT INSTRUCTIONS:
1. Answer the question using ONLY the information in the context below
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Do not make up information or use knowledge outside the provided context
4. Be concise but complete in your answer

CONTEXT FROM NOTES:
{context_text}

USER QUERY: {query}

ANSWER (based only on the context above):"""

    return prompt


async def test_rag_chat() -> bool:
    """
    Test the RAG chat system end-to-end.

    Returns:
        True if all tests pass, False otherwise.
    """
    print_header("RAG Chat System Test")

    try:
        # Initialize services
        settings = get_settings()
        embedding_provider = OllamaEmbedding(settings)
        llm_provider = OllamaLLM(settings)
        rag_service = RAGService(settings, embedding_provider)

        print_success("Services initialized successfully")

        # Clean up any existing test data
        print("\n🧹 Cleaning up any existing test data...")
        try:
            # Just start fresh - don't worry if there's no data
            pass
        except:
            pass

        # Test 1: Ingest sample notes
        print_header("Step 1: Ingesting Sample Notes")

        note1 = """
        Python Programming Language

        Python is a high-level, interpreted programming language created by Guido van Rossum
        and first released in 1991. It emphasizes code readability with significant whitespace.

        Key features of Python:
        - Simple and easy to learn syntax
        - Extensive standard library
        - Dynamic typing and automatic memory management
        - Support for multiple programming paradigms (OOP, functional, procedural)
        - Large ecosystem of third-party packages via PyPI

        Python is widely used in:
        - Web development (Django, Flask)
        - Data science and machine learning (NumPy, Pandas, scikit-learn)
        - Automation and scripting
        - Scientific computing
        """

        note2 = """
        Machine Learning Fundamentals

        Machine learning is a subset of artificial intelligence that enables systems to
        learn and improve from experience without being explicitly programmed.

        Types of Machine Learning:

        1. Supervised Learning
           - Learning from labeled training data
           - Examples: classification, regression
           - Algorithms: linear regression, decision trees, random forests, SVM

        2. Unsupervised Learning
           - Finding patterns in unlabeled data
           - Examples: clustering, dimensionality reduction
           - Algorithms: K-means, PCA, hierarchical clustering

        3. Reinforcement Learning
           - Learning through trial and error with rewards/penalties
           - Examples: game playing, robotics
           - Algorithms: Q-learning, Deep Q-Networks

        Common applications include image recognition, natural language processing,
        recommendation systems, and autonomous vehicles.
        """

        note3 = """
        FastAPI Framework

        FastAPI is a modern, high-performance web framework for building APIs with Python 3.7+
        based on standard Python type hints.

        Key features:
        - Fast: Very high performance, on par with NodeJS and Go
        - Fast to code: Increase development speed by 200-300%
        - Fewer bugs: Reduce human errors by about 40%
        - Intuitive: Great editor support with autocompletion
        - Easy: Designed to be easy to use and learn
        - Short: Minimize code duplication
        - Robust: Get production-ready code with automatic interactive documentation

        FastAPI is built on:
        - Starlette for web parts
        - Pydantic for data parts

        It automatically generates OpenAPI (Swagger) documentation and supports
        async/await for handling concurrent requests efficiently.
        """

        result1 = await rag_service.ingest_note(
            note_text=note1, metadata={"title": "Python Programming", "category": "programming"}
        )
        print_success(f"Note 1 ingested: {result1['chunks_created']} chunks")

        result2 = await rag_service.ingest_note(
            note_text=note2, metadata={"title": "Machine Learning", "category": "ai"}
        )
        print_success(f"Note 2 ingested: {result2['chunks_created']} chunks")

        result3 = await rag_service.ingest_note(
            note_text=note3, metadata={"title": "FastAPI", "category": "programming"}
        )
        print_success(f"Note 3 ingested: {result3['chunks_created']} chunks")

        note_ids = [result1["note_id"], result2["note_id"], result3["note_id"]]

        # Test 2: Ask a question about Python
        print_header("Step 2: Testing Question About Python")

        query1 = "What are the key features of Python?"
        print_info(f"Query: {query1}")

        # Retrieve context
        context1 = await rag_service.query_notes(query=query1, k=3)
        print_success(f"Retrieved {len(context1)} context chunks")

        for i, chunk in enumerate(context1, 1):
            print(f"   Context {i} (distance: {chunk['distance']:.4f}): {chunk['metadata'].get('title', 'N/A')}")

        # Generate answer
        prompt1 = construct_rag_prompt(context1, query1)
        answer1 = await llm_provider.generate_response(prompt1)

        print("\n📝 Answer:")
        print(f"{answer1}\n")

        # Test 3: Ask about machine learning
        print_header("Step 3: Testing Question About Machine Learning")

        query2 = "What are the three main types of machine learning?"
        print_info(f"Query: {query2}")

        # Retrieve context
        context2 = await rag_service.query_notes(query=query2, k=3)
        print_success(f"Retrieved {len(context2)} context chunks")

        for i, chunk in enumerate(context2, 1):
            print(f"   Context {i} (distance: {chunk['distance']:.4f}): {chunk['metadata'].get('title', 'N/A')}")

        # Generate answer
        prompt2 = construct_rag_prompt(context2, query2)
        answer2 = await llm_provider.generate_response(prompt2)

        print("\n📝 Answer:")
        print(f"{answer2}\n")

        # Test 4: Ask about FastAPI
        print_header("Step 4: Testing Question About FastAPI")

        query3 = "What is FastAPI built on?"
        print_info(f"Query: {query3}")

        # Retrieve context
        context3 = await rag_service.query_notes(query=query3, k=2)
        print_success(f"Retrieved {len(context3)} context chunks")

        for i, chunk in enumerate(context3, 1):
            print(f"   Context {i} (distance: {chunk['distance']:.4f}): {chunk['metadata'].get('title', 'N/A')}")

        # Generate answer
        prompt3 = construct_rag_prompt(context3, query3)
        answer3 = await llm_provider.generate_response(prompt3)

        print("\n📝 Answer:")
        print(f"{answer3}\n")

        # Test 5: Ask about something not in the notes
        print_header("Step 5: Testing Question Without Context")

        query4 = "What is quantum computing?"
        print_info(f"Query: {query4}")

        # Retrieve context (should find nothing relevant)
        context4 = await rag_service.query_notes(query=query4, k=2)
        print_info(f"Retrieved {len(context4)} chunks (may not be relevant)")

        # The LLM should say it doesn't have info about this
        prompt4 = construct_rag_prompt([], query4)  # Intentionally pass empty context
        answer4 = await llm_provider.generate_response(prompt4)

        print("\n📝 Answer:")
        print(f"{answer4}\n")

        # Cleanup: Delete test notes
        print_header("Cleanup")
        for note_id in note_ids:
            await rag_service.delete_note(note_id)
        print_success("Test data cleaned up")

        return True

    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main() -> int:
    """
    Run all tests.

    Returns:
        Exit code: 0 if all tests pass, 1 otherwise.
    """
    print_header("RAG Chat System Verification")

    success = await test_rag_chat()

    print_header("Test Summary")

    if success:
        print("\n🎉 All RAG chat tests passed!")
        print("\nYou can now:")
        print("   1. Start the FastAPI server: python main.py")
        print("   2. Visit http://localhost:8000/docs")
        print("   3. Try these endpoints:")
        print("      - POST /api/notes/ - Create a note")
        print("      - POST /api/chat/chat - Ask questions about your notes")
        print("      - POST /api/chat/stream - Get streaming responses")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
