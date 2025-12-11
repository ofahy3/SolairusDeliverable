"""
Intelligence Processing - Public API

Re-exports from the processors package for backwards compatibility.
"""

from solairus_intelligence.config.clients import ClientSector, CLIENT_SECTOR_MAPPING
from solairus_intelligence.core.processors.base import IntelligenceItem, SectorIntelligence
from solairus_intelligence.core.processors.ergomind import ErgoMindProcessor
from solairus_intelligence.core.processors.gta import GTAProcessor
from solairus_intelligence.core.processors.fred import FREDProcessor
from solairus_intelligence.core.processors.merger import IntelligenceMerger

__all__ = [
    "ClientSector",
    "CLIENT_SECTOR_MAPPING",
    "IntelligenceItem",
    "SectorIntelligence",
    "ErgoMindProcessor",
    "GTAProcessor",
    "FREDProcessor",
    "IntelligenceMerger",
]
