"""
Application Configuration Management.

This module uses Pydantic Settings to manage environment variables and configuration.
Configuration values can be set via .env file or environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    All settings can be overridden by setting environment variables with the same name.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="RAG Notes App", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="FastAPI host")
    api_port: int = Field(default=8000, description="FastAPI port")

    # Ollama Settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API",
    )
    ollama_llm_model: str = Field(
        default="llama3.2:3b",
        description="Ollama model to use for text generation",
    )
    ollama_embedding_model: str = Field(
        default="nomic-embed-text:latest",
        description="Ollama model to use for embeddings",
    )
    ollama_timeout: int = Field(
        default=120,
        description="Timeout for Ollama API requests in seconds",
    )

    # ChromaDB Settings
    chroma_db_path: str = Field(
        default="./data/chroma",
        description="Path to ChromaDB persistent storage",
    )
    chroma_collection_name: str = Field(
        default="notes_collection",
        description="Name of the ChromaDB collection",
    )

    # RAG Settings
    rag_top_k: int = Field(
        default=5,
        description="Number of documents to retrieve for RAG context",
    )
    rag_similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score for retrieved documents",
    )
    rag_chunk_size: int = Field(
        default=512,
        description="Size of text chunks for embedding",
    )
    rag_chunk_overlap: int = Field(
        default=50,
        description="Overlap between consecutive chunks",
    )

    # Streamlit Settings
    streamlit_port: int = Field(
        default=8501,
        description="Port for Streamlit frontend",
    )

    def get_chroma_db_path(self) -> Path:
        """
        Get ChromaDB path as a Path object.

        Returns:
            Path object pointing to ChromaDB storage directory.
        """
        path = Path(self.chroma_db_path)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    This function uses LRU cache to ensure settings are loaded only once.
    Useful for FastAPI dependency injection.

    Returns:
        Settings instance with all configuration values.
    """
    return Settings()
