"""
Chat routes for the conversational UI.

This module provides FastAPI routes for handling chat interactions,
including message processing and response generation using the enhanced
static response service with sophisticated keyword matching.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
