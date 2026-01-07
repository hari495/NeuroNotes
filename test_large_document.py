"""
Test script for large document ingestion (500+ pages / 1000+ chunks).

This script demonstrates the robust batch processing with:
- RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
- Batch processing (50 chunks at a time)
- Progress logging
- Error handling that continues on batch failure
- 0.5s sleep between batches for LLM cooling
"""

import asyncio
import time
from pathlib import Path

# Add the app directory to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.services.rag_service import RAGService
from app.services.ollama_service import OllamaEmbeddingProvider


async def create_large_test_document(num_pages: int = 500) -> str:
    """
    Create a large test document simulating a math textbook.

    Args:
        num_pages: Number of pages to simulate (default: 500)

    Returns:
        Large text document with ~1000 characters per page
    """
    print(f"\n📖 Creating simulated {num_pages}-page mathematics textbook...")

    pages = []
    for page_num in range(1, num_pages + 1):
        page_content = f"""
Page {page_num}

Chapter {(page_num // 20) + 1}: Advanced Mathematical Concepts

Section {page_num % 10 + 1}: Theory and Applications

This section introduces fundamental concepts in mathematical analysis.
The theorem states that for any continuous function f(x) defined on the
interval [a, b], there exists a value c in (a, b) such that f'(c) equals
the average rate of change of the function over the interval.

Definition {page_num}.1: A sequence (a_n) is said to converge to a limit L
if for every ε > 0, there exists an N such that for all n > N,
|a_n - L| < ε. This fundamental concept underlies much of modern analysis.

Theorem {page_num}.2: If f and g are integrable functions on [a, b], then
f + g is also integrable, and ∫(f + g) = ∫f + ∫g. This linearity property
is essential for many applications in physics and engineering.

Example {page_num}.3: Consider the function f(x) = x² + 2x + 1. We can apply
the fundamental theorem of calculus to find its derivative: f'(x) = 2x + 2.
This demonstrates the relationship between differentiation and integration.

Exercises:
1. Prove that the limit of (n² + 3n)/(2n² - 1) as n approaches infinity equals 1/2.
2. Find the derivative of g(x) = sin(x²) using the chain rule.
3. Evaluate the integral ∫₀¹ (3x² + 2x + 1) dx.
4. Determine whether the series Σ(1/n²) converges or diverges.
5. Show that the function h(x) = |x| is continuous but not differentiable at x = 0.
"""
        pages.append(page_content)

    full_text = "\n\n".join(pages)
    print(f"✅ Created document with {len(full_text):,} characters")
    print(f"   Estimated chunks (chunk_size=1000): ~{len(full_text) // 1000}")

    return full_text


async def test_large_document_ingestion():
    """Test ingesting a large document with batch processing."""

    print("=" * 60)
    print("LARGE DOCUMENT INGESTION TEST")
    print("=" * 60)

    # Initialize services
    settings = get_settings()
    embedding_provider = OllamaEmbeddingProvider(settings)
    rag_service = RAGService(settings, embedding_provider)

    print("\n✅ Services initialized")
    print(f"   ChromaDB path: {settings.get_chroma_db_path()}")
    print(f"   Ollama URL: {settings.ollama_base_url}")

    # Create large test document (500 pages)
    test_document = await create_large_test_document(num_pages=500)

    # Add metadata
    metadata = {
        "title": "Advanced Mathematics Textbook",
        "author": "Test Author",
        "subject": "Mathematics",
        "pages": 500,
        "type": "textbook",
    }

    print("\n🚀 Starting ingestion with batch processing...")
    print("   Watch for progress logs below:")
    print("=" * 60)

    start_time = time.time()

    try:
        # Ingest the document
        result = await rag_service.ingest_note(
            note_text=test_document,
            metadata=metadata,
        )

        end_time = time.time()
        duration = end_time - start_time

        # Print results
        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📊 Final Results:")
        print(f"   Note ID: {result['note_id']}")
        print(f"   Total chunks created: {result['chunks_created']}")
        print(f"   Total chunks failed: {result.get('chunks_failed', 0)}")
        print(f"   Total characters: {result['total_characters']:,}")
        print(f"   Embedding dimension: {result['embedding_dimension']}")
        print(f"   Success rate: {result.get('success_rate', '100%')}")
        print(f"   Time taken: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"   Average time per chunk: {duration/result['chunks_created']:.2f}s")

        # Verify in ChromaDB
        stats = rag_service.get_collection_stats()
        print(f"\n📚 ChromaDB Collection Stats:")
        print(f"   Collection name: {stats['collection_name']}")
        print(f"   Total chunks in DB: {stats['total_chunks']}")

        print("\n✅ Test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_query_after_ingestion():
    """Test querying the large document after ingestion."""

    print("\n" + "=" * 60)
    print("QUERY TEST")
    print("=" * 60)

    # Initialize services
    settings = get_settings()
    embedding_provider = OllamaEmbeddingProvider(settings)
    rag_service = RAGService(settings, embedding_provider)

    # Test queries
    test_queries = [
        "What is the definition of sequence convergence?",
        "Explain the fundamental theorem of calculus",
        "What are the properties of integrable functions?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        try:
            results = await rag_service.query_notes(query, k=3)
            print(f"   ✅ Found {len(results)} relevant chunks")
            if results:
                print(f"   Top result (distance: {results[0]['distance']:.4f}):")
                print(f"   {results[0]['text'][:150]}...")
        except Exception as e:
            print(f"   ❌ Query failed: {str(e)}")

    print("\n✅ Query test completed!")


async def main():
    """Run all tests."""

    print("\n" + "=" * 60)
    print("LARGE DOCUMENT PROCESSING TEST SUITE")
    print("=" * 60)
    print("\nThis script tests:")
    print("  ✓ RecursiveCharacterTextSplitter (1000/200)")
    print("  ✓ Batch processing (50 chunks/batch)")
    print("  ✓ Progress logging")
    print("  ✓ Error handling")
    print("  ✓ 0.5s sleep between batches")
    print()

    # Test 1: Ingest large document
    success = await test_large_document_ingestion()

    if success:
        # Test 2: Query the ingested document
        await test_query_after_ingestion()

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
