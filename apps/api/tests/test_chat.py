"""
Unit tests for the chat API endpoints.

This module contains comprehensive tests for the chat API endpoints,
including message processing, keyword matching, and response validation.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestChatEndpoints:
    """Test cases for chat API endpoints."""

    def test_send_revenue_message(self):
        """Test sending a revenue-related message."""
        message_data = {"message": "What's our revenue this quarter?"}
        response = client.post("/api/chat", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "suggestions" in data
        assert "metadata" in data
        assert "revenue summary" in data["response"].lower()
        assert "total_revenue" in data["data"]

    def test_send_sales_message(self):
        """Test sending a sales-related message."""
        message_data = {"message": "How are our sales performing?"}
        response = client.post("/api/chat", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "revenue summary" in data["response"].lower()
        assert "total_revenue" in data["data"]

    def test_send_promotion_message(self):
        """Test sending a promotion-related message."""
        message_data = {"message": "Show me our promotion performance"}
        response = client.post("/api/chat", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "promotion analysis" in data["response"].lower()
        assert "active_promotions" in data["data"]

    def test_send_pricing_message(self):
        """Test sending a pricing-related message."""
        message_data = {"message": "What's our pricing strategy?"}
        response = client.post("/api/chat", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "pricing analysis" in data["response"].lower()
        assert "price_optimization_opportunities" in data["data"]

    def test_send_product_message(self):
        """Test sending a product-related message."""
        message_data = {"message": "Which products are top performers?"}
        response = client.post("/api/chat", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "product performance" in data["response"].lower()
        assert "total_products" in data["data"]

    def test_send_help_message(self):
        """Test sending a help-related message."""
        message_data = {"message": "What can you help me with?"}
        response = client.post("/api/chat", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert (
            "help" in data["response"].lower() or "assist" in data["response"].lower()
        )

    def test_send_unknown_message(self):
        """Test sending an unrecognized message."""
        message_data = {"message": "What's the weather like?"}
        response = client.post("/api/chat", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "revenue, sales, and promotion" in data["response"]
        assert "available_topics" in data["data"]

    def test_send_empty_message(self):
        """Test sending an empty message."""
        message_data = {"message": ""}
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 422  # Validation error

    def test_send_whitespace_only_message(self):
        """Test sending a message with only whitespace."""
        message_data = {"message": "   "}
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 422  # Validation error

    def test_send_too_long_message(self):
        """Test sending a message that exceeds maximum length."""
        long_message = "x" * 2001  # Exceeds 2000 character limit
        message_data = {"message": long_message}
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 422  # Validation error

    def test_get_available_keywords(self):
        """Test getting available keywords."""
        response = client.get("/api/chat/keywords")

        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert "usage" in data
        assert "examples" in data
        assert "revenue" in data["keywords"]
        assert "sales" in data["keywords"]
        assert "promotion" in data["keywords"]

    def test_case_insensitive_keyword_matching(self):
        """Test that keyword matching is case insensitive."""
        message_data = {"message": "What's our REVENUE this quarter?"}
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "revenue summary" in data["response"].lower()
        assert "total_revenue" in data["data"]

    def test_partial_keyword_matching(self):
        """Test that partial keywords don't trigger responses."""
        message_data = {
            "message": "What about revenuestream?"
        }  # "revenuestream" should not match "revenue"
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 200
        data = response.json()
        # Should get default response, not revenue response
        assert "revenue, sales, and promotion" in data["response"]
