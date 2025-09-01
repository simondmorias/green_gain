"""
Locust configuration for load testing entity recognition API.
"""

import json
import random

from locust import HttpUser, between, task


class EntityRecognitionUser(HttpUser):
    """Locust user for testing entity recognition endpoints."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize test data when user starts."""
        self.test_queries = [
            "Show me Coca-Cola revenue",
            "What's the performance of Pepsi products in Q1 2024?",
            "Compare Unilever and P&G market share",
            "Cadbury chocolate sales trends",
            "Revenue growth for premium brands",
            "Seasonal patterns in beverage sales",
            "Price elasticity analysis for snacks",
            "Market penetration of organic products",
            "Consumer preference shifts in dairy",
            "Regional performance of confectionery brands",
            "Promotional effectiveness for CPG products",
            "Supply chain impact on product availability",
            "Brand loyalty metrics for household goods",
            "Cross-category purchase behavior analysis",
            "Digital marketing ROI for food brands",
        ]

        self.fuzzy_queries = [
            "Show me Coca Cola revenu",
            "Whats the performace of Pepsi prodcts?",
            "Compare Unilver and P&G market shar",
            "Cadburry chocolate sales trens",
            "Revenu growth for premum brands",
        ]

    @task(10)
    def test_entity_recognition(self):
        """Test entity recognition endpoint with exact matching."""
        query = random.choice(self.test_queries)

        payload = {
            "text": query,
            "options": {"fuzzy_matching": False, "confidence_threshold": 0.8},
        }

        with self.client.post(
            "/api/chat/recognize-entities", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    processing_time = data.get("processing_time_ms", 0)

                    # Check if processing time meets target
                    if processing_time > 100:
                        response.failure(
                            f"Processing time too high: {processing_time}ms"
                        )
                    else:
                        response.success()

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(5)
    def test_fuzzy_matching(self):
        """Test entity recognition with fuzzy matching enabled."""
        query = random.choice(self.fuzzy_queries)

        payload = {
            "text": query,
            "options": {"fuzzy_matching": True, "confidence_threshold": 0.8},
        }

        with self.client.post(
            "/api/chat/recognize-entities", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    processing_time = data.get("processing_time_ms", 0)

                    # Fuzzy matching can take longer, allow up to 200ms
                    if processing_time > 200:
                        response.failure(
                            f"Fuzzy processing time too high: {processing_time}ms"
                        )
                    else:
                        response.success()

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)
    def test_chat_endpoint(self):
        """Test the main chat endpoint."""
        query = random.choice(self.test_queries)

        payload = {"message": query}

        with self.client.post(
            "/api/chat", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "response" in data:
                        response.success()
                    else:
                        response.failure("Missing response field")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def test_cache_stats(self):
        """Test cache statistics endpoint."""
        with self.client.get("/api/chat/cache/stats", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "cache" in data:
                        response.success()
                    else:
                        response.failure("Missing cache field")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def test_health_check(self):
        """Test health check endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure(f"Unhealthy status: {data.get('status')}")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")


class AdminUser(HttpUser):
    """Locust user for testing admin endpoints."""

    wait_time = between(5, 10)  # Admin operations are less frequent

    @task(1)
    def test_artifact_stats(self):
        """Test artifact statistics endpoint."""
        with self.client.get(
            "/api/admin/artifacts/stats", catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "artifact_stats" in data:
                        response.success()
                    else:
                        response.failure("Missing artifact_stats field")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def test_admin_health(self):
        """Test admin health check endpoint."""
        with self.client.get("/api/admin/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure(f"Unhealthy status: {data.get('status')}")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")


# Custom load test scenarios
class HighLoadUser(EntityRecognitionUser):
    """User with higher request frequency for stress testing."""

    wait_time = between(0.1, 0.5)  # Very frequent requests

    @task(20)
    def rapid_entity_recognition(self):
        """Rapid-fire entity recognition requests."""
        query = random.choice(self.test_queries)

        payload = {
            "text": query,
            "options": {"fuzzy_matching": False, "confidence_threshold": 0.8},
        }

        with self.client.post(
            "/api/chat/recognize-entities", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    processing_time = data.get("processing_time_ms", 0)

                    # Stricter requirements for high load
                    if processing_time > 50:
                        response.failure(
                            f"Processing time too high under load: {processing_time}ms"
                        )
                    else:
                        response.success()

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")


class CacheTestUser(HttpUser):
    """User specifically for testing cache behavior."""

    wait_time = between(0.5, 1)

    def on_start(self):
        """Initialize with a small set of queries for cache testing."""
        self.cache_test_queries = [
            "Show me Coca-Cola revenue",
            "Pepsi market share",
            "Unilever products",
        ]

    @task(10)
    def test_cache_hits(self):
        """Test cache hit behavior with repeated queries."""
        query = random.choice(self.cache_test_queries)

        payload = {
            "text": query,
            "options": {"fuzzy_matching": False, "confidence_threshold": 0.8},
        }

        with self.client.post(
            "/api/chat/recognize-entities", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    processing_time = data.get("processing_time_ms", 0)

                    # Cache hits should be very fast
                    if processing_time > 20:
                        response.failure(f"Cache hit too slow: {processing_time}ms")
                    else:
                        response.success()

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")


# Load test configuration examples:
#
# Basic load test:
# locust -f locustfile.py --host=http://localhost:8000 -u 10 -r 2 -t 60s
#
# High load test:
# locust -f locustfile.py --host=http://localhost:8000 -u 100 -r 10 -t 300s EntityRecognitionUser
#
# Stress test:
# locust -f locustfile.py --host=http://localhost:8000 -u 50 -r 5 -t 180s HighLoadUser
#
# Cache test:
# locust -f locustfile.py --host=http://localhost:8000 -u 20 -r 4 -t 120s CacheTestUser
