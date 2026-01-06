"""
Main FastAPI Application Entry Point.

This module initializes and configures the FastAPI application for the RAG Notes App.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup: Initialize services, database connections, etc.
    settings = get_settings()
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📍 ChromaDB path: {settings.chroma_db_path}")
    print(f"🤖 Ollama URL: {settings.ollama_base_url}")

    yield

    # Shutdown: Cleanup resources
    print("👋 Shutting down RAG Notes App")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A local-first RAG Notes App using Ollama and ChromaDB",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": settings.app_version}

    # TODO: Register API routers here
    # from app.api import notes_router, chat_router
    # app.include_router(notes_router, prefix="/api/notes", tags=["notes"])
    # app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
