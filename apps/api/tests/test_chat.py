"""
Tests for the chat endpoints.

This module contains tests for the chat API endpoints including message
processing, keyword matching, and input validation.
"""

from fastapi.testclient import TestClient

from app.main import app

# Create test client
client = TestClient(app)


class TestChatEndpoints:
    """Test cases for chat endpoints."""

    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gain-api"

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Welcome to Gain API" in data["message"]
        assert data["version"] == "1.0.0"

    def test_send_message_revenue_keyword(self):
        """Test sending a message with revenue keyword."""
        message_data = {"message": "What's our revenue this quarter?"}
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "revenue summary" in data["response"].lower()
        assert "total_revenue" in data["data"]
        assert data["data"]["total_revenue"] == 2450000

    def test_send_message_sales_keyword(self):
        """Test sending a message with sales keyword."""
        message_data = {"message": "Show me sales performance"}
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "sales performance" in data["response"].lower()
        assert "total_sales" in data["data"]
        assert data["data"]["total_sales"] == 1247

    def test_send_message_promotion_keyword(self):
        """Test sending a message with promotion keyword."""
        message_data = {"message": "How are our promotions doing?"}
        response = client.post("/api/chat/message", json=message_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "data" in data
        assert "promotion analysis" in data["response"].lower()
        assert "active_promotions" in data["data"]
        assert data["data"]["active_promotions"] == 5

    def test_send_message_default_response(self):
        """Test sending a message that triggers default response."""
        message_data = {"message": "Hello, how can you help me?"}
        response = client.post("/api/chat/message", json=message_data)

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
