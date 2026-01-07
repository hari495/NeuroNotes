"""
Test Script for File Upload Functionality.

Tests:
1. Single file upload (.txt, .md, .pdf)
2. Batch file upload
3. Error handling for unsupported files
4. Verification that uploaded files are searchable
"""

import io
import httpx
from pathlib import Path


# Configuration
API_BASE_URL = "http://localhost:8000"


def create_test_files():
    """Create sample test files in memory."""
    test_files = {}

    # Test TXT file
    test_files["sample.txt"] = b"""Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience.

Key Concepts:
1. Supervised Learning: Training with labeled data
2. Unsupervised Learning: Finding patterns in unlabeled data
3. Reinforcement Learning: Learning through rewards and penalties

Common algorithms include linear regression, decision trees, neural networks, and support vector machines."""

    # Test MD file
    test_files["sample.md"] = b"""# Python Best Practices

## Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Write docstrings for all functions

## Testing
- Write unit tests for critical functions
- Use pytest for test automation
- Aim for high code coverage

## Performance
- Profile your code before optimizing
- Use built-in functions when possible
- Consider algorithmic complexity"""

    # Test PDF (create a simple text-based PDF using ReportLab if available, or skip)
    # For this test, we'll create a mock PDF using PyPDF2's capabilities
    # In reality, you'd need a real PDF file or use reportlab to generate one

    return test_files


def test_single_txt_upload():
    """Test uploading a single .txt file."""
    print("\n" + "="*60)
    print("TEST 1: Single TXT File Upload")
    print("="*60)

    test_files = create_test_files()

    try:
        files = {"file": ("sample.txt", test_files["sample.txt"])}
        response = httpx.post(
            f"{API_BASE_URL}/api/notes/upload",
            files=files,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ SUCCESS: Uploaded {data['filename']}")
        print(f"   Note ID: {data['note_id'][:16]}...")
        print(f"   File Type: {data['file_type']}")
        print(f"   Chunks Created: {data['chunks_created']}")
        print(f"   Total Characters: {data['total_characters']}")
        print(f"   File Size: {data['file_size']} bytes")

        return data['note_id']

    except httpx.HTTPStatusError as e:
        print(f"❌ FAILED: HTTP {e.response.status_code}")
        print(f"   Error: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return None


def test_single_md_upload():
    """Test uploading a single .md file."""
    print("\n" + "="*60)
    print("TEST 2: Single MD File Upload")
    print("="*60)

    test_files = create_test_files()

    try:
        files = {"file": ("sample.md", test_files["sample.md"])}
        response = httpx.post(
            f"{API_BASE_URL}/api/notes/upload",
            files=files,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ SUCCESS: Uploaded {data['filename']}")
        print(f"   Note ID: {data['note_id'][:16]}...")
        print(f"   Chunks Created: {data['chunks_created']}")

        return data['note_id']

    except httpx.HTTPStatusError as e:
        print(f"❌ FAILED: HTTP {e.response.status_code}")
        print(f"   Error: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return None


def test_batch_upload():
    """Test uploading multiple files at once."""
    print("\n" + "="*60)
    print("TEST 3: Batch File Upload")
    print("="*60)

    test_files = create_test_files()

    try:
        files = [
            ("files", ("batch_test1.txt", test_files["sample.txt"])),
            ("files", ("batch_test2.md", test_files["sample.md"])),
        ]

        response = httpx.post(
            f"{API_BASE_URL}/api/notes/upload/batch",
            files=files,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ SUCCESS: Batch upload completed")
        print(f"   Success Count: {data['success_count']}")
        print(f"   Failed Count: {data['failed_count']}")

        if data['results']:
            total_chunks = sum(r['chunks_created'] for r in data['results'])
            print(f"   Total Chunks Created: {total_chunks}")
            print(f"\n   Uploaded Files:")
            for result in data['results']:
                print(f"     - {result['filename']} ({result['chunks_created']} chunks)")

        if data['errors']:
            print(f"\n   Errors:")
            for error in data['errors']:
                print(f"     - {error}")

        return data

    except httpx.HTTPStatusError as e:
        print(f"❌ FAILED: HTTP {e.response.status_code}")
        print(f"   Error: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return None


def test_unsupported_file():
    """Test uploading an unsupported file type."""
    print("\n" + "="*60)
    print("TEST 4: Unsupported File Type (should fail gracefully)")
    print("="*60)

    try:
        fake_docx = b"fake docx content"
        files = {"file": ("test.docx", fake_docx)}

        response = httpx.post(
            f"{API_BASE_URL}/api/notes/upload",
            files=files,
            timeout=30.0,
        )

        if response.status_code == 400:
            print(f"✅ SUCCESS: Correctly rejected unsupported file")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error Message: {response.json().get('detail', 'N/A')}")
        else:
            print(f"⚠️  UNEXPECTED: Got status {response.status_code}, expected 400")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            print(f"✅ SUCCESS: Correctly rejected unsupported file")
            print(f"   Error: {e.response.json().get('detail', 'N/A')}")
        else:
            print(f"❌ FAILED: Unexpected error")
            print(f"   HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")


def test_chat_with_uploaded_file():
    """Test that uploaded files are searchable via chat."""
    print("\n" + "="*60)
    print("TEST 5: Chat with Uploaded Files")
    print("="*60)

    try:
        # Ask a question about content from our test files
        query = "What is machine learning?"

        response = httpx.post(
            f"{API_BASE_URL}/api/chat/chat",
            json={
                "query": query,
                "k": 3,
                "include_sources": True,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ SUCCESS: Chat query executed")
        print(f"   Query: {query}")
        print(f"   Chunks Used: {data.get('num_chunks', 0)}")
        print(f"   Has Context: {data.get('has_context', False)}")
        print(f"\n   Answer:")
        print(f"   {data['answer'][:200]}...")

        if data.get('context_used'):
            print(f"\n   Sources:")
            for i, source in enumerate(data['context_used'][:2], 1):
                title = source['metadata'].get('title', 'Unknown')
                similarity = 1 - source['distance']
                print(f"     {i}. {title} (similarity: {similarity:.2%})")

    except httpx.HTTPStatusError as e:
        print(f"❌ FAILED: HTTP {e.response.status_code}")
        print(f"   Error: {e.response.text}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")


def test_get_supported_types():
    """Test the supported file types endpoint."""
    print("\n" + "="*60)
    print("TEST 6: Get Supported File Types")
    print("="*60)

    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/notes/upload/supported-types",
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ SUCCESS: Retrieved supported file types")
        print(f"   Supported Extensions: {', '.join(data.get('supported_extensions', []))}")

        if 'description' in data:
            print(f"\n   Descriptions:")
            for ext, desc in data['description'].items():
                print(f"     {ext}: {desc}")

    except httpx.HTTPStatusError as e:
        print(f"❌ FAILED: HTTP {e.response.status_code}")
        print(f"   Error: {e.response.text}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")


def test_collection_stats():
    """Test getting collection statistics after uploads."""
    print("\n" + "="*60)
    print("TEST 7: Collection Statistics")
    print("="*60)

    try:
        response = httpx.get(
            f"{API_BASE_URL}/api/notes/stats",
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        print(f"✅ SUCCESS: Retrieved collection stats")
        print(f"   Collection Name: {data.get('collection_name', 'N/A')}")
        print(f"   Total Chunks: {data.get('total_chunks', 0)}")
        print(f"   Embedding Dimension: {data.get('embedding_dimension', 0)}")

    except httpx.HTTPStatusError as e:
        print(f"❌ FAILED: HTTP {e.response.status_code}")
        print(f"   Error: {e.response.text}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")


def main():
    """Run all file upload tests."""
    print("\n" + "="*60)
    print("FILE UPLOAD TEST SUITE")
    print("="*60)
    print(f"API Base URL: {API_BASE_URL}")
    print("\nMake sure the FastAPI server is running!")
    print("Run: uvicorn app.main:app --reload")
    print("="*60)

    # Wait for user confirmation
    input("\nPress Enter to start tests...")

    # Run tests
    test_get_supported_types()
    test_single_txt_upload()
    test_single_md_upload()
    test_batch_upload()
    test_unsupported_file()
    test_chat_with_uploaded_file()
    test_collection_stats()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
