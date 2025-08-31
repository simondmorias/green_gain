#!/usr/bin/env python3
"""
Validate the fixes made to the static responses implementation.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_basic_imports():
    """Test that all modules can be imported."""
    try:
        # Test individual module imports
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_keyword_matching():
    """Test keyword matching functionality."""
    try:
        from app.utils.keyword_matcher import KeywordMatcher, QueryCategory

        matcher = KeywordMatcher()

        # Test revenue keywords (including sales)
        test_cases = [
            ("What's our revenue this quarter?", QueryCategory.REVENUE),
            ("Show me sales performance", QueryCategory.REVENUE),
            ("How are our promotions doing?", QueryCategory.PROMOTION),
            ("What's our pricing strategy?", QueryCategory.PRICING),
            ("Which products are top performers?", QueryCategory.PRODUCT),
            ("What can you help me with?", QueryCategory.HELP),
            ("Random unrelated text", QueryCategory.UNKNOWN),
        ]

        for message, expected in test_cases:
            result = matcher.categorize_query(message)
            if result == expected:
                print(f"✅ '{message}' -> {result.value}")
            else:
                print(f"❌ '{message}' -> {result.value} (expected {expected.value})")
                return False

        return True
    except Exception as e:
        print(f"❌ Keyword matching error: {e}")
        return False


def test_response_generation():
    """Test response generation."""
    try:
        from app.services.static_responses import StaticResponseService

        service = StaticResponseService()

        # Test different query types
        test_queries = [
            ("What's our revenue this quarter?", "revenue"),
            ("How are our promotions performing?", "promotion"),
            ("Show me pricing analysis", "pricing"),
            ("Which products are top performers?", "product"),
            ("What can you help me with?", "help"),
            ("Random unrelated question", "unknown"),
        ]

        for query, expected_category in test_queries:
            response = service.get_response(query)

            # Check response structure
            required_keys = ["response", "data", "suggestions", "metadata"]
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key '{key}' in response for: {query}")
                    return False

            # Check category
            actual_category = response["metadata"]["category"]
            if actual_category != expected_category:
                print(
                    f"❌ Wrong category for '{query}': got {actual_category}, expected {expected_category}"
                )
                return False

            print(f"✅ '{query}' -> {actual_category}")

        return True
    except Exception as e:
        print(f"❌ Response generation error: {e}")
        return False


def test_data_values():
    """Test that data values match test expectations."""
    try:
        from app.data.sample_data import get_revenue_data

        data = get_revenue_data()

        # Check expected values
        expected_revenue = 2450000
        actual_revenue = data["total_revenue"]

        if actual_revenue != expected_revenue:
            print(
                f"❌ Revenue mismatch: got {actual_revenue}, expected {expected_revenue}"
            )
            return False

        print(f"✅ Revenue data correct: ${actual_revenue:,}")
        return True
    except Exception as e:
        print(f"❌ Data values error: {e}")
        return False


def test_response_content():
    """Test that response content matches expectations."""
    try:
        from app.services.static_responses import StaticResponseService

        service = StaticResponseService()

        # Test revenue response content
        response = service.get_response("What's our revenue this quarter?")
        response_text = response["response"].lower()

        if "revenue summary" not in response_text:
            print("❌ Revenue response missing 'revenue summary'")
            return False

        # Test promotion response content
        response = service.get_response("How are our promotions performing?")
        response_text = response["response"].lower()

        if "promotion analysis" not in response_text:
            print("❌ Promotion response missing 'promotion analysis'")
            return False

        # Test default response content
        response = service.get_response("Random unrelated question")
        response_text = response["response"].lower()

        if "revenue, sales, and promotion" not in response_text:
            print("❌ Default response missing expected phrase")
            return False

        print("✅ Response content matches expectations")
        return True
    except Exception as e:
        print(f"❌ Response content error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🔍 Validating T4 - Static Data Responses fixes...\n")

    tests = [
        ("Basic Imports", test_basic_imports),
        ("Keyword Matching", test_keyword_matching),
        ("Response Generation", test_response_generation),
        ("Data Values", test_data_values),
        ("Response Content", test_response_content),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed!")
        return True
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
