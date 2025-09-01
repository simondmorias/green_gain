"""
Fuzzy matching service using RapidFuzz for entity recognition.
"""

import logging
import re
import time
from typing import Optional, Union

try:
    from rapidfuzz import fuzz, process
    from rapidfuzz.distance import Levenshtein

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    # Create mock objects for when RapidFuzz is not available
    process = None
    fuzz = None
    Levenshtein = None
    RAPIDFUZZ_AVAILABLE = False
    logging.warning("RapidFuzz not available, fuzzy matching disabled")

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """Fuzzy matching service for entity recognition using RapidFuzz."""

    def __init__(
        self,
        gazetteer: Optional[dict] = None,
        aliases: Optional[Union[dict, list[dict]]] = None,
        confidence_threshold: float = 0.8,
    ):
        """
        Initialize fuzzy matcher with entity data.

        Args:
            gazetteer: Dictionary of entity types to entity lists
            aliases: Dictionary of aliases to canonical names or list of alias dicts
            confidence_threshold: Minimum confidence score for matches (0.0-1.0)
        """
        self.gazetteer = gazetteer or {}
        self.aliases = aliases or []
        self.confidence_threshold = confidence_threshold
        self.enabled = RAPIDFUZZ_AVAILABLE

        # Build searchable entity lists
        self._build_search_index()

        # Cache for fuzzy match results
        self._match_cache: dict[str, list[dict]] = {}

        logger.info(
            f"FuzzyMatcher initialized with {len(self._all_entities)} entities, "
            f"threshold={confidence_threshold}, enabled={self.enabled}"
        )

    def _build_search_index(self):
        """Build searchable index of all entities."""
        self._all_entities = []
        self._entity_metadata = {}

        # Add gazetteer entities
        for entity_type, entities in self.gazetteer.items():
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict):
                        text = entity.get("name", entity.get("text", ""))
                        if text:
                            self._all_entities.append(text)
                            self._entity_metadata[text] = {
                                "type": entity_type,
                                "full_name": entity.get("full_name", text),
                                "metadata": entity,
                            }
                    elif isinstance(entity, str):
                        self._all_entities.append(entity)
                        self._entity_metadata[entity] = {
                            "type": entity_type,
                            "full_name": entity,
                            "metadata": {"name": entity},
                        }

        # Add aliases (handle both dict and list formats)
        if isinstance(self.aliases, dict):
            # Original dict format
            for alias, canonical in self.aliases.items():
                if alias not in self._entity_metadata:
                    self._all_entities.append(alias)
                    # Try to find metadata from canonical name
                    canonical_meta = self._entity_metadata.get(canonical, {})
                    self._entity_metadata[alias] = {
                        "type": canonical_meta.get("type", "alias"),
                        "full_name": canonical,
                        "metadata": {"name": alias, "canonical": canonical},
                    }
        elif isinstance(self.aliases, list):
            # List of dicts format (from artifact loader)
            for alias_entry in self.aliases:
                alias = alias_entry.get("alias", "")
                canonical = alias_entry.get("name", "")
                if alias and alias not in self._entity_metadata:
                    self._all_entities.append(alias)
                    self._entity_metadata[alias] = {
                        "type": alias_entry.get("type", "alias"),
                        "full_name": canonical,
                        "metadata": alias_entry,
                    }

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in self._all_entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)

        self._all_entities = unique_entities
        logger.info(
            f"Built search index with {len(self._all_entities)} unique entities"
        )

    def find_fuzzy_matches(self, text: str, max_matches: int = 3) -> list[dict]:
        """
        Find fuzzy matches for the given text.

        Args:
            text: Text to match against entities
            max_matches: Maximum number of matches to return

        Returns:
            List of match dictionaries with text, confidence, type, and metadata
        """
        if not self.enabled or not text or len(text) < 2 or not process or not fuzz:
            return []

        # Check cache first
        cache_key = f"{text}:{max_matches}"
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        start_time = time.time()

        try:
            # Use RapidFuzz to find best matches
            matches = process.extract(
                text,
                self._all_entities,
                scorer=fuzz.WRatio,  # Weighted ratio for better results
                limit=max_matches * 2,  # Get more candidates to filter
                score_cutoff=self.confidence_threshold
                * 100,  # RapidFuzz uses 0-100 scale
            )

            results = []
            for match_text, score, _ in matches:
                confidence = score / 100.0  # Convert to 0-1 scale

                if confidence >= self.confidence_threshold:
                    metadata = self._entity_metadata.get(match_text, {})

                    # Calculate Levenshtein distance if available
                    levenshtein_dist = 0
                    if Levenshtein:
                        try:
                            levenshtein_dist = Levenshtein.distance(
                                text.lower(), match_text.lower()
                            )
                        except Exception:
                            levenshtein_dist = 0

                    result = {
                        "text": match_text,
                        "confidence": confidence,
                        "type": metadata.get("type", "unknown"),
                        "full_name": metadata.get("full_name", match_text),
                        "metadata": metadata.get("metadata", {}),
                        "match_type": "fuzzy",
                        "original_query": text,
                        "levenshtein_distance": levenshtein_dist,
                    }
                    results.append(result)

            # Sort by confidence (highest first) and limit results
            results.sort(key=lambda x: x["confidence"], reverse=True)
            results = results[:max_matches]

            # Cache the results
            self._match_cache[cache_key] = results

            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Fuzzy matching for '{text}' took {elapsed_ms:.1f}ms, "
                f"found {len(results)} matches"
            )

            return results

        except Exception as e:
            logger.error(f"Fuzzy matching failed for '{text}': {e}")
            return []

    def find_fuzzy_matches_in_segments(self, segments: list[str]) -> list[dict]:
        """
        Find fuzzy matches for multiple text segments.

        Args:
            segments: List of text segments to match

        Returns:
            List of all matches found across segments
        """
        all_matches = []

        for segment in segments:
            segment = segment.strip()
            if len(segment) >= 2:  # Skip very short segments
                matches = self.find_fuzzy_matches(segment, max_matches=3)
                all_matches.extend(matches)

        # Remove duplicates and sort by confidence
        seen_texts = set()
        unique_matches = []

        for match in sorted(all_matches, key=lambda x: x["confidence"], reverse=True):
            if match["text"] not in seen_texts:
                seen_texts.add(match["text"])
                unique_matches.append(match)

        return unique_matches

    def enhance_with_fuzzy_matching(self, text: str, exact_matches: list[dict]) -> dict:
        """
        Enhance exact matches with fuzzy matching for unmatched segments.

        Args:
            text: Original input text
            exact_matches: List of exact matches found

        Returns:
            Dictionary with enhanced results including fuzzy matches
        """
        if not self.enabled:
            return {
                "fuzzy_matches": [],
                "suggestions": [],
                "enhanced_entities": exact_matches,
            }

        # Find unmatched segments
        unmatched_segments = self._find_unmatched_segments(text, exact_matches)

        # Find fuzzy matches for unmatched segments
        fuzzy_matches = self.find_fuzzy_matches_in_segments(unmatched_segments)

        # Generate suggestions for low-confidence matches
        suggestions = []
        high_confidence_fuzzy = []

        for match in fuzzy_matches:
            if match["confidence"] >= self.confidence_threshold:
                high_confidence_fuzzy.append(match)
            else:
                suggestions.append(
                    {
                        "text": match["text"],
                        "confidence": match["confidence"],
                        "type": match["type"],
                        "suggestion_type": "fuzzy_match",
                        "original_query": match["original_query"],
                    }
                )

        # Combine exact and high-confidence fuzzy matches
        enhanced_entities = exact_matches + high_confidence_fuzzy

        return {
            "fuzzy_matches": fuzzy_matches,
            "suggestions": suggestions[:5],  # Limit suggestions
            "enhanced_entities": enhanced_entities,
        }

    def _find_unmatched_segments(
        self, text: str, exact_matches: list[dict]
    ) -> list[str]:
        """
        Find text segments that weren't matched by exact matching.

        Args:
            text: Original input text
            exact_matches: List of exact matches with start/end positions

        Returns:
            List of unmatched text segments
        """
        if not exact_matches:
            # Split text into words if no exact matches
            return [
                word.strip() for word in re.split(r"\W+", text) if len(word.strip()) > 1
            ]

        # Sort matches by start position
        sorted_matches = sorted(exact_matches, key=lambda x: x.get("start", 0))

        unmatched_segments = []
        last_end = 0

        for match in sorted_matches:
            start = match.get("start", 0)
            end = match.get("end", start + len(match.get("text", "")))

            # Extract text before this match
            if start > last_end:
                segment = text[last_end:start].strip()
                if segment:
                    # Split segment into words
                    words = [
                        word.strip()
                        for word in re.split(r"\W+", segment)
                        if len(word.strip()) > 1
                    ]
                    unmatched_segments.extend(words)

            last_end = end

        # Extract text after the last match
        if last_end < len(text):
            segment = text[last_end:].strip()
            if segment:
                words = [
                    word.strip()
                    for word in re.split(r"\W+", segment)
                    if len(word.strip()) > 1
                ]
                unmatched_segments.extend(words)

        return unmatched_segments

    def get_similarity_score(self, text1: str, text2: str) -> float:
        """
        Get similarity score between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not self.enabled or not fuzz:
            return 0.0

        try:
            score = fuzz.WRatio(text1.lower(), text2.lower())
            return score / 100.0
        except Exception:
            return 0.0

    def clear_cache(self):
        """Clear the fuzzy match cache."""
        self._match_cache.clear()
        logger.info("Fuzzy match cache cleared")

    def get_stats(self) -> dict:
        """Get fuzzy matcher statistics."""
        return {
            "enabled": self.enabled,
            "total_entities": len(self._all_entities),
            "confidence_threshold": self.confidence_threshold,
            "cache_size": len(self._match_cache),
            "rapidfuzz_available": RAPIDFUZZ_AVAILABLE,
        }


# Singleton instance
_fuzzy_matcher_instance: Optional[FuzzyMatcher] = None


def get_fuzzy_matcher(
    gazetteer: Optional[dict] = None,
    aliases: Optional[Union[dict, list[dict]]] = None,
    confidence_threshold: float = 0.8,
) -> FuzzyMatcher:
    """Get or create the singleton fuzzy matcher instance."""
    global _fuzzy_matcher_instance

    if _fuzzy_matcher_instance is None or gazetteer is not None:
        _fuzzy_matcher_instance = FuzzyMatcher(gazetteer, aliases, confidence_threshold)

    return _fuzzy_matcher_instance
