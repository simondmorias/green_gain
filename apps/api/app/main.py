"""
FastAPI main application module.

This module initializes the FastAPI application with CORS support and includes
the chat routes for the conversational UI feature.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import chat

# Create FastAPI application instance
app = FastAPI(
    title="Gain API",
    description="Backend API for the Gain conversational interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "healthy", "service": "gain-api"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {"message": "Welcome to Gain API", "version": "1.0.0", "docs": "/docs"}
