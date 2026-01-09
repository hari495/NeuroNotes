"""
RAG (Retrieval-Augmented Generation) Service.

This module provides the core RAG functionality including document ingestion,
chunking, embedding, and semantic retrieval using ChromaDB with FlashRank re-ranking.
"""

import logging
import time
import uuid
from typing import Any, List

import chromadb
from chromadb.config import Settings as ChromaSettings
from flashrank import Ranker, RerankRequest

from app.core.config import Settings
from app.core.interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG Service for managing document ingestion and retrieval.

    This service handles:
    - Document chunking
    - Embedding generation via EmbeddingProvider
    - Vector storage in ChromaDB
    - Semantic search with FlashRank re-ranking for improved accuracy
    """

    def __init__(self, settings: Settings, embedding_provider: EmbeddingProvider) -> None:
        """
        Initialize the RAG service.

        Args:
            settings: Application settings containing ChromaDB configuration.
            embedding_provider: Provider for generating text embeddings.
        """
        self.settings = settings
        self.embedding_provider = embedding_provider

        # Initialize ChromaDB client with persistent storage
        chroma_path = settings.get_chroma_db_path()
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

        # Initialize FlashRank re-ranker (fast, local, lightweight)
        # Using ms-marco-MiniLM-L-12-v2 model (default, optimized for speed)
        try:
            self.reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir=str(chroma_path / "flashrank"))
            self.reranker_available = True
            logger.info("FlashRank re-ranker initialized successfully")
        except Exception as e:
            logger.warning(f"FlashRank initialization failed: {e}. Falling back to vector search only.")
            self.reranker = None
            self.reranker_available = False

    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Split text into chunks using recursive character splitting.

        This method implements a RecursiveCharacterTextSplitter that tries to split
        on natural boundaries (paragraphs, sentences, words) before falling back to
        character-level splitting. This prevents cutting sentences in half, which is
        crucial for technical and math textbooks.

        Splitting hierarchy:
        1. Double newlines (paragraphs)
        2. Single newlines (lines)
        3. Spaces (words)
        4. Characters (fallback)

        Args:
            text: The input text to chunk.
            chunk_size: Maximum size of each chunk (default: 1000).
            chunk_overlap: Number of characters to overlap between chunks (default: 200).

        Returns:
            List of text chunks.
        """
        # Handle empty or very short text
        if not text or not text.strip():
            return []

        if len(text) <= chunk_size:
            return [text]

        # Separators in order of preference (try to split on natural boundaries first)
        separators = ["\n\n", "\n", ". ", " ", ""]

        return self._recursive_split(text, chunk_size, chunk_overlap, separators)

    def _recursive_split(
        self, text: str, chunk_size: int, chunk_overlap: int, separators: List[str]
    ) -> List[str]:
        """
        Recursively split text using the provided separators.

        Args:
            text: Text to split.
            chunk_size: Maximum chunk size.
            chunk_overlap: Overlap between chunks.
            separators: List of separators to try in order.

        Returns:
            List of text chunks.
        """
        final_chunks: List[str] = []

        # Get the current separator
        separator = separators[0] if separators else ""

        # Split the text by the current separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)  # Character-level split

        # Process each split
        good_splits: List[str] = []
        for split in splits:
            if len(split) <= chunk_size:
                good_splits.append(split)
            else:
                # This split is too large, need to split it further
                if good_splits:
                    # Merge accumulated good splits first
                    final_chunks.extend(
                        self._merge_splits(good_splits, chunk_size, chunk_overlap, separator)
                    )
                    good_splits = []

                # Recursively split the large chunk with next separator
                if len(separators) > 1:
                    final_chunks.extend(
                        self._recursive_split(split, chunk_size, chunk_overlap, separators[1:])
                    )
                else:
                    # No more separators, force split at chunk_size
                    for i in range(0, len(split), chunk_size - chunk_overlap):
                        final_chunks.append(split[i : i + chunk_size])

        # Merge any remaining good splits
        if good_splits:
            final_chunks.extend(self._merge_splits(good_splits, chunk_size, chunk_overlap, separator))

        return [chunk for chunk in final_chunks if chunk.strip()]

    def _merge_splits(
        self, splits: List[str], chunk_size: int, chunk_overlap: int, separator: str
    ) -> List[str]:
        """
        Merge small splits into chunks of appropriate size.

        Args:
            splits: List of text segments to merge.
            chunk_size: Maximum chunk size.
            chunk_overlap: Overlap between chunks.
            separator: Separator used to join splits.

        Returns:
            List of merged chunks.
        """
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for split in splits:
            split_len = len(split)
            separator_len = len(separator) if current_chunk else 0

            # Check if adding this split would exceed chunk_size
            if current_length + split_len + separator_len > chunk_size and current_chunk:
                # Save current chunk and start a new one
                chunk_text = separator.join(current_chunk)
                chunks.append(chunk_text)

                # Create overlap by keeping some of the previous content
                # Keep splits that fit within the overlap window
                overlap_length = 0
                overlap_splits: List[str] = []
                for prev_split in reversed(current_chunk):
                    if overlap_length + len(prev_split) + len(separator) <= chunk_overlap:
                        overlap_splits.insert(0, prev_split)
                        overlap_length += len(prev_split) + len(separator)
                    else:
                        break

                current_chunk = overlap_splits
                current_length = overlap_length

            # Add the split to current chunk
            current_chunk.append(split)
            current_length += split_len + separator_len

        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(separator.join(current_chunk))

        return chunks

    async def ingest_note(
        self,
        note_text: str,
        metadata: dict[str, Any] | None = None,
        batch_size: int = 50,
    ) -> dict[str, Any]:
        """
        Ingest a note into the RAG system with robust batch processing.

        This function:
        1. Chunks the note text using RecursiveCharacterTextSplitter
        2. Generates embeddings for chunks in batches
        3. Stores chunks and embeddings in ChromaDB with progress logging
        4. Handles errors gracefully, continuing to next batch on failure

        Args:
            note_text: The text content of the note.
            metadata: Optional metadata to attach to the note chunks.
            batch_size: Number of chunks to process per batch (default: 50).

        Returns:
            A dictionary containing ingestion statistics and the note ID.

        Raises:
            ValueError: If note text is empty or chunking fails.
            Exception: If all batches fail during ingestion.
        """
        if not note_text or not note_text.strip():
            raise ValueError("Note text cannot be empty")

        # Generate a unique ID for this note
        note_id = str(uuid.uuid4())

        # Prepare metadata
        base_metadata = metadata or {}
        base_metadata["note_id"] = note_id

        # Chunk the text using RecursiveCharacterTextSplitter with optimized settings
        chunks = self.chunk_text(note_text, chunk_size=1000, chunk_overlap=200)

        if not chunks:
            raise ValueError("Text chunking resulted in no chunks")

        total_chunks = len(chunks)
        logger.info(f"Chunking complete: {total_chunks} chunks created")
        logger.debug(f"Processing in batches of {batch_size}")

        # Track statistics
        successful_chunks = 0
        failed_chunks = 0
        failed_batches: List[int] = []

        # Process chunks in batches
        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size

            batch_chunks = chunks[batch_start:batch_end]
            batch_size_actual = len(batch_chunks)

            try:
                # Generate embeddings for this batch
                logger.debug(
                    f"Processing batch {batch_num}/{total_batches} "
                    f"(chunks {batch_start + 1}-{batch_end}/{total_chunks})"
                )

                embeddings = await self.embedding_provider.get_embeddings_batch(batch_chunks)

                # Prepare data for ChromaDB
                batch_ids = [
                    f"{note_id}_chunk_{i}" for i in range(batch_start, batch_end)
                ]
                batch_metadatas = [
                    {
                        **base_metadata,
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                    }
                    for i in range(batch_start, batch_end)
                ]

                # Add batch to ChromaDB collection
                self.collection.add(
                    ids=batch_ids,
                    embeddings=embeddings,
                    documents=batch_chunks,
                    metadatas=batch_metadatas,
                )

                successful_chunks += batch_size_actual
                logger.debug(
                    f"Batch {batch_num}/{total_batches} completed successfully "
                    f"({successful_chunks}/{total_chunks} chunks processed)"
                )

                # Add small delay between batches to let the local LLM cool down
                # Skip delay for last batch
                if batch_end < total_chunks:
                    time.sleep(0.5)

            except Exception as e:
                # Log error but continue with next batch
                failed_chunks += batch_size_actual
                failed_batches.append(batch_num)
                logger.error(f"Batch {batch_num}/{total_batches} failed: {str(e)}")
                logger.warning(
                    f"Continuing to next batch... "
                    f"({failed_chunks} chunks failed so far)"
                )
                continue

        # Log final summary
        logger.info("=" * 60)
        logger.info(f"Ingestion Summary:")
        logger.info(f"  Total chunks: {total_chunks}")
        logger.info(f"  Successful: {successful_chunks}")
        logger.info(f"  Failed: {failed_chunks}")
        if failed_batches:
            logger.info(f"  Failed batches: {failed_batches}")
        logger.info("=" * 60)

        # If all batches failed, raise an exception
        if successful_chunks == 0:
            raise Exception(
                f"All {total_batches} batches failed during ingestion. "
                f"Check your embedding provider and ChromaDB connection."
            )

        # Return statistics (include both successful and failed chunks)
        return {
            "note_id": note_id,
            "chunks_created": successful_chunks,
            "chunks_failed": failed_chunks,
            "total_chunks": total_chunks,
            "total_characters": len(note_text),
            "embedding_dimension": (
                self.embedding_provider.get_embedding_dimension()
                if successful_chunks > 0
                else 0
            ),
            "success_rate": f"{(successful_chunks / total_chunks * 100):.1f}%",
        }

    async def query_notes(
        self,
        query: str,
        k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> List[dict[str, Any]]:
        """
        Query the RAG system for relevant note chunks with re-ranking and context expansion.

        This function implements a multi-stage retrieval strategy for improved accuracy:
        1. Generates an embedding for the query
        2. Performs semantic search in ChromaDB to retrieve 50 candidate chunks (high recall)
        3. Uses FlashRank to re-score and re-rank the candidates against the query
        4. Returns the top k most relevant chunks (high precision)
        5. Expands context by fetching neighboring chunks (±1 chunk) for each result

        Context Expansion:
            - For each top-k chunk, fetches the previous chunk (chunk_index - 1) and
              next chunk (chunk_index + 1) if they exist
            - Merges them as: [Previous Context] + [Main Match] + [Next Context]
            - Handles edge cases: first chunk (no previous), last chunk (no next)
            - Performance: Single batched ChromaDB query for all neighbors

        This approach allows deep search across all chunks while providing rich
        surrounding context to the LLM for better understanding.

        Args:
            query: The search query text.
            k: Number of final results to return after re-ranking (default: 5, max: 50).
            filter_metadata: Optional metadata filters for the search.

        Returns:
            List of dictionaries containing:
            - id: Chunk ID
            - text: EXPANDED chunk text with neighboring context
            - metadata: Chunk metadata with additional fields:
                - context_expanded: bool (True if expansion applied)
                - original_text: str (original text before expansion)
                - expansion_info: dict (neighbor information)
            - distance: Similarity distance (lower = more similar, from ChromaDB)
            - rerank_score: Re-ranking score (higher = more relevant, only if re-ranker available)

        Raises:
            ValueError: If query is empty.
            Exception: If query fails.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Limit k to reasonable bounds
        k = max(1, min(k, 50))

        # STEP 1: Generate embedding for the query
        query_embedding = await self.embedding_provider.get_embedding(query)

        # STEP 2: Retrieve candidate chunks from ChromaDB (high recall)
        # Retrieve 50 chunks to maximize recall, then re-rank for precision
        initial_k = 50
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=initial_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        # Format initial results
        candidate_chunks = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                candidate_chunks.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                    }
                )

        # If no results or re-ranker unavailable, return vector search results
        if not candidate_chunks:
            return []

        if not self.reranker_available or self.reranker is None:
            # Fallback: return top k from vector search with context expansion
            expanded_results = self._expand_context(candidate_chunks[:k])
            return expanded_results

        # STEP 3: Re-rank using FlashRank for improved relevance
        try:
            # Prepare passages for re-ranking
            passages = [
                {
                    "id": i,
                    "text": chunk["text"],
                    "meta": {
                        "chunk_id": chunk["id"],
                        "distance": chunk["distance"],
                        "metadata": chunk["metadata"],
                    },
                }
                for i, chunk in enumerate(candidate_chunks)
            ]

            # Perform re-ranking
            rerank_request = RerankRequest(query=query, passages=passages)
            reranked_results = self.reranker.rerank(rerank_request)

            # STEP 4: Format and return top k re-ranked results
            final_results = []
            for result in reranked_results[:k]:
                original_chunk = candidate_chunks[result["id"]]
                final_results.append(
                    {
                        "id": original_chunk["id"],
                        "text": original_chunk["text"],
                        "metadata": original_chunk["metadata"],
                        "distance": original_chunk["distance"],  # Original vector distance
                        "rerank_score": result["score"],  # FlashRank relevance score
                    }
                )

            # STEP 5: Apply context expansion
            expanded_results = self._expand_context(final_results)
            return expanded_results

        except Exception as e:
            # If re-ranking fails, log error and fall back to vector search
            logger.warning(f"FlashRank re-ranking failed: {e}. Falling back to vector search.")
            expanded_results = self._expand_context(candidate_chunks[:k])
            return expanded_results

    def _expand_context(self, chunks: List[dict[str, Any]]) -> List[dict[str, Any]]:
        """
        Expand context by fetching neighboring chunks for each result.

        For each chunk, fetches the previous chunk (chunk_index - 1) and next chunk
        (chunk_index + 1) if they exist, then merges them into a single expanded context.

        Args:
            chunks: List of chunk dictionaries with 'id', 'text', 'metadata', etc.

        Returns:
            List of chunks with expanded text in the 'text' field and additional metadata:
            - context_expanded: bool (True if expansion was applied)
            - original_text: str (original chunk text before expansion)
            - expansion_info: dict (details about which chunks were added)

        Edge Cases Handled:
            - First chunk (index=0): No previous chunk, only add next
            - Last chunk (index=total_chunks-1): No next chunk, only add previous
            - Single chunk document: No neighbors, return as-is
            - Missing metadata: Return chunk without expansion
            - ChromaDB fetch failure: Log warning and return original chunk
        """
        if not chunks:
            return chunks

        # Step 1: Collect all neighbor IDs for batch fetching
        neighbor_requests = []  # List of (chunk_idx, prev_id, next_id)
        all_neighbor_ids = []

        for idx, chunk in enumerate(chunks):
            metadata = chunk.get('metadata', {})
            note_id = metadata.get('note_id')
            chunk_index = metadata.get('chunk_index')
            total_chunks = metadata.get('total_chunks')

            # Validate metadata
            if not all([note_id is not None, chunk_index is not None, total_chunks is not None]):
                logger.warning(f"Chunk {chunk.get('id')} missing required metadata for expansion. Skipping.")
                neighbor_requests.append((idx, None, None))
                continue

            # Calculate neighbor IDs
            prev_id = f"{note_id}_chunk_{chunk_index - 1}" if chunk_index > 0 else None
            next_id = f"{note_id}_chunk_{chunk_index + 1}" if chunk_index < total_chunks - 1 else None

            neighbor_requests.append((idx, prev_id, next_id))

            if prev_id:
                all_neighbor_ids.append(prev_id)
            if next_id:
                all_neighbor_ids.append(next_id)

        # Step 2: Batch fetch all neighbors in a single query
        neighbor_map = {}
        if all_neighbor_ids:
            try:
                neighbor_results = self.collection.get(
                    ids=all_neighbor_ids,
                    include=["documents"]
                )

                # Build lookup map
                if neighbor_results and neighbor_results.get('ids'):
                    neighbor_map = {
                        chunk_id: doc
                        for chunk_id, doc in zip(neighbor_results['ids'], neighbor_results['documents'])
                    }
            except Exception as e:
                logger.warning(f"Context expansion failed during ChromaDB fetch: {e}")
                logger.warning("Returning original chunks without expansion.")
                return chunks

        # Step 3: Expand each chunk
        expanded_chunks = []

        for chunk_idx, prev_id, next_id in neighbor_requests:
            chunk = chunks[chunk_idx]

            # If metadata was invalid, return chunk as-is
            if prev_id is None and next_id is None and chunk.get('metadata', {}).get('chunk_index') is None:
                chunk_copy = chunk.copy()
                chunk_copy['metadata'] = chunk.get('metadata', {}).copy()
                chunk_copy['metadata']['context_expanded'] = False
                expanded_chunks.append(chunk_copy)
                continue

            # Fetch neighbor texts
            prev_text = neighbor_map.get(prev_id) if prev_id else None
            next_text = neighbor_map.get(next_id) if next_id else None

            # Build expanded text
            expanded_sections = []

            if prev_text:
                expanded_sections.append("[Previous Context]\n" + prev_text)

            expanded_sections.append("[Main Match]\n" + chunk['text'])

            if next_text:
                expanded_sections.append("[Next Context]\n" + next_text)

            expanded_text = "\n\n".join(expanded_sections)

            # Create expanded chunk
            expanded_chunk = chunk.copy()
            expanded_chunk['metadata'] = chunk.get('metadata', {}).copy()
            expanded_chunk['text'] = expanded_text
            expanded_chunk['metadata']['context_expanded'] = True
            expanded_chunk['metadata']['original_text'] = chunk['text']
            expanded_chunk['metadata']['expansion_info'] = {
                'has_previous': prev_text is not None,
                'has_next': next_text is not None,
                'previous_chunk_id': prev_id,
                'next_chunk_id': next_id,
            }

            expanded_chunks.append(expanded_chunk)

        return expanded_chunks

    async def delete_note(self, note_id: str) -> dict[str, Any]:
        """
        Delete all chunks associated with a note.

        Args:
            note_id: The ID of the note to delete.

        Returns:
            A dictionary with deletion statistics.
        """
        # Query to find all chunks with this note_id
        results = self.collection.get(
            where={"note_id": note_id},
            include=["metadatas"],
        )

        if not results["ids"]:
            return {
                "note_id": note_id,
                "chunks_deleted": 0,
                "found": False,
            }

        # Delete all chunks
        self.collection.delete(ids=results["ids"])

        return {
            "note_id": note_id,
            "chunks_deleted": len(results["ids"]),
            "found": True,
        }

    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the ChromaDB collection.

        Returns:
            Dictionary containing collection statistics.
        """
        count = self.collection.count()

        return {
            "collection_name": self.settings.chroma_collection_name,
            "total_chunks": count,
            "embedding_dimension": self.embedding_provider.get_embedding_dimension(),
        }

    def list_notes(self, limit: int = 100) -> List[dict[str, Any]]:
        """
        List all unique notes in the collection.

        Args:
            limit: Maximum number of notes to return.

        Returns:
            List of note summaries with metadata.
        """
        # Get all items from collection
        results = self.collection.get(
            limit=limit * 10,  # Get more to account for multiple chunks per note
            include=["metadatas"],
        )

        # Group by note_id
        notes_map: dict[str, dict[str, Any]] = {}
        for metadata in results.get("metadatas", []):
            note_id = metadata.get("note_id")
            if note_id and note_id not in notes_map:
                notes_map[note_id] = {
                    "note_id": note_id,
                    "metadata": {
                        k: v for k, v in metadata.items() if k not in ["note_id", "chunk_index", "total_chunks"]
                    },
                    "total_chunks": metadata.get("total_chunks", 1),
                }

        # Return limited list
        return list(notes_map.values())[:limit]

    def reset_collection(self) -> dict[str, str]:
        """
        Delete all data from the collection.

        WARNING: This is irreversible!

        Returns:
            Confirmation message.
        """
        self.client.delete_collection(name=self.settings.chroma_collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        return {
            "status": "success",
            "message": f"Collection '{self.settings.chroma_collection_name}' has been reset",
        }
