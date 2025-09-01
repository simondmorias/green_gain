"""
Integration tests for cache functionality.
"""

import time
from unittest.mock import Mock, patch

from app.services.artifact_loader import ArtifactLoader, get_artifact_loader
from app.services.cache_manager import CacheManager, get_cache_manager
from app.services.entity_recognizer import EntityRecognitionService


class TestCacheIntegration:
    """Integration tests for cache functionality."""

    def test_cache_manager_fallback_when_redis_unavailable(self):
        """Test that system works when Redis is unavailable."""
        # Test with Redis unavailable
        with patch("app.services.cache_manager.REDIS_AVAILABLE", False):
            cache_manager = CacheManager()

            assert cache_manager.enabled is False
            assert cache_manager.get("test") is None
            assert cache_manager.set("test", "value") is False
            assert cache_manager.delete("test") is False

            stats = cache_manager.get_stats()
            assert stats["enabled"] is False
            assert stats["hits"] == 0
            assert stats["misses"] == 1  # From the get call above

    def test_artifact_loader_with_cache_disabled(self):
        """Test artifact loader when cache is disabled."""
        mock_cache_manager = Mock()
        mock_cache_manager.enabled = False

        loader = ArtifactLoader(mock_cache_manager)

        # Should load defaults when files don't exist and cache is disabled
        result = loader.load_artifacts()

        assert result is True  # Successfully loaded defaults
        assert loader.loaded is True  # But defaults were loaded
        assert "manufacturers" in loader.gazetteer["entities"]
        assert len(loader.aliases) > 0

    def test_entity_recognition_with_cache_integration(self):
        """Test entity recognition service with cache integration."""
        # Mock cache manager
        mock_cache_manager = Mock()
        mock_cache_manager.enabled = True
        mock_cache_manager.get.return_value = None  # Cache miss
        mock_cache_manager.set.return_value = True
        mock_cache_manager.get_stats.return_value = {"hits": 0, "misses": 1}

        # Mock artifact loader
        mock_artifact_loader = Mock()
        mock_artifact_loader.load_artifacts.return_value = True
        mock_artifact_loader.get_gazetteer.return_value = {
            "entities": {
                "manufacturers": ["Cadbury", "Mars"],
                "brands": ["Dairy Milk", "Galaxy"],
            },
            "metrics": ["revenue", "sales"],
            "timewords": ["Q1", "Q2"],
        }
        mock_artifact_loader.get_aliases.return_value = [
            {
                "type": "manufacturer",
                "name": "Cadbury",
                "alias": "cadburys",
                "confidence": 0.9,
            }
        ]

        # Test entity recognition service initialization
        with patch(
            "app.services.entity_recognizer.get_cache_manager",
            return_value=mock_cache_manager,
        ):
            with patch(
                "app.services.entity_recognizer.get_artifact_loader",
                return_value=mock_artifact_loader,
            ):
                service = EntityRecognitionService()

                assert service.cache_manager == mock_cache_manager
                assert service.artifact_loader == mock_artifact_loader
                assert service.artifacts_loaded is True

    def test_cache_warming_performance(self):
        """Test that cache warming completes within time limits."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        with patch("app.services.cache_manager.redis") as mock_redis_module:
            with patch("app.services.cache_manager.REDIS_AVAILABLE", True):
                mock_redis_module.ConnectionPool.return_value = Mock()
                mock_redis_module.Redis.return_value = mock_redis

                cache_manager = CacheManager()

                # Test cache warming with realistic data
                artifacts = {
                    "gazetteer": {
                        "entities": {
                            "manufacturers": ["Cadbury"]
                            * 100,  # Simulate larger dataset
                            "brands": ["Brand"] * 200,
                        }
                    },
                    "aliases": [{"name": f"alias_{i}"} for i in range(500)],
                }

                start_time = time.time()
                result = cache_manager.warm_cache(artifacts)
                elapsed = time.time() - start_time

                assert result is True
                assert elapsed < 5.0  # Should complete in under 5 seconds
                assert mock_redis.setex.call_count == 2  # gazetteer + aliases

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation accuracy."""
        cache_manager = CacheManager()
        cache_manager.enabled = False  # Disable to control stats manually

        # Simulate cache operations
        cache_manager.stats = {
            "hits": 80,
            "misses": 20,
            "errors": 0,
            "total_latency_ms": 1000,
            "total_requests": 100,
        }

        stats = cache_manager.get_stats()

        assert stats["hit_rate"] == 80.0
        assert stats["avg_latency_ms"] == 10.0
        assert stats["total_requests"] == 100

    def test_cache_invalidation_patterns(self):
        """Test cache invalidation with different patterns."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.keys.side_effect = [
            ["entity:gazetteer", "entity:aliases"],  # First pattern
            ["result:func1:args", "result:func2:args"],  # Second pattern
        ]
        mock_redis.delete.side_effect = [2, 2]  # Return counts

        with patch("app.services.cache_manager.redis") as mock_redis_module:
            with patch("app.services.cache_manager.REDIS_AVAILABLE", True):
                mock_redis_module.ConnectionPool.return_value = Mock()
                mock_redis_module.Redis.return_value = mock_redis

                cache_manager = CacheManager()

                # Test pattern deletion
                count1 = cache_manager.delete_pattern("entity:*")
                count2 = cache_manager.delete_pattern("result:*")

                assert count1 == 2
                assert count2 == 2
                assert mock_redis.keys.call_count == 2
                assert mock_redis.delete.call_count == 2

    def test_artifact_loader_cache_fallback_chain(self):
        """Test the complete fallback chain: cache -> files -> defaults."""
        mock_cache_manager = Mock()
        mock_cache_manager.enabled = True
        mock_cache_manager.get.return_value = None  # Cache miss
        mock_cache_manager.warm_cache.return_value = True

        loader = ArtifactLoader(mock_cache_manager)

        # Set paths to non-existent files to trigger defaults
        loader.gazetteer_path = (
            loader.gazetteer_path.parent / "nonexistent_gazetteer.json"
        )
        loader.aliases_path = loader.aliases_path.parent / "nonexistent_aliases.jsonl"

        result = loader.load_artifacts()

        # Should have tried cache first (miss), then files (not found), then defaults
        assert mock_cache_manager.get.call_count == 2  # gazetteer + aliases
        assert result is True  # Successfully loaded defaults
        assert loader.loaded is True  # But defaults loaded
        assert loader.gazetteer["entities"]["manufacturers"]  # Has default data
        assert len(loader.aliases) > 0  # Has default aliases

    def test_singleton_instances(self):
        """Test that singleton instances work correctly."""
        # Clear any existing singletons
        import app.services.artifact_loader
        import app.services.cache_manager

        app.services.cache_manager._cache_manager = None
        app.services.artifact_loader._artifact_loader = None

        # Test cache manager singleton
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        assert manager1 is manager2

        # Test artifact loader singleton
        loader1 = get_artifact_loader()
        loader2 = get_artifact_loader()
        assert loader1 is loader2

    def test_cache_stats_reset(self):
        """Test cache statistics reset functionality."""
        cache_manager = CacheManager()

        # Set some stats
        cache_manager.stats["hits"] = 100
        cache_manager.stats["misses"] = 50
        cache_manager.stats["errors"] = 5

        # Reset stats
        cache_manager.reset_stats()

        # Verify reset
        assert cache_manager.stats["hits"] == 0
        assert cache_manager.stats["misses"] == 0
        assert cache_manager.stats["errors"] == 0
        assert cache_manager.stats["total_latency_ms"] == 0
        assert cache_manager.stats["total_requests"] == 0

    def test_cache_connection_cleanup(self):
        """Test proper cleanup of cache connections."""
        mock_redis = Mock()
        mock_pool = Mock()

        with patch("app.services.cache_manager.redis") as mock_redis_module:
            with patch("app.services.cache_manager.REDIS_AVAILABLE", True):
                mock_redis_module.ConnectionPool.return_value = mock_pool
                mock_redis_module.Redis.return_value = mock_redis
                mock_redis.ping.return_value = True

                cache_manager = CacheManager()
                cache_manager.close()

                mock_redis.close.assert_called_once()
                mock_pool.disconnect.assert_called_once()


class TestCachePerformance:
    """Performance-related cache tests."""

    def test_cache_latency_tracking(self):
        """Test that cache latency is properly tracked."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = '{"test": "data"}'

        with patch("app.services.cache_manager.redis") as mock_redis_module:
            with patch("app.services.cache_manager.REDIS_AVAILABLE", True):
                mock_redis_module.ConnectionPool.return_value = Mock()
                mock_redis_module.Redis.return_value = mock_redis

                cache_manager = CacheManager()

                # Perform cache operations
                result1 = cache_manager.get("key1")
                result2 = cache_manager.get("key2")

                assert result1 == {"test": "data"}
                assert result2 == {"test": "data"}

                stats = cache_manager.get_stats()
                assert stats["total_requests"] == 2
                assert stats["hits"] == 2
                assert stats["avg_latency_ms"] >= 0

    def test_large_data_serialization(self):
        """Test caching of large data structures."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True

        with patch("app.services.cache_manager.redis") as mock_redis_module:
            with patch("app.services.cache_manager.REDIS_AVAILABLE", True):
                mock_redis_module.ConnectionPool.return_value = Mock()
                mock_redis_module.Redis.return_value = mock_redis

                cache_manager = CacheManager()

                # Create large data structure
                large_data = {
                    "entities": {
                        f"category_{i}": [f"item_{j}" for j in range(100)]
                        for i in range(50)
                    }
                }

                result = cache_manager.set("large_data", large_data, ttl_seconds=3600)

                assert result is True
                mock_redis.setex.assert_called_once()

                # Verify JSON serialization occurred
                call_args = mock_redis.setex.call_args
                serialized_data = call_args[0][2]
                assert isinstance(serialized_data, str)
                assert "category_0" in serialized_data
