#!/usr/bin/env python3
"""
Simple verification that the revenue data is now consistent.
This script directly checks the data without imports.
"""


# Directly check the revenue data from sample_data.py
def check_revenue_data():
    # Read the sample_data.py file and extract the revenue data
    with open("app/data/sample_data.py") as f:
        content = f.read()

    # Extract the breakdown values
    import re

    # Find the breakdown section
    breakdown_match = re.search(r'"breakdown":\s*{([^}]+)}', content)
    if not breakdown_match:
        print("❌ Could not find breakdown section")
        return False

    breakdown_content = breakdown_match.group(1)

    # Extract individual values
    beverages_match = re.search(r'"beverages":\s*(\d+)', breakdown_content)
    snacks_match = re.search(r'"snacks":\s*(\d+)', breakdown_content)
    dairy_match = re.search(r'"dairy":\s*(\d+)', breakdown_content)
    frozen_match = re.search(r'"frozen_foods":\s*(\d+)', breakdown_content)

    if not all([beverages_match, snacks_match, dairy_match, frozen_match]):
        print("❌ Could not extract all breakdown values")
        return False

    beverages = int(beverages_match.group(1)) if beverages_match else 0
    snacks = int(snacks_match.group(1)) if snacks_match else 0
    dairy = int(dairy_match.group(1)) if dairy_match else 0
    frozen = int(frozen_match.group(1)) if frozen_match else 0

    breakdown_total = beverages + snacks + dairy + frozen

    # Extract total revenue
    total_match = re.search(r'"total_revenue":\s*(\d+)', content)
    if not total_match:
        print("❌ Could not find total revenue")
        return False

    total_revenue = int(total_match.group(1))

    print(f"Total Revenue: ${total_revenue:,}")
    print(f"Breakdown Total: ${breakdown_total:,}")
    print(f"  - Beverages: ${beverages:,}")
    print(f"  - Snacks: ${snacks:,}")
    print(f"  - Dairy: ${dairy:,}")
    print(f"  - Frozen: ${frozen:,}")

    difference = abs(breakdown_total - total_revenue)
    percentage_diff = (difference / total_revenue) * 100

    print(f"Difference: ${difference:,} ({percentage_diff:.1f}%)")

    if percentage_diff < 10:
        print("✅ Revenue data consistency FIXED!")
        return True
    else:
        print("❌ Revenue data consistency still broken!")
        return False


def check_default_response():
    # Check if the default response contains the expected phrase
    with open("app/services/static_responses.py") as f:
        content = f.read()

    # Look for the phrase in the default response
    if "revenue, sales, and promotion" in content:
        print("✅ Default response contains expected phrase!")
        return True
    else:
        print("❌ Default response missing expected phrase!")
        return False


if __name__ == "__main__":
    print("Checking fixes...\n")

    fix1 = check_revenue_data()
    print()
    fix2 = check_default_response()

    if fix1 and fix2:
        print("\n🎉 All fixes verified!")
    else:
        print("\n❌ Some fixes still needed!")
