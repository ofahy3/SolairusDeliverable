"""
Client Configuration - Single Source of Truth for Grainger Customer Sectors

This module defines Grainger's actual customer segments for MRO market analysis.
These sectors represent Grainger's key customer base for MRO demand intelligence.

Per Grainger client dossier:
- Manufacturing: Industrial/factory customers (largest segment)
- Government: Federal, state, military ($2B gov business, $400M military)
- Commercial Facilities: Office buildings, retail, hospitality
- Contractors: Construction, electrical, plumbing contractors
"""

from enum import Enum
from typing import Dict, List, Set


class ClientSector(Enum):
    """Grainger's actual customer segments for MRO demand analysis"""

    MANUFACTURING = "manufacturing"      # Industrial/factory customers
    GOVERNMENT = "government"            # Federal, state, military ($2B gov biz, $400M military)
    COMMERCIAL_FACILITIES = "commercial" # Office buildings, retail, hospitality
    CONTRACTORS = "contractors"          # Construction, electrical, plumbing contractors
    GENERAL = "general"                  # Cross-sector analysis


# Master sector mapping with all relevant metadata for MRO market analysis
# "So What for Grainger" analysis should answer: "How does this affect MRO DEMAND from this customer segment?"
CLIENT_SECTOR_MAPPING: Dict[ClientSector, Dict] = {
    ClientSector.MANUFACTURING: {
        "companies": [],  # Grainger serves all manufacturing - no specific company focus
        "display_name": "Manufacturing",
        "description": "Industrial/factory customers - Grainger's largest segment",
        "keywords": [
            "industrial production",
            "factory output",
            "machinery",
            "equipment",
            "automation",
            "robotics",
            "manufacturing",
            "assembly",
            "fabrication",
            "production line",
            "OEM",
            "plant operations",
            "industrial equipment",
            "machine tools",
            "process manufacturing",
            "discrete manufacturing",
            "lean manufacturing",
            "quality control",
            "maintenance",
            "downtime",
            "spare parts",
            "reshoring",
            "nearshoring",
            "capex",
            "capital expenditure",
        ],
        "geopolitical_triggers": [
            "reshoring",
            "tariffs on industrial goods",
            "supply chain disruptions",
            "China manufacturing",
            "nearshoring",
            "USMCA",
            "trade war",
            "export controls",
            "industrial policy",
            "Made in America",
            "semiconductor shortage",
            "chip supply",
            "automation investments",
            "labor shortages",
            "factory construction",
            "steel tariffs",
            "aluminum tariffs",
            "China tariffs",
            "Section 301",
            "Section 232",
        ],
        "mro_demand_drivers": [
            "Production volume increases",
            "New facility construction",
            "Equipment maintenance cycles",
            "Safety compliance requirements",
            "Automation upgrades",
        ],
        "grainger_products": [
            "Safety equipment (PPE)",
            "Lubricants and chemicals",
            "Fasteners and hardware",
            "Material handling",
            "Power tools",
            "Motors and drives",
        ],
        "mro_impact": "Direct impact on MRO consumables, spare parts, safety equipment, and maintenance supplies. Production volume and capex directly correlate with MRO spend.",
    },
    ClientSector.GOVERNMENT: {
        "companies": [],
        "display_name": "Government",
        "description": "Federal, state, local government and military - $2B+ in Grainger revenue",
        "keywords": [
            "federal",
            "government",
            "military",
            "defense",
            "DoD",
            "Department of Defense",
            "GSA",
            "state government",
            "local government",
            "municipal",
            "public sector",
            "VA",
            "Veterans Affairs",
            "federal procurement",
            "government contracts",
            "base maintenance",
            "facility management",
            "public works",
            "infrastructure",
            "government spending",
            "fiscal policy",
            "budget",
            "appropriations",
        ],
        "geopolitical_triggers": [
            "defense budget",
            "federal spending",
            "infrastructure bill",
            "government shutdown",
            "continuing resolution",
            "procurement policy",
            "Buy American",
            "domestic sourcing",
            "military modernization",
            "base realignment",
            "BRAC",
            "federal hiring",
            "government efficiency",
            "GSA schedule",
            "NDAA",
            "defense authorization",
        ],
        "mro_demand_drivers": [
            "Defense budget changes",
            "Infrastructure spending bills",
            "Federal facility maintenance cycles",
            "Military base operations",
            "State/local budget allocations",
        ],
        "grainger_products": [
            "Facility maintenance supplies",
            "Safety and security equipment",
            "HVAC supplies",
            "Electrical supplies",
            "Plumbing materials",
            "Fleet maintenance",
        ],
        "mro_impact": "Government MRO demand driven by appropriations and spending bills. Defense and infrastructure budgets directly impact Grainger's $2B+ government business.",
    },
    ClientSector.COMMERCIAL_FACILITIES: {
        "companies": [],
        "display_name": "Commercial Facilities",
        "description": "Office buildings, retail, hospitality, healthcare facilities",
        "keywords": [
            "commercial real estate",
            "office building",
            "retail",
            "hospitality",
            "hotel",
            "hospital",
            "healthcare facility",
            "facility management",
            "building maintenance",
            "property management",
            "HVAC",
            "lighting",
            "janitorial",
            "cleaning",
            "elevator",
            "fire safety",
            "security systems",
            "building automation",
            "energy efficiency",
            "tenant improvements",
            "commercial construction",
            "office occupancy",
            "return to office",
        ],
        "geopolitical_triggers": [
            "interest rates",
            "commercial vacancy rates",
            "return to office",
            "remote work trends",
            "retail foot traffic",
            "hospitality recovery",
            "healthcare expansion",
            "building codes",
            "energy efficiency mandates",
            "ADA compliance",
            "fire safety regulations",
            "indoor air quality",
            "ESG requirements",
        ],
        "mro_demand_drivers": [
            "Commercial vacancy/occupancy rates",
            "Return-to-office trends",
            "Healthcare facility expansion",
            "Retail activity levels",
            "Building code compliance",
        ],
        "grainger_products": [
            "HVAC supplies and filters",
            "Lighting and electrical",
            "Janitorial supplies",
            "Plumbing fixtures",
            "Safety and security",
            "Building maintenance",
        ],
        "mro_impact": "Commercial facilities MRO demand tied to occupancy rates and economic activity. Interest rates affect new construction and renovation projects.",
    },
    ClientSector.CONTRACTORS: {
        "companies": [],
        "display_name": "Contractors",
        "description": "Construction, electrical, plumbing, HVAC contractors",
        "keywords": [
            "contractor",
            "construction",
            "electrical contractor",
            "plumbing contractor",
            "HVAC contractor",
            "general contractor",
            "subcontractor",
            "trades",
            "skilled trades",
            "electrician",
            "plumber",
            "building",
            "infrastructure",
            "renovation",
            "remodel",
            "new construction",
            "commercial construction",
            "residential construction",
            "industrial construction",
            "housing starts",
            "building permits",
            "construction spending",
            "project pipeline",
        ],
        "geopolitical_triggers": [
            "interest rates",
            "housing starts",
            "building permits",
            "construction spending",
            "infrastructure bill",
            "materials costs",
            "steel prices",
            "lumber prices",
            "labor availability",
            "immigration policy",
            "skilled trades shortage",
            "prevailing wage",
            "union labor",
            "building codes",
            "zoning regulations",
        ],
        "mro_demand_drivers": [
            "Housing starts and permits",
            "Commercial construction spending",
            "Infrastructure project pipeline",
            "Materials costs (affects project economics)",
            "Labor availability",
        ],
        "grainger_products": [
            "Power tools",
            "Hand tools",
            "Fasteners",
            "Electrical supplies",
            "Plumbing supplies",
            "Safety equipment (PPE)",
            "Ladders and scaffolding",
        ],
        "mro_impact": "Contractor demand directly tied to construction activity. Interest rates, housing starts, and infrastructure spending are leading indicators.",
    },
    ClientSector.GENERAL: {
        "companies": [],
        "display_name": "Cross-Sector",
        "description": "Analysis relevant across all Grainger customer segments",
        "keywords": [],
        "geopolitical_triggers": [],
        "mro_demand_drivers": [],
        "grainger_products": [],
        "mro_impact": "General MRO market trends affecting all customer segments",
    },
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


def get_sector_mro_impact(sector: ClientSector) -> str:
    """Get MRO impact description for a specific sector"""
    mapping = CLIENT_SECTOR_MAPPING.get(sector, {})
    impact: str = mapping.get("mro_impact", "")
    return impact


def get_all_sectors() -> List[ClientSector]:
    """Get all active MRO sectors (excluding GENERAL)"""
    return [s for s in ClientSector if s != ClientSector.GENERAL]
