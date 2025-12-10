"""
Intelligence Processing Engine
Main facade that orchestrates the focused processor modules

This module provides backwards compatibility while delegating
to focused processors in solairus_intelligence.core.processors/
"""

from typing import List, Dict, Optional, Any, cast
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
        result = await self.ergomind_processor.process_intelligence_async(raw_text, category)
        return cast(IntelligenceItem, result)

    def process_intelligence(self, raw_text: str, category: str = "general") -> IntelligenceItem:
        """Process a single piece of raw ErgoMind intelligence (sync)"""
        result = self.ergomind_processor.process_intelligence(raw_text, category)
        return cast(IntelligenceItem, result)

    # =====================================================================
    # GTA Processing (delegated)
    # =====================================================================

    def process_gta_intervention(self, intervention: Any, category: str = "trade_intervention") -> IntelligenceItem:
        """Convert a GTA intervention into an IntelligenceItem"""
        result = self.gta_processor.process_intervention(intervention, category)
        return cast(IntelligenceItem, result)

    # Backwards compatibility aliases
    def _calculate_gta_relevance(self, intervention: Any) -> float:
        result = self.gta_processor._calculate_relevance(intervention)
        return cast(float, result)

    def _generate_gta_so_what(self, intervention: Any) -> str:
        result = self.gta_processor._generate_so_what(intervention)
        return cast(str, result)

    def _map_gta_to_sectors(self, intervention: Any) -> List[ClientSector]:
        result = self.gta_processor._map_to_sectors(intervention)
        return cast(List[ClientSector], result)

    def _generate_gta_action_items(self, intervention: Any, sectors: List[ClientSector]) -> List[str]:
        result = self.gta_processor._generate_action_items(intervention, sectors)
        return cast(List[str], result)

    # =====================================================================
    # FRED Processing (delegated)
    # =====================================================================

    def process_fred_observation(self, observation: Any, category: str) -> IntelligenceItem:
        """Convert FRED economic data observation to IntelligenceItem"""
        result = self.fred_processor.process_observation(observation, category)
        return cast(IntelligenceItem, result)

    # Backwards compatibility aliases
    def _format_fred_value(self, observation: Any) -> str:
        result = self.fred_processor._format_value(observation)
        return cast(str, result)

    def _calculate_fred_relevance(self, observation: Any) -> float:
        result = self.fred_processor._calculate_relevance(observation)
        return cast(float, result)

    def _generate_fred_so_what(self, observation: Any) -> str:
        result = self.fred_processor._generate_so_what(observation)
        return cast(str, result)

    def _map_fred_to_sectors(self, observation: Any) -> List[ClientSector]:
        result = self.fred_processor._map_to_sectors(observation)
        return cast(List[ClientSector], result)

    def _generate_fred_action_items(self, observation: Any, sectors: List[ClientSector]) -> List[str]:
        result = self.fred_processor._generate_action_items(observation, sectors)
        return cast(List[str], result)

    # =====================================================================
    # Merging and Organization (delegated)
    # =====================================================================

    def merge_intelligence_sources(self, *source_lists: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Intelligently merge multiple intelligence sources"""
        result = self.merger.merge_sources(*source_lists)
        return cast(List[IntelligenceItem], result)

    def organize_by_sector(self, items: List[IntelligenceItem]) -> Dict[ClientSector, SectorIntelligence]:
        """Organize intelligence items by client sector"""
        result = self.merger.organize_by_sector(items)
        return cast(Dict[ClientSector, SectorIntelligence], result)

    # =====================================================================
    # Backwards Compatibility - Internal Methods
    # =====================================================================

    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score (0-1) for Solairus"""
        result = self.ergomind_processor.calculate_base_relevance(text)
        return cast(float, result)

    def _identify_affected_sectors(self, text: str) -> List[ClientSector]:
        """Identify which client sectors are affected"""
        result = self.ergomind_processor._identify_affected_sectors(text)
        return cast(List[ClientSector], result)

    def _generate_action_items(self, text: str, sectors: List[ClientSector]) -> List[str]:
        """Generate action items"""
        result = self.ergomind_processor._generate_action_items(text, sectors)
        return cast(List[str], result)

    def _calculate_confidence(self, processed_content: str) -> float:
        """Calculate confidence in the processed intelligence"""
        result = self.ergomind_processor._calculate_confidence(processed_content)
        return cast(float, result)

    def _generate_so_what(self, text: str, category: str, item: Optional[IntelligenceItem] = None) -> str:
        """Generate 'So What' statement"""
        result = self.ergomind_processor._generate_so_what(text, category, item)
        return cast(str, result)

    def _generate_so_what_template(self, text: str, category: str) -> str:
        """Template-based 'So What' generator"""
        result = self.ergomind_processor._generate_so_what_template(text, category)
        return cast(str, result)

    def _clean_and_structure(self, text: str) -> str:
        """Clean and structure raw text"""
        result = self.ergomind_processor._clean_and_structure(text)
        return cast(str, result)

    def _extract_key_sentences(self, sentences: List[str]) -> List[str]:
        """Extract key sentences"""
        result = self.ergomind_processor._extract_key_sentences(sentences)
        return cast(List[str], result)

    def _initialize_client_mapping(self) -> Dict[ClientSector, Dict[str, List[str]]]:
        """Get client mapping from centralized config"""
        return CLIENT_SECTOR_MAPPING

    def _initialize_relevance_keywords(self) -> Dict[str, List[str]]:
        """Get relevance keywords"""
        result = self.ergomind_processor.RELEVANCE_KEYWORDS
        return cast(Dict[str, List[str]], result)

    # Merger methods
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        result = self.merger._calculate_similarity(content1, content2)
        return cast(float, result)

    def _apply_source_priority(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        result = self.merger._apply_source_priority(items)
        return cast(List[IntelligenceItem], result)

    def _generate_sector_summary(self, sector: ClientSector, items: List[IntelligenceItem]) -> str:
        result = self.merger._generate_sector_summary(sector, items)
        return cast(str, result)

    def _extract_risks(self, items: List[IntelligenceItem]) -> List[str]:
        result = self.merger._extract_risks(items)
        return cast(List[str], result)

    def _extract_opportunities(self, items: List[IntelligenceItem]) -> List[str]:
        result = self.merger._extract_opportunities(items)
        return cast(List[str], result)
