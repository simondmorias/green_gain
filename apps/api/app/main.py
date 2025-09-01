"""
FastAPI main application module.

This module initializes the FastAPI application with CORS support and includes
the chat routes for the conversational UI feature.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import admin, chat
from .services.artifact_loader import get_artifact_loader
from .services.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Gain API...")

    # Initialize cache manager and artifact loader
    cache_manager = get_cache_manager()
    artifact_loader = get_artifact_loader()

    # Load artifacts (with cache warming if Redis is available)
    try:
        success = artifact_loader.load_artifacts()
        if success:
            logger.info("Artifacts loaded successfully")
            if cache_manager.enabled:
                logger.info("Cache warming completed")
        else:
            logger.warning("Artifacts loaded with fallback to defaults")
    except Exception as e:
        logger.error(f"Failed to load artifacts: {e}")

    logger.info("Gain API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Gain API...")

    # Close cache connections
    if cache_manager.enabled:
        cache_manager.close()
        logger.info("Cache connections closed")

    logger.info("Gain API shutdown complete")


# Create FastAPI application instance
app = FastAPI(
    title="Gain API",
    description="Backend API for the Gain conversational interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include chat routes
app.include_router(chat.router, prefix="/api")

# Include admin routes
app.include_router(admin.router, prefix="/api")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    cache_manager = get_cache_manager()
    artifact_loader = get_artifact_loader()

    return {
        "status": "healthy",
        "service": "gain-api",
        "cache_enabled": cache_manager.enabled,
        "artifacts_loaded": artifact_loader.loaded,
        "cache_stats": cache_manager.get_stats() if cache_manager.enabled else None,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {"message": "Welcome to Gain API", "version": "1.0.0", "docs": "/docs"}
