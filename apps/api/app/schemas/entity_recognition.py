"""
Pydantic schemas for entity recognition API.
"""

from typing import Optional

from pydantic import BaseModel, Field


class RecognitionOptions(BaseModel):
    """Options for entity recognition processing."""

    fuzzy_matching: bool = Field(
        default=False, description="Enable fuzzy matching for entities"
    )
    confidence_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum confidence for matches"
    )


class EntityRecognitionRequest(BaseModel):
    """Request schema for entity recognition."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Text to process for entity recognition",
    )
    options: Optional[RecognitionOptions] = Field(
        default=None, description="Processing options"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Show me Cadbury revenue for Q1 2025",
                "options": {"fuzzy_matching": True, "confidence_threshold": 0.8},
            }
        }


class EntityMetadata(BaseModel):
    """Metadata for a recognized entity."""

    display_name: str = Field(..., description="Display name of the entity")
    full_name: Optional[str] = Field(
        None, description="Full name if different from display"
    )
    parent: Optional[str] = Field(None, description="Parent entity if applicable")
    unit: Optional[str] = Field(None, description="Unit for metrics")
    aggregation: Optional[str] = Field(None, description="Aggregation type for metrics")
    start_date: Optional[str] = Field(None, description="Start date for time periods")
    end_date: Optional[str] = Field(None, description="End date for time periods")


class RecognizedEntity(BaseModel):
    """A recognized entity with its metadata."""

    text: str = Field(..., description="The matched text from the input")
    type: str = Field(
        ...,
        description="Entity type (manufacturer, product, metric, time_period, etc.)",
    )
    start: int = Field(..., ge=0, description="Start position in the text")
    end: int = Field(..., gt=0, description="End position in the text")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score of the match"
    )
    id: Optional[str] = Field(None, description="Entity ID from the data warehouse")
    metadata: EntityMetadata = Field(..., description="Additional entity metadata")


class EntityRecognitionResponse(BaseModel):
    """Response schema for entity recognition."""

    tagged_text: str = Field(..., description="Text with XML-style entity tags")
    entities: list[RecognizedEntity] = Field(
        ..., description="List of recognized entities"
    )
    processing_time_ms: float = Field(
        ..., ge=0, description="Processing time in milliseconds"
    )
    suggestions: Optional[list[dict]] = Field(
        default=[], description="Alternative suggestions for low confidence matches"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")

    class Config:
        json_schema_extra = {
            "example": {
                "tagged_text": "Show me <manufacturer>Cadbury</manufacturer> <metric>revenue</metric> for <time-period>Q1 2025</time-period>",
                "entities": [
                    {
                        "text": "Cadbury",
                        "type": "manufacturer",
                        "start": 8,
                        "end": 15,
                        "confidence": 1.0,
                        "id": "MFR_001",
                        "metadata": {
                            "display_name": "Cadbury",
                            "full_name": "Cadbury UK Limited",
                            "parent": "Mondelez International",
                        },
                    },
                    {
                        "text": "revenue",
                        "type": "metric",
                        "start": 16,
                        "end": 23,
                        "confidence": 1.0,
                        "id": "MTR_REV",
                        "metadata": {
                            "display_name": "revenue",
                            "unit": "GBP",
                            "aggregation": "sum",
                        },
                    },
                    {
                        "text": "Q1 2025",
                        "type": "time_period",
                        "start": 28,
                        "end": 35,
                        "confidence": 1.0,
                        "id": None,
                        "metadata": {
                            "display_name": "Q1 2025",
                            "start_date": "2025-01-01",
                            "end_date": "2025-03-31",
                        },
                    },
                ],
                "processing_time_ms": 45.2,
                "suggestions": [],
            }
        }
