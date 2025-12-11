"""
Configuration module for Solairus Intelligence
Single source of truth for client mappings and application constants
"""

from solairus_intelligence.config.clients import (
    CLIENT_SECTOR_MAPPING,
    COMPANY_NAMES_BY_SECTOR,
    get_all_company_names,
    get_companies_for_sector,
)

__all__ = [
    "CLIENT_SECTOR_MAPPING",
    "COMPANY_NAMES_BY_SECTOR",
    "get_all_company_names",
    "get_companies_for_sector",
]
