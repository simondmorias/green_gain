#!/usr/bin/env python3
"""
Quick test script to verify the fixes are working.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data.sample_data import get_revenue_data
from app.services.static_responses import StaticResponseService


def test_revenue_data_consistency():
    """Test that revenue breakdown sums to total revenue."""
    print("Testing revenue data consistency...")
    data = get_revenue_data()

    total_revenue = data["total_revenue"]
    breakdown_total = sum(data["breakdown"].values())

    print(f"Total Revenue: ${total_revenue:,}")
    print(f"Breakdown Total: ${breakdown_total:,}")
    print(f"Breakdown: {data['breakdown']}")

    difference = abs(breakdown_total - total_revenue)
    percentage_diff = (difference / total_revenue) * 100

    print(f"Difference: ${difference:,} ({percentage_diff:.1f}%)")

    if percentage_diff < 10:
        print("✅ Revenue data consistency test PASSED")
        return True
    else:
        print("❌ Revenue data consistency test FAILED")
        return False


def test_default_response():
    """Test that default response contains expected phrase."""
    print("\nTesting default response...")
    service = StaticResponseService()
    response = service.get_response("Random unrelated question")

    response_text = response["response"].lower()
    print(f"Response category: {response['metadata']['category']}")
    print(
        f"Response contains 'revenue, sales, and promotion': {'revenue, sales, and promotion' in response_text}"
    )

    if "revenue, sales, and promotion" in response_text:
        print("✅ Default response test PASSED")
        return True
    else:
        print("❌ Default response test FAILED")
        print(f"Actual response: {response['response'][:200]}...")
        return False


if __name__ == "__main__":
    print("Running fix verification tests...\n")

    test1_passed = test_revenue_data_consistency()
    test2_passed = test_default_response()

    if test1_passed and test2_passed:
        print("\n🎉 All tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED!")
        sys.exit(1)
