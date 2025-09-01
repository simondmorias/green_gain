"""
Aho-Corasick algorithm implementation for efficient multi-pattern string matching.
Using pyahocorasick library for reliable performance.
"""

import re
from typing import Optional

try:
    import ahocorasick
    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False
    ahocorasick = None


class AhoCorasickMatcher:
    """
    Aho-Corasick automaton for efficient multi-pattern matching.
    Uses pyahocorasick library for reliable implementation.
    """

    def __init__(self, case_sensitive: bool = False):
        if not AHOCORASICK_AVAILABLE:
            raise ImportError("pyahocorasick library is required but not available")
            
        self.automaton = ahocorasick.Automaton()
        self.case_sensitive = case_sensitive
        self.patterns_added = False
        self.pattern_metadata = {}

    def add_pattern(self, pattern: str, metadata: dict):
        """Add a pattern to the automaton with associated metadata."""
        if not pattern:
            return

        pattern_key = pattern if self.case_sensitive else pattern.lower()
        
        # Store metadata for later retrieval
        self.pattern_metadata[pattern_key] = {
            'original_pattern': pattern,
            'metadata': metadata
        }
        
        # Add to automaton
        self.automaton.add_word(pattern_key, (pattern_key, metadata))

    def build_failure_links(self):
        """Build the automaton (equivalent to building failure links)."""
        self.automaton.make_automaton()
        self.patterns_added = True

    def find_all(self, text: str, word_boundaries: bool = True) -> list[dict]:
        """
        Find all pattern matches in the text.

        Args:
            text: Text to search in
            word_boundaries: If True, only match whole words

        Returns:
            List of match dictionaries with start, end, text, and metadata
        """
        if not self.patterns_added:
            return []

        text_to_search = text if self.case_sensitive else text.lower()
        matches = []

        for end_index, (pattern_key, metadata) in self.automaton.iter(text_to_search):
            start_index = end_index - len(pattern_key) + 1
            
            # Check word boundaries if requested
            if word_boundaries:
                if not self._is_word_boundary(text_to_search, start_index, end_index + 1):
                    continue

            # Get original pattern text from the original input
            original_text = text[start_index:end_index + 1]
            
            matches.append({
                "start": start_index,
                "end": end_index + 1,
                "text": original_text,
                "pattern": pattern_key,
                **metadata
            })

        return matches

    def _is_word_boundary(self, text: str, start: int, end: int) -> bool:
        """Check if the match is at word boundaries."""
        if start > 0 and text[start - 1].isalnum():
            return False
        if end < len(text) and text[end].isalnum():
            return False
        return True


class EntityMatcher:
    """
    Entity matcher using Aho-Corasick for efficient recognition.
    """

    def __init__(self, gazetteer: dict, aliases: list[dict]):
        """
        Initialize the entity matcher with gazetteer and aliases.

        Args:
            gazetteer: Dictionary of entity lists by type
            aliases: List of entity aliases with metadata
        """
        self.matcher = AhoCorasickMatcher(case_sensitive=False)
        self.stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
        }

        self._load_patterns(gazetteer, aliases)
        self.matcher.build_failure_links()

    def _load_patterns(self, gazetteer: dict, aliases: list[dict]):
        """Load patterns from gazetteer and aliases."""
        # Load entities from gazetteer
        for entity_type, entities in gazetteer.get("entities", {}).items():
            for entity in entities:
                if entity.lower() not in self.stopwords:
                    self.matcher.add_pattern(
                        entity,
                        {
                            "type": entity_type.rstrip("s"),
                            "display_name": entity,
                            "confidence": 1.0,
                        },
                    )

        # Load aliases
        for alias_entry in aliases:
            if alias_entry["alias"].lower() not in self.stopwords:
                self.matcher.add_pattern(
                    alias_entry["alias"],
                    {
                        "type": alias_entry["type"],
                        "display_name": alias_entry["name"],
                        "id": alias_entry.get("id"),
                        "confidence": alias_entry.get("confidence", 0.9),
                    },
                )

        # Load metrics
        for metric in gazetteer.get("metrics", []):
            self.matcher.add_pattern(
                metric, {"type": "metric", "display_name": metric, "confidence": 1.0}
            )

        # Load timewords
        for timeword in gazetteer.get("timewords", []):
            self.matcher.add_pattern(
                timeword,
                {"type": "time_period", "display_name": timeword, "confidence": 1.0},
            )

        # Load special tokens
        for token in gazetteer.get("special_tokens", []):
            self.matcher.add_pattern(
                token, {"type": "special", "display_name": token, "confidence": 1.0}
            )

    def recognize_entities(self, text: str) -> dict:
        """
        Recognize entities in the given text.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with entities list and tagged text
        """
        if not text or not text.strip():
            return {"entities": [], "tagged_text": text}

        # Find all matches
        matches = self.matcher.find_all(text, word_boundaries=True)

        # Resolve overlapping matches by priority
        matches = self._resolve_overlaps(matches)

        # Sort matches by position for XML tagging
        matches.sort(key=lambda x: x["start"])

        # Generate XML-tagged text
        tagged_text = self._create_tagged_text(text, matches)

        return {"entities": matches, "tagged_text": tagged_text}

    def _resolve_overlaps(self, matches: list[dict]) -> list[dict]:
        """Resolve overlapping matches by preferring longest matches, then by entity type priority."""
        if not matches:
            return matches

        # Sort by length (descending) first, then by start position
        # This ensures we process longer matches first
        matches.sort(key=lambda x: (-(x["end"] - x["start"]), x["start"]))

        # Priority order (higher priority first) - used as tiebreaker for same-length matches
        type_priority = {
            "manufacturer": 4,
            "brand": 3,
            "product": 2,
            "category": 2,
            "metric": 1,
            "time_period": 1,
            "special": 0,
        }

        resolved = []
        used_positions = set()

        for match in matches:
            # Check if this match overlaps with any already selected matches
            overlap = False
            for pos in range(match["start"], match["end"]):
                if pos in used_positions:
                    overlap = True
                    break

            if not overlap:
                # No overlap, add this match (longer matches are processed first)
                resolved.append(match)
                for pos in range(match["start"], match["end"]):
                    used_positions.add(pos)

        return resolved

    def _create_tagged_text(self, text: str, matches: list[dict]) -> str:
        """Create XML-tagged text with entity markers."""
        if not matches:
            return text

        # Sort matches by start position (descending) to process from end to start
        matches_desc = sorted(matches, key=lambda x: x["start"], reverse=True)

        result = text
        for match in matches_desc:
            entity_type = match["type"]
            start = match["start"]
            end = match["end"]
            entity_text = match["text"]

            # Create XML tag
            tag = f'<{entity_type}>{entity_text}</{entity_type}>'
            result = result[:start] + tag + result[end:]

        return result