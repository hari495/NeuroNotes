"""
Chat API Routes.

This module provides RAG-augmented chat endpoints that combine semantic search
with LLM generation to answer questions based on your notes.
"""

from typing import Any, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.dependencies import LLMDep, RAGDep


router = APIRouter()


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    query: str = Field(
        ...,
        description="The user's question or query",
        min_length=1,
        max_length=2000,
        examples=["What is machine learning?"],
    )
    k: int = Field(
        default=5,
        description="Number of context chunks to retrieve from notes (after re-ranking)",
        ge=1,
        le=10,
    )
    note_id: str | None = Field(
        default=None,
        description="Filter by specific note ID (searches only that note)",
    )
    filter_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata filters for context retrieval",
    )
    include_sources: bool = Field(
        default=True,
        description="Whether to include source information in the response",
    )


class ContextChunk(BaseModel):
    """Model for a context chunk used in the response."""

    text: str = Field(..., description="The text content of the chunk")
    metadata: dict[str, Any] = Field(..., description="Metadata about the chunk")
    distance: float = Field(..., description="Similarity distance (lower = more relevant)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    query: str = Field(..., description="The user's original query")
    answer: str = Field(..., description="The LLM-generated answer")
    context_used: List[ContextChunk] = Field(
        ...,
        description="The context chunks used to generate the answer",
    )
    num_chunks: int = Field(..., description="Number of context chunks used")
    has_context: bool = Field(
        ...,
        description="Whether any relevant context was found",
    )


class StreamChatRequest(BaseModel):
    """Request model for streaming chat endpoint."""

    query: str = Field(
        ...,
        description="The user's question or query",
        min_length=1,
        max_length=2000,
    )
    k: int = Field(
        default=5,
        description="Number of context chunks to retrieve (after re-ranking)",
        ge=1,
        le=10,
    )
    filter_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata filters for context retrieval",
    )


class SimpleChatResponse(BaseModel):
    """Response model for simplified chat endpoint."""

    query: str = Field(..., description="The user's original query")
    answer: str = Field(..., description="The LLM-generated answer")
    num_chunks_used: int = Field(..., description="Number of context chunks used")


# Helper Functions
def construct_rag_prompt(context_chunks: List[dict[str, Any]], query: str) -> str:
    """
    Construct a RAG prompt that instructs the LLM to answer based only on context.

    Args:
        context_chunks: List of retrieved context chunks.
        query: The user's query.

    Returns:
        The constructed prompt string.
    """
    if not context_chunks:
        return f"""You are a helpful assistant. The user asked a question, but no relevant \
context was found in the knowledge base.

Please politely inform the user that you don't have information about this topic in the \
current knowledge base, and suggest they either:
1. Add relevant notes about this topic first
2. Rephrase their question

User Query: {query}"""

    # Build context section with descriptive titles
    context_text = "\n\n---\n\n".join(
        [
            f"[From: {chunk.get('metadata', {}).get('title', f'Note {i+1}')}]\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ]
    )

    prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context from the user's notes.

IMPORTANT INSTRUCTIONS:
1. Answer the question using ONLY the information in the context below
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Do not make up information or use knowledge outside the provided context
4. When citing sources, use the note titles shown in [From: ...] format (e.g., "According to the Linear Algebra notes...")
5. Be concise but complete in your answer
6. Use markdown formatting for better readability (headers, lists, code blocks, etc.)

7. CRITICAL - Mathematical Notation Requirements:
   You MUST output ALL mathematical content using standard LaTeX notation.

   LaTeX Formatting Rules:
   - Inline math: Use single dollar signs $...$ (e.g., $x^2$, $\\vec{{v}}$, $\\alpha$)
   - Display/block math: Use double dollar signs $$...$$ (e.g., $$\\int_0^1 x^2 dx$$)
   - NEVER use non-standard delimiters like {{#, #», », \\(, \\[, etc.
   - ALWAYS use proper LaTeX commands for:
     * Vectors: $\\vec{{v}}$, $\\mathbf{{x}}$
     * Greek letters: $\\alpha$, $\\beta$, $\\theta$, etc.
     * Subscripts/superscripts: $x_1$, $x^2$, $v_{{ij}}$
     * Sets: $\\mathbb{{R}}$, $\\mathbb{{N}}$, $\\mathbb{{Z}}$, $\\mathbb{{C}}$
     * Functions: $\\sin(x)$, $\\cos(\\theta)$, $\\log(n)$
     * Fractions: $\\frac{{a}}{{b}}$
     * Matrices: $\\begin{{bmatrix}} a & b \\\\ c & d \\end{{bmatrix}}$
     * Sums/products: $\\sum_{{i=1}}^n$, $\\prod_{{i=1}}^n$

8. CRITICAL - Clean PDF Artifacts:
   The context may contain malformed PDF characters. You MUST convert them to proper LaTeX:

   Common PDF artifacts and their LaTeX equivalents:
   - Any text with "»", "#", "# »" before variables → clean LaTeX vectors
     Examples: "#v", "#»v", "# »v" → $\\vec{{v}}$
              "#e1", "#»e1", "# »e1" → $\\vec{{e_1}}$
              "#x", "#»x" → $\\vec{{x}}$ (if it's a vector)

   - Malformed subscripts: "x1", "v2" → $x_1$, $v_2$ (when context indicates subscript)
   - Malformed superscripts: "x2", "R3" → $x^2$, $\\mathbb{{R}}^3$ (when context indicates power/dimension)
   - Broken symbols: "∈" → $\\in$, "∞" → $\\infty$, "≤" → $\\leq$, "≥" → $\\geq$
   - Broken Greek: "alpha", "beta" → $\\alpha$, $\\beta$

   ALWAYS interpret context carefully to determine if a character is a subscript, superscript, or vector notation

CONTEXT FROM NOTES:
{context_text}

USER QUERY: {query}

ANSWER (based only on the context above, with proper LaTeX formatting):"""

    return prompt


# API Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, rag: RAGDep, llm: LLMDep) -> ChatResponse:
    """
    Chat with your notes using RAG.

    This endpoint:
    1. Retrieves relevant context from your notes using semantic search
    2. Constructs a prompt with the context
    3. Uses the LLM to generate an answer based ONLY on the retrieved context

    The LLM is instructed to only use information from your notes, ensuring
    factual answers grounded in your knowledge base.
    """
    try:
        # Build filter metadata
        filter_metadata = request.filter_metadata or {}

        # If note_id is provided, filter by that specific note
        if request.note_id:
            filter_metadata["note_id"] = request.note_id

        # Step 1: Retrieve relevant context
        context_chunks = await rag.query_notes(
            query=request.query,
            k=request.k,
            filter_metadata=filter_metadata if filter_metadata else None,
        )

        # Step 2: Construct RAG prompt
        prompt = construct_rag_prompt(context_chunks, request.query)

        # Step 3: Generate answer using LLM
        answer = await llm.generate_response(prompt)

        # Step 4: Format response
        return ChatResponse(
            query=request.query,
            answer=answer.strip(),
            context_used=[
                ContextChunk(
                    text=chunk["text"],
                    metadata=chunk["metadata"],
                    distance=chunk["distance"],
                )
                for chunk in context_chunks
            ] if request.include_sources else [],
            num_chunks=len(context_chunks),
            has_context=len(context_chunks) > 0,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_stream(request: StreamChatRequest, rag: RAGDep, llm: LLMDep) -> StreamingResponse:
    """
    Chat with your notes using RAG (streaming response).

    Similar to the /chat endpoint, but streams the LLM response as it's generated.
    This provides a better user experience for long responses.

    The response is streamed as plain text chunks.
    """
    try:
        # Step 1: Retrieve relevant context
        context_chunks = await rag.query_notes(
            query=request.query,
            k=request.k,
            filter_metadata=request.filter_metadata,
        )

        # Step 2: Construct RAG prompt
        prompt = construct_rag_prompt(context_chunks, request.query)

        # Step 3: Create streaming generator
        async def generate_stream():
            """Generate streaming response chunks."""
            async for chunk in llm.generate_response_stream(prompt):
                yield chunk

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process streaming chat request: {str(e)}",
        )


@router.post("/chat/simple", response_model=SimpleChatResponse)
async def chat_simple(
    query: str,
    k: int = 5,
    rag: RAGDep = RAGDep,
    llm: LLMDep = LLMDep,
) -> SimpleChatResponse:
    """
    Simplified chat endpoint for quick testing.

    Args:
        query: The user's question.
        k: Number of context chunks to retrieve (default: 5, after re-ranking).

    Returns:
        A simple response with query, answer, and number of chunks used.
    """
    try:
        # Retrieve context
        context_chunks = await rag.query_notes(query=query, k=k)

        # Construct prompt
        prompt = construct_rag_prompt(context_chunks, query)

        # Generate answer
        answer = await llm.generate_response(prompt)

        return SimpleChatResponse(
            query=query,
            answer=answer.strip(),
            num_chunks_used=len(context_chunks),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process simple chat: {str(e)}",
        )
