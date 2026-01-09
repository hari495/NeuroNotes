"""
Main FastAPI Application Entry Point.

This module initializes and configures the FastAPI application for the RAG Notes App.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup: Initialize services, database connections, etc.
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"ChromaDB path: {settings.chroma_db_path}")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")

    yield

    # Shutdown: Cleanup resources
    logger.info("Shutting down RAG Notes App")


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

    # Register API routers
    from app.api.ai_routes import router as ai_router
    from app.api.chat_routes import router as chat_router
    from app.api.notes_routes import router as notes_router
    from app.api.study_routes import router as study_router

    app.include_router(ai_router, prefix="/api/ai", tags=["AI Services"])
    app.include_router(notes_router, prefix="/api/notes", tags=["Notes & RAG"])
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(study_router, prefix="/api/study", tags=["Study Mode"])

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
