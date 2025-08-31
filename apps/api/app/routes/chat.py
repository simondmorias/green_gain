"""
Chat routes for the conversational UI.

This module defines the chat endpoint that accepts user messages and returns
static responses based on keyword matching.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..services.static_responses import StaticResponseService

# Create router instance
router = APIRouter(tags=["chat"])

# Initialize static response service
response_service = StaticResponseService()


class ChatMessage(BaseModel):
    """Request model for chat messages."""

    message: str = Field(
        ..., min_length=1, max_length=2000, description="The user's message text"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        """Validate message content."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or contain only whitespace")
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat responses."""

    response: str = Field(..., description="The assistant's response text")
    data: dict[str, Any] = Field(..., description="Associated data for the response")


@router.post("/chat/message", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage) -> ChatResponse:
    """
    Process a chat message and return a static response.

    This endpoint accepts user messages and returns appropriate static responses
    based on keyword matching for revenue, sales, and promotion queries.

    Args:
        chat_message: The chat message from the user

    Returns:
        ChatResponse containing the assistant's response and associated data

    Raises:
        HTTPException: If message validation fails or processing error occurs
    """
    try:
        # Get response from static response service
        response_data = response_service.get_response(chat_message.message)

        # Return structured response
        return ChatResponse(
            response=response_data["response"], data=response_data["data"]
        )

    except Exception as e:
        # Log error in production, for now just raise HTTP exception
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        ) from e


@router.get("/chat/keywords")
async def get_available_keywords() -> dict[str, Any]:
    """
    Get list of available keywords that trigger specific responses.

    This endpoint returns the keywords that users can include in their messages
    to get specific types of responses.

    Returns:
        Dictionary containing available keywords and usage information
    """
    keywords = response_service.get_available_keywords()

    return {
        "keywords": keywords,
        "usage": "Include these keywords in your message to get specific responses",
        "examples": [
            "What's our revenue this quarter?",
            "Show me sales performance",
            "How are our promotions doing?",
        ],
    }
