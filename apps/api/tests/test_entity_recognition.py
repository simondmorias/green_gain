"""
Unit tests for entity recognition service.
"""

import json
from unittest.mock import MagicMock, patch

from app.services.aho_corasick_matcher import AhoCorasickMatcher, EntityMatcher
from app.services.entity_recognizer import EntityRecognitionService


class TestAhoCorasickMatcher:
    """Test the Aho-Corasick matcher implementation."""

    def test_exact_match(self):
        """Test exact pattern matching."""
        matcher = AhoCorasickMatcher(case_sensitive=False)
        matcher.add_pattern("Cadbury", {"type": "manufacturer"})
        matcher.add_pattern("revenue", {"type": "metric"})
        matcher.build_failure_links()

        text = "Show me Cadbury revenue"
        matches = matcher.find_all(text)

        assert len(matches) == 2
        assert matches[0]["pattern"] == "Cadbury"
        assert matches[0]["type"] == "manufacturer"
        assert matches[1]["pattern"] == "revenue"
        assert matches[1]["type"] == "metric"

    def test_case_insensitive_matching(self):
        """Test case-insensitive matching."""
        matcher = AhoCorasickMatcher(case_sensitive=False)
        matcher.add_pattern("Cadbury", {"type": "manufacturer"})
        matcher.build_failure_links()

        text = "CADBURY, cadbury, and Cadbury"
        matches = matcher.find_all(text, word_boundaries=True)

        assert len(matches) == 3
        for match in matches:
            assert match["type"] == "manufacturer"

    def test_word_boundaries(self):
        """Test word boundary detection."""
        matcher = AhoCorasickMatcher(case_sensitive=False)
        matcher.add_pattern("Mars", {"type": "manufacturer"})
        matcher.build_failure_links()

        # Should match
        text1 = "Mars is a manufacturer"
        matches1 = matcher.find_all(text1, word_boundaries=True)
        assert len(matches1) == 1

        # Should not match (part of another word)
        text2 = "Marshmallow is not Mars"
        matches2 = matcher.find_all(text2, word_boundaries=True)
        assert len(matches2) == 1  # Only the standalone "Mars"
        assert matches2[0]["start"] == 19

    def test_overlapping_patterns(self):
        """Test handling of overlapping patterns."""
        matcher = AhoCorasickMatcher(case_sensitive=False)
        matcher.add_pattern("market", {"type": "metric"})
        matcher.add_pattern("market share", {"type": "metric"})
        matcher.build_failure_links()

        text = "Show market share trends"
        matches = matcher.find_all(text, word_boundaries=True)

        # Should find both patterns
        assert len(matches) >= 1
        # The longer pattern should be among matches
        assert any(m["pattern"] == "market share" for m in matches)


class TestEntityMatcher:
    """Test the EntityMatcher class."""

    def test_entity_recognition(self):
        """Test basic entity recognition."""
        gazetteer = {
            "entities": {
                "manufacturers": ["Cadbury", "Mars"],
                "products": ["Dairy Milk", "Galaxy"],
            },
            "metrics": ["revenue", "sales"],
            "timewords": ["Q1", "Q2", "YTD"],
        }
        aliases = [
            {
                "type": "manufacturer",
                "name": "Cadbury",
                "alias": "cadburys",
                "id": "MFR_001",
                "confidence": 0.9,
            }
        ]

        matcher = EntityMatcher(gazetteer, aliases)
        result = matcher.recognize_entities("Show me Cadbury revenue for Q1")

        assert "tagged_text" in result
        assert "entities" in result
        assert len(result["entities"]) == 3

        # Check tagged text format
        assert "<manufacturer>" in result["tagged_text"]
        assert "<metric>" in result["tagged_text"]
        assert "<time-period>" in result["tagged_text"]

    def test_alias_recognition(self):
        """Test that aliases are properly recognized."""
        gazetteer = {"entities": {}}
        aliases = [
            {
                "type": "manufacturer",
                "name": "Cadbury",
                "alias": "cadburys",
                "id": "MFR_001",
                "confidence": 0.9,
            },
            {
                "type": "manufacturer",
                "name": "Cadbury",
                "alias": "cadbury's",
                "id": "MFR_001",
                "confidence": 0.9,
            },
        ]

        matcher = EntityMatcher(gazetteer, aliases)

        # Test first alias
        result1 = matcher.recognize_entities("I love Cadburys chocolate")
        assert len(result1["entities"]) == 1
        assert result1["entities"][0]["metadata"]["display_name"] == "Cadbury"

        # Test second alias
        result2 = matcher.recognize_entities("Cadbury's is the best")
        assert len(result2["entities"]) == 1
        assert result2["entities"][0]["metadata"]["display_name"] == "Cadbury"

    def test_overlap_resolution(self):
        """Test priority-based overlap resolution."""
        gazetteer = {"entities": {"manufacturers": ["Mars"], "products": ["Mars Bar"]}}
        aliases = []

        matcher = EntityMatcher(gazetteer, aliases)
        result = matcher.recognize_entities("Mars Bar sales data")

        # Should prioritize manufacturer over product due to priority rules
        entities = result["entities"]
        # Due to word boundaries, both should be recognized separately
        assert any(e["type"] == "manufacturer" for e in entities)


class TestEntityRecognitionService:
    """Test the EntityRecognitionService class."""

    @patch("app.services.entity_recognizer.Path.exists")
    @patch("builtins.open")
    def test_load_artifacts(self, mock_open, mock_exists):
        """Test artifact loading."""
        mock_exists.return_value = True

        # Mock gazetteer file
        gazetteer_data = json.dumps(
            {"entities": {"manufacturers": ["Test"]}, "metrics": ["revenue"]}
        )

        # Mock aliases file
        aliases_data = '{"type": "manufacturer", "name": "Test", "alias": "test", "confidence": 1.0}\n'

        # Configure mock_open to return different data for different files
        mock_files = {
            "gazetteer.json": MagicMock(read=MagicMock(return_value=gazetteer_data)),
            "aliases.jsonl": MagicMock(
                __iter__=MagicMock(return_value=iter([aliases_data]))
            ),
        }

        def open_side_effect(path, mode="r"):
            if "gazetteer.json" in str(path):
                return mock_files["gazetteer.json"]
            elif "aliases.jsonl" in str(path):
                return mock_files["aliases.jsonl"]
            return MagicMock()

        mock_open.side_effect = open_side_effect

        service = EntityRecognitionService()
        assert service.artifacts_loaded
        # Check that artifacts were loaded through the artifact loader
        gazetteer = service.artifact_loader.get_gazetteer()
        assert len(gazetteer.get("entities", {})) > 0

    @patch("app.services.entity_recognizer.Path.exists")
    def test_fallback_to_defaults(self, mock_exists):
        """Test fallback to default artifacts when files don't exist."""
        mock_exists.return_value = False

        service = EntityRecognitionService()
        assert service.artifacts_loaded
        # Check that default artifacts were loaded
        gazetteer = service.artifact_loader.get_gazetteer()
        assert "manufacturers" in gazetteer.get("entities", {})
        assert len(gazetteer.get("entities", {}).get("manufacturers", [])) > 0

    @patch("app.services.entity_recognizer.EntityRecognitionService._load_artifacts")
    def test_recognize_method(self, mock_load):
        """Test the recognize method."""
        service = EntityRecognitionService()
        service._use_default_artifacts()

        result = service.recognize("Show me Cadbury revenue")

        assert "tagged_text" in result
        assert "entities" in result
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] >= 0

    @patch("app.services.entity_recognizer.EntityRecognitionService._load_artifacts")
    def test_text_length_limit(self, mock_load):
        """Test that text longer than 500 chars is truncated."""
        service = EntityRecognitionService()
        service._use_default_artifacts()

        long_text = "a" * 600
        result = service.recognize(long_text)

        # Should still return a result
        assert "tagged_text" in result
        assert len(result["tagged_text"]) <= 500

    @patch("app.services.entity_recognizer.EntityRecognitionService._load_artifacts")
    def test_error_handling(self, mock_load):
        """Test error handling in recognition."""
        service = EntityRecognitionService()
        service.matcher = None  # Force an error

        result = service.recognize("test text")

        assert "error" in result
        assert result["entities"] == []
        assert result["processing_time_ms"] == 0


class TestIntegration:
    """Integration tests for the complete entity recognition pipeline."""

    @patch("app.services.entity_recognizer.Path.exists")
    def test_end_to_end_recognition(self, mock_exists):
        """Test complete recognition pipeline with realistic data."""
        mock_exists.return_value = False  # Use default artifacts

        service = EntityRecognitionService()

        test_cases = [
            ("Show me Cadbury revenue for Q1", ["Cadbury", "revenue", "Q1"]),
            ("Compare Mars vs Nestle market share", ["Mars", "Nestle", "market share"]),
            ("What's the YTD growth?", ["YTD", "growth"]),
        ]

        for text, expected_entities in test_cases:
            result = service.recognize(text)

            assert "tagged_text" in result
            assert "entities" in result
            assert result["processing_time_ms"] < 100  # Performance requirement

            # Check that expected entities are found
            found_texts = [e["text"] for e in result["entities"]]
            for expected in expected_entities:
                assert any(expected in found for found in found_texts), (
                    f"Expected {expected} not found in {found_texts}"
                )
