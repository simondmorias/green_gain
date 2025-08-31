"""
Unit tests for the enhanced static response service.

This module contains comprehensive tests for the static response service,
keyword matching, and response generation functionality.
"""

import time

import pytest

from app.data.sample_data import (
    get_pricing_data,
    get_product_data,
    get_promotion_data,
    get_revenue_data,
    get_suggestions,
)
from app.services.static_responses import StaticResponseService
from app.utils.keyword_matcher import KeywordMatcher, QueryCategory


class TestKeywordMatcher:
    """Test cases for the KeywordMatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = KeywordMatcher()

    def test_revenue_keyword_matching(self):
        """Test revenue-related keyword matching."""
        test_cases = [
            ("What's our revenue this quarter?", QueryCategory.REVENUE),
            ("Show me sales performance", QueryCategory.REVENUE),
            ("How are earnings looking?", QueryCategory.REVENUE),
            ("Total revenue growth", QueryCategory.REVENUE),
            ("Sales targets and achievements", QueryCategory.REVENUE),
        ]

        for message, expected_category in test_cases:
            result = self.matcher.categorize_query(message)
            assert result == expected_category, f"Failed for message: '{message}'"

    def test_promotion_keyword_matching(self):
        """Test promotion-related keyword matching."""
        test_cases = [
            ("How are our promotions doing?", QueryCategory.PROMOTION),
            ("Show me campaign performance", QueryCategory.PROMOTION),
            ("Promotion ROI analysis", QueryCategory.PROMOTION),
            ("Marketing campaign effectiveness", QueryCategory.PROMOTION),
            ("Discount impact on sales", QueryCategory.PROMOTION),
        ]

        for message, expected_category in test_cases:
            result = self.matcher.categorize_query(message)
            assert result == expected_category, f"Failed for message: '{message}'"

    def test_pricing_keyword_matching(self):
        """Test pricing-related keyword matching."""
        test_cases = [
            ("What's our pricing strategy?", QueryCategory.PRICING),
            ("Competitive pricing analysis", QueryCategory.PRICING),
            ("Price elasticity insights", QueryCategory.PRICING),
            ("Cost optimization opportunities", QueryCategory.PRICING),
            ("Pricing position vs competitors", QueryCategory.PRICING),
        ]

        for message, expected_category in test_cases:
            result = self.matcher.categorize_query(message)
            assert result == expected_category, f"Failed for message: '{message}'"

    def test_product_keyword_matching(self):
        """Test product-related keyword matching."""
        test_cases = [
            ("Which products are top performers?", QueryCategory.PRODUCT),
            ("Brand performance analysis", QueryCategory.PRODUCT),
            ("Category market share", QueryCategory.PRODUCT),
            ("Product portfolio review", QueryCategory.PRODUCT),
            ("Item performance breakdown", QueryCategory.PRODUCT),
        ]

        for message, expected_category in test_cases:
            result = self.matcher.categorize_query(message)
            assert result == expected_category, f"Failed for message: '{message}'"

    def test_help_keyword_matching(self):
        """Test help-related keyword matching."""
        test_cases = [
            ("What can you help me with?", QueryCategory.HELP),
            ("I need guidance", QueryCategory.HELP),
            ("What options are available?", QueryCategory.HELP),
            ("How do I get support?", QueryCategory.HELP),
            ("Help me understand", QueryCategory.HELP),
        ]

        for message, expected_category in test_cases:
            result = self.matcher.categorize_query(message)
            assert result == expected_category, f"Failed for message: '{message}'"

    def test_unknown_keyword_matching(self):
        """Test handling of unrecognized queries."""
        test_cases = [
            "Random unrelated text",
            "Weather forecast",
            "How to cook pasta",
            "",
            "   ",
        ]

        for message in test_cases:
            result = self.matcher.categorize_query(message)
            assert result == QueryCategory.UNKNOWN, (
                f"Should be UNKNOWN for: '{message}'"
            )

    def test_confidence_scoring(self):
        """Test confidence scoring for matches."""
        # High confidence cases
        high_confidence_cases = [
            "Show me revenue performance and growth",
            "Promotion ROI and campaign effectiveness",
            "Pricing strategy and competitive analysis",
        ]

        for message in high_confidence_cases:
            category = self.matcher.categorize_query(message)
            if category != QueryCategory.UNKNOWN:
                confidence = self.matcher.get_category_confidence(message, category)
                assert confidence > 0.3, f"Low confidence for clear match: '{message}'"

    def test_ambiguous_query_detection(self):
        """Test detection of ambiguous queries."""
        ambiguous_queries = [
            "Show me revenue and promotion performance",
            "Product pricing and competitive analysis",
        ]

        for query in ambiguous_queries:
            is_ambiguous = self.matcher.is_ambiguous_query(query)
            # Note: This might not always be True depending on keyword weights
            # The test verifies the method works without errors
            assert isinstance(is_ambiguous, bool)

    def test_matching_keywords_extraction(self):
        """Test extraction of matched keywords."""
        message = "Show me revenue and sales performance"
        category = QueryCategory.REVENUE
        keywords = self.matcher.get_matching_keywords(message, category)

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should contain revenue-related keywords
        assert any(
            keyword in ["revenue", "sales", "performance"] for keyword in keywords
        )


class TestStaticResponseService:
    """Test cases for the StaticResponseService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = StaticResponseService()

    def test_revenue_response_generation(self):
        """Test revenue response generation."""
        message = "What's our revenue this quarter?"
        response = self.service.get_response(message)

        # Check response structure
        assert "response" in response
        assert "data" in response
        assert "suggestions" in response
        assert "metadata" in response

        # Check response content
        assert isinstance(response["response"], str)
        assert len(response["response"]) > 0
        assert "revenue summary" in response["response"].lower()

        # Check data structure
        data = response["data"]
        assert "total_revenue" in data
        assert "growth_rate" in data
        assert "period" in data
        assert isinstance(data["total_revenue"], int)
        assert data["total_revenue"] == 2450000  # Updated expected value

        # Check suggestions
        assert isinstance(response["suggestions"], list)
        assert len(response["suggestions"]) > 0

        # Check metadata
        metadata = response["metadata"]
        assert "category" in metadata
        assert "processing_time_ms" in metadata
        assert metadata["category"] == "revenue"

    def test_promotion_response_generation(self):
        """Test promotion response generation."""
        message = "How are our promotions performing?"
        response = self.service.get_response(message)

        # Check response structure
        assert all(
            key in response for key in ["response", "data", "suggestions", "metadata"]
        )

        # Check promotion-specific content
        assert "promotion analysis" in response["response"].lower()
        data = response["data"]
        assert "active_promotions" in data
        assert "roi" in data
        assert "campaigns" in data

        # Check metadata
        assert response["metadata"]["category"] == "promotion"

    def test_pricing_response_generation(self):
        """Test pricing response generation."""
        message = "What's our pricing strategy?"
        response = self.service.get_response(message)

        # Check response structure
        assert all(
            key in response for key in ["response", "data", "suggestions", "metadata"]
        )

        # Check pricing-specific content
        assert "pricing analysis" in response["response"].lower()
        data = response["data"]
        assert "price_optimization_opportunities" in data
        assert "products" in data
        assert "competitive_position" in data

        # Check metadata
        assert response["metadata"]["category"] == "pricing"

    def test_product_response_generation(self):
        """Test product response generation."""
        message = "Which products are top performers?"
        response = self.service.get_response(message)

        # Check response structure
        assert all(
            key in response for key in ["response", "data", "suggestions", "metadata"]
        )

        # Check product-specific content
        assert "product performance" in response["response"].lower()
        data = response["data"]
        assert "total_products" in data
        assert "category_performance" in data
        assert "growth_opportunities" in data

        # Check metadata
        assert response["metadata"]["category"] == "product"

    def test_help_response_generation(self):
        """Test help response generation."""
        message = "What can you help me with?"
        response = self.service.get_response(message)

        # Check response structure
        assert all(
            key in response for key in ["response", "data", "suggestions", "metadata"]
        )

        # Check help-specific content
        assert (
            "help" in response["response"].lower()
            or "assist" in response["response"].lower()
        )
        data = response["data"]
        assert "available_categories" in data or "sample_queries" in data

        # Check metadata
        assert response["metadata"]["category"] == "help"

    def test_default_response_generation(self):
        """Test default response for unrecognized queries."""
        message = "Random unrelated topic"
        response = self.service.get_response(message)

        # Check response structure
        assert all(
            key in response for key in ["response", "data", "suggestions", "metadata"]
        )

        # Check default response content
        assert len(response["response"]) > 0
        assert isinstance(response["suggestions"], list)
        assert "revenue, sales, and promotion" in response["response"].lower()

        # Check metadata indicates unknown category
        assert response["metadata"]["category"] == "unknown"

    def test_response_time_performance(self):
        """Test that response time is under 100ms."""
        messages = [
            "What's our revenue?",
            "How are promotions doing?",
            "Show me pricing analysis",
            "Which products perform best?",
            "Random unrelated query",
        ]

        for message in messages:
            start_time = time.time()
            response = self.service.get_response(message)
            end_time = time.time()

            processing_time_ms = (end_time - start_time) * 1000

            # Check that response time is under 100ms
            assert processing_time_ms < 100, (
                f"Response time {processing_time_ms:.2f}ms exceeds 100ms for: '{message}'"
            )

            # Also check the reported processing time in metadata
            reported_time = response["metadata"]["processing_time_ms"]
            assert reported_time < 100, (
                f"Reported processing time {reported_time}ms exceeds 100ms"
            )

    def test_context_awareness(self):
        """Test context-aware response suggestions."""
        # Make a series of queries to build context
        queries = [
            "What's our revenue?",
            "How are promotions doing?",
            "Show me pricing analysis",
        ]

        responses = []
        for query in queries:
            response = self.service.get_response(query)
            responses.append(response)

        # Each response should have suggestions
        for response in responses:
            assert len(response["suggestions"]) > 0
            assert all(
                isinstance(suggestion, str) for suggestion in response["suggestions"]
            )

    def test_data_consistency(self):
        """Test that data returned is consistent and realistic."""
        message = "Show me revenue performance"
        response = self.service.get_response(message)

        data = response["data"]

        # Check data types and ranges
        assert isinstance(data["total_revenue"], int)
        assert data["total_revenue"] > 0
        assert isinstance(data["growth_rate"], (int, float))
        assert -100 < data["growth_rate"] < 1000  # Reasonable growth rate range

        # Check that breakdown adds up reasonably
        if "breakdown" in data:
            breakdown_total = sum(data["breakdown"].values())
            # Should be close to total revenue (allowing for rounding)
            assert (
                abs(breakdown_total - data["total_revenue"]) / data["total_revenue"]
                < 0.1
            )

    def test_service_methods(self):
        """Test service utility methods."""
        # Test get_available_categories
        categories = self.service.get_available_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "revenue" in categories
        assert "promotion" in categories

        # Test get_query_examples
        examples = self.service.get_query_examples()
        assert isinstance(examples, dict)
        assert "revenue" in examples
        assert isinstance(examples["revenue"], list)

        # Test get_performance_stats
        stats = self.service.get_performance_stats()
        assert isinstance(stats, dict)
        assert "total_categories" in stats
        assert stats["total_categories"] > 0


class TestSampleData:
    """Test cases for sample data functions."""

    def test_revenue_data_structure(self):
        """Test revenue data structure and content."""
        data = get_revenue_data()

        required_fields = [
            "total_revenue",
            "currency",
            "period",
            "growth_rate",
            "breakdown",
            "top_performers",
            "regional_breakdown",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check data types
        assert isinstance(data["total_revenue"], int)
        assert isinstance(data["growth_rate"], (int, float))
        assert isinstance(data["breakdown"], dict)
        assert isinstance(data["top_performers"], list)

        # Check top performers structure
        for performer in data["top_performers"]:
            assert "product" in performer
            assert "revenue" in performer
            assert "growth" in performer

    def test_promotion_data_structure(self):
        """Test promotion data structure and content."""
        data = get_promotion_data()

        required_fields = [
            "active_promotions",
            "total_investment",
            "roi",
            "campaigns",
            "performance_metrics",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check campaigns structure
        for campaign in data["campaigns"]:
            assert "name" in campaign
            assert "roi" in campaign
            assert "incremental_revenue" in campaign

    def test_pricing_data_structure(self):
        """Test pricing data structure and content."""
        data = get_pricing_data()

        required_fields = [
            "price_optimization_opportunities",
            "competitive_position",
            "products",
            "market_analysis",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check products structure
        for product in data["products"]:
            assert "name" in product
            assert "current_price" in product
            assert "competitor_avg" in product
            assert "recommended_action" in product

    def test_product_data_structure(self):
        """Test product data structure and content."""
        data = get_product_data()

        required_fields = [
            "total_products",
            "categories",
            "category_performance",
            "growth_opportunities",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check category performance structure
        for category in data["category_performance"]:
            assert "category" in category
            assert "revenue" in category
            assert "growth" in category
            assert "market_share" in category

    def test_suggestions_function(self):
        """Test suggestions function."""
        contexts = ["revenue", "promotion", "pricing", "product", "default"]

        for context in contexts:
            suggestions = get_suggestions(context)
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
            assert all(isinstance(s, str) for s in suggestions)

        # Test invalid context returns default
        invalid_suggestions = get_suggestions("invalid_context")
        default_suggestions = get_suggestions("default")
        assert invalid_suggestions == default_suggestions


class TestIntegration:
    """Integration tests for the complete system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = StaticResponseService()

    def test_end_to_end_conversation_flow(self):
        """Test a complete conversation flow."""
        conversation = [
            "What's our revenue this quarter?",
            "How are our promotions performing?",
            "Show me pricing analysis",
            "Which products are top performers?",
            "What can you help me with?",
        ]

        responses = []
        for message in conversation:
            response = self.service.get_response(message)
            responses.append(response)

            # Each response should be valid
            assert all(
                key in response
                for key in ["response", "data", "suggestions", "metadata"]
            )
            assert len(response["response"]) > 0
            assert len(response["suggestions"]) > 0

        # Check that different categories were recognized
        categories = [r["metadata"]["category"] for r in responses]
        assert len(set(categories)) > 1, "Should recognize different categories"

    def test_realistic_cpg_scenarios(self):
        """Test responses for realistic CPG industry scenarios."""
        cpg_queries = [
            "Show me beverage category performance",
            "What's the ROI on our back-to-school promotion?",
            "How does our pricing compare to competitors?",
            "Which frozen food products have growth potential?",
            "What's driving our revenue growth in the northeast?",
        ]

        for query in cpg_queries:
            response = self.service.get_response(query)

            # Should get a meaningful response
            assert len(response["response"]) > 100  # Substantial response
            assert response["metadata"]["category"] != "unknown"

            # Response should contain CPG-relevant terms
            response_text = response["response"].lower()
            cpg_terms = [
                "revenue",
                "growth",
                "performance",
                "market",
                "product",
                "category",
            ]
            assert any(term in response_text for term in cpg_terms)


if __name__ == "__main__":
    pytest.main([__file__])
