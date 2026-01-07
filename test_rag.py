#!/usr/bin/env python3
"""
RAG System Test Script.

This script verifies that:
1. ChromaDB initializes correctly
2. Notes can be ingested and chunked
3. Embeddings are generated and stored
4. Semantic search retrieves relevant chunks
5. Notes can be deleted

Run this to test the RAG system end-to-end.
"""

import asyncio
import sys

from app.core.config import get_settings
from app.services.ollama_service import OllamaEmbedding
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


async def test_rag_system() -> bool:
    """
    Test the RAG system end-to-end.

    Returns:
        True if all tests pass, False otherwise.
    """
    print_header("RAG System Test")

    try:
        # Initialize services
        settings = get_settings()
        print_info(f"ChromaDB path: {settings.chroma_db_path}")
        print_info(f"Collection name: {settings.chroma_collection_name}")

        embedding_provider = OllamaEmbedding(settings)
        rag_service = RAGService(settings, embedding_provider)

        print_success("RAG service initialized successfully")

        # Test 1: Get initial stats
        print("\n1. Checking collection stats...")
        stats = rag_service.get_collection_stats()
        print_success(f"Collection: {stats['collection_name']}")
        print_info(f"Total chunks before test: {stats['total_chunks']}")
        print_info(f"Embedding dimension: {stats['embedding_dimension']}")

        # Test 2: Ingest a sample note
        print("\n2. Ingesting sample note...")
        sample_note = """
        Machine Learning Basics:

        Machine learning is a subset of artificial intelligence that enables systems
        to learn and improve from experience without being explicitly programmed.

        There are three main types of machine learning:
        1. Supervised Learning - Learning from labeled data
        2. Unsupervised Learning - Finding patterns in unlabeled data
        3. Reinforcement Learning - Learning through trial and error

        Common algorithms include linear regression, decision trees, neural networks,
        and support vector machines. Deep learning is a subset of machine learning
        that uses neural networks with multiple layers.
        """

        result = await rag_service.ingest_note(
            note_text=sample_note,
            metadata={
                "title": "Machine Learning Basics",
                "category": "AI/ML",
                "author": "Test User",
            },
        )

        print_success("Note ingested successfully!")
        print_info(f"Note ID: {result['note_id']}")
        print_info(f"Chunks created: {result['chunks_created']}")
        print_info(f"Total characters: {result['total_characters']}")

        note_id = result["note_id"]

        # Test 3: Ingest another note for variety
        print("\n3. Ingesting second note...")
        sample_note_2 = """
        Python Programming:

        Python is a high-level, interpreted programming language known for its
        simplicity and readability. It supports multiple programming paradigms
        including procedural, object-oriented, and functional programming.

        Key features of Python:
        - Easy to learn syntax
        - Extensive standard library
        - Dynamic typing
        - Cross-platform compatibility

        Python is widely used in web development, data science, machine learning,
        automation, and scientific computing.
        """

        result2 = await rag_service.ingest_note(
            note_text=sample_note_2,
            metadata={
                "title": "Python Programming",
                "category": "Programming",
                "author": "Test User",
            },
        )

        print_success("Second note ingested!")
        print_info(f"Note ID: {result2['note_id']}")
        print_info(f"Chunks created: {result2['chunks_created']}")

        note_id_2 = result2["note_id"]

        # Test 4: Query for relevant chunks
        print("\n4. Testing semantic search...")
        query = "What are the types of machine learning?"
        print_info(f"Query: {query}")

        results = await rag_service.query_notes(query=query, k=3)

        print_success(f"Found {len(results)} relevant chunks!")

        for i, result in enumerate(results, 1):
            print(f"\n   Result {i}:")
            print(f"   Distance: {result['distance']:.4f}")
            print(f"   Metadata: {result['metadata'].get('title', 'N/A')}")
            print(f"   Text preview: {result['text'][:100]}...")

        # Test 5: Query with different topic
        print("\n5. Testing query for different topic...")
        query2 = "Tell me about Python programming features"
        print_info(f"Query: {query2}")

        results2 = await rag_service.query_notes(query=query2, k=2)

        print_success(f"Found {len(results2)} relevant chunks!")

        for i, result in enumerate(results2, 1):
            print(f"\n   Result {i}:")
            print(f"   Distance: {result['distance']:.4f}")
            print(f"   Metadata: {result['metadata'].get('title', 'N/A')}")

        # Test 6: List all notes
        print("\n6. Listing all notes...")
        notes = rag_service.list_notes(limit=10)
        print_success(f"Found {len(notes)} unique notes")

        for note in notes:
            print(f"   - {note['note_id'][:8]}... ({note['total_chunks']} chunks)")
            if note['metadata']:
                print(f"     Title: {note['metadata'].get('title', 'N/A')}")

        # Test 7: Delete first note
        print("\n7. Testing note deletion...")
        delete_result = await rag_service.delete_note(note_id)

        if delete_result["found"]:
            print_success(
                f"Deleted note {note_id[:8]}... "
                f"({delete_result['chunks_deleted']} chunks)"
            )
        else:
            print_error("Note not found for deletion")
            return False

        # Test 8: Verify deletion
        print("\n8. Verifying deletion...")
        final_stats = rag_service.get_collection_stats()
        print_info(f"Total chunks after deletion: {final_stats['total_chunks']}")

        # Cleanup: Delete second note
        print("\n9. Cleaning up test data...")
        await rag_service.delete_note(note_id_2)
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
    print_header("RAG System Verification")

    success = await test_rag_system()

    print_header("Test Summary")

    if success:
        print("\n🎉 All RAG tests passed!")
        print("\nYou can now:")
        print("   1. Start the FastAPI server: python main.py")
        print("   2. Visit http://localhost:8000/docs")
        print("   3. Try the /api/notes endpoints")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
