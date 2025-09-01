"""
Redis cache management service for entity recognition.
"""

import json
import logging
import time
from datetime import timedelta
from functools import wraps
from typing import Any, Optional

try:
    import redis
    from redis import ConnectionPool

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis caching for entity recognition service."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        max_connections: int = 50,
        decode_responses: bool = True,
    ):
        """
        Initialize the cache manager.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            max_connections: Maximum connections in pool
            decode_responses: Whether to decode responses to strings
        """
        self.enabled = REDIS_AVAILABLE
        self.redis_client: Optional[redis.Redis] = None
        self.pool: Optional[ConnectionPool] = None
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_latency_ms": 0,
            "total_requests": 0,
        }

        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Caching disabled.")
            return

        try:
            # Create connection pool for better performance
            self.pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                max_connections=max_connections,
                decode_responses=decode_responses,
            )

            self.redis_client = redis.Redis(connection_pool=self.pool)

            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache connected to {host}:{port}")

            # Configure Redis settings
            self._configure_redis()

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False
            self.redis_client = None

    def _configure_redis(self):
        """Configure Redis with appropriate settings."""
        try:
            # Set max memory to 2GB
            self.redis_client.config_set("maxmemory", "2gb")

            # Set LRU eviction policy
            self.redis_client.config_set("maxmemory-policy", "allkeys-lru")

            logger.info("Redis configured with 2GB memory limit and LRU eviction")

        except Exception as e:
            logger.warning(f"Could not configure Redis settings: {e}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            self.stats["misses"] += 1
            return None

        start_time = time.time()

        try:
            value = self.redis_client.get(key)
            latency_ms = (time.time() - start_time) * 1000
            self.stats["total_latency_ms"] += latency_ms
            self.stats["total_requests"] += 1

            if value is not None:
                self.stats["hits"] += 1
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                self.stats["misses"] += 1
                return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats["errors"] += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (deprecated, use ttl)
            ttl: TTL as timedelta

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            # Handle TTL
            if ttl:
                return self.redis_client.setex(key, ttl, value)
            elif ttl_seconds:
                return self.redis_client.setex(
                    key, timedelta(seconds=ttl_seconds), value
                )
            else:
                return self.redis_client.set(key, value)

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.stats["errors"] += 1
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "entity:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache statistics
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        avg_latency = (
            self.stats["total_latency_ms"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0
        )

        return {
            "enabled": self.enabled,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": self.stats["total_requests"],
            "avg_latency_ms": round(avg_latency, 2),
        }

    def reset_stats(self):
        """Reset performance statistics."""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_latency_ms": 0,
            "total_requests": 0,
        }

    def warm_cache(self, artifacts: dict[str, Any]) -> bool:
        """
        Warm the cache with entity artifacts.

        Args:
            artifacts: Dictionary of artifacts to cache

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            start_time = time.time()

            # Cache gazetteer with 24-hour TTL
            if "gazetteer" in artifacts:
                self.set(
                    "entity:gazetteer", artifacts["gazetteer"], ttl=timedelta(hours=24)
                )

            # Cache aliases with 24-hour TTL
            if "aliases" in artifacts:
                self.set(
                    "entity:aliases", artifacts["aliases"], ttl=timedelta(hours=24)
                )

            elapsed = time.time() - start_time
            logger.info(f"Cache warmed in {elapsed:.2f} seconds")

            if elapsed > 5:
                logger.warning(
                    f"Cache warming exceeded 5-second target: {elapsed:.2f}s"
                )

            return True

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return False

    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()
            if self.pool:
                self.pool.disconnect()
            logger.info("Redis connection closed")


def cache_result(ttl_seconds: int = 900):  # 15 minutes default
    """
    Decorator to cache function results.

    Args:
        ttl_seconds: TTL in seconds (default 15 minutes)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Only cache if cache manager is available
            if not hasattr(self, "cache_manager") or not self.cache_manager.enabled:
                return func(self, *args, **kwargs)

            # Create cache key from function name and arguments
            cache_key = f"result:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached

            # Execute function and cache result
            result = func(self, *args, **kwargs)
            self.cache_manager.set(cache_key, result, ttl_seconds=ttl_seconds)

            return result

        return wrapper

    return decorator


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create singleton cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
