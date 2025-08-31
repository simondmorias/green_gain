"""
Enhanced static response service for the conversational UI.

This module provides sophisticated keyword-based response matching for revenue-related queries
and returns static responses with realistic CPG sample data for the MVP.
"""

import time
from typing import Any

from ..data.sample_data import (
    get_pricing_data,
    get_product_data,
    get_promotion_data,
    get_revenue_data,
    get_suggestions,
)
from ..utils.keyword_matcher import KeywordMatcher, QueryCategory


class StaticResponseService:
    """Enhanced service for generating static responses based on sophisticated keyword matching."""

    def __init__(self):
        """Initialize the static response service with keyword matcher and response templates."""
        self.keyword_matcher = KeywordMatcher()
        self._context_history: list[QueryCategory] = []
        self._max_history = 5  # Keep last 5 queries for context

        # Response templates for each category
        self._response_templates = {
            QueryCategory.REVENUE: self._create_revenue_response,
            QueryCategory.PROMOTION: self._create_promotion_response,
            QueryCategory.PRICING: self._create_pricing_response,
            QueryCategory.PRODUCT: self._create_product_response,
            QueryCategory.HELP: self._create_help_response,
        }

    def get_response(self, message: str) -> dict[str, Any]:
        """
        Get a static response based on sophisticated keyword matching.

        Args:
            message: The user's input message

        Returns:
            Dictionary containing response text, data, and suggestions
        """
        start_time = time.time()

        # Categorize the query
        category = self.keyword_matcher.categorize_query(message)

        # Update context history
        self._update_context_history(category)

        # Generate response based on category
        if category in self._response_templates:
            response_data = self._response_templates[category](message)
            response_category = category.value
        else:
            response_data = self._create_default_response(message)
            response_category = "unknown"  # Force unknown for default responses

        # Add processing time for monitoring
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        response_data["metadata"] = {
            "category": response_category,
            "processing_time_ms": round(processing_time, 2),
            "confidence": self.keyword_matcher.get_category_confidence(
                message, category
            ),
        }

        return response_data

    def _create_revenue_response(self, message: str) -> dict[str, Any]:
        """Create a revenue-focused response with CPG data."""
        data = get_revenue_data()

        response_text = f"""Here's your revenue summary for {data["period"]}:

📈 **Total Revenue:** ${data["total_revenue"]:,} ({data["growth_rate"]:+.1f}% growth)
📊 **Year-over-Year:** {data["yoy_growth"]:+.1f}% vs ${data["year_ago_revenue"]:,}

**Top Performing Categories:**
• Beverages: ${data["breakdown"]["beverages"]:,}
• Snacks: ${data["breakdown"]["snacks"]:,}
• Dairy: ${data["breakdown"]["dairy"]:,}

**Star Products:**"""

        for product in data["top_performers"]:
            response_text += f"\n• {product['product']}: ${product['revenue']:,} ({product['growth']:+.1f}% growth)"

        response_text += "\n\n**Regional Leaders:**"
        for region, metrics in data["regional_breakdown"].items():
            response_text += f"\n• {region.title()}: ${metrics['revenue']:,} ({metrics['growth']:+.1f}%)"

        return {
            "response": response_text,
            "data": data,
            "suggestions": get_suggestions("revenue"),
        }

    def _create_promotion_response(self, message: str) -> dict[str, Any]:
        """Create a promotion-focused response with campaign data."""
        data = get_promotion_data()

        response_text = f"""Here's your promotion analysis for {data["period"]}:

🎯 **Campaign Overview:** {data["active_promotions"]} active promotions
💰 **Total Investment:** ${data["total_investment"]:,}
📈 **Incremental Revenue:** ${data["total_incremental_revenue"]:,}
🔥 **Overall ROI:** {data["roi"]:.1f}x

**Top Performing Campaigns:**"""

        for campaign in data["campaigns"][:3]:  # Show top 3
            response_text += (
                f"\n• **{campaign['name']}** ({campaign['category'].title()})"
            )
            response_text += f"\n  - ROI: {campaign['roi']:.1f}x | Revenue: ${campaign['incremental_revenue']:,}"
            response_text += f"\n  - {campaign['units_sold']:,} units sold"

        response_text += "\n\n**Key Metrics:**"
        metrics = data["performance_metrics"]
        response_text += (
            f"\n• Customer Acquisition: +{metrics['customer_acquisition']:.1f}%"
        )
        response_text += (
            f"\n• Retention Improvement: +{metrics['retention_improvement']:.1f}%"
        )
        response_text += (
            f"\n• Basket Size Increase: +{metrics['basket_size_increase']:.1f}%"
        )

        return {
            "response": response_text,
            "data": data,
            "suggestions": get_suggestions("promotion"),
        }

    def _create_pricing_response(self, message: str) -> dict[str, Any]:
        """Create a pricing-focused response with competitive analysis."""
        data = get_pricing_data()

        response_text = f"""Here's your pricing analysis for {data["period"]}:

💡 **Optimization Opportunities:** {data["price_optimization_opportunities"]} identified
📈 **Potential Revenue Uplift:** ${data["potential_revenue_uplift"]:,}
🏆 **Competitive Position:** {data["competitive_position"].title()}

**Product Pricing Analysis:**"""

        for product in data["products"]:
            action_emoji = "⬆️" if product["recommended_action"] == "increase" else "➡️"
            response_text += f"\n{action_emoji} **{product['name']}**"
            response_text += f"\n  - Current: ${product['current_price']:.2f} | Competitor Avg: ${product['competitor_avg']:.2f}"
            response_text += f"\n  - Position: {product['market_position'].title()}"
            if product["potential_uplift"] > 0:
                response_text += f" | Uplift: +{product['potential_uplift']:.1f}%"

        response_text += "\n\n**Market Insights:**"
        market = data["market_analysis"]
        response_text += f"\n• Price Sensitivity: {market['price_sensitivity'].title()}"
        response_text += f"\n• Competition: {market['competitive_intensity'].title()}"
        response_text += (
            f"\n• Premium Opportunity: {market['premium_opportunity'].title()}"
        )

        return {
            "response": response_text,
            "data": data,
            "suggestions": get_suggestions("pricing"),
        }

    def _create_product_response(self, message: str) -> dict[str, Any]:
        """Create a product-focused response with performance breakdown."""
        data = get_product_data()

        response_text = f"""Here's your product performance for {data["period"]}:

📦 **Portfolio Overview:** {data["total_products"]} products across {data["categories"]} categories
⭐ **Star Performers:** {data["star_performers"]} products
⚠️ **Need Attention:** {data["underperformers"]} products

**Category Performance:**"""

        for category in data["category_performance"]:
            trend_emoji = (
                "🚀"
                if category["trend"] == "growing"
                else "📈"
                if category["trend"] == "stable"
                else "🔄"
            )
            response_text += f"\n{trend_emoji} **{category['category'].title()}**"
            response_text += f"\n  - Revenue: ${category['revenue']:,} ({category['growth']:+.1f}% growth)"
            response_text += f"\n  - Market Share: {category['market_share']:.1f}% | {category['products']} products"

        response_text += "\n\n**Growth Opportunities:**"
        for opportunity in data["growth_opportunities"]:
            response_text += f"\n💡 **{opportunity['category'].title()}:** {opportunity['opportunity']}"
            response_text += f"\n  - Potential: ${opportunity['potential_revenue']:,} | Investment: ${opportunity['investment_required']:,}"
            response_text += f"\n  - Timeline: {opportunity['timeline']}"

        return {
            "response": response_text,
            "data": data,
            "suggestions": get_suggestions("product"),
        }

    def _create_help_response(self, message: str) -> dict[str, Any]:
        """Create a help response with guidance."""
        response_text = """I'm your RGM (Revenue Growth Management) assistant! I can help you with:

🔍 **What I can analyze:**
• **Revenue Performance** - Growth rates, regional breakdown, top performers
• **Promotion Analysis** - Campaign ROI, effectiveness metrics, optimization
• **Pricing Strategy** - Competitive positioning, elasticity, opportunities
• **Product Insights** - Category performance, market share, growth opportunities

💬 **Try asking me:**
• "Show me our revenue performance"
• "How are our promotions doing?"
• "What's our pricing strategy?"
• "Which products are top performers?"
• "What growth opportunities do we have?"

📊 **I provide:**
• Real-time data and insights
• Actionable recommendations
• Competitive analysis
• Performance trends

What would you like to explore first?"""

        return {
            "response": response_text,
            "data": {
                "available_categories": [
                    cat.value
                    for cat in QueryCategory
                    if cat not in [QueryCategory.UNKNOWN, QueryCategory.HELP]
                ],
                "sample_queries": [
                    "Show me revenue performance",
                    "How are promotions doing?",
                    "What's our pricing strategy?",
                    "Which products are top performers?",
                ],
            },
            "suggestions": get_suggestions("default"),
        }

    def _create_default_response(self, message: str) -> dict[str, Any]:
        """Create a default response for unrecognized queries."""
        # Check if query is ambiguous
        if self.keyword_matcher.is_ambiguous_query(message):
            response_text = """I found multiple topics in your question. Could you be more specific?

I can help you with:
• **Revenue** - Performance, growth, regional breakdown
• **Promotions** - Campaign ROI, effectiveness, optimization
• **Pricing** - Strategy, competitive analysis, opportunities
• **Products** - Performance, market share, growth opportunities

Try asking about one specific area, like "Show me revenue performance" or "How are promotions doing?"."""
        else:
            response_text = """I'm not sure I understand that question. I specialize in revenue, sales, and promotion analysis.

🔍 **I can help you with:**
• Revenue performance and growth analysis
• Promotion effectiveness and ROI
• Pricing strategy and competitive positioning
• Product performance and opportunities

💬 **Try asking:**
• "What's our revenue this quarter?"
• "How are our promotions performing?"
• "Show me pricing analysis"
• "Which products are doing well?"

What specific insights would you like to see?"""

        return {
            "response": response_text,
            "data": {
                "query_category": "unrecognized",
                "available_help": True,
                "context_suggestions": self._get_context_suggestions(),
            },
            "suggestions": get_suggestions("default"),
        }

    def _update_context_history(self, category: QueryCategory) -> None:
        """Update the context history with the latest query category."""
        if category != QueryCategory.UNKNOWN:
            self._context_history.append(category)
            # Keep only the last N queries
            if len(self._context_history) > self._max_history:
                self._context_history.pop(0)

    def _get_context_suggestions(self) -> list[str]:
        """Get context-aware suggestions based on query history."""
        if not self._context_history:
            return get_suggestions("default")

        # Get suggestions based on the most recent category
        recent_category = self._context_history[-1]
        return get_suggestions(recent_category.value)

    def get_available_categories(self) -> list[str]:
        """
        Get list of available query categories.

        Returns:
            List of available category names
        """
        return [
            cat.value for cat in QueryCategory if cat not in [QueryCategory.UNKNOWN]
        ]

    def get_query_examples(self) -> dict[str, list[str]]:
        """
        Get example queries for each category.

        Returns:
            Dictionary mapping categories to example queries
        """
        return {
            "revenue": [
                "What's our revenue this quarter?",
                "Show me revenue growth",
                "How are we performing vs target?",
                "Which regions have the best revenue?",
            ],
            "promotion": [
                "How are our promotions doing?",
                "What's the ROI on our campaigns?",
                "Show me promotion effectiveness",
                "Which promotions are most successful?",
            ],
            "pricing": [
                "What's our pricing strategy?",
                "How do we compare to competitors?",
                "Show me pricing opportunities",
                "What's our price positioning?",
            ],
            "product": [
                "Which products are top performers?",
                "Show me product performance",
                "What are our growth opportunities?",
                "How are our categories doing?",
            ],
        }

    def get_performance_stats(self) -> dict[str, Any]:
        """
        Get performance statistics for monitoring.

        Returns:
            Dictionary with performance metrics
        """
        return {
            "total_categories": len(QueryCategory) - 1,  # Exclude UNKNOWN
            "context_history_size": len(self._context_history),
            "max_history_size": self._max_history,
            "available_templates": len(self._response_templates),
        }
