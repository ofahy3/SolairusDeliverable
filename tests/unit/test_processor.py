"""
Unit tests for IntelligenceProcessor
"""

import pytest
from solairus_intelligence.core.processor import (
    IntelligenceProcessor,
    IntelligenceItem,
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

    def test_assess_relevance_high_score(self):
        """Test relevance assessment for aviation-related content"""
        processor = IntelligenceProcessor()

        text = "Aviation fuel prices increase significantly due to sanctions"
        score = processor._assess_relevance(text, "economic")

        assert score > 0.7, "Aviation-related content should have high relevance"

    def test_assess_relevance_medium_score(self):
        """Test relevance assessment for moderately relevant content"""
        processor = IntelligenceProcessor()

        text = "Oil prices rise globally affecting transportation costs"
        score = processor._assess_relevance(text, "economic")

        assert 0.4 < score < 0.8, "Moderately relevant content should have medium score"

    def test_assess_relevance_low_score(self):
        """Test relevance assessment for irrelevant content"""
        processor = IntelligenceProcessor()

        text = "Local restaurant opens new location downtown"
        score = processor._assess_relevance(text, "business")

        assert score < 0.4, "Irrelevant content should have low score"

    def test_categorize_by_sector(self, sample_intelligence_item):
        """Test sector categorization"""
        processor = IntelligenceProcessor()

        # Modify item to mention technology companies
        sample_intelligence_item.processed_content = "Intel and AMD face export restrictions"

        sectors = processor._categorize_by_sector(sample_intelligence_item)

        assert ClientSector.TECHNOLOGY in sectors

    def test_merge_intelligence_sources(self, sample_intelligence_items):
        """Test merging intelligence from multiple sources"""
        processor = IntelligenceProcessor()

        # Split items by source
        ergomind_items = [i for i in sample_intelligence_items if i.source_type == "ergomind"]
        gta_items = [i for i in sample_intelligence_items if i.source_type == "gta"]
        fred_items = [i for i in sample_intelligence_items if i.source_type == "fred"]

        merged = processor.merge_intelligence_sources(ergomind_items, gta_items, fred_items)

        assert len(merged) > 0
        # ErgoMind items should be weighted higher
        ergomind_in_top = any(i.source_type == "ergomind" for i in merged[:1])
        assert ergomind_in_top, "ErgoMind should be prioritized"

    def test_organize_by_sector(self, sample_intelligence_items):
        """Test organizing intelligence by client sector"""
        processor = IntelligenceProcessor()

        sector_intel = processor.organize_by_sector(sample_intelligence_items)

        assert len(sector_intel) > 0
        assert ClientSector.TECHNOLOGY in sector_intel or ClientSector.GENERAL in sector_intel
