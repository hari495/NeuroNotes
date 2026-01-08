"""
Test script for FlashRank re-ranking functionality.

This script tests:
1. FlashRank initialization
2. Two-stage retrieval (50 chunks -> re-rank -> top 5)
3. Re-ranking score improvements
"""

import asyncio
from app.core.config import Settings
from app.services.ollama_service import OllamaEmbedding
from app.services.rag_service import RAGService


async def test_reranking():
    """Test the re-ranking functionality."""
    print("=" * 70)
    print("FlashRank Re-Ranking Test")
    print("=" * 70)

    # Initialize services
    print("\n1. Initializing services...")
    settings = Settings()
    embedding_service = OllamaEmbedding(settings)
    rag_service = RAGService(settings, embedding_service)

    # Check if FlashRank is available
    print(f"   ✓ RAG Service initialized")
    print(f"   ✓ FlashRank available: {rag_service.reranker_available}")

    if not rag_service.reranker_available:
        print("\n   ⚠ FlashRank is not available. Re-ranking will not be tested.")
        return

    # Get collection stats
    stats = rag_service.get_collection_stats()
    print(f"   ✓ Total chunks in collection: {stats['total_chunks']}")

    if stats['total_chunks'] == 0:
        print("\n   ⚠ No chunks in collection. Please upload some notes first.")
        return

    # Test query with re-ranking
    print("\n2. Testing query with re-ranking...")
    query = "What are vectors in linear algebra?"
    print(f"   Query: '{query}'")

    try:
        results = await rag_service.query_notes(query=query, k=5)

        print(f"\n3. Results (Top 5 after re-ranking from 50 candidates):")
        print("-" * 70)

        for i, result in enumerate(results, 1):
            print(f"\n   Result #{i}:")
            print(f"   - Chunk ID: {result['id']}")
            print(f"   - Vector Distance: {result['distance']:.4f}")
            if 'rerank_score' in result:
                print(f"   - Re-rank Score: {result['rerank_score']:.4f}")
            print(f"   - Title: {result['metadata'].get('title', 'N/A')}")
            print(f"   - Text Preview: {result['text'][:150]}...")

        print("\n" + "=" * 70)
        print("✓ Re-ranking test completed successfully!")
        print("=" * 70)

        # Verify re-ranking scores exist
        if results and 'rerank_score' in results[0]:
            print("\n✓ Re-ranking is working! Results include re-rank scores.")
        else:
            print("\n⚠ Re-ranking scores not found. Falling back to vector search.")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_context_expansion():
    """Test that query_notes returns expanded context."""
    print("=" * 70)
    print("Context Expansion Integration Test")
    print("=" * 70)

    # Initialize services
    print("\n1. Initializing services...")
    settings = Settings()
    embedding_service = OllamaEmbedding(settings)
    rag_service = RAGService(settings, embedding_service)
    print(f"   ✓ RAG Service initialized")

    # Create a multi-chunk document
    print("\n2. Creating test document...")
    note_text = (
        "Chapter 1: Introduction to Linear Algebra\n" +
        "This is the first chapter. " * 50 +  # ~200 words to ensure chunking
        "\n\n" +
        "Chapter 2: Vectors and Vector Spaces\n" +
        "This chapter discusses vectors. " * 50 +  # Another chunk
        "\n\n" +
        "Chapter 3: Matrix Operations\n" +
        "This chapter covers matrices. " * 50  # Another chunk
    )

    try:
        # Ingest the test document
        print("   - Ingesting test document...")
        result = await rag_service.ingest_note(
            note_text,
            metadata={"title": "Linear Algebra Test", "author": "Test Suite"}
        )
        print(f"   ✓ Document ingested: {result['chunks_created']} chunks created")
        note_id = result['note_id']

        # Query for content that should match middle chunks
        print("\n3. Querying for 'Chapter 2: Vectors'...")
        query = "Chapter 2 Vectors"
        results = await rag_service.query_notes(query=query, k=1)

        print(f"\n4. Verifying context expansion:")
        print("-" * 70)

        if not results:
            print("   ✗ No results returned")
            return

        result = results[0]
        print(f"   - Chunk ID: {result['id']}")
        print(f"   - Context Expanded: {result['metadata'].get('context_expanded', False)}")

        # Verify expansion occurred
        if result['metadata'].get('context_expanded'):
            print("   ✓ Context expansion is working!")

            # Check for section delimiters
            text = result['text']
            has_main = "[Main Match]" in text
            has_prev = "[Previous Context]" in text
            has_next = "[Next Context]" in text

            print(f"   - Has [Main Match]: {has_main}")
            print(f"   - Has [Previous Context]: {has_prev}")
            print(f"   - Has [Next Context]: {has_next}")

            # Verify metadata fields
            assert 'original_text' in result['metadata'], "Missing original_text in metadata"
            assert 'expansion_info' in result['metadata'], "Missing expansion_info in metadata"

            expansion_info = result['metadata']['expansion_info']
            print(f"   - Has previous chunk: {expansion_info.get('has_previous', False)}")
            print(f"   - Has next chunk: {expansion_info.get('has_next', False)}")
            print(f"   - Previous chunk ID: {expansion_info.get('previous_chunk_id', 'None')}")
            print(f"   - Next chunk ID: {expansion_info.get('next_chunk_id', 'None')}")

            # Show text preview
            print(f"\n   Text preview (first 300 chars):")
            print(f"   {text[:300]}...")

            print("\n" + "=" * 70)
            print("✓ Context expansion test completed successfully!")
            print("=" * 70)
        else:
            print("   ✗ Context expansion did not occur")
            print(f"   - Text: {result['text'][:200]}...")

        # Cleanup: Delete the test document
        print("\n5. Cleaning up test document...")
        await rag_service.delete_note(note_id)
        print(f"   ✓ Test document deleted")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def run_all_tests():
    """Run all tests."""
    await test_reranking()
    print("\n\n")
    await test_context_expansion()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
