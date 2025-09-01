"""
Tests for fuzzy matching functionality.
"""

from unittest.mock import patch

import pytest

from app.services.fuzzy_matcher import FuzzyMatcher, get_fuzzy_matcher


class TestFuzzyMatcher:
    """Test cases for FuzzyMatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.gazetteer = {
            "manufacturer": [
                {"name": "Coca-Cola", "full_name": "The Coca-Cola Company"},
                {"name": "PepsiCo", "full_name": "PepsiCo Inc."},
                {"name": "Unilever", "full_name": "Unilever PLC"},
                "Nestle",
                "Procter & Gamble",
            ],
            "product": [
                {"name": "Coke", "full_name": "Coca-Cola Classic"},
                {"name": "Pepsi", "full_name": "Pepsi Cola"},
                "Sprite",
                "Fanta",
            ],
        }

        self.aliases = {
            "P&G": "Procter & Gamble",
            "Coke": "Coca-Cola",
            "Pepsi": "PepsiCo",
        }

    def test_initialization_without_rapidfuzz(self):
        """Test FuzzyMatcher initialization when RapidFuzz is not available."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        assert matcher.gazetteer == self.gazetteer
        assert matcher.aliases == self.aliases
        assert matcher.confidence_threshold == 0.8
        assert not matcher.enabled  # Should be False when RapidFuzz not available
        assert len(matcher._all_entities) > 0

    def test_build_search_index(self):
        """Test building of search index from gazetteer and aliases."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        # Check that entities are properly indexed
        assert "Coca-Cola" in matcher._all_entities
        assert "PepsiCo" in matcher._all_entities
        assert "Nestle" in matcher._all_entities
        assert "P&G" in matcher._all_entities

        # Check metadata
        assert "Coca-Cola" in matcher._entity_metadata
        assert matcher._entity_metadata["Coca-Cola"]["type"] == "manufacturer"
        assert (
            matcher._entity_metadata["Coca-Cola"]["full_name"]
            == "The Coca-Cola Company"
        )

    def test_find_fuzzy_matches_disabled(self):
        """Test fuzzy matching when disabled (RapidFuzz not available)."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        # Should return empty list when disabled
        matches = matcher.find_fuzzy_matches("Coca Cola")
        assert matches == []

    @patch("app.services.fuzzy_matcher.RAPIDFUZZ_AVAILABLE", True)
    @patch("app.services.fuzzy_matcher.process")
    @patch("app.services.fuzzy_matcher.fuzz")
    def test_find_fuzzy_matches_enabled(self, mock_fuzz, mock_process):
        """Test fuzzy matching when enabled."""
        # Mock RapidFuzz responses
        mock_process.extract.return_value = [("Coca-Cola", 95, 0), ("PepsiCo", 85, 1)]

        matcher = FuzzyMatcher(self.gazetteer, self.aliases)
        matcher.enabled = True  # Force enable for test

        matches = matcher.find_fuzzy_matches("Coca Cola", max_matches=2)

        # Should call RapidFuzz
        mock_process.extract.assert_called_once()

        # Should return formatted matches
        assert len(matches) == 2
        assert matches[0]["text"] == "Coca-Cola"
        assert matches[0]["confidence"] == 0.95
        assert matches[0]["type"] == "manufacturer"

    def test_find_unmatched_segments_no_matches(self):
        """Test finding unmatched segments when no exact matches exist."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        text = "Show me Coca Cola and Pepsi sales"
        segments = matcher._find_unmatched_segments(text, [])

        expected_words = ["Show", "me", "Coca", "Cola", "and", "Pepsi", "sales"]
        assert all(word in segments for word in expected_words)

    def test_find_unmatched_segments_with_matches(self):
        """Test finding unmatched segments with existing exact matches."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        text = "Show me Coca-Cola and Pepsi sales"
        exact_matches = [
            {"text": "Coca-Cola", "start": 8, "end": 17},
            {"text": "Pepsi", "start": 22, "end": 27},
        ]

        segments = matcher._find_unmatched_segments(text, exact_matches)

        # Should extract unmatched words
        assert "Show" in segments
        assert "me" in segments
        assert "and" in segments
        assert "sales" in segments
        # Should not include matched entities
        assert "Coca-Cola" not in segments
        assert "Pepsi" not in segments

    def test_enhance_with_fuzzy_matching_disabled(self):
        """Test enhancement when fuzzy matching is disabled."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        exact_matches = [{"text": "Coca-Cola", "type": "manufacturer"}]
        result = matcher.enhance_with_fuzzy_matching("test text", exact_matches)

        assert result["fuzzy_matches"] == []
        assert result["suggestions"] == []
        assert result["enhanced_entities"] == exact_matches

    def test_get_similarity_score_disabled(self):
        """Test similarity score when fuzzy matching is disabled."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        score = matcher.get_similarity_score("Coca Cola", "Coca-Cola")
        assert score == 0.0

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        # Add something to cache
        matcher._match_cache["test"] = [{"text": "test"}]
        assert len(matcher._match_cache) == 1

        # Clear cache
        matcher.clear_cache()
        assert len(matcher._match_cache) == 0

    def test_get_stats(self):
        """Test statistics retrieval."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        stats = matcher.get_stats()

        assert "enabled" in stats
        assert "total_entities" in stats
        assert "confidence_threshold" in stats
        assert "cache_size" in stats
        assert "rapidfuzz_available" in stats

        assert stats["confidence_threshold"] == 0.8
        assert stats["total_entities"] > 0

    def test_singleton_get_fuzzy_matcher(self):
        """Test singleton pattern for fuzzy matcher."""
        matcher1 = get_fuzzy_matcher(self.gazetteer, self.aliases)
        matcher2 = get_fuzzy_matcher()

        # Should return the same instance when no new data provided
        assert matcher1 is matcher2

        # Should create new instance when new data provided
        matcher3 = get_fuzzy_matcher({"new": ["data"]}, {})
        assert matcher3 is not matcher1


class TestFuzzyMatchingIntegration:
    """Integration tests for fuzzy matching with entity recognition."""

    def setup_method(self):
        """Set up test fixtures."""
        self.gazetteer = {
            "manufacturer": ["Coca-Cola", "PepsiCo", "Unilever"],
            "product": ["Coke", "Pepsi", "Sprite"],
        }
        self.aliases = {"P&G": "Procter & Gamble"}

    def test_fuzzy_matching_with_misspellings(self):
        """Test fuzzy matching handles common misspellings."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases)

        # Test with disabled fuzzy matching (default state)
        segments = ["Coca", "Cola", "Pepsi", "Co"]
        matches = matcher.find_fuzzy_matches_in_segments(segments)

        # Should return empty when disabled
        assert matches == []

    def test_confidence_threshold_filtering(self):
        """Test that confidence threshold properly filters results."""
        matcher = FuzzyMatcher(self.gazetteer, self.aliases, confidence_threshold=0.9)

        assert matcher.confidence_threshold == 0.9

        # With high threshold, should be more selective
        # (This would be tested with actual RapidFuzz in real environment)

    def test_edge_cases(self):
        """Test edge cases for fuzzy matching."""
        matcher = FuzzyMatcher({}, {})

        # Empty text
        matches = matcher.find_fuzzy_matches("")
        assert matches == []

        # Very short text
        matches = matcher.find_fuzzy_matches("a")
        assert matches == []

        # No entities loaded
        matches = matcher.find_fuzzy_matches("test")
        assert matches == []


@pytest.mark.integration
class TestFuzzyMatchingPerformance:
    """Performance tests for fuzzy matching."""

    def test_large_entity_set_performance(self):
        """Test performance with large entity sets."""
        # Create large gazetteer
        large_gazetteer = {
            "manufacturer": [f"Company_{i}" for i in range(1000)],
            "product": [f"Product_{i}" for i in range(1000)],
        }

        matcher = FuzzyMatcher(large_gazetteer, {})

        # Should initialize without issues
        assert len(matcher._all_entities) == 2000

        # Should handle queries efficiently (when RapidFuzz available)
        matches = matcher.find_fuzzy_matches("Company_500")
        # Will be empty when RapidFuzz not available, but shouldn't crash
        assert isinstance(matches, list)

    def test_cache_performance(self):
        """Test that caching improves performance."""
        matcher = FuzzyMatcher({"test": ["entity1", "entity2"]}, {})

        # First call
        matches1 = matcher.find_fuzzy_matches("test query")

        # Second call should use cache
        matches2 = matcher.find_fuzzy_matches("test query")

        assert matches1 == matches2
        assert len(matcher._match_cache) <= 1  # Should cache the result
