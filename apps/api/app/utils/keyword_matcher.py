"""
Keyword matching utility for conversational UI.

This module provides sophisticated keyword matching logic to categorize
user queries and determine appropriate response types.
"""

import re
from enum import Enum


class QueryCategory(Enum):
    """Enumeration of query categories."""

    REVENUE = "revenue"
    PROMOTION = "promotion"
    PRICING = "pricing"
    PRODUCT = "product"
    HELP = "help"
    UNKNOWN = "unknown"


class KeywordMatcher:
    """Advanced keyword matcher for categorizing user queries."""

    def __init__(self):
        """Initialize the keyword matcher with predefined keyword sets."""
        self._keyword_patterns = {
            QueryCategory.REVENUE: {
                "primary": [
                    r"\b(revenue|revenues)\b",
                    r"\b(sales|sale)\b",
                    r"\b(earnings|earning)\b",
                    r"\b(income|incomes)\b",
                    r"\b(turnover)\b",
                    r"\b(performance)\b",
                ],
                "secondary": [
                    r"\b(growth|growing|grew)\b",
                    r"\b(total|overall)\b",
                    r"\b(quarterly|monthly|yearly)\b",
                    r"\b(target|targets|goal|goals)\b",
                    r"\b(achievement|achievements)\b",
                ],
            },
            QueryCategory.PROMOTION: {
                "primary": [
                    r"\b(promotion|promotions|promo|promos)\b",
                    r"\b(campaign|campaigns)\b",
                    r"\b(discount|discounts)\b",
                    r"\b(offer|offers|offering)\b",
                    r"\b(deal|deals)\b",
                    r"\b(marketing)\b",
                ],
                "secondary": [
                    r"\b(roi|return)\b",
                    r"\b(effectiveness|effective)\b",
                    r"\b(performance|performing)\b",
                    r"\b(impact|impacts)\b",
                    r"\b(optimization|optimize)\b",
                ],
            },
            QueryCategory.PRICING: {
                "primary": [
                    r"\b(price|prices|pricing)\b",
                    r"\b(cost|costs|costing)\b",
                    r"\b(competitor|competitors|competitive)\b",
                    r"\b(elasticity|elastic)\b",
                    r"\b(positioning|position)\b",
                ],
                "secondary": [
                    r"\b(strategy|strategies)\b",
                    r"\b(analysis|analyze)\b",
                    r"\b(comparison|compare|comparing)\b",
                    r"\b(optimization|optimize)\b",
                    r"\b(recommendation|recommendations)\b",
                ],
            },
            QueryCategory.PRODUCT: {
                "primary": [
                    r"\b(product|products)\b",
                    r"\b(brand|brands|branding)\b",
                    r"\b(category|categories)\b",
                    r"\b(item|items)\b",
                    r"\b(portfolio)\b",
                ],
                "secondary": [
                    r"\b(performance|performing)\b",
                    r"\b(market share|share)\b",
                    r"\b(growth|growing)\b",
                    r"\b(opportunity|opportunities)\b",
                    r"\b(analysis|analyze)\b",
                ],
            },
            QueryCategory.HELP: {
                "primary": [
                    r"\b(help|helping)\b",
                    r"\b(what can|what do|how do)\b",
                    r"\b(available|options)\b",
                    r"\b(guide|guidance)\b",
                    r"\b(support)\b",
                ],
                "secondary": [
                    r"\b(questions|question)\b",
                    r"\b(ask|asking)\b",
                    r"\b(information|info)\b",
                    r"\b(assistance|assist)\b",
                ],
            },
        }

        # Compile patterns for better performance
        self._compiled_patterns = {}
        for category, patterns in self._keyword_patterns.items():
            self._compiled_patterns[category] = {
                "primary": [
                    re.compile(pattern, re.IGNORECASE)
                    for pattern in patterns["primary"]
                ],
                "secondary": [
                    re.compile(pattern, re.IGNORECASE)
                    for pattern in patterns["secondary"]
                ],
            }

    def categorize_query(self, message: str) -> QueryCategory:
        """
        Categorize a user query based on keyword matching.

        Args:
            message: The user's input message

        Returns:
            QueryCategory enum representing the best match
        """
        if not message or not message.strip():
            return QueryCategory.UNKNOWN

        message = message.strip().lower()

        # Calculate scores for each category
        category_scores = {}
        for category in QueryCategory:
            if category in [QueryCategory.UNKNOWN]:
                continue
            category_scores[category] = self._calculate_category_score(
                message, category
            )

        # Find the category with the highest score
        if not category_scores:
            return QueryCategory.UNKNOWN

        best_category = max(category_scores.items(), key=lambda x: x[1])

        # Return the best category if it has a meaningful score, otherwise unknown
        if best_category[1] > 0:
            return best_category[0]
        else:
            return QueryCategory.UNKNOWN

    def _calculate_category_score(self, message: str, category: QueryCategory) -> float:
        """
        Calculate a score for how well a message matches a category.

        Args:
            message: The message to score
            category: The category to score against

        Returns:
            Float score (higher is better match)
        """
        if category not in self._compiled_patterns:
            return 0.0

        patterns = self._compiled_patterns[category]
        score = 0.0

        # Primary keywords have higher weight
        for pattern in patterns["primary"]:
            matches = len(pattern.findall(message))
            score += matches * 2.0

        # Secondary keywords have lower weight
        for pattern in patterns["secondary"]:
            matches = len(pattern.findall(message))
            score += matches * 1.0

        return score

    def get_matching_keywords(self, message: str, category: QueryCategory) -> list[str]:
        """
        Get the specific keywords that matched for a category.

        Args:
            message: The message to analyze
            category: The category to check

        Returns:
            List of matched keyword strings
        """
        if category not in self._compiled_patterns:
            return []

        matched_keywords = []
        patterns = self._compiled_patterns[category]

        # Check primary patterns
        for pattern in patterns["primary"]:
            matches = pattern.findall(message.lower())
            matched_keywords.extend(matches)

        # Check secondary patterns
        for pattern in patterns["secondary"]:
            matches = pattern.findall(message.lower())
            matched_keywords.extend(matches)

        return list(set(matched_keywords))  # Remove duplicates

    def get_category_confidence(self, message: str, category: QueryCategory) -> float:
        """
        Get confidence score for a category match (0.0 to 1.0).

        Args:
            message: The message to analyze
            category: The category to check

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = self._calculate_category_score(message, category)

        # Normalize score to 0-1 range (assuming max reasonable score is 10)
        max_score = 10.0
        confidence = min(score / max_score, 1.0)

        return confidence

    def get_all_category_scores(self, message: str) -> dict[QueryCategory, float]:
        """
        Get scores for all categories.

        Args:
            message: The message to analyze

        Returns:
            Dictionary mapping categories to their scores
        """
        scores = {}
        for category in QueryCategory:
            if category != QueryCategory.UNKNOWN:
                scores[category] = self._calculate_category_score(message, category)
        return scores

    def is_ambiguous_query(self, message: str, threshold: float = 0.3) -> bool:
        """
        Check if a query is ambiguous (matches multiple categories similarly).

        Args:
            message: The message to analyze
            threshold: Minimum difference required between top scores

        Returns:
            True if query is ambiguous, False otherwise
        """
        scores = self.get_all_category_scores(message)
        if len(scores) < 2:
            return False

        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) < 2:
            return False

        # If the top score is very low, it's not ambiguous, it's just unknown
        if sorted_scores[0] < 0.1:
            return False

        # Check if top two scores are too close
        return (sorted_scores[0] - sorted_scores[1]) < threshold
