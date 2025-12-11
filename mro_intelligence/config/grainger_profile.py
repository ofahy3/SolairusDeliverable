"""
Grainger Company Profile and Report Configuration

This module contains Grainger-specific parameters that drive
query filtering, relevance scoring, and report generation.

Client Contact: Jenna Anderson (VP of Strategy, Analytics, and Technology Finance)
Workflow: Sends weekly insights newsletter to DG (CEO) and Nancy (CLO)
Renewal date: March 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set


# =============================================================================
# COMPANY PROFILE
# =============================================================================

COMPANY_PROFILE: Dict = {
    "name": "Grainger",
    "full_name": "W.W. Grainger, Inc.",
    "business_model": "MRO (Maintenance, Repair & Operations) distribution",
    "primary_market": "United States (USMCA region)",
    "key_segments": [
        "Manufacturing (industrial/factory customers - largest segment)",
        "Government (federal, state, military - $2B+ revenue, $400M military)",
        "Commercial facilities (office, retail, hospitality, healthcare)",
        "Contractors (construction, electrical, plumbing, HVAC)",
    ],
    "value_proposition": "Same-day/next-day delivery of MRO supplies",
    "geographic_focus": "US domestic with limited Canada/Mexico operations",
    "supply_chain_exposure": {
        "china_cogs_percent": 20,  # 20% of COGS from China - tariff sensitive
        "critical_commodities": ["steel", "aluminum", "plastics"],
    },
    "competitive_context": {
        "primary_threat": "Amazon Business ($25B in sales)",
        "competitive_keywords": ["amazon business", "industrial marketplace", "B2B ecommerce", "MRO pricing pressure"],
    },
    "not_interested_in": [
        "International expansion beyond USMCA",
        "Long-term geopolitical forecasts (>6 months)",
        "Generic geopolitical commentary without MRO implications",
        "Sectors outside their customer base",
    ],
}


# =============================================================================
# REPORT SETTINGS
# Jenna sends a "weekly insights newsletter" to leadership (DG CEO, Nancy CLO)
# Report should be easy for her to excerpt
# =============================================================================

REPORT_SETTINGS: Dict = {
    "lookback_months": 3,  # Pull Flashpoints data from last 3 months
    "forecast_horizon": "90 days",  # Near-term focus per Jenna's request
    "max_pages": 3,
    "update_frequency": "biweekly",  # Every 2 weeks per the call
    "delivery_format": "DOCX optimized for Google Docs",
}

# Report structure optimized for Jenna's weekly newsletter workflow
REPORT_STRUCTURE: Dict = {
    "executive_summary": {
        "title": "MRO Market Intelligence Summary",
        "description": "Top 3-4 findings with direct Grainger implications",
        "format": "Bullet points Jenna can copy into her newsletter",
        "max_items": 4,
    },
    "pricing_section": {
        "title": "Pricing & Cost Outlook",
        "content": [
            "Steel and aluminum price trends",
            "Tariff cost impacts",
            "Pricing pass-through recommendations",
        ],
        "jenna_question": "How much price should we be passing through?",
    },
    "demand_section": {
        "title": "MRO Demand Outlook",
        "content": [
            "Manufacturing activity trends",
            "Construction and capital project pipeline",
            "Government/defense spending outlook",
        ],
        "jenna_question": "What are outlooks for the US MRO market?",
    },
    "risk_section": {
        "title": "Supply Chain & Trade Risks",
        "content": [
            "China sourcing exposure (20% COGS)",
            "Tariff policy developments",
            "Logistics and shipping costs",
        ],
        "jenna_question": "What's happening with tariffs that would impact the MRO market?",
    },
}


# =============================================================================
# RELEVANCE FILTERS
# =============================================================================

RELEVANCE_FILTERS: Dict = {
    "must_include_keywords": [
        "US",
        "domestic",
        "manufacturing",
        "industrial",
        "MRO",
        "supply chain",
        "construction",
        "maintenance",
        "repair",
        "operations",
        "equipment",
        "facilities",
        "contractor",
    ],
    "exclude_keywords": [
        "aviation",
        "aerospace",
        "defense",
        "international expansion",
        "global footprint",
        "emerging markets",
        "asia pacific",
        "EMEA",
        "africa",
    ],
    "minimum_relevance_score": 0.6,
}


# =============================================================================
# GEOGRAPHIC FOCUS
# Grainger: "Most of our business is focused in North America"
# "Geopolitical insights don't pertain as much to our business" (unless trade-related to US)
# =============================================================================

GEOGRAPHIC_FOCUS: Dict = {
    "primary_regions": ["United States", "US", "USA", "America", "domestic"],
    "secondary_regions": ["Canada", "Mexico", "USMCA", "North America"],
    "exclude_regions": [
        # Only exclude if NOT trade-related to US
        "Europe",
        "EU",
        "Asia Pacific",
        "Middle East",
        "Africa",
        "Latin America",
        "APAC",
        "EMEA",
    ],
    # International content ONLY relevant if it directly impacts US MRO market
    "international_relevance_context": [
        "tariff",
        "trade",
        "supply chain",
        "sourcing",
        "import",
        "export",
        "Section 301",
        "Section 232",
    ],
    "region_relevance_boost": {
        "US": 0.3,
        "USA": 0.3,
        "United States": 0.3,
        "domestic": 0.25,
        "America": 0.2,
        "USMCA": 0.2,
        "Canada": 0.1,
        "Mexico": 0.1,
        "North America": 0.15,
    },
}


def filter_for_geographic_relevance(content: str) -> bool:
    """
    Filter content to focus on US/USMCA impacts.
    International content only relevant if it directly impacts US MRO market.

    Args:
        content: Text content to evaluate

    Returns:
        True if content is geographically relevant for Grainger
    """
    content_lower = content.lower()

    # Always include if mentions primary US regions
    for region in GEOGRAPHIC_FOCUS["primary_regions"]:
        if region.lower() in content_lower:
            return True

    # Always include if mentions secondary USMCA regions
    for region in GEOGRAPHIC_FOCUS["secondary_regions"]:
        if region.lower() in content_lower:
            return True

    # Check if international content has US trade relevance
    has_excluded_region = any(
        region.lower() in content_lower
        for region in GEOGRAPHIC_FOCUS["exclude_regions"]
    )

    if has_excluded_region:
        # Only include if it has trade/tariff context that affects US
        has_trade_context = any(
            context.lower() in content_lower
            for context in GEOGRAPHIC_FOCUS["international_relevance_context"]
        )
        return has_trade_context

    # Default: include if no explicit regional focus (general economic content)
    return True


# =============================================================================
# "SO WHAT FOR GRAINGER" ANALYSIS PROMPT
# This prompt guides AI generation of Grainger-specific implications
# Answers Jenna's question: "How does this affect Grainger's MRO business?"
# =============================================================================

SO_WHAT_PROMPT: str = """
For each intelligence item, provide a "Grainger Implication" that answers:
1. How does this affect MRO DEMAND from Grainger's customers?
   - Manufacturing (factory customers)
   - Government (federal, state, military - $2B+ segment)
   - Commercial Facilities (office, retail, hospitality)
   - Contractors (construction, electrical, plumbing)

2. How does this affect Grainger's SUPPLY COSTS or sourcing?
   - 20% of COGS from China (tariff sensitive)
   - Steel pricing (critical commodity)
   - Aluminum pricing (critical commodity)

3. What PRICING or COMPETITIVE implications does this have?
   - Pricing pass-through opportunities/requirements
   - Amazon Business competitive dynamics

4. What should Grainger DO or WATCH based on this?
   - Specific, actionable recommendations
   - Timeframe for impact (immediate, 30-day, 90-day)

Keep implications specific and actionable. Avoid generic geopolitical commentary.
Jenna needs to connect these dots for her economic team and leadership.
Focus on US/USMCA impacts only (international only if trade-related to US).
"""


# =============================================================================
# SECTOR PRIORITIES
# =============================================================================

SECTOR_PRIORITIES: Dict[str, float] = {
    # Tier 1: Core MRO demand drivers
    "manufacturing": 1.0,
    "industrial": 1.0,
    "construction": 0.95,
    "facilities": 0.9,
    # Tier 2: Important sectors
    "energy": 0.85,
    "utilities": 0.85,
    "transportation": 0.8,
    "logistics": 0.8,
    "warehousing": 0.8,
    # Tier 3: Secondary sectors
    "agriculture": 0.7,
    "food processing": 0.7,
    "government": 0.75,
    "institutional": 0.75,
    "healthcare facilities": 0.7,
    # Lower priority
    "retail": 0.5,
    "hospitality": 0.4,
    "financial services": 0.3,
    "technology": 0.4,
}


# =============================================================================
# DATACLASS FOR TYPE-SAFE ACCESS
# =============================================================================


@dataclass
class GraingerConfig:
    """
    Type-safe configuration for Grainger-specific parameters.
    Use this class for programmatic access to configuration.
    """

    # Company info
    company_name: str = COMPANY_PROFILE["name"]
    full_name: str = COMPANY_PROFILE["full_name"]
    business_model: str = COMPANY_PROFILE["business_model"]
    primary_market: str = COMPANY_PROFILE["primary_market"]
    key_segments: List[str] = field(
        default_factory=lambda: COMPANY_PROFILE["key_segments"]
    )
    geographic_focus: str = COMPANY_PROFILE["geographic_focus"]

    # Report settings
    lookback_months: int = REPORT_SETTINGS["lookback_months"]
    forecast_horizon: str = REPORT_SETTINGS["forecast_horizon"]
    max_pages: int = REPORT_SETTINGS["max_pages"]
    update_frequency: str = REPORT_SETTINGS["update_frequency"]

    # Relevance thresholds
    minimum_relevance_score: float = RELEVANCE_FILTERS["minimum_relevance_score"]
    must_include_keywords: List[str] = field(
        default_factory=lambda: RELEVANCE_FILTERS["must_include_keywords"]
    )
    exclude_keywords: List[str] = field(
        default_factory=lambda: RELEVANCE_FILTERS["exclude_keywords"]
    )

    def is_relevant_content(self, text: str) -> bool:
        """
        Check if content is relevant for Grainger based on keywords.

        Args:
            text: Content to check

        Returns:
            True if content passes relevance filters
        """
        text_lower = text.lower()

        # Check for excluded keywords
        for keyword in self.exclude_keywords:
            if keyword.lower() in text_lower:
                return False

        # Check for at least one must-include keyword
        for keyword in self.must_include_keywords:
            if keyword.lower() in text_lower:
                return True

        # If no must-include found, still allow if score meets threshold
        return False

    def calculate_relevance_boost(self, text: str) -> float:
        """
        Calculate relevance score boost based on Grainger priorities.

        Args:
            text: Content to analyze

        Returns:
            Boost value to add to relevance score (0.0 to 0.5)
        """
        text_lower = text.lower()
        boost = 0.0

        # Geographic boost
        for region, region_boost in GEOGRAPHIC_FOCUS["region_relevance_boost"].items():
            if region.lower() in text_lower:
                boost += region_boost
                break  # Only apply one geographic boost

        # Sector boost
        for sector, priority in SECTOR_PRIORITIES.items():
            if sector.lower() in text_lower:
                boost += (priority - 0.5) * 0.2  # Convert priority to boost
                break  # Only apply one sector boost

        # Keyword boost
        keyword_matches = sum(
            1 for kw in self.must_include_keywords if kw.lower() in text_lower
        )
        boost += min(keyword_matches * 0.05, 0.15)  # Cap at 0.15

        return min(boost, 0.5)  # Cap total boost at 0.5

    def should_exclude(self, text: str) -> bool:
        """
        Check if content should be excluded based on Grainger priorities.

        Args:
            text: Content to check

        Returns:
            True if content should be excluded
        """
        text_lower = text.lower()

        # Check excluded keywords
        for keyword in self.exclude_keywords:
            if keyword.lower() in text_lower:
                return True

        # Check excluded regions
        for region in GEOGRAPHIC_FOCUS["exclude_regions"]:
            # Only exclude if region is prominent (appears multiple times or in title)
            if text_lower.count(region.lower()) >= 2:
                return True

        return False


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global configuration instance
grainger_config = GraingerConfig()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_grainger_config() -> GraingerConfig:
    """Get the global Grainger configuration instance."""
    return grainger_config


def get_lookback_months() -> int:
    """Get the lookback period in months for data retrieval."""
    return REPORT_SETTINGS["lookback_months"]


def get_forecast_horizon() -> str:
    """Get the forecast horizon for reports."""
    return REPORT_SETTINGS["forecast_horizon"]


def get_minimum_relevance_score() -> float:
    """Get the minimum relevance score threshold."""
    return RELEVANCE_FILTERS["minimum_relevance_score"]


def get_must_include_keywords() -> List[str]:
    """Get keywords that should be included for relevance."""
    return RELEVANCE_FILTERS["must_include_keywords"]


def get_exclude_keywords() -> List[str]:
    """Get keywords that should trigger exclusion."""
    return RELEVANCE_FILTERS["exclude_keywords"]


def get_sector_priority(sector: str) -> float:
    """
    Get the priority weight for a given sector.

    Args:
        sector: Sector name to look up

    Returns:
        Priority weight (0.0 to 1.0)
    """
    return SECTOR_PRIORITIES.get(sector.lower(), 0.5)


def filter_for_grainger_relevance(
    items: List, min_score: float = None
) -> List:
    """
    Filter a list of items for Grainger relevance.

    Args:
        items: List of items with 'relevance_score' and content attributes
        min_score: Minimum score threshold (defaults to config value)

    Returns:
        Filtered list of relevant items
    """
    if min_score is None:
        min_score = get_minimum_relevance_score()

    filtered = []
    config = get_grainger_config()

    for item in items:
        # Skip if below minimum score
        if hasattr(item, "relevance_score") and item.relevance_score < min_score:
            continue

        # Get content for checking
        content = ""
        if hasattr(item, "processed_content"):
            content += item.processed_content
        if hasattr(item, "so_what_statement") and item.so_what_statement:
            content += " " + item.so_what_statement
        if hasattr(item, "raw_content"):
            content += " " + item.raw_content

        # Skip if should be excluded
        if content and config.should_exclude(content):
            continue

        filtered.append(item)

    return filtered
