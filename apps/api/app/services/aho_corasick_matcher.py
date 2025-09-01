"""
Aho-Corasick algorithm implementation for efficient multi-pattern string matching.
"""

from collections import deque
from typing import Optional


class AhoCorasickNode:
    """Node in the Aho-Corasick trie."""

    def __init__(self):
        self.children: dict[str, AhoCorasickNode] = {}
        self.failure: Optional[AhoCorasickNode] = None
        self.outputs: list[tuple[str, dict]] = []
        self.is_end: bool = False


class AhoCorasickMatcher:
    """
    Aho-Corasick automaton for efficient multi-pattern matching.
    """

    def __init__(self, case_sensitive: bool = False):
        self.root = AhoCorasickNode()
        self.case_sensitive = case_sensitive
        self.patterns_added = False

    def add_pattern(self, pattern: str, metadata: dict):
        """Add a pattern to the trie with associated metadata."""
        if not pattern:
            return

        current = self.root
        pattern_key = pattern if self.case_sensitive else pattern.lower()

        for char in pattern_key:
            if char not in current.children:
                current.children[char] = AhoCorasickNode()
            current = current.children[char]

        current.is_end = True
        current.outputs.append((pattern, metadata))

    def build_failure_links(self):
        """Build failure links for the Aho-Corasick automaton."""
        queue = deque()

        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)

        while queue:
            current = queue.popleft()

            for char, child in current.children.items():
                queue.append(child)

                failure = current.failure
                while failure and char not in failure.children:
                    failure = failure.failure

                if failure:
                    child.failure = failure.children.get(char, self.root)
                else:
                    child.failure = self.root

                if child.failure.outputs:
                    child.outputs.extend(child.failure.outputs)

        self.patterns_added = True

    def find_all(self, text: str, word_boundaries: bool = True) -> list[dict]:
        """
        Find all pattern matches in the text.

        Args:
            text: Text to search in
            word_boundaries: If True, only match whole words

        Returns:
            List of matches with position and metadata
        """
        if not self.patterns_added:
            self.build_failure_links()

        matches = []
        search_text = text if self.case_sensitive else text.lower()
        current = self.root

        for i, char in enumerate(search_text):
            while current and char not in current.children:
                current = current.failure or self.root

            if char in current.children:
                current = current.children[char]
            else:
                current = self.root

            if current.outputs:
                for pattern, metadata in current.outputs:
                    start_pos = (
                        i - len(pattern if self.case_sensitive else pattern.lower()) + 1
                    )
                    end_pos = i + 1

                    if word_boundaries:
                        if not self._is_word_boundary(text, start_pos, end_pos):
                            continue

                    matches.append(
                        {
                            "text": text[start_pos:end_pos],
                            "pattern": pattern,
                            "start": start_pos,
                            "end": end_pos,
                            **metadata,
                        }
                    )

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

        for metric in gazetteer.get("metrics", []):
            self.matcher.add_pattern(
                metric, {"type": "metric", "display_name": metric, "confidence": 1.0}
            )

        for timeword in gazetteer.get("timewords", []):
            self.matcher.add_pattern(
                timeword,
                {"type": "time_period", "display_name": timeword, "confidence": 1.0},
            )

    def recognize_entities(self, text: str) -> dict:
        """
        Recognize entities in the text.

        Args:
            text: Input text to process

        Returns:
            Dictionary with tagged text and entity list
        """
        matches = self.matcher.find_all(text, word_boundaries=True)

        matches = self._resolve_overlaps(matches)

        tagged_text = self._generate_tagged_text(text, matches)

        entities = [
            {
                "text": match["text"],
                "type": match["type"],
                "start": match["start"],
                "end": match["end"],
                "confidence": match.get("confidence", 1.0),
                "id": match.get("id"),
                "metadata": {"display_name": match.get("display_name", match["text"])},
            }
            for match in matches
        ]

        return {"tagged_text": tagged_text, "entities": entities}

    def _resolve_overlaps(self, matches: list[dict]) -> list[dict]:
        """
        Resolve overlapping entities using priority rules.
        Priority: manufacturer > brand > product > category > metric > time_period
        """
        if not matches:
            return []

        type_priority = {
            "manufacturer": 1,
            "brand": 2,
            "product": 3,
            "category": 4,
            "metric": 5,
            "time_period": 6,
        }

        matches = sorted(matches, key=lambda x: (x["start"], -x["end"]))

        resolved = []
        last_end = -1

        for match in matches:
            if match["start"] >= last_end:
                resolved.append(match)
                last_end = match["end"]
            elif match["type"] in type_priority and resolved:
                last_match = resolved[-1]
                if last_match["type"] in type_priority:
                    if type_priority[match["type"]] < type_priority[last_match["type"]]:
                        resolved[-1] = match
                        last_end = match["end"]

        return resolved

    def _generate_tagged_text(self, text: str, matches: list[dict]) -> str:
        """Generate XML-style tagged text from matches."""
        if not matches:
            return text

        matches = sorted(matches, key=lambda x: x["start"])

        result = []
        last_pos = 0

        for match in matches:
            if match["start"] > last_pos:
                result.append(text[last_pos : match["start"]])

            tag_type = match["type"].replace("_", "-")
            result.append(f"<{tag_type}>{match['text']}</{tag_type}>")
            last_pos = match["end"]

        if last_pos < len(text):
            result.append(text[last_pos:])

        return "".join(result)
