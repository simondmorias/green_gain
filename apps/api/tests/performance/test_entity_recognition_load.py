"""
Performance tests for entity recognition system.
"""

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import pytest

try:
    from app.services.artifact_loader import get_artifact_loader
    from app.services.cache_manager import get_cache_manager
    from app.services.entity_recognizer import get_entity_recognition_service

    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False


class PerformanceTestSuite:
    """Performance test suite for entity recognition."""

    def __init__(self):
        if not SERVICES_AVAILABLE:
            raise ImportError("Required services not available for performance testing")

        self.entity_service = get_entity_recognition_service()
        self.cache_manager = get_cache_manager()
        self.artifact_loader = get_artifact_loader()

        # Test queries of varying complexity
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

        # Misspelled queries for fuzzy matching tests
        self.fuzzy_queries = [
            "Show me Coca Cola revenu",
            "Whats the performace of Pepsi prodcts?",
            "Compare Unilver and P&G market shar",
            "Cadburry chocolate sales trens",
            "Revenu growth for premum brands",
        ]

    def measure_latency(
        self, query: str, options: Optional[dict] = None
    ) -> dict[str, Any]:
        """
        Measure latency for a single query.

        Args:
            query: Query to test
            options: Recognition options

        Returns:
            Dictionary with timing and result information
        """
        start_time = time.perf_counter()

        try:
            result = self.entity_service.recognize(query, options or {})
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000

            return {
                "query": query,
                "latency_ms": latency_ms,
                "success": True,
                "entities_found": len(result.get("entities", [])),
                "processing_time_reported": result.get("processing_time_ms", 0),
                "error": result.get("error"),
            }

        except Exception as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            return {
                "query": query,
                "latency_ms": latency_ms,
                "success": False,
                "entities_found": 0,
                "processing_time_reported": 0,
                "error": str(e),
            }

    def run_concurrent_test(
        self, queries: list[str], concurrent_users: int, options: Optional[dict] = None
    ) -> dict[str, Any]:
        """
        Run concurrent load test.

        Args:
            queries: List of queries to test
            concurrent_users: Number of concurrent users to simulate
            options: Recognition options

        Returns:
            Dictionary with performance metrics
        """
        print(f"Running concurrent test with {concurrent_users} users...")

        # Prepare query list for concurrent execution
        query_list = []
        queries_per_user = max(1, len(queries) // concurrent_users)

        for i in range(concurrent_users):
            start_idx = (i * queries_per_user) % len(queries)
            end_idx = min(start_idx + queries_per_user, len(queries))
            user_queries = queries[start_idx:end_idx]
            if not user_queries:
                user_queries = [queries[i % len(queries)]]
            query_list.extend(user_queries)

        # Run concurrent requests
        start_time = time.perf_counter()
        results = []

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            future_to_query = {
                executor.submit(self.measure_latency, query, options): query
                for query in query_list
            }

            for future in as_completed(future_to_query):
                result = future.result()
                results.append(result)

        end_time = time.perf_counter()
        total_duration = end_time - start_time

        # Calculate metrics
        latencies = [r["latency_ms"] for r in results if r["success"]]
        successful_requests = len(latencies)
        failed_requests = len(results) - successful_requests

        if latencies:
            p50 = statistics.median(latencies)
            p95 = (
                statistics.quantiles(latencies, n=20)[18]
                if len(latencies) >= 20
                else max(latencies)
            )
            p99 = (
                statistics.quantiles(latencies, n=100)[98]
                if len(latencies) >= 100
                else max(latencies)
            )
            avg_latency = statistics.mean(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
        else:
            p50 = p95 = p99 = avg_latency = max_latency = min_latency = 0

        throughput = len(results) / total_duration if total_duration > 0 else 0

        return {
            "concurrent_users": concurrent_users,
            "total_requests": len(results),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / len(results) if results else 0,
            "total_duration_seconds": total_duration,
            "throughput_rps": throughput,
            "latency_metrics": {
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "avg_ms": avg_latency,
                "min_ms": min_latency,
                "max_ms": max_latency,
            },
            "individual_results": results,
        }

    def test_cache_performance(self) -> dict[str, Any]:
        """
        Test cache hit rates and performance impact.

        Returns:
            Dictionary with cache performance metrics
        """
        print("Testing cache performance...")

        # Clear cache first
        if hasattr(self.cache_manager, "clear_all"):
            self.cache_manager.clear_all()

        # Test queries multiple times to measure cache impact
        test_query = "Show me Coca-Cola revenue for Q1 2024"
        iterations = 10

        # First run (cache miss)
        first_run_times = []
        for _ in range(3):  # Average of 3 runs
            result = self.measure_latency(test_query)
            first_run_times.append(result["latency_ms"])

        avg_cache_miss_time = statistics.mean(first_run_times)

        # Subsequent runs (cache hits)
        cache_hit_times = []
        for _ in range(iterations):
            result = self.measure_latency(test_query)
            cache_hit_times.append(result["latency_ms"])

        avg_cache_hit_time = statistics.mean(cache_hit_times)

        # Calculate cache benefit
        cache_improvement = (
            ((avg_cache_miss_time - avg_cache_hit_time) / avg_cache_miss_time * 100)
            if avg_cache_miss_time > 0
            else 0
        )

        return {
            "cache_miss_avg_ms": avg_cache_miss_time,
            "cache_hit_avg_ms": avg_cache_hit_time,
            "cache_improvement_percent": cache_improvement,
            "cache_stats": self.cache_manager.get_stats(),
        }

    def test_fuzzy_matching_performance(self) -> dict[str, Any]:
        """
        Test performance impact of fuzzy matching.

        Returns:
            Dictionary with fuzzy matching performance metrics
        """
        print("Testing fuzzy matching performance...")

        exact_times = []
        fuzzy_times = []

        # Test exact matching
        for query in self.fuzzy_queries:
            result = self.measure_latency(query, {"fuzzy_matching": False})
            exact_times.append(result["latency_ms"])

        # Test fuzzy matching
        for query in self.fuzzy_queries:
            result = self.measure_latency(query, {"fuzzy_matching": True})
            fuzzy_times.append(result["latency_ms"])

        avg_exact_time = statistics.mean(exact_times)
        avg_fuzzy_time = statistics.mean(fuzzy_times)

        fuzzy_overhead = (
            ((avg_fuzzy_time - avg_exact_time) / avg_exact_time * 100)
            if avg_exact_time > 0
            else 0
        )

        return {
            "exact_matching_avg_ms": avg_exact_time,
            "fuzzy_matching_avg_ms": avg_fuzzy_time,
            "fuzzy_overhead_percent": fuzzy_overhead,
            "fuzzy_overhead_ms": avg_fuzzy_time - avg_exact_time,
        }

    def memory_usage_test(self) -> dict[str, Any]:
        """
        Test memory usage during load.

        Returns:
            Dictionary with memory usage metrics
        """
        print("Testing memory usage...")

        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())

            # Baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Run intensive test
            results = []
            for _ in range(100):
                for query in self.test_queries:
                    result = self.measure_latency(query)
                    results.append(result)

            # Peak memory
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            return {
                "baseline_memory_mb": baseline_memory,
                "peak_memory_mb": peak_memory,
                "memory_increase_mb": peak_memory - baseline_memory,
                "memory_increase_percent": (
                    (peak_memory - baseline_memory) / baseline_memory * 100
                )
                if baseline_memory > 0
                else 0,
                "requests_processed": len(results),
            }

        except ImportError:
            return {
                "error": "psutil not available for memory testing",
                "baseline_memory_mb": 0,
                "peak_memory_mb": 0,
                "memory_increase_mb": 0,
                "memory_increase_percent": 0,
                "requests_processed": 0,
            }

    def run_full_performance_suite(self) -> dict[str, Any]:
        """
        Run complete performance test suite.

        Returns:
            Dictionary with all performance metrics
        """
        print("Starting full performance test suite...")

        results = {
            "test_timestamp": time.time(),
            "test_configuration": {
                "total_test_queries": len(self.test_queries),
                "fuzzy_test_queries": len(self.fuzzy_queries),
                "entity_service_stats": self.entity_service.get_stats(),
                "cache_stats": self.cache_manager.get_stats(),
            },
        }

        # Single user baseline
        print("Running single user baseline...")
        single_user_results = []
        for query in self.test_queries:
            result = self.measure_latency(query)
            single_user_results.append(result)

        single_user_latencies = [
            r["latency_ms"] for r in single_user_results if r["success"]
        ]
        results["single_user_baseline"] = {
            "avg_latency_ms": statistics.mean(single_user_latencies)
            if single_user_latencies
            else 0,
            "p95_latency_ms": statistics.quantiles(single_user_latencies, n=20)[18]
            if len(single_user_latencies) >= 20
            else 0,
            "success_rate": len(single_user_latencies) / len(single_user_results)
            if single_user_results
            else 0,
        }

        # Concurrent user tests
        concurrent_tests = [10, 50, 100]
        results["concurrent_tests"] = {}

        for users in concurrent_tests:
            if users <= 100:  # Limit for testing environment
                concurrent_result = self.run_concurrent_test(self.test_queries, users)
                results["concurrent_tests"][f"{users}_users"] = concurrent_result

        # Cache performance
        results["cache_performance"] = self.test_cache_performance()

        # Fuzzy matching performance
        results["fuzzy_matching_performance"] = self.test_fuzzy_matching_performance()

        # Memory usage
        results["memory_usage"] = self.memory_usage_test()

        # Performance summary
        results["performance_summary"] = self._generate_performance_summary(results)

        return results

    def _generate_performance_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Generate performance summary and recommendations."""
        summary = {
            "meets_p95_target": False,
            "meets_p99_target": False,
            "meets_throughput_target": False,
            "recommendations": [],
        }

        # Check P95 latency target (<100ms)
        if "100_users" in results.get("concurrent_tests", {}):
            p95_latency = results["concurrent_tests"]["100_users"]["latency_metrics"][
                "p95_ms"
            ]
            summary["meets_p95_target"] = p95_latency < 100

            if not summary["meets_p95_target"]:
                summary["recommendations"].append(
                    f"P95 latency ({p95_latency:.1f}ms) exceeds 100ms target"
                )

        # Check P99 latency target (<200ms)
        if "100_users" in results.get("concurrent_tests", {}):
            p99_latency = results["concurrent_tests"]["100_users"]["latency_metrics"][
                "p99_ms"
            ]
            summary["meets_p99_target"] = p99_latency < 200

            if not summary["meets_p99_target"]:
                summary["recommendations"].append(
                    f"P99 latency ({p99_latency:.1f}ms) exceeds 200ms target"
                )

        # Check throughput target (>100 RPS)
        if "100_users" in results.get("concurrent_tests", {}):
            throughput = results["concurrent_tests"]["100_users"]["throughput_rps"]
            summary["meets_throughput_target"] = throughput > 100

            if not summary["meets_throughput_target"]:
                summary["recommendations"].append(
                    f"Throughput ({throughput:.1f} RPS) below 100 RPS target"
                )

        # Cache recommendations
        cache_perf = results.get("cache_performance", {})
        if cache_perf.get("cache_improvement_percent", 0) < 50:
            summary["recommendations"].append(
                "Cache improvement is low - consider optimizing cache strategy"
            )

        # Memory recommendations
        memory_usage = results.get("memory_usage", {})
        if memory_usage.get("memory_increase_percent", 0) > 50:
            summary["recommendations"].append(
                "High memory usage detected - consider memory optimization"
            )

        return summary

    def save_results(self, results: dict[str, Any], filename: Optional[str] = None):
        """Save performance test results to file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"performance_results_{timestamp}.json"

        results_dir = Path("performance_results")
        results_dir.mkdir(exist_ok=True)

        filepath = results_dir / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Performance results saved to {filepath}")


# Test functions for pytest
@pytest.mark.performance
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
def test_single_user_performance():
    """Test single user performance baseline."""
    suite = PerformanceTestSuite()

    # Test a few queries
    test_queries = suite.test_queries[:5]
    results = []

    for query in test_queries:
        result = suite.measure_latency(query)
        results.append(result)
        assert result["success"], f"Query failed: {query}"
        assert result["latency_ms"] < 1000, f"Query too slow: {result['latency_ms']}ms"

    avg_latency = statistics.mean([r["latency_ms"] for r in results])
    assert avg_latency < 500, f"Average latency too high: {avg_latency}ms"


@pytest.mark.performance
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
def test_concurrent_users_10():
    """Test performance with 10 concurrent users."""
    suite = PerformanceTestSuite()

    result = suite.run_concurrent_test(suite.test_queries[:10], 10)

    assert result["success_rate"] > 0.95, (
        f"Success rate too low: {result['success_rate']}"
    )
    assert result["latency_metrics"]["p95_ms"] < 200, (
        f"P95 latency too high: {result['latency_metrics']['p95_ms']}ms"
    )
    assert result["throughput_rps"] > 10, (
        f"Throughput too low: {result['throughput_rps']} RPS"
    )


@pytest.mark.performance
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
def test_cache_effectiveness():
    """Test cache effectiveness."""
    suite = PerformanceTestSuite()

    result = suite.test_cache_performance()

    # Cache should provide some improvement
    assert result["cache_improvement_percent"] >= 0, (
        "Cache should not make performance worse"
    )

    # Cache hit should be faster than cache miss (or at least not slower)
    assert result["cache_hit_avg_ms"] <= result["cache_miss_avg_ms"] * 1.1, (
        "Cache hits should be faster"
    )


@pytest.mark.performance
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Services not available")
def test_fuzzy_matching_overhead():
    """Test fuzzy matching performance overhead."""
    suite = PerformanceTestSuite()

    result = suite.test_fuzzy_matching_performance()

    # Fuzzy matching should not add more than 200% overhead
    assert result["fuzzy_overhead_percent"] < 200, (
        f"Fuzzy matching overhead too high: {result['fuzzy_overhead_percent']}%"
    )

    # Absolute overhead should be reasonable
    assert result["fuzzy_overhead_ms"] < 100, (
        f"Fuzzy matching adds too much latency: {result['fuzzy_overhead_ms']}ms"
    )


if __name__ == "__main__":
    # Run full performance suite when executed directly
    if SERVICES_AVAILABLE:
        suite = PerformanceTestSuite()
        results = suite.run_full_performance_suite()
        suite.save_results(results)

        # Print summary
        print("\n" + "=" * 50)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 50)

        summary = results["performance_summary"]
        print(f"P95 Target (<100ms): {'✓' if summary['meets_p95_target'] else '✗'}")
        print(f"P99 Target (<200ms): {'✓' if summary['meets_p99_target'] else '✗'}")
        print(
            f"Throughput Target (>100 RPS): {'✓' if summary['meets_throughput_target'] else '✗'}"
        )

        if summary["recommendations"]:
            print("\nRecommendations:")
            for rec in summary["recommendations"]:
                print(f"- {rec}")
        else:
            print("\n✓ All performance targets met!")

        print("=" * 50)
    else:
        print("Services not available for performance testing")
