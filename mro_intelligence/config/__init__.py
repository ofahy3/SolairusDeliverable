"""
Configuration module for MRO Intelligence
Single source of truth for client mappings, content filtering, and Grainger profile
"""

from mro_intelligence.config.clients import (
    CLIENT_SECTOR_MAPPING,
    COMPANY_NAMES_BY_SECTOR,
    ClientSector,
    get_all_company_names,
    get_all_sectors,
    get_companies_for_sector,
    get_sector_keywords,
    get_sector_mro_impact,
    get_sector_triggers,
)
from mro_intelligence.config.content_blocklist import (
    BLOCKED_PATTERNS,
    BLOCKED_TERMS,
    check_content,
    is_content_clean,
    sanitize_content,
)

__all__ = [
    # Client sector mappings
    "CLIENT_SECTOR_MAPPING",
    "COMPANY_NAMES_BY_SECTOR",
    "ClientSector",
    "get_all_company_names",
    "get_all_sectors",
    "get_companies_for_sector",
    "get_sector_keywords",
    "get_sector_mro_impact",
    "get_sector_triggers",
    # Content blocklist
    "BLOCKED_PATTERNS",
    "BLOCKED_TERMS",
    "check_content",
    "is_content_clean",
    "sanitize_content",
]
