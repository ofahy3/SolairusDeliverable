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


class IntelligenceProcessor:
    """
    Facade for processing intelligence from multiple sources.

    Coordinates ErgoMind, GTA, and FRED processors with intelligent merging.
    """

    def __init__(self):
        self.ergomind = ErgoMindProcessor()
        self.gta = GTAProcessor()
        self.fred = FREDProcessor()
        self.merger = IntelligenceMerger()

        # Backwards compatibility aliases
        self.client_mapping = CLIENT_SECTOR_MAPPING
        self.relevance_keywords = self.ergomind.RELEVANCE_KEYWORDS

    async def process_intelligence_async(self, raw_text: str, category: str = "general") -> IntelligenceItem:
        """Process ErgoMind intelligence asynchronously."""
        return await self.ergomind.process_intelligence_async(raw_text, category)

    def process_intelligence(self, raw_text: str, category: str = "general") -> IntelligenceItem:
        """Process ErgoMind intelligence synchronously."""
        return self.ergomind.process_intelligence(raw_text, category)

    def process_gta_intervention(self, intervention, category: str = "trade_intervention") -> IntelligenceItem:
        """Convert a GTA intervention into an IntelligenceItem."""
        return self.gta.process_intervention(intervention, category)

    def process_fred_observation(self, observation, category: str) -> IntelligenceItem:
        """Convert FRED economic data into an IntelligenceItem."""
        return self.fred.process_observation(observation, category)

    def merge_intelligence_sources(self, *source_lists) -> list:
        """Merge multiple intelligence sources with deduplication."""
        return self.merger.merge_sources(*source_lists)

    def organize_by_sector(self, items: list) -> dict:
        """Organize intelligence items by client sector."""
        return self.merger.organize_by_sector(items)


__all__ = [
    "ClientSector",
    "CLIENT_SECTOR_MAPPING",
    "IntelligenceItem",
    "SectorIntelligence",
    "IntelligenceProcessor",
    "ErgoMindProcessor",
    "GTAProcessor",
    "FREDProcessor",
    "IntelligenceMerger",
]
