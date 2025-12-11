"""
Intelligence Processors Package
Focused modules for processing different data sources
"""

from solairus_intelligence.core.processors.base import (
    BaseProcessor,
    IntelligenceItem,
    SectorIntelligence,
)
from solairus_intelligence.core.processors.ergomind import ErgoMindProcessor
from solairus_intelligence.core.processors.fred import FREDProcessor
from solairus_intelligence.core.processors.gta import GTAProcessor
from solairus_intelligence.core.processors.merger import IntelligenceMerger

__all__ = [
    "IntelligenceItem",
    "SectorIntelligence",
    "BaseProcessor",
    "ErgoMindProcessor",
    "GTAProcessor",
    "FREDProcessor",
    "IntelligenceMerger",
]
