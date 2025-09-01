"""
Artifact loader service with caching support.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.services.cache_manager import CacheManager, get_cache_manager

logger = logging.getLogger(__name__)


class ArtifactLoader:
    """Loads and caches entity artifacts for recognition service."""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize the artifact loader.

        Args:
            cache_manager: Optional cache manager instance
        """
        self.cache_manager = cache_manager or get_cache_manager()
        self.artifacts_dir = Path(__file__).parent.parent / "data" / "artifacts"
        self.gazetteer_path = self.artifacts_dir / "gazetteer.json"
        self.aliases_path = self.artifacts_dir / "aliases.jsonl"

        self.gazetteer: dict = {}
        self.aliases: list[dict] = []
        self.loaded = False
        self.load_time = 0.0

    def load_artifacts(self, force_reload: bool = False) -> bool:
        """
        Load artifacts from cache or files.

        Args:
            force_reload: Force reload from files even if cached

        Returns:
            True if artifacts loaded successfully
        """
        start_time = time.time()

        try:
            # Try to load from cache first (unless force reload)
            if not force_reload and self._load_from_cache():
                self.load_time = time.time() - start_time
                logger.info(f"Artifacts loaded from cache in {self.load_time:.2f}s")
                return True

            # Load from files
            if not self._load_from_files():
                logger.warning("Failed to load artifacts from files, using defaults")
                self._load_defaults()

            # Warm the cache with loaded artifacts
            if self.cache_manager.enabled:
                self._warm_cache()

            self.load_time = time.time() - start_time
            logger.info(f"Artifacts loaded from files in {self.load_time:.2f}s")

            if self.load_time > 5:
                logger.warning(
                    f"Artifact loading exceeded 5-second target: {self.load_time:.2f}s"
                )

            self.loaded = True
            return True

        except Exception as e:
            logger.error(f"Failed to load artifacts: {e}")
            self._load_defaults()
            self.loaded = True
            return False

    def _load_from_cache(self) -> bool:
        """
        Try to load artifacts from cache.

        Returns:
            True if loaded from cache successfully
        """
        if not self.cache_manager.enabled:
            return False

        try:
            # Try to get from cache
            cached_gazetteer = self.cache_manager.get("entity:gazetteer")
            cached_aliases = self.cache_manager.get("entity:aliases")

            if cached_gazetteer and cached_aliases:
                self.gazetteer = cached_gazetteer
                self.aliases = cached_aliases
                self.loaded = True
                return True

            return False

        except Exception as e:
            logger.debug(f"Cache load failed: {e}")
            return False

    def _load_from_files(self) -> bool:
        """
        Load artifacts from files.

        Returns:
            True if loaded successfully
        """
        try:
            if not self.gazetteer_path.exists() or not self.aliases_path.exists():
                logger.warning("Artifact files not found")
                return False

            # Load gazetteer
            with open(self.gazetteer_path) as f:
                self.gazetteer = json.load(f)

            # Load aliases
            self.aliases = []
            with open(self.aliases_path) as f:
                for line in f:
                    if line.strip():
                        self.aliases.append(json.loads(line))

            logger.info(
                f"Loaded {len(self.gazetteer.get('entities', {}))} entity types, "
                f"{len(self.aliases)} aliases from files"
            )

            self.loaded = True
            return True

        except Exception as e:
            logger.error(f"Failed to load from files: {e}")
            return False

    def _load_defaults(self):
        """Load default artifacts as fallback."""
        self.gazetteer = {
            "entities": {
                "manufacturers": ["Cadbury", "Mars", "Nestle", "Ferrero", "Thorntons"],
                "brands": ["Dairy Milk", "Galaxy", "KitKat", "Snickers", "Roses"],
                "categories": ["Chocolate", "Confectionery", "Biscuits"],
                "products": ["Chocolate Bars", "Boxed Chocolates", "Seasonal"],
            },
            "metrics": [
                "revenue",
                "sales",
                "market share",
                "growth",
                "volume",
                "price",
                "promotion",
                "elasticity",
                "margin",
                "profit",
            ],
            "timewords": [
                "Q1",
                "Q2",
                "Q3",
                "Q4",
                "quarter",
                "month",
                "year",
                "YTD",
                "MTD",
                "QTD",
                "last",
                "previous",
                "current",
            ],
            "special_tokens": ["vs", "versus", "compare", "analyze", "show"],
        }

        self.aliases = [
            {
                "type": "manufacturer",
                "name": "Cadbury",
                "alias": "cadburys",
                "confidence": 0.9,
            },
            {
                "type": "manufacturer",
                "name": "Cadbury",
                "alias": "cadbury's",
                "confidence": 0.9,
            },
            {
                "type": "brand",
                "name": "Dairy Milk",
                "alias": "dairy milk chocolate",
                "confidence": 0.9,
            },
            {
                "type": "metric",
                "name": "market share",
                "alias": "share",
                "confidence": 0.9,
            },
            {"type": "metric", "name": "revenue", "alias": "sales", "confidence": 0.9},
        ]

        logger.info("Loaded default artifacts")
        self.loaded = True

    def _warm_cache(self):
        """Warm the cache with loaded artifacts."""
        try:
            artifacts = {"gazetteer": self.gazetteer, "aliases": self.aliases}

            if self.cache_manager.warm_cache(artifacts):
                logger.info("Cache warmed successfully")
            else:
                logger.warning("Cache warming failed")

        except Exception as e:
            logger.error(f"Cache warming error: {e}")

    def get_gazetteer(self) -> dict:
        """
        Get the loaded gazetteer.

        Returns:
            Gazetteer dictionary
        """
        if not self.loaded:
            self.load_artifacts()
        return self.gazetteer

    def get_aliases(self) -> list[dict]:
        """
        Get the loaded aliases.

        Returns:
            List of alias dictionaries
        """
        if not self.loaded:
            self.load_artifacts()
        return self.aliases

    def invalidate_cache(self) -> bool:
        """
        Invalidate cached artifacts.

        Returns:
            True if cache invalidated successfully
        """
        if not self.cache_manager.enabled:
            return False

        try:
            deleted = self.cache_manager.delete_pattern("entity:*")
            deleted += self.cache_manager.delete_pattern("result:*")
            logger.info(f"Invalidated {deleted} cache entries")
            return True

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return False

    def reload(self) -> bool:
        """
        Reload artifacts from files and update cache.

        Returns:
            True if reload successful
        """
        logger.info("Reloading artifacts")
        self.loaded = False
        return self.load_artifacts(force_reload=True)

    def get_stats(self) -> dict:
        """
        Get loader statistics.

        Returns:
            Dictionary with loader stats
        """
        return {
            "loaded": self.loaded,
            "load_time_seconds": self.load_time,
            "gazetteer_entities": len(self.gazetteer.get("entities", {})),
            "aliases_count": len(self.aliases),
            "cache_stats": self.cache_manager.get_stats() if self.cache_manager else {},
        }


# Singleton instance
_artifact_loader: Optional[ArtifactLoader] = None


def get_artifact_loader() -> ArtifactLoader:
    """Get or create singleton artifact loader."""
    global _artifact_loader
    if _artifact_loader is None:
        _artifact_loader = ArtifactLoader()
    return _artifact_loader
