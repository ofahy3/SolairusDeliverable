"""
Unit tests for IntelligenceProcessor
"""

import pytest
from solairus_intelligence.core.processor import (
    IntelligenceProcessor,
    IntelligenceItem,
    SectorIntelligence,
    ClientSector
)


class TestIntelligenceProcessor:
    """Test suite for IntelligenceProcessor"""

    def test_processor_initialization(self):
        """Test that processor initializes correctly"""
        processor = IntelligenceProcessor()
        assert processor is not None
        assert hasattr(processor, 'client_mapping')
        assert ClientSector.TECHNOLOGY in processor.client_mapping

    def test_relevance_keywords_loaded(self):
        """Test that relevance keywords are loaded"""
        processor = IntelligenceProcessor()

        assert hasattr(processor, 'relevance_keywords')
        assert len(processor.relevance_keywords) > 0

    def test_client_mapping_structure(self):
        """Test client mapping has expected structure"""
        processor = IntelligenceProcessor()

        # Should have technology sector
        assert ClientSector.TECHNOLOGY in processor.client_mapping
        tech_mapping = processor.client_mapping[ClientSector.TECHNOLOGY]
        assert 'companies' in tech_mapping or isinstance(tech_mapping, dict)

    def test_client_mapping_completeness(self):
        """Test expected sectors are present"""
        processor = IntelligenceProcessor()

        # Technology should always be present
        assert ClientSector.TECHNOLOGY in processor.client_mapping

        # Should have multiple sectors defined
        assert len(processor.client_mapping) >= 3

    def test_merge_intelligence_sources_empty(self):
        """Test merging empty intelligence sources"""
        processor = IntelligenceProcessor()

        merged = processor.merge_intelligence_sources([], [], [])

        assert merged == []

    def test_merge_intelligence_sources_single(self):
        """Test merging single item"""
        processor = IntelligenceProcessor()

        items = [
            IntelligenceItem(
                raw_content="Test content",
                processed_content="Test processed",
                category="economic",
                relevance_score=0.8,
                so_what_statement="Test impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="ergomind"
            )
        ]

        merged = processor.merge_intelligence_sources(items)

        assert len(merged) == 1
        assert merged[0].source_type == "ergomind"

    def test_organize_by_sector(self):
        """Test organizing intelligence by client sector"""
        processor = IntelligenceProcessor()

        items = [
            IntelligenceItem(
                raw_content="Test content",
                processed_content="Test processed",
                category="test",
                relevance_score=0.8,
                so_what_statement="Test impact",
                affected_sectors=[ClientSector.TECHNOLOGY],
                source_type="ergomind"
            )
        ]

        sector_intel = processor.organize_by_sector(items)

        assert len(sector_intel) > 0
        assert ClientSector.TECHNOLOGY in sector_intel or ClientSector.GENERAL in sector_intel

    def test_organize_by_sector_empty(self):
        """Test organizing empty list"""
        processor = IntelligenceProcessor()

        sector_intel = processor.organize_by_sector([])

        assert isinstance(sector_intel, dict)


class TestIntelligenceItem:
    """Test IntelligenceItem dataclass"""

    def test_item_creation(self):
        """Test creating an intelligence item"""
        item = IntelligenceItem(
            raw_content="Raw data",
            processed_content="Processed analysis",
            category="economic",
            relevance_score=0.85,
            so_what_statement="Impact on aviation",
            affected_sectors=[ClientSector.GENERAL]
        )

        assert item.raw_content == "Raw data"
        assert item.relevance_score == 0.85
        assert ClientSector.GENERAL in item.affected_sectors

    def test_item_optional_fields(self):
        """Test item with optional fields"""
        item = IntelligenceItem(
            raw_content="Test",
            processed_content="Test processed",
            category="test",
            relevance_score=0.7,
            so_what_statement="Impact",
            affected_sectors=[ClientSector.TECHNOLOGY],
            source_type="gta",
            confidence=0.9
        )

        assert item.source_type == "gta"
        assert item.confidence == 0.9


class TestSectorIntelligence:
    """Test SectorIntelligence dataclass"""

    def test_sector_intel_creation(self):
        """Test creating sector intelligence"""
        items = [
            IntelligenceItem(
                raw_content="Test",
                processed_content="Test processed",
                category="test",
                relevance_score=0.8,
                so_what_statement="Impact",
                affected_sectors=[ClientSector.TECHNOLOGY]
            )
        ]

        sector_intel = SectorIntelligence(
            sector=ClientSector.TECHNOLOGY,
            items=items,
            summary="Technology sector update"
        )

        assert sector_intel.sector == ClientSector.TECHNOLOGY
        assert len(sector_intel.items) == 1
        assert sector_intel.summary == "Technology sector update"
