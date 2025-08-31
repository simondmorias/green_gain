"""
Static response service for the conversational UI.

This module provides keyword-based response matching for revenue-related queries
and returns static responses with sample data for the MVP.
"""

import re
from typing import Any


class StaticResponseService:
    """Service for generating static responses based on keyword matching."""

    def __init__(self):
        """Initialize the static response service with predefined responses."""
        self._responses = {
            "revenue": {
                "response": "Here's your revenue summary for the current period:",
                "data": {
                    "total_revenue": 2450000,
                    "currency": "USD",
                    "period": "Q3 2025",
                    "growth_rate": 12.5,
                    "breakdown": {
                        "product_sales": 1800000,
                        "services": 450000,
                        "subscriptions": 200000,
                    },
                    "top_performers": [
                        {"product": "Premium Package", "revenue": 850000},
                        {"product": "Standard Package", "revenue": 650000},
                        {"product": "Basic Package", "revenue": 300000},
                    ],
                },
            },
            "sales": {
                "response": "Here's your sales performance data:",
                "data": {
                    "total_sales": 1247,
                    "period": "Q3 2025",
                    "target": 1200,
                    "achievement_rate": 103.9,
                    "by_region": {
                        "north_america": 687,
                        "europe": 342,
                        "asia_pacific": 218,
                    },
                    "top_salespeople": [
                        {"name": "Sarah Johnson", "sales": 89, "target": 80},
                        {"name": "Mike Chen", "sales": 76, "target": 75},
                        {"name": "Emma Rodriguez", "sales": 71, "target": 70},
                    ],
                    "conversion_rate": 24.8,
                },
            },
            "promotion": {
                "response": "Here's your promotion analysis:",
                "data": {
                    "active_promotions": 5,
                    "total_discount_given": 125000,
                    "promotion_roi": 3.2,
                    "period": "Q3 2025",
                    "promotions": [
                        {
                            "name": "Summer Sale 2025",
                            "discount_percent": 20,
                            "revenue_impact": 45000,
                            "units_sold": 234,
                            "status": "active",
                        },
                        {
                            "name": "Back to School",
                            "discount_percent": 15,
                            "revenue_impact": 32000,
                            "units_sold": 189,
                            "status": "active",
                        },
                        {
                            "name": "New Customer Bonus",
                            "discount_percent": 25,
                            "revenue_impact": 28000,
                            "units_sold": 156,
                            "status": "active",
                        },
                    ],
                    "effectiveness": {
                        "customer_acquisition": 12.3,
                        "retention_improvement": 8.7,
                        "average_order_value_increase": 15.2,
                    },
                },
            },
        }

        self._default_response = {
            "response": "I can help you with revenue, sales, and promotion insights. Try asking about:\n\n• Revenue performance and growth\n• Sales metrics and targets\n• Promotion effectiveness and ROI\n\nWhat would you like to know more about?",
            "data": {
                "available_topics": ["revenue", "sales", "promotion"],
                "suggestion": "Ask me about your revenue, sales performance, or promotion analysis",
            },
        }

    def get_response(self, message: str) -> dict[str, Any]:
        """
        Get a static response based on keyword matching.

        Args:
            message: The user's input message

        Returns:
            Dictionary containing response text and associated data
        """
        # Convert message to lowercase for case-insensitive matching
        message_lower = message.lower()

        # Check for keywords in the message
        for keyword, response_data in self._responses.items():
            if self._contains_keyword(message_lower, keyword):
                return response_data.copy()

        # Return default response if no keywords match
        return self._default_response.copy()

    def _contains_keyword(self, message: str, keyword: str) -> bool:
        """
        Check if a keyword is present in the message using word boundary matching.

        Args:
            message: The message to search in (lowercase)
            keyword: The keyword to search for

        Returns:
            True if keyword is found, False otherwise
        """
        # Handle both singular and plural forms
        if keyword == "promotion":
            pattern = r"\b(promotion|promotions)\b"
        elif keyword == "revenue":
            pattern = r"\b(revenue|revenues)\b"
        elif keyword == "sales":
            pattern = r"\b(sales|sale)\b"
        else:
            # Default to exact match for other keywords
            pattern = rf"\b{re.escape(keyword)}\b"
        return bool(re.search(pattern, message))

    def get_available_keywords(self) -> list[str]:
        """
        Get list of available keywords that trigger responses.

        Returns:
            List of available keywords
        """
        return list(self._responses.keys())
