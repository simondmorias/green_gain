"""
Unit tests for cache manager service.
"""

from datetime import timedelta
from unittest.mock import Mock, patch

from app.services.cache_manager import CacheManager, get_cache_manager


class TestCacheManager:
    """Test the Redis cache manager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock Redis to avoid requiring actual Redis connection
        self.mock_redis = Mock()
        self.mock_pool = Mock()

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_cache_manager_initialization(self, mock_redis_module):
        """Test cache manager initialization with Redis available."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True

        cache_manager = CacheManager()

        assert cache_manager.enabled is True
        assert cache_manager.redis_client == self.mock_redis
        mock_redis_module.ConnectionPool.assert_called_once()
        self.mock_redis.ping.assert_called_once()

    @patch("app.services.cache_manager.REDIS_AVAILABLE", False)
    def test_cache_manager_redis_unavailable(self):
        """Test cache manager when Redis is not available."""
        cache_manager = CacheManager()

        assert cache_manager.enabled is False
        assert cache_manager.redis_client is None

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_cache_manager_connection_failure(self, mock_redis_module):
        """Test cache manager when Redis connection fails."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.side_effect = Exception("Connection failed")

        cache_manager = CacheManager()

        assert cache_manager.enabled is False
        assert cache_manager.redis_client is None

    def test_get_cache_disabled(self):
        """Test get operation when cache is disabled."""
        cache_manager = CacheManager()
        cache_manager.enabled = False

        result = cache_manager.get("test_key")

        assert result is None
        assert cache_manager.stats["misses"] == 1

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_get_cache_hit(self, mock_redis_module):
        """Test successful cache get operation."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.get.return_value = '{"test": "data"}'

        cache_manager = CacheManager()
        result = cache_manager.get("test_key")

        assert result == {"test": "data"}
        assert cache_manager.stats["hits"] == 1
        assert cache_manager.stats["total_requests"] == 1
        self.mock_redis.get.assert_called_once_with("test_key")

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_get_cache_miss(self, mock_redis_module):
        """Test cache miss scenario."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.get.return_value = None

        cache_manager = CacheManager()
        result = cache_manager.get("test_key")

        assert result is None
        assert cache_manager.stats["misses"] == 1
        assert cache_manager.stats["total_requests"] == 1

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_get_cache_error(self, mock_redis_module):
        """Test cache get with Redis error."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.get.side_effect = Exception("Redis error")

        cache_manager = CacheManager()
        result = cache_manager.get("test_key")

        assert result is None
        assert cache_manager.stats["errors"] == 1

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_set_with_ttl(self, mock_redis_module):
        """Test cache set operation with TTL."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.setex.return_value = True

        cache_manager = CacheManager()
        result = cache_manager.set("test_key", {"test": "data"}, ttl=timedelta(hours=1))

        assert result is True
        self.mock_redis.setex.assert_called_once()
        # Check that JSON serialization occurred
        call_args = self.mock_redis.setex.call_args
        assert '"test": "data"' in call_args[0][2]  # JSON serialized value

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_set_without_ttl(self, mock_redis_module):
        """Test cache set operation without TTL."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.set.return_value = True

        cache_manager = CacheManager()
        result = cache_manager.set("test_key", "simple_value")

        assert result is True
        self.mock_redis.set.assert_called_once_with("test_key", "simple_value")

    def test_set_cache_disabled(self):
        """Test set operation when cache is disabled."""
        cache_manager = CacheManager()
        cache_manager.enabled = False

        result = cache_manager.set("test_key", "value")

        assert result is False

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_delete_key(self, mock_redis_module):
        """Test cache delete operation."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.delete.return_value = 1

        cache_manager = CacheManager()
        result = cache_manager.delete("test_key")

        assert result is True
        self.mock_redis.delete.assert_called_once_with("test_key")

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_delete_pattern(self, mock_redis_module):
        """Test pattern-based cache deletion."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.keys.return_value = ["entity:gazetteer", "entity:aliases"]
        self.mock_redis.delete.return_value = 2

        cache_manager = CacheManager()
        result = cache_manager.delete_pattern("entity:*")

        assert result == 2
        self.mock_redis.keys.assert_called_once_with("entity:*")
        self.mock_redis.delete.assert_called_once_with(
            "entity:gazetteer", "entity:aliases"
        )

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_exists(self, mock_redis_module):
        """Test cache key existence check."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.exists.return_value = 1

        cache_manager = CacheManager()
        result = cache_manager.exists("test_key")

        assert result is True
        self.mock_redis.exists.assert_called_once_with("test_key")

    def test_get_stats(self):
        """Test cache statistics retrieval."""
        cache_manager = CacheManager()
        cache_manager.stats = {
            "hits": 80,
            "misses": 20,
            "errors": 2,
            "total_latency_ms": 1000,
            "total_requests": 100,
        }

        stats = cache_manager.get_stats()

        assert stats["hits"] == 80
        assert stats["misses"] == 20
        assert stats["errors"] == 2
        assert stats["hit_rate"] == 80.0
        assert stats["avg_latency_ms"] == 10.0
        assert stats["total_requests"] == 100

    def test_reset_stats(self):
        """Test cache statistics reset."""
        cache_manager = CacheManager()
        cache_manager.stats["hits"] = 100
        cache_manager.stats["misses"] = 50

        cache_manager.reset_stats()

        assert cache_manager.stats["hits"] == 0
        assert cache_manager.stats["misses"] == 0
        assert cache_manager.stats["errors"] == 0

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_warm_cache(self, mock_redis_module):
        """Test cache warming functionality."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.setex.return_value = True

        cache_manager = CacheManager()
        artifacts = {
            "gazetteer": {"entities": {"manufacturers": ["Cadbury"]}},
            "aliases": [{"name": "Cadbury", "alias": "cadburys"}],
        }

        result = cache_manager.warm_cache(artifacts)

        assert result is True
        # Should call setex twice (once for gazetteer, once for aliases)
        assert self.mock_redis.setex.call_count == 2

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_warm_cache_slow_warning(self, mock_redis_module):
        """Test cache warming with slow performance warning."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True
        self.mock_redis.setex.return_value = True

        cache_manager = CacheManager()
        artifacts = {"gazetteer": {}, "aliases": []}

        # Mock time.time to simulate slow warming
        with patch("app.services.cache_manager.time.time") as mock_time:
            mock_time.side_effect = [0, 6]  # 6 second elapsed time

            with patch("app.services.cache_manager.logger") as mock_logger:
                result = cache_manager.warm_cache(artifacts)

                assert result is True
                mock_logger.warning.assert_called_once()
                assert "exceeded 5-second target" in mock_logger.warning.call_args[0][0]

    def test_warm_cache_disabled(self):
        """Test cache warming when cache is disabled."""
        cache_manager = CacheManager()
        cache_manager.enabled = False

        result = cache_manager.warm_cache({"gazetteer": {}, "aliases": []})

        assert result is False

    @patch("app.services.cache_manager.redis")
    @patch("app.services.cache_manager.REDIS_AVAILABLE", True)
    def test_close_connection(self, mock_redis_module):
        """Test cache connection closing."""
        mock_redis_module.ConnectionPool.return_value = self.mock_pool
        mock_redis_module.Redis.return_value = self.mock_redis
        self.mock_redis.ping.return_value = True

        cache_manager = CacheManager()
        cache_manager.close()

        self.mock_redis.close.assert_called_once()
        self.mock_pool.disconnect.assert_called_once()


class TestCacheManagerSingleton:
    """Test the cache manager singleton functionality."""

    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns the same instance."""
        # Clear any existing singleton
        import app.services.cache_manager

        app.services.cache_manager._cache_manager = None

        manager1 = get_cache_manager()
        manager2 = get_cache_manager()

        assert manager1 is manager2


class TestCacheResultDecorator:
    """Test the cache result decorator."""

    def test_cache_result_decorator_no_cache_manager(self):
        """Test decorator when cache manager is not available."""
        from app.services.cache_manager import cache_result

        class TestService:
            def __init__(self):
                pass  # No cache_manager attribute

            @cache_result(ttl_seconds=300)
            def test_method(self, arg1, arg2):
                return f"result_{arg1}_{arg2}"

        service = TestService()
        result = service.test_method("a", "b")

        assert result == "result_a_b"

    def test_cache_result_decorator_with_cache(self):
        """Test decorator with cache manager available."""
        from app.services.cache_manager import cache_result

        mock_cache_manager = Mock()
        mock_cache_manager.enabled = True
        mock_cache_manager.get.return_value = None  # Cache miss
        mock_cache_manager.set.return_value = True

        class TestService:
            def __init__(self):
                self.cache_manager = mock_cache_manager

            @cache_result(ttl_seconds=300)
            def test_method(self, arg1):
                return f"result_{arg1}"

        service = TestService()
        result = service.test_method("test")

        assert result == "result_test"
        mock_cache_manager.get.assert_called_once()
        mock_cache_manager.set.assert_called_once()

    def test_cache_result_decorator_cache_hit(self):
        """Test decorator with cache hit."""
        from app.services.cache_manager import cache_result

        mock_cache_manager = Mock()
        mock_cache_manager.enabled = True
        mock_cache_manager.get.return_value = "cached_result"

        class TestService:
            def __init__(self):
                self.cache_manager = mock_cache_manager

            @cache_result(ttl_seconds=300)
            def test_method(self, arg1):
                return f"result_{arg1}"  # This should not be called

        service = TestService()
        result = service.test_method("test")

        assert result == "cached_result"
        mock_cache_manager.get.assert_called_once()
        mock_cache_manager.set.assert_not_called()
