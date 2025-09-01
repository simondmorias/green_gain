"""
Entity recognition service for live intent highlighting.
"""

import logging
import time
from functools import lru_cache
from typing import Any, Optional

from app.services.aho_corasick_matcher import EntityMatcher
from app.services.artifact_loader import get_artifact_loader
from app.services.cache_manager import get_cache_manager
from app.services.fuzzy_matcher import get_fuzzy_matcher

logger = logging.getLogger(__name__)


class EntityRecognitionService:
    """Service for recognizing entities in user queries."""

    def __init__(self):
        self.matcher: Optional[EntityMatcher] = None
        self.fuzzy_matcher = None
        self.artifacts_loaded = False

        # Initialize cache and artifact loader
        self.cache_manager = get_cache_manager()
        self.artifact_loader = get_artifact_loader()

        # Load artifacts through the loader
        self._load_artifacts()

    def _load_artifacts(self):
        """Load entity artifacts through the artifact loader."""
        try:
            # Load artifacts via the loader (with caching)
            if self.artifact_loader.load_artifacts():
                gazetteer = self.artifact_loader.get_gazetteer()
                aliases = self.artifact_loader.get_aliases()

                self.matcher = EntityMatcher(gazetteer, aliases)
                self.fuzzy_matcher = get_fuzzy_matcher(gazetteer, aliases)
                self.artifacts_loaded = True

                logger.info("Artifacts loaded via artifact loader")
            else:
                logger.warning("Failed to load artifacts via loader, using defaults")
                self._use_default_artifacts()

        except Exception as e:
            logger.error(f"Failed to load artifacts: {e}")
            self._use_default_artifacts()

    def _use_default_artifacts(self):
        """Use minimal default artifacts as fallback."""
        # Artifact loader already has defaults, just get them
        self.artifact_loader._load_defaults()
        gazetteer = self.artifact_loader.get_gazetteer()
        aliases = self.artifact_loader.get_aliases()

        self.matcher = EntityMatcher(gazetteer, aliases)
        self.fuzzy_matcher = get_fuzzy_matcher(gazetteer, aliases)
        self.artifacts_loaded = True
        logger.info("Using default artifacts")

    def recognize(self, text: str, options: Optional[dict] = None) -> dict:
        """
        Recognize entities in the given text.

        Args:
            text: Input text to process
            options: Optional processing options (fuzzy_matching, confidence_threshold)

        Returns:
            Dictionary with tagged_text, entities, and processing_time_ms
        """
        if not self.matcher:
            logger.error("Entity matcher not initialized")
            return {
                "tagged_text": text,
                "entities": [],
                "processing_time_ms": 0,
                "error": "Entity recognition service not available",
            }

        start_time = time.time()

        try:
            if len(text) > 500:
                logger.warning(f"Text length ({len(text)}) exceeds 500 character limit")
                text = text[:500]

            # Parse options
            options = options or {}
            fuzzy_matching = options.get("fuzzy_matching", False)
            confidence_threshold = options.get("confidence_threshold", 0.8)

            # First, perform exact matching
            exact_result = self.matcher.recognize_entities(text)

            # If fuzzy matching is enabled and we have a fuzzy matcher, enhance results
            if fuzzy_matching and self.fuzzy_matcher and self.fuzzy_matcher.enabled:
                try:
                    # Update fuzzy matcher confidence threshold if provided
                    if confidence_threshold != self.fuzzy_matcher.confidence_threshold:
                        self.fuzzy_matcher.confidence_threshold = confidence_threshold

                    # Enhance with fuzzy matching
                    fuzzy_enhancement = self.fuzzy_matcher.enhance_with_fuzzy_matching(
                        text, exact_result.get("entities", [])
                    )

                    # Merge results
                    enhanced_entities = fuzzy_enhancement.get("enhanced_entities", [])
                    suggestions = fuzzy_enhancement.get("suggestions", [])

                    # Update the result with enhanced entities
                    result = {
                        **exact_result,
                        "entities": enhanced_entities,
                        "suggestions": suggestions,
                        "fuzzy_matches": fuzzy_enhancement.get("fuzzy_matches", []),
                        "fuzzy_enabled": True,
                    }

                    logger.debug(
                        f"Fuzzy matching enhanced {len(exact_result.get('entities', []))} "
                        f"exact matches with {len(fuzzy_enhancement.get('fuzzy_matches', []))} "
                        f"fuzzy matches"
                    )

                except Exception as e:
                    logger.error(f"Fuzzy matching failed: {e}")
                    # Fall back to exact results
                    result = {
                        **exact_result,
                        "fuzzy_enabled": False,
                        "fuzzy_error": str(e),
                    }
            else:
                result = {**exact_result, "fuzzy_enabled": False}

            elapsed_ms = (time.time() - start_time) * 1000

            if elapsed_ms > 100:
                logger.warning(
                    f"Recognition time ({elapsed_ms:.1f}ms) exceeds 100ms target"
                )

            return {**result, "processing_time_ms": elapsed_ms}

        except Exception as e:
            logger.error(f"Entity recognition failed: {e}")
            elapsed_ms = (time.time() - start_time) * 1000

            return {
                "tagged_text": text,
                "entities": [],
                "processing_time_ms": elapsed_ms,
                "error": str(e),
            }

    def reload_artifacts(self):
        """Reload artifacts from files."""
        logger.info("Reloading entity artifacts")
        self._load_artifacts()

        # Clear fuzzy matcher cache if it exists
        if self.fuzzy_matcher:
            self.fuzzy_matcher.clear_cache()

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics including fuzzy matching stats."""
        result: dict[str, Any] = {
            "artifacts_loaded": self.artifacts_loaded,
            "matcher_available": self.matcher is not None,
            "fuzzy_matcher_available": self.fuzzy_matcher is not None,
        }

        if self.fuzzy_matcher:
            fuzzy_stats = self.fuzzy_matcher.get_stats()
            result["fuzzy_stats"] = fuzzy_stats

        return result


_service_instance: Optional[EntityRecognitionService] = None


def get_entity_recognition_service() -> EntityRecognitionService:
    """Get or create the singleton entity recognition service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = EntityRecognitionService()
    return _service_instance


# Cached recognition function (module-level for lru_cache compatibility)
@lru_cache(maxsize=1000)
def _cached_recognize(text: str, fuzzy_matching: bool = False) -> str:
    """Cached version of recognize for repeated queries - returns JSON string."""
    import json
    service = get_entity_recognition_service()
    options = {"fuzzy_matching": fuzzy_matching} if fuzzy_matching else None
    result = service.recognize(text, options)
    return json.dumps(result, sort_keys=True)


def recognize_cached(text: str, fuzzy_matching: bool = False) -> dict:
    """Public interface for cached recognition."""
    import json
    result_json = _cached_recognize(text, fuzzy_matching)
    return json.loads(result_json)
