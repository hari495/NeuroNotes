"""
Unit tests for Context Expansion functionality in RAGService.

Tests cover:
1. First chunk (no previous context)
2. Last chunk (no next context)
3. Single chunk document
4. Middle chunk (full expansion)
5. Missing metadata
6. ChromaDB fetch failure
7. Batch fetching efficiency
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any

from app.services.rag_service import RAGService
from app.core.config import Settings
from app.core.interfaces import EmbeddingProvider


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.get_chroma_db_path.return_value = "/tmp/test_chroma"
    settings.chroma_collection_name = "test_collection"
    return settings


@pytest.fixture
def mock_embedding_provider():
    """Create mock embedding provider."""
    provider = Mock(spec=EmbeddingProvider)
    return provider


@pytest.fixture
def rag_service(mock_settings, mock_embedding_provider):
    """Create RAGService instance with mocked dependencies."""
    with patch('app.services.rag_service.chromadb.PersistentClient'):
        with patch('app.services.rag_service.Ranker'):
            service = RAGService(mock_settings, mock_embedding_provider)
            service.collection = Mock()
            service.reranker = None
            service.reranker_available = False
            return service


def test_expand_first_chunk(rag_service):
    """Test expansion of first chunk (index=0) - should only have next context."""
    # Arrange
    chunks = [
        {
            "id": "note1_chunk_0",
            "text": "First chunk content",
            "metadata": {
                "note_id": "note1",
                "chunk_index": 0,
                "total_chunks": 3
            },
            "distance": 0.1
        }
    ]

    # Mock ChromaDB get() to return next chunk
    rag_service.collection.get.return_value = {
        "ids": ["note1_chunk_1"],
        "documents": ["Second chunk content"]
    }

    # Act
    result = rag_service._expand_context(chunks)

    # Assert
    assert len(result) == 1
    assert "[Main Match]" in result[0]["text"]
    assert "[Next Context]" in result[0]["text"]
    assert "[Previous Context]" not in result[0]["text"]
    assert "First chunk content" in result[0]["text"]
    assert "Second chunk content" in result[0]["text"]
    assert result[0]["metadata"]["context_expanded"] is True
    assert result[0]["metadata"]["expansion_info"]["has_previous"] is False
    assert result[0]["metadata"]["expansion_info"]["has_next"] is True

    # Verify ChromaDB was called with correct ID
    rag_service.collection.get.assert_called_once()
    call_args = rag_service.collection.get.call_args
    assert "note1_chunk_1" in call_args[1]["ids"]


def test_expand_last_chunk(rag_service):
    """Test expansion of last chunk - should only have previous context."""
    # Arrange
    chunks = [
        {
            "id": "note1_chunk_2",
            "text": "Last chunk content",
            "metadata": {
                "note_id": "note1",
                "chunk_index": 2,
                "total_chunks": 3
            },
            "distance": 0.2
        }
    ]

    # Mock ChromaDB get() to return previous chunk
    rag_service.collection.get.return_value = {
        "ids": ["note1_chunk_1"],
        "documents": ["Middle chunk content"]
    }

    # Act
    result = rag_service._expand_context(chunks)

    # Assert
    assert len(result) == 1
    assert "[Main Match]" in result[0]["text"]
    assert "[Previous Context]" in result[0]["text"]
    assert "[Next Context]" not in result[0]["text"]
    assert "Last chunk content" in result[0]["text"]
    assert "Middle chunk content" in result[0]["text"]
    assert result[0]["metadata"]["context_expanded"] is True
    assert result[0]["metadata"]["expansion_info"]["has_previous"] is True
    assert result[0]["metadata"]["expansion_info"]["has_next"] is False


def test_expand_single_chunk_doc(rag_service):
    """Test expansion of single chunk document - should only have main match."""
    # Arrange
    chunks = [
        {
            "id": "note1_chunk_0",
            "text": "Only chunk content",
            "metadata": {
                "note_id": "note1",
                "chunk_index": 0,
                "total_chunks": 1
            },
            "distance": 0.1
        }
    ]

    # ChromaDB get() should not be called (no neighbors)
    rag_service.collection.get.return_value = {
        "ids": [],
        "documents": []
    }

    # Act
    result = rag_service._expand_context(chunks)

    # Assert
    assert len(result) == 1
    assert "[Main Match]" in result[0]["text"]
    assert "[Previous Context]" not in result[0]["text"]
    assert "[Next Context]" not in result[0]["text"]
    assert "Only chunk content" in result[0]["text"]
    assert result[0]["metadata"]["context_expanded"] is True
    assert result[0]["metadata"]["expansion_info"]["has_previous"] is False
    assert result[0]["metadata"]["expansion_info"]["has_next"] is False


def test_expand_middle_chunk(rag_service):
    """Test expansion of middle chunk - should have all three sections."""
    # Arrange
    chunks = [
        {
            "id": "note1_chunk_5",
            "text": "Middle chunk content",
            "metadata": {
                "note_id": "note1",
                "chunk_index": 5,
                "total_chunks": 10
            },
            "distance": 0.15
        }
    ]

    # Mock ChromaDB get() to return both neighbors
    rag_service.collection.get.return_value = {
        "ids": ["note1_chunk_4", "note1_chunk_6"],
        "documents": ["Previous chunk content", "Next chunk content"]
    }

    # Act
    result = rag_service._expand_context(chunks)

    # Assert
    assert len(result) == 1
    assert "[Previous Context]" in result[0]["text"]
    assert "[Main Match]" in result[0]["text"]
    assert "[Next Context]" in result[0]["text"]
    assert "Previous chunk content" in result[0]["text"]
    assert "Middle chunk content" in result[0]["text"]
    assert "Next chunk content" in result[0]["text"]
    assert result[0]["metadata"]["context_expanded"] is True
    assert result[0]["metadata"]["expansion_info"]["has_previous"] is True
    assert result[0]["metadata"]["expansion_info"]["has_next"] is True
    assert result[0]["metadata"]["original_text"] == "Middle chunk content"

    # Verify correct order in expanded text
    text = result[0]["text"]
    prev_idx = text.index("Previous chunk content")
    main_idx = text.index("Middle chunk content")
    next_idx = text.index("Next chunk content")
    assert prev_idx < main_idx < next_idx


def test_expand_missing_metadata(rag_service):
    """Test expansion with missing metadata - should return original chunk."""
    # Arrange
    chunks = [
        {
            "id": "note1_chunk_0",
            "text": "Chunk with missing metadata",
            "metadata": {
                "note_id": "note1",
                # Missing chunk_index and total_chunks
            },
            "distance": 0.1
        }
    ]

    # Act
    result = rag_service._expand_context(chunks)

    # Assert
    assert len(result) == 1
    assert result[0]["text"] == "Chunk with missing metadata"  # Original text unchanged
    assert result[0]["metadata"]["context_expanded"] is False
    assert "expansion_info" not in result[0]["metadata"]

    # ChromaDB should not be called
    rag_service.collection.get.assert_not_called()


def test_expand_chromadb_error(rag_service):
    """Test graceful degradation when ChromaDB fetch fails."""
    # Arrange
    chunks = [
        {
            "id": "note1_chunk_5",
            "text": "Middle chunk content",
            "metadata": {
                "note_id": "note1",
                "chunk_index": 5,
                "total_chunks": 10
            },
            "distance": 0.15
        }
    ]

    # Mock ChromaDB get() to raise exception
    rag_service.collection.get.side_effect = Exception("ChromaDB connection failed")

    # Act
    result = rag_service._expand_context(chunks)

    # Assert - should return original chunks without expansion
    assert len(result) == 1
    assert result[0]["text"] == "Middle chunk content"
    assert result[0]["id"] == "note1_chunk_5"
    assert "context_expanded" not in result[0]["metadata"]  # No modification on error


def test_batch_fetch_efficiency(rag_service):
    """Test that all neighbors are fetched in a single ChromaDB query."""
    # Arrange - 3 chunks, each needing 2 neighbors (6 total neighbor IDs)
    chunks = [
        {
            "id": "note1_chunk_1",
            "text": "Chunk 1",
            "metadata": {"note_id": "note1", "chunk_index": 1, "total_chunks": 5},
            "distance": 0.1
        },
        {
            "id": "note1_chunk_3",
            "text": "Chunk 3",
            "metadata": {"note_id": "note1", "chunk_index": 3, "total_chunks": 5},
            "distance": 0.2
        },
        {
            "id": "note2_chunk_2",
            "text": "Chunk 2",
            "metadata": {"note_id": "note2", "chunk_index": 2, "total_chunks": 5},
            "distance": 0.3
        }
    ]

    # Mock ChromaDB get() to return all neighbors
    rag_service.collection.get.return_value = {
        "ids": ["note1_chunk_0", "note1_chunk_2", "note1_chunk_2", "note1_chunk_4",
                "note2_chunk_1", "note2_chunk_3"],
        "documents": ["Content 0", "Content 2", "Content 2", "Content 4",
                     "Content 1", "Content 3"]
    }

    # Act
    result = rag_service._expand_context(chunks)

    # Assert
    assert len(result) == 3

    # CRITICAL: ChromaDB get() should be called exactly ONCE (batch fetch)
    assert rag_service.collection.get.call_count == 1

    # Verify all 6 neighbor IDs were requested in the single call
    call_args = rag_service.collection.get.call_args
    requested_ids = call_args[1]["ids"]
    assert len(requested_ids) == 6
    assert "note1_chunk_0" in requested_ids  # Previous of chunk 1
    assert "note1_chunk_2" in requested_ids  # Next of chunk 1 (and prev of chunk 3)
    assert "note1_chunk_4" in requested_ids  # Next of chunk 3
    assert "note2_chunk_1" in requested_ids  # Previous of chunk 2
    assert "note2_chunk_3" in requested_ids  # Next of chunk 2

    # Verify all chunks were expanded
    for chunk in result:
        assert chunk["metadata"]["context_expanded"] is True


def test_expand_empty_chunks():
    """Test that empty chunk list returns empty list."""
    # This test doesn't need the fixture since it's a simple edge case
    with patch('app.services.rag_service.chromadb.PersistentClient'):
        with patch('app.services.rag_service.Ranker'):
            settings = Mock(spec=Settings)
            settings.get_chroma_db_path.return_value = "/tmp/test"
            settings.chroma_collection_name = "test"
            provider = Mock(spec=EmbeddingProvider)
            service = RAGService(settings, provider)

            # Act
            result = service._expand_context([])

            # Assert
            assert result == []
