"""
Intelligence Processing Engine
Main facade that orchestrates the focused processor modules

This module provides backwards compatibility while delegating
to focused processors in solairus_intelligence.core.processors/
"""

from typing import List, Dict, Optional
from dataclasses import replace

# Re-export from centralized config for backwards compatibility
from solairus_intelligence.config.clients import (
    ClientSector,
    CLIENT_SECTOR_MAPPING,
)

# Re-export from base processors for backwards compatibility
from solairus_intelligence.core.processors.base import (
    IntelligenceItem,
    SectorIntelligence,
)

# Import focused processors
from solairus_intelligence.core.processors.ergomind import ErgoMindProcessor
from solairus_intelligence.core.processors.gta import GTAProcessor
from solairus_intelligence.core.processors.fred import FREDProcessor
from solairus_intelligence.core.processors.merger import IntelligenceMerger


class IntelligenceProcessor:
    """
    Main intelligence processing engine - facade over focused processors

    Maintains backwards compatibility with existing code while delegating
    to specialized processors for each data source.
    """

    def __init__(self):
        self.ergomind_processor = ErgoMindProcessor()
        self.gta_processor = GTAProcessor()
        self.fred_processor = FREDProcessor()
        self.merger = IntelligenceMerger()

        # Backwards compatibility aliases
        self.client_mapping = CLIENT_SECTOR_MAPPING
        self.ai_generator = self.ergomind_processor.ai_generator
        self.relevance_keywords = self.ergomind_processor.RELEVANCE_KEYWORDS

    # =====================================================================
    # ErgoMind Processing (delegated)
    # =====================================================================

    async def process_intelligence_async(self, raw_text: str, category: str = "general") -> IntelligenceItem:
        """Process a single piece of raw ErgoMind intelligence (async)"""
        return await self.ergomind_processor.process_intelligence_async(raw_text, category)

    def process_intelligence(self, raw_text: str, category: str = "general") -> IntelligenceItem:
        """Process a single piece of raw ErgoMind intelligence (sync)"""
        return self.ergomind_processor.process_intelligence(raw_text, category)

    # =====================================================================
    # GTA Processing (delegated)
    # =====================================================================

    def process_gta_intervention(self, intervention, category: str = "trade_intervention") -> IntelligenceItem:
        """Convert a GTA intervention into an IntelligenceItem"""
        return self.gta_processor.process_intervention(intervention, category)

    # Backwards compatibility aliases
    def _calculate_gta_relevance(self, intervention) -> float:
        return self.gta_processor._calculate_relevance(intervention)

    def _generate_gta_so_what(self, intervention) -> str:
        return self.gta_processor._generate_so_what(intervention)

    def _map_gta_to_sectors(self, intervention) -> List[ClientSector]:
        return self.gta_processor._map_to_sectors(intervention)

    def _generate_gta_action_items(self, intervention, sectors: List[ClientSector]) -> List[str]:
        return self.gta_processor._generate_action_items(intervention, sectors)

    # =====================================================================
    # FRED Processing (delegated)
    # =====================================================================

    def process_fred_observation(self, observation, category: str) -> IntelligenceItem:
        """Convert FRED economic data observation to IntelligenceItem"""
        return self.fred_processor.process_observation(observation, category)

    # Backwards compatibility aliases
    def _format_fred_value(self, observation) -> str:
        return self.fred_processor._format_value(observation)

    def _calculate_fred_relevance(self, observation) -> float:
        return self.fred_processor._calculate_relevance(observation)

    def _generate_fred_so_what(self, observation) -> str:
        return self.fred_processor._generate_so_what(observation)

    def _map_fred_to_sectors(self, observation) -> List[ClientSector]:
        return self.fred_processor._map_to_sectors(observation)

    def _generate_fred_action_items(self, observation, sectors: List[ClientSector]) -> List[str]:
        return self.fred_processor._generate_action_items(observation, sectors)

    # =====================================================================
    # Merging and Organization (delegated)
    # =====================================================================

    def merge_intelligence_sources(self, *source_lists: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Intelligently merge multiple intelligence sources"""
        return self.merger.merge_sources(*source_lists)

    def organize_by_sector(self, items: List[IntelligenceItem]) -> Dict[ClientSector, SectorIntelligence]:
        """Organize intelligence items by client sector"""
        return self.merger.organize_by_sector(items)

    # =====================================================================
    # Backwards Compatibility - Internal Methods
    # =====================================================================

    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score (0-1) for Solairus"""
        return self.ergomind_processor.calculate_base_relevance(text)

    def _identify_affected_sectors(self, text: str) -> List[ClientSector]:
        """Identify which client sectors are affected"""
        return self.ergomind_processor._identify_affected_sectors(text)

    def _generate_action_items(self, text: str, sectors: List[ClientSector]) -> List[str]:
        """Generate action items"""
        return self.ergomind_processor._generate_action_items(text, sectors)

    def _calculate_confidence(self, processed_content: str) -> float:
        """Calculate confidence in the processed intelligence"""
        return self.ergomind_processor._calculate_confidence(processed_content)

    def _generate_so_what(self, text: str, category: str, item: Optional[IntelligenceItem] = None) -> str:
        """Generate 'So What' statement"""
        return self.ergomind_processor._generate_so_what(text, category, item)

    def _generate_so_what_template(self, text: str, category: str) -> str:
        """Template-based 'So What' generator"""
        return self.ergomind_processor._generate_so_what_template(text, category)

    def _clean_and_structure(self, text: str) -> str:
        """Clean and structure raw text"""
        return self.ergomind_processor._clean_and_structure(text)

    def _extract_key_sentences(self, sentences: List[str]) -> List[str]:
        """Extract key sentences"""
        return self.ergomind_processor._extract_key_sentences(sentences)

    def _initialize_client_mapping(self) -> Dict[ClientSector, Dict]:
        """Get client mapping from centralized config"""
        return CLIENT_SECTOR_MAPPING

    def _initialize_relevance_keywords(self) -> Dict[str, List[str]]:
        """Get relevance keywords"""
        return self.ergomind_processor.RELEVANCE_KEYWORDS

    # Merger methods
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        return self.merger._calculate_similarity(content1, content2)

    def _apply_source_priority(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        return self.merger._apply_source_priority(items)

    def _generate_sector_summary(self, sector: ClientSector, items: List[IntelligenceItem]) -> str:
        return self.merger._generate_sector_summary(sector, items)

    def _extract_risks(self, items: List[IntelligenceItem]) -> List[str]:
        return self.merger._extract_risks(items)

    def _extract_opportunities(self, items: List[IntelligenceItem]) -> List[str]:
        return self.merger._extract_opportunities(items)
