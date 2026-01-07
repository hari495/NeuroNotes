"""
Streamlit Chat Interface for RAG Notes App.

This provides a web-based interface for:
- Creating and managing notes
- Chatting with your notes using RAG
- Viewing sources and conversation history
"""

import streamlit as st
import httpx
from typing import List, Dict, Any
import asyncio


# Configuration
API_BASE_URL = "http://localhost:8000"


# Page Configuration
st.set_page_config(
    page_title="RAG Notes Chat",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stChatMessage {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .source-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "notes_count" not in st.session_state:
    st.session_state.notes_count = 0


# Helper Functions
def create_note(title: str, text: str) -> Dict[str, Any]:
    """
    Create a new note via the API.

    Args:
        title: Note title
        text: Note content

    Returns:
        API response dict
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/notes/",
            json={"title": title, "text": text},
            timeout=30.0,
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def chat_with_notes(query: str, k: int = 3, include_sources: bool = True) -> Dict[str, Any]:
    """
    Chat with notes via the API.

    Args:
        query: User's question
        k: Number of context chunks to retrieve
        include_sources: Whether to include source information

    Returns:
        API response dict
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/chat/chat",
            json={
                "query": query,
                "k": k,
                "include_sources": include_sources,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_collection_stats() -> Dict[str, Any]:
    """Get statistics about the note collection."""
    try:
        response = httpx.get(f"{API_BASE_URL}/api/notes/stats", timeout=10.0)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_notes(limit: int = 100) -> Dict[str, Any]:
    """List all notes."""
    try:
        response = httpx.get(f"{API_BASE_URL}/api/notes/list?limit={limit}", timeout=10.0)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Sidebar - Note Creation
st.sidebar.title("📝 Create New Note")

with st.sidebar:
    # Stats display
    st.markdown("---")
    stats_result = get_collection_stats()
    if stats_result["success"]:
        stats = stats_result["data"]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Chunks", stats.get("total_chunks", 0))
        with col2:
            st.metric("Embedding Dim", stats.get("embedding_dimension", 0))

    st.markdown("---")

    # Note creation form
    with st.form("note_form", clear_on_submit=True):
        note_title = st.text_input(
            "Title",
            placeholder="Enter note title...",
            help="A descriptive title for your note",
        )

        note_content = st.text_area(
            "Content",
            placeholder="Enter note content...",
            height=200,
            help="The main content of your note",
        )

        submitted = st.form_submit_button("💾 Save Note", use_container_width=True)

        if submitted:
            if not note_title or not note_content:
                st.error("⚠️ Please provide both title and content!")
            else:
                with st.spinner("Saving note..."):
                    result = create_note(note_title, note_content)

                    if result["success"]:
                        data = result["data"]
                        st.success(f"✅ Note saved successfully!")
                        st.info(
                            f"📊 Created {data['chunks_created']} chunks "
                            f"from {data['total_characters']} characters"
                        )
                        # Update stats
                        st.session_state.notes_count = (
                            st.session_state.notes_count + 1
                        )
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result['error']}")

    # View notes section
    st.markdown("---")
    st.subheader("📚 Your Notes")

    if st.button("🔄 Refresh Notes", use_container_width=True):
        st.rerun()

    notes_result = list_notes(limit=20)
    if notes_result["success"]:
        notes = notes_result["data"].get("notes", [])
        if notes:
            for note in notes:
                with st.expander(f"📄 {note['metadata'].get('title', 'Untitled')}"):
                    st.write(f"**Note ID:** {note['note_id'][:8]}...")
                    st.write(f"**Chunks:** {note['total_chunks']}")
                    if note['metadata']:
                        st.write("**Metadata:**")
                        for key, value in note['metadata'].items():
                            if key != 'note_id':
                                st.write(f"  - {key}: {value}")
        else:
            st.info("No notes yet. Create your first note above!")
    else:
        st.warning("Could not load notes.")

    # Settings
    st.markdown("---")
    st.subheader("⚙️ Chat Settings")

    num_chunks = st.slider(
        "Context Chunks (k)",
        min_value=1,
        max_value=10,
        value=3,
        help="Number of relevant chunks to retrieve for context",
    )

    show_sources = st.checkbox(
        "Show Sources",
        value=True,
        help="Display which notes were used to generate the answer",
    )

    # Store settings in session state
    st.session_state.num_chunks = num_chunks
    st.session_state.show_sources = show_sources


# Main Chat Interface
st.title("💬 Chat with Your Notes")

st.markdown(
    """
    Ask questions about your notes and get answers powered by RAG (Retrieval-Augmented Generation).
    The AI will search your notes for relevant information and provide answers based **only** on your content.
    """
)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display sources if available
        if "sources" in message and message["sources"]:
            with st.expander(f"📚 Sources ({len(message['sources'])} chunks used)"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(
                        f"""
                        <div class="source-box">
                            <strong>Source {i}</strong> -
                            {source['metadata'].get('title', 'Untitled')}
                            (similarity: {1 - source['distance']:.2%})
                            <br><br>
                            <em>{source['text'][:200]}...</em>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# Chat input
if prompt := st.chat_input("Ask a question about your notes..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get settings from session state
    k = st.session_state.get("num_chunks", 3)
    show_sources = st.session_state.get("show_sources", True)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching notes and generating answer..."):
            result = chat_with_notes(prompt, k=k, include_sources=show_sources)

            if result["success"]:
                data = result["data"]
                answer = data["answer"]

                # Display answer
                st.markdown(answer)

                # Add assistant message to chat history
                assistant_message = {
                    "role": "assistant",
                    "content": answer,
                }

                # Add sources if available
                if show_sources and data.get("context_used"):
                    assistant_message["sources"] = data["context_used"]

                    # Display sources
                    with st.expander(f"📚 Sources ({data['num_chunks']} chunks used)"):
                        if data["has_context"]:
                            for i, source in enumerate(data["context_used"], 1):
                                st.markdown(
                                    f"""
                                    <div class="source-box">
                                        <strong>Source {i}</strong> -
                                        {source['metadata'].get('title', 'Untitled')}
                                        (similarity: {1 - source['distance']:.2%})
                                        <br><br>
                                        <em>{source['text'][:200]}...</em>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info(
                                "ℹ️ No relevant context found in your notes. "
                                "Try adding more notes or rephrasing your question."
                            )

                st.session_state.messages.append(assistant_message)

            else:
                error_msg = f"❌ Error: {result['error']}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

# Clear chat button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        Powered by <strong>Ollama</strong> (LLM & Embeddings) + <strong>ChromaDB</strong> (Vector Store)
        <br>
        💡 Tip: Create notes in the sidebar, then ask questions about them!
    </div>
    """,
    unsafe_allow_html=True,
)
