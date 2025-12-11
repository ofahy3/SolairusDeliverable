"""
Content extraction and parsing for MRO Intelligence Reports.

Extracts insights, themes, and structured content from intelligence items.
Integrates Grainger-specific filtering and relevance scoring.
"""

import re
from typing import Dict, List, Tuple

from mro_intelligence.config.grainger_profile import (
    RELEVANCE_FILTERS,
    get_grainger_config,
    get_minimum_relevance_score,
)
from mro_intelligence.core.processor import IntelligenceItem


class ContentExtractor:
    """
    Extracts and structures content from intelligence items.

    Handles parsing of themes, key findings, watch factors, and
    other analytical content from raw intelligence data.

    Integrates Grainger configuration for:
    - Filtering by minimum relevance score
    - Prioritizing US/USMCA content
    - Excluding non-MRO-relevant items
    """

    def __init__(self):
        """Initialize with Grainger configuration"""
        self.grainger_config = get_grainger_config()
        self.min_relevance = get_minimum_relevance_score()

    def extract_analytical_insights(self, items: List[IntelligenceItem]) -> Dict[str, List[str]]:
        """
        Extract analytical insights from intelligence items.

        Applies Grainger filtering:
        - Only includes items above minimum relevance threshold
        - Excludes items with non-Grainger-relevant content
        - Prioritizes US/USMCA and MRO-relevant items

        Returns:
            Dictionary with 'bottom_line', 'key_findings', 'watch_factors'
        """
        bottom_line: List[str] = []
        key_findings: List[str] = []
        watch_factors: List[str] = []

        # Filter items by Grainger relevance
        filtered_items = [
            item for item in items
            if item.relevance_score >= self.min_relevance
            and not self._should_exclude_for_grainger(item)
        ]

        # Sort items by relevance
        sorted_items = sorted(filtered_items, key=lambda x: x.relevance_score, reverse=True)

        # Extract insights from top items
        for item in sorted_items[:10]:
            if item.so_what_statement:
                # Categorize based on content
                statement = item.so_what_statement.strip()
                if self._is_bottom_line_worthy(item):
                    bottom_line.append(statement)
                elif self._is_watch_factor(item):
                    watch_factors.append(statement)
                else:
                    key_findings.append(statement)

        return {
            "bottom_line": bottom_line[:3],
            "key_findings": key_findings[:5],
            "watch_factors": watch_factors[:3],
        }

    def _should_exclude_for_grainger(self, item: IntelligenceItem) -> bool:
        """
        Check if an item should be excluded based on Grainger relevance filters.

        Args:
            item: Intelligence item to check

        Returns:
            True if item should be excluded
        """
        content = ""
        if item.processed_content:
            content += item.processed_content
        if item.so_what_statement:
            content += " " + item.so_what_statement

        return self.grainger_config.should_exclude(content)

    def _is_bottom_line_worthy(self, item: IntelligenceItem) -> bool:
        """Check if item is significant enough for bottom line"""
        return item.relevance_score >= 0.85 and item.confidence >= 0.8

    def _is_watch_factor(self, item: IntelligenceItem) -> bool:
        """Check if item should be categorized as watch factor"""
        watch_keywords = [
            "monitor",
            "watch",
            "emerging",
            "developing",
            "potential",
            "risk",
            "uncertainty",
            "volatile",
        ]
        content = (item.processed_content + " " + item.so_what_statement).lower()
        return any(kw in content for kw in watch_keywords)

    def extract_theme(self, text: str, so_what: str) -> str:
        """
        Extract the main theme from content.

        Args:
            text: Main content text
            so_what: So-what statement

        Returns:
            Extracted theme string
        """
        combined = f"{text} {so_what}".lower()

        # Theme detection keywords
        themes = {
            "Geopolitical Risk": ["conflict", "tension", "sanction", "war", "military"],
            "Economic Pressure": ["inflation", "recession", "gdp", "economic"],
            "Trade Policy": ["tariff", "trade", "export", "import", "policy"],
            "Supply Chain": ["supply", "chain", "shortage", "logistics"],
            "Regulatory": ["regulation", "compliance", "policy", "law"],
            "Market Volatility": ["volatility", "market", "price", "fluctuation"],
            "Technology": ["technology", "cyber", "digital", "innovation"],
        }

        for theme, keywords in themes.items():
            if any(kw in combined for kw in keywords):
                return theme

        return "Strategic Development"

    def craft_bottom_line_statement(self, item: IntelligenceItem) -> str:
        """
        Craft a compelling bottom line statement.

        Args:
            item: Intelligence item

        Returns:
            Formatted bottom line statement
        """
        if item.so_what_statement:
            statement = item.so_what_statement.strip()
            # Ensure it ends properly
            if not statement.endswith((".", "!", "?")):
                statement += "."
            return statement

        # Fallback to processed content summary
        content = item.processed_content[:200]
        if len(item.processed_content) > 200:
            content = content.rsplit(" ", 1)[0] + "..."
        return content

    def craft_key_finding_statement(self, item: IntelligenceItem) -> str:
        """
        Craft a key finding statement.

        Args:
            item: Intelligence item

        Returns:
            Formatted key finding statement
        """
        theme = self.extract_theme(item.processed_content, item.so_what_statement)

        # Build structured finding
        finding = f"{theme}: {item.so_what_statement}"

        return finding.strip()

    def craft_watch_factor_statement(self, item: IntelligenceItem) -> str:
        """
        Craft a watch factor statement.

        Args:
            item: Intelligence item

        Returns:
            Formatted watch factor statement
        """
        return f"Monitor: {item.so_what_statement}"

    def parse_key_finding(self, finding_text: str) -> Tuple[str, str, List[str]]:
        """
        Parse a key finding into components.

        Args:
            finding_text: Raw finding text

        Returns:
            Tuple of (header, description, bullets)
        """
        # Try to split on colon
        if ":" in finding_text:
            parts = finding_text.split(":", 1)
            header = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""
        else:
            header = "Key Development"
            description = finding_text.strip()

        # Generate contextual bullets
        bullets = self._generate_contextual_bullets(description.lower(), header, 2)

        return header, description, bullets

    def parse_watch_factor(self, factor_text: str) -> Tuple[str, str, List[str]]:
        """
        Parse a watch factor into components.

        Args:
            factor_text: Raw factor text

        Returns:
            Tuple of (title, description, bullets)
        """
        if ":" in factor_text:
            parts = factor_text.split(":", 1)
            title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""
        else:
            title = "Developing Situation"
            description = factor_text.strip()

        bullets = self._generate_contextual_bullets(description.lower(), title, 2)

        return title, description, bullets

    def _generate_contextual_bullets(
        self, text_lower: str, subheader: str, count: int
    ) -> List[str]:
        """
        Generate contextual bullet points for MRO market.

        Args:
            text_lower: Lowercase text to analyze
            subheader: Section subheader for context
            count: Number of bullets to generate

        Returns:
            List of bullet point strings
        """
        bullets: List[str] = []

        # MRO-focused context-aware bullet generation
        if "manufacturing" in text_lower or "industrial" in text_lower:
            bullets.append("Review inventory levels for manufacturing supplies")
            bullets.append("Monitor production indices for demand signals")
        elif "construction" in text_lower or "building" in text_lower:
            bullets.append("Track permit trends for construction supply demand")
            bullets.append("Assess contractor account activity")
        elif "economic" in text_lower or "market" in text_lower:
            bullets.append("Monitor economic indicators for MRO demand impact")
            bullets.append("Review pricing strategy assumptions")
        elif "tariff" in text_lower or "trade" in text_lower:
            bullets.append("Assess supplier exposure to trade policy changes")
            bullets.append("Review sourcing alternatives for affected products")
        elif "supply chain" in text_lower or "logistics" in text_lower:
            bullets.append("Monitor supplier lead times and availability")
            bullets.append("Review inventory buffer requirements")
        elif "energy" in text_lower or "oil" in text_lower:
            bullets.append("Track energy sector equipment demand")
            bullets.append("Monitor fuel cost impact on logistics")
        else:
            bullets.append("Continue monitoring for MRO demand implications")
            bullets.append("Assess potential impact on product categories")

        return bullets[:count]

    def strip_markdown(self, text: str) -> str:
        """
        Remove markdown formatting from text.

        Args:
            text: Text potentially containing markdown

        Returns:
            Clean text without markdown
        """
        if not text:
            return ""

        # Remove bold markers
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        # Remove italic markers
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        # Remove headers
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        # Remove bullet markers
        text = re.sub(r"^\s*[-*•]\s*", "", text, flags=re.MULTILINE)
        # Clean extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def extract_indicator_name(self, item: IntelligenceItem) -> str:
        """Extract economic indicator name from item"""
        category = item.category.lower()

        indicator_map = {
            "inflation": "CPI Inflation",
            "interest": "Interest Rate",
            "fuel": "Crude Oil Price",
            "gdp": "GDP Growth",
            "employment": "Employment",
            "confidence": "Consumer Confidence",
        }

        for key, name in indicator_map.items():
            if key in category:
                return name

        return "Economic Indicator"

    def extract_value(self, item: IntelligenceItem) -> str:
        """Extract value from item content"""
        content = item.processed_content

        # Look for percentage patterns
        percent_match = re.search(r"(\d+\.?\d*)\s*%", content)
        if percent_match:
            return f"{percent_match.group(1)}%"

        # Look for dollar patterns
        dollar_match = re.search(r"\$(\d+\.?\d*)", content)
        if dollar_match:
            return f"${dollar_match.group(1)}"

        # Look for any number
        num_match = re.search(r"(\d+\.?\d*)", content)
        if num_match:
            return num_match.group(1)

        return "N/A"

    def determine_trend(self, item: IntelligenceItem) -> str:
        """Determine trend direction from item"""
        content = (item.processed_content + " " + item.so_what_statement).lower()

        up_words = ["increase", "rise", "grew", "higher", "up", "gain"]
        down_words = ["decrease", "fall", "decline", "lower", "down", "drop"]

        if any(word in content for word in up_words):
            return "↑"
        elif any(word in content for word in down_words):
            return "↓"
        else:
            return "→"

    def generate_economic_impact(self, item: IntelligenceItem) -> str:
        """Generate impact statement for economic indicator"""
        if item.so_what_statement:
            # Truncate to reasonable length
            impact = item.so_what_statement[:100]
            if len(item.so_what_statement) > 100:
                impact = impact.rsplit(" ", 1)[0] + "..."
            return impact

        return "Monitor for operational impact"
