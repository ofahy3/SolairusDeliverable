"""
Intelligence Processing - Public API

Re-exports from the processors package for backwards compatibility.
"""

from mro_intelligence.config.clients import CLIENT_SECTOR_MAPPING, ClientSector
from mro_intelligence.core.processors.base import IntelligenceItem, SectorIntelligence
from mro_intelligence.core.processors.ergomind import ErgoMindProcessor
from mro_intelligence.core.processors.fred import FREDProcessor
from mro_intelligence.core.processors.gta import GTAProcessor
from mro_intelligence.core.processors.merger import IntelligenceMerger

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
