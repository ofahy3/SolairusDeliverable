"""
Client Configuration - Single Source of Truth

This module defines all client-related mappings used throughout the application.
Consolidates data previously duplicated in processor.py and pii_sanitizer.py.
"""

from enum import Enum
from typing import Dict, List, Set


class ClientSector(Enum):
    """Client industry sectors"""

    TECHNOLOGY = "technology"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    ENTERTAINMENT = "entertainment"
    ENERGY = "energy"
    HEALTHCARE = "healthcare"
    GENERAL = "general"


# Master client-to-sector mapping with all relevant metadata
CLIENT_SECTOR_MAPPING: Dict[ClientSector, Dict] = {
    ClientSector.TECHNOLOGY: {
        "companies": ["Cisco", "Palantir", "NantWorks", "Pluralsight"],
        "keywords": [
            "technology",
            "silicon valley",
            "semiconductor",
            "AI",
            "cyber",
            "data",
            "software",
            "cloud",
            "digital",
            "innovation",
            "startup",
        ],
        "geopolitical_triggers": [
            "US-China",
            "export controls",
            "data sovereignty",
            "CHIPS Act",
            "technology transfer",
            "intellectual property",
            "sanctions",
        ],
    },
    ClientSector.FINANCE: {
        "companies": [
            "ICONIQ Capital",
            "Vista Equity",
            "Affinius Capital",
            "Ribbit Management",
            "ArcLight Capital",
        ],
        "keywords": [
            "financial",
            "investment",
            "private equity",
            "capital markets",
            "interest rates",
            "inflation",
            "banking",
            "credit",
            "currency",
            "M&A",
            "IPO",
            "valuation",
        ],
        "geopolitical_triggers": [
            "central bank",
            "Federal Reserve",
            "ECB",
            "monetary policy",
            "Basel",
            "financial regulation",
            "capital controls",
            "sovereign debt",
        ],
    },
    ClientSector.REAL_ESTATE: {
        "companies": [
            "Presidium Development",
            "Restoration Hardware",
            "Grassy Creek",
            "Bay Grove Capital",
        ],
        "keywords": [
            "real estate",
            "construction",
            "property",
            "development",
            "infrastructure",
            "urban",
            "commercial",
            "residential",
            "REIT",
        ],
        "geopolitical_triggers": [
            "zoning",
            "housing policy",
            "infrastructure spending",
            "construction costs",
            "supply chain",
            "materials",
            "labor",
        ],
    },
    ClientSector.ENTERTAINMENT: {
        "companies": ["WME IMG", "Anheuser-Busch InBev"],
        "keywords": [
            "entertainment",
            "media",
            "sports",
            "content",
            "streaming",
            "production",
            "talent",
            "broadcasting",
            "gaming",
        ],
        "geopolitical_triggers": [
            "content regulation",
            "censorship",
            "cultural policy",
            "international co-production",
            "talent mobility",
            "visa",
        ],
    },
    ClientSector.ENERGY: {
        "companies": ["ArcLight Capital Partners"],
        "keywords": [
            "energy",
            "oil",
            "gas",
            "renewable",
            "solar",
            "wind",
            "petroleum",
            "electricity",
            "power",
            "utilities",
            "carbon",
        ],
        "geopolitical_triggers": [
            "OPEC",
            "energy security",
            "pipeline",
            "sanctions",
            "climate",
            "Paris Agreement",
            "energy transition",
            "grid",
            "LNG",
        ],
    },
    ClientSector.HEALTHCARE: {
        "companies": [],
        "keywords": [
            "healthcare",
            "pharmaceutical",
            "medical",
            "biotech",
            "clinical",
            "hospital",
            "health policy",
        ],
        "geopolitical_triggers": [
            "FDA",
            "drug pricing",
            "healthcare regulation",
            "pandemic",
            "medical supply chain",
        ],
    },
    ClientSector.GENERAL: {"companies": [], "keywords": [], "geopolitical_triggers": []},
}

# Flat mapping of company names to sectors for quick lookup
COMPANY_NAMES_BY_SECTOR: Dict[ClientSector, List[str]] = {
    sector: mapping["companies"] for sector, mapping in CLIENT_SECTOR_MAPPING.items()
}


def get_all_company_names() -> Set[str]:
    """Get all company names across all sectors"""
    all_names = set()
    for companies in COMPANY_NAMES_BY_SECTOR.values():
        all_names.update(companies)
    return all_names


def get_companies_for_sector(sector: ClientSector) -> List[str]:
    """Get company names for a specific sector"""
    return COMPANY_NAMES_BY_SECTOR.get(sector, [])


def get_sector_keywords(sector: ClientSector) -> List[str]:
    """Get keywords for a specific sector"""
    mapping = CLIENT_SECTOR_MAPPING.get(sector, {})
    keywords: List[str] = mapping.get("keywords", [])
    return keywords


def get_sector_triggers(sector: ClientSector) -> List[str]:
    """Get geopolitical triggers for a specific sector"""
    mapping = CLIENT_SECTOR_MAPPING.get(sector, {})
    triggers: List[str] = mapping.get("geopolitical_triggers", [])
    return triggers
