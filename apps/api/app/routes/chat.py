"""
Chat routes for the conversational UI.

This module provides FastAPI routes for handling chat interactions,
including message processing and response generation using the enhanced
static response service with sophisticated keyword matching.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..schemas.entity_recognition import (
    EntityRecognitionRequest,
    EntityRecognitionResponse,
)
from ..services.artifact_loader import get_artifact_loader
from ..services.cache_manager import get_cache_manager
from ..services.entity_recognizer import get_entity_recognition_service
from ..services.static_responses import StaticResponseService

# Create router instance
router = APIRouter(tags=["chat"])

# Initialize the enhanced static response service
response_service = StaticResponseService()


class ChatMessage(BaseModel):
    """Request model for chat messages."""

    message: str


class ChatResponse(BaseModel):
    """Response model for chat responses."""

    response: str
    data: dict[str, Any]
    suggestions: list[str]
    metadata: dict[str, Any]


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage) -> ChatResponse:
    """
    Process a chat message and return an enhanced static response.

    This endpoint accepts user messages and returns appropriate static responses
    based on sophisticated keyword matching for revenue, promotion, pricing,
    and product queries.

    Args:
        chat_message: The chat message from the user

    Returns:
        ChatResponse containing the assistant's response, data, suggestions, and metadata

    Raises:
        HTTPException: If message validation fails or processing error occurs
    """
    try:
        # Get response from enhanced static response service
        response_data = response_service.get_response(chat_message.message)

        # Return structured response with all fields
        return ChatResponse(
            response=response_data["response"],
            data=response_data["data"],
            suggestions=response_data.get("suggestions", []),
            metadata=response_data.get("metadata", {}),
        )

    except Exception as e:
        # Log error in production, for now just raise HTTP exception
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        ) from e


@router.get("/chat/categories")
async def get_available_categories() -> dict[str, Any]:
    """
    Get list of available query categories and examples.

    This endpoint returns the categories that the system can handle
    along with example queries for each category.

    Returns:
        Dictionary containing available categories and example queries
    """
    categories = response_service.get_available_categories()
    examples = response_service.get_query_examples()

    return {
        "categories": categories,
        "examples": examples,
        "usage": "Include keywords from these categories in your message to get specific responses",
        "total_categories": len(categories),
    }


@router.get("/chat/keywords")
async def get_available_keywords() -> dict[str, Any]:
    """
    Get list of available keywords that trigger specific responses.

    This endpoint returns the keywords that users can include in their messages
    to get specific types of responses. Maintained for backward compatibility.

    Returns:
        Dictionary containing available keywords and usage information
    """
    categories = response_service.get_available_categories()

    return {
        "keywords": categories,  # Categories are the main keywords
        "usage": "Include these keywords in your message to get specific responses",
        "examples": [
            "What's our revenue this quarter?",
            "Show me promotion performance",
            "How's our pricing positioned?",
            "Which products are top performers?",
        ],
        "note": "Use /chat/categories for more detailed examples",
    }


@router.get("/chat/stats")
async def get_performance_stats() -> dict[str, Any]:
    """
    Get performance statistics for the chat service.

    This endpoint returns performance metrics and statistics about
    the chat service for monitoring purposes.

    Returns:
        Dictionary containing performance statistics
    """
    stats = response_service.get_performance_stats()

    return {
        "service_stats": stats,
        "status": "operational",
        "features": [
            "Enhanced keyword matching",
            "Context-aware responses",
            "Realistic CPG data",
            "Performance monitoring",
            "Suggestion system",
        ],
    }


@router.post("/chat/recognize-entities", response_model=EntityRecognitionResponse)
async def recognize_entities(
    request: EntityRecognitionRequest,
) -> EntityRecognitionResponse:
    """
    Recognize entities in the provided text for live intent highlighting.

    This endpoint processes user input text and identifies entities such as
    manufacturers, products, metrics, and time periods, returning both
    tagged text and entity metadata.

    Args:
        request: Entity recognition request with text and options

    Returns:
        EntityRecognitionResponse with tagged text and recognized entities

    Raises:
        HTTPException: If entity recognition fails
    """
    try:
        # Get entity recognition service
        entity_service = get_entity_recognition_service()

        # Process the text
        result = entity_service.recognize(
            text=request.text,
            options=request.options.model_dump() if request.options else None,
        )

        # Convert to response format
        entities = []
        for entity in result.get("entities", []):
            entities.append(
                {
                    "text": entity["text"],
                    "type": entity["type"],
                    "start": entity["start"],
                    "end": entity["end"],
                    "confidence": entity.get("confidence", 1.0),
                     "id": str(entity.get("id")) if entity.get("id") is not None else None,
                    "metadata": entity.get(
                        "metadata", {"display_name": entity["text"]}
                    ),
                }
            )

        return EntityRecognitionResponse(
            tagged_text=result["tagged_text"],
            entities=entities,
            processing_time_ms=result.get("processing_time_ms", 0),
            suggestions=result.get("suggestions", []),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Entity recognition failed: {str(e)}"
        ) from e


@router.post("/chat/cache/invalidate")
async def invalidate_cache() -> dict[str, Any]:
    """
    Invalidate all cached artifacts and results.

    This endpoint clears the Redis cache to force a reload of artifacts
    and clear cached recognition results.

    Returns:
        Dictionary with invalidation status
    """
    try:
        artifact_loader = get_artifact_loader()
        cache_manager = get_cache_manager()

        # Invalidate cache
        success = artifact_loader.invalidate_cache()

        # Force reload artifacts
        artifact_loader.reload()

        return {
            "status": "success" if success else "partial",
            "message": "Cache invalidated and artifacts reloaded",
            "cache_enabled": cache_manager.enabled,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Cache invalidation failed: {str(e)}"
        ) from e


@router.get("/chat/cache/stats")
async def get_cache_stats() -> dict[str, Any]:
    """
    Get cache performance statistics.

    This endpoint returns cache hit rates, latency metrics,
    and artifact loading statistics.

    Returns:
        Dictionary with cache statistics
    """
    try:
        cache_manager = get_cache_manager()
        artifact_loader = get_artifact_loader()

        return {
            "cache": cache_manager.get_stats(),
            "artifacts": artifact_loader.get_stats(),
            "status": "operational",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        ) from e


@router.post("/chat/artifacts/reload")
async def reload_artifacts() -> dict[str, Any]:
    """
    Reload entity artifacts from files.

    This endpoint forces a reload of entity artifacts from the file system,
    bypassing the cache and updating it with fresh data.

    Returns:
        Dictionary with reload status
    """
    try:
        artifact_loader = get_artifact_loader()
        entity_service = get_entity_recognition_service()

        # Reload artifacts
        success = artifact_loader.reload()

        # Reload in entity service
        entity_service.reload_artifacts()

        return {
            "status": "success" if success else "failed",
            "message": "Artifacts reloaded from files",
            "stats": artifact_loader.get_stats(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Artifact reload failed: {str(e)}"
        ) from e
