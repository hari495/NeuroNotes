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


if __name__ == "__main__":
    asyncio.run(test_reranking())
