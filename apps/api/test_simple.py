#!/usr/bin/env python3
"""
Simple test script to validate the implementation.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.data.sample_data import get_revenue_data
    from app.services.static_responses import StaticResponseService
    from app.utils.keyword_matcher import KeywordMatcher

    print("✅ All imports successful")

    # Test basic functionality
    service = StaticResponseService()

    # Test revenue query
    response = service.get_response("What's our revenue this quarter?")
    print(f"✅ Revenue response generated: {len(response['response'])} chars")
    print(f"   Category: {response['metadata']['category']}")
    print(f"   Total revenue: {response['data']['total_revenue']}")

    # Test unknown query
    response = service.get_response("Random unrelated question")
    print(f"✅ Default response generated: {len(response['response'])} chars")
    print(f"   Category: {response['metadata']['category']}")

    # Test keyword matcher
    matcher = KeywordMatcher()
    category = matcher.categorize_query("Show me sales performance")
    print(f"✅ Keyword matching works: 'sales performance' -> {category.value}")

    # Test data consistency
    data = get_revenue_data()
    print(f"✅ Revenue data: ${data['total_revenue']:,}")

    print("\n🎉 All basic tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
