#!/usr/bin/env python3
"""Verify that the data consistency fix is working."""

# Test revenue data consistency
from app.data.sample_data import get_revenue_data


def main():
    data = get_revenue_data()

    total_revenue = data["total_revenue"]
    breakdown_total = sum(data["breakdown"].values())

    print(f"Total Revenue: ${total_revenue:,}")
    print(f"Breakdown Total: ${breakdown_total:,}")
    print(f"Breakdown details: {data['breakdown']}")

    difference = abs(breakdown_total - total_revenue)
    percentage_diff = (difference / total_revenue) * 100

    print(f"Difference: ${difference:,} ({percentage_diff:.1f}%)")

    if percentage_diff < 10:
        print("✅ Revenue data consistency FIXED!")
        return True
    else:
        print("❌ Revenue data consistency still broken!")
        return False


if __name__ == "__main__":
    main()
