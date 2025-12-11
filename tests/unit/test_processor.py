"""
Unit tests for intelligence processing components
"""

import pytest

from mro_intelligence.core.processor import (
    ClientSector,
    ErgoMindProcessor,
    FREDProcessor,
    GTAProcessor,
    IntelligenceItem,
    IntelligenceMerger,
    SectorIntelligence,
)


class TestIntelligenceItem:
    """Test IntelligenceItem dataclass"""

    def test_item_creation(self):
        """Test creating an intelligence item"""
        item = IntelligenceItem(
            raw_content="Raw data",
            processed_content="Processed analysis",
            category="economic",
            relevance_score=0.85,
            so_what_statement="Impact on industrial",
            affected_sectors=[ClientSector.GENERAL],
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
            affected_sectors=[ClientSector.MANUFACTURING],
            source_type="gta",
            confidence=0.9,
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
                affected_sectors=[ClientSector.MANUFACTURING],
            )
        ]

        sector_intel = SectorIntelligence(
            sector=ClientSector.MANUFACTURING, items=items, summary="Technology sector update"
        )

        assert sector_intel.sector == ClientSector.MANUFACTURING
        assert len(sector_intel.items) == 1
        assert sector_intel.summary == "Technology sector update"

    def test_sector_intel_multiple_items(self):
        """Test sector intelligence with multiple items"""
        items = [
            IntelligenceItem(
                raw_content="Test 1",
                processed_content="Processed 1",
                category="test",
                relevance_score=0.9,
                so_what_statement="Impact 1",
                affected_sectors=[ClientSector.GOVERNMENT],
            ),
            IntelligenceItem(
                raw_content="Test 2",
                processed_content="Processed 2",
                category="test",
                relevance_score=0.85,
                so_what_statement="Impact 2",
                affected_sectors=[ClientSector.GOVERNMENT],
            ),
        ]

        sector_intel = SectorIntelligence(
            sector=ClientSector.GOVERNMENT, items=items, summary="Finance sector update"
        )

        assert len(sector_intel.items) == 2

    def test_sector_intel_empty_items(self):
        """Test sector intelligence with no items"""
        sector_intel = SectorIntelligence(
            sector=ClientSector.GENERAL, items=[], summary="No items this period"
        )

        assert len(sector_intel.items) == 0
        assert sector_intel.summary is not None


class TestErgoMindProcessor:
    """Test ErgoMind intelligence processing"""

    @pytest.fixture
    def processor(self):
        return ErgoMindProcessor()

    def test_process_intelligence_basic(self, processor):
        """Test basic intelligence processing"""
        content = """
        The Federal Reserve announced interest rate changes that will impact
        corporate borrowing costs and MRO financing.
        """

        item = processor.process_intelligence(content, category="economic")

        assert item is not None
        assert item.raw_content is not None
        assert item.processed_content is not None
        assert item.category == "economic"

    def test_process_intelligence_industrial(self, processor):
        """Test processing industrial-related content"""
        content = """
        New FAA regulations affecting business jet operations in controlled airspace.
        Operations safety requirements updated for private industrial operators.
        """

        item = processor.process_intelligence(content, category="industrial_security")

        assert item is not None
        assert item.relevance_score > 0

    def test_process_intelligence_trade(self, processor):
        """Test processing trade-related content"""
        content = """
        New export controls on semiconductor manufacturing equipment.
        Tariffs implemented affecting technology supply chains.
        """

        item = processor.process_intelligence(content, category="sanctions_trade")

        assert item is not None
        assert item.so_what_statement is not None

    def test_process_intelligence_relevance_scoring(self, processor):
        """Test relevance scoring for different content"""
        high_relevance_content = """
        Industrial security threat assessment indicates increased risk for business
        jet operations in Middle East airspace due to ongoing conflicts.
        """

        low_relevance_content = "General weather patterns observed."

        high_item = processor.process_intelligence(
            high_relevance_content, category="industrial_security"
        )
        low_item = processor.process_intelligence(low_relevance_content, category="other")

        assert high_item.relevance_score >= low_item.relevance_score

    def test_relevance_keywords_loaded(self):
        """Test that relevance keywords are loaded"""
        processor = ErgoMindProcessor()

        assert hasattr(processor, "RELEVANCE_KEYWORDS")
        assert len(processor.RELEVANCE_KEYWORDS) > 0


class TestGTAProcessor:
    """Test GTA intervention processing"""

    @pytest.fixture
    def processor(self):
        return GTAProcessor()

    def test_process_intervention(self, processor):
        """Test processing GTA intervention"""
        from mro_intelligence.clients.gta_client import GTAIntervention

        intervention = GTAIntervention(
            intervention_id=12345,
            title="US Export Controls on Semiconductors",
            description="New restrictions on semiconductor exports to China",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[{"name": "United States"}],
            affected_jurisdictions=[{"name": "China"}],
            intervention_type="Export control",
            intervention_type_id=1,
        )

        item = processor.process_intervention(intervention, category="sanctions_trade")

        assert item is not None
        assert item.source_type == "gta"
        assert item.gta_intervention_id == 12345

    def test_process_harmful_intervention(self, processor):
        """Test processing harmful intervention"""
        from mro_intelligence.clients.gta_client import GTAIntervention

        intervention = GTAIntervention(
            intervention_id=99999,
            title="Tariff Increase",
            description="25% tariff on imported goods",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[{"name": "United States"}],
            affected_jurisdictions=[{"name": "European Union"}],
            intervention_type="Tariff",
            intervention_type_id=2,
        )

        item = processor.process_intervention(intervention, category="sanctions_trade")

        assert item is not None
        assert item.relevance_score > 0


class TestFREDProcessor:
    """Test FRED observation processing"""

    @pytest.fixture
    def processor(self):
        return FREDProcessor()

    def test_process_observation(self, processor):
        """Test processing FRED observation"""
        from mro_intelligence.clients.fred_client import FREDObservation

        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        item = processor.process_observation(obs, category="inflation")

        assert item is not None
        assert item.source_type == "fred"

    def test_process_fuel_observation(self, processor):
        """Test processing fuel price observation"""
        from mro_intelligence.clients.fred_client import FREDObservation

        obs = FREDObservation(
            series_id="DJFUELUSGULF",
            series_name="US Gulf Coast Crude Oil",
            value=2.85,
            date="2024-11-01",
            units="$/Gallon",
            category="fuel_costs",
        )

        item = processor.process_observation(obs, category="fuel_costs")

        assert item is not None
        assert "fuel" in item.category.lower() or "economic" in item.category.lower()


class TestIntelligenceMerger:
    """Test merging intelligence from multiple sources"""

    @pytest.fixture
    def merger(self):
        return IntelligenceMerger()

    def test_merge_empty_sources(self, merger):
        """Test merging empty intelligence sources"""
        merged = merger.merge_sources([], [], [])
        assert merged == []

    def test_merge_single_item(self, merger):
        """Test merging single item"""
        items = [
            IntelligenceItem(
                raw_content="Test content",
                processed_content="Test processed",
                category="economic",
                relevance_score=0.8,
                so_what_statement="Test impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="ergomind",
            )
        ]

        merged = merger.merge_sources(items)

        assert len(merged) == 1
        assert merged[0].source_type == "ergomind"

    def test_merge_multiple_sources(self, merger):
        """Test merging items from different sources"""
        ergomind_item = IntelligenceItem(
            raw_content="ErgoMind content",
            processed_content="Processed ErgoMind",
            category="geopolitical",
            relevance_score=0.85,
            so_what_statement="ErgoMind impact",
            affected_sectors=[ClientSector.GENERAL],
            source_type="ergomind",
        )

        gta_item = IntelligenceItem(
            raw_content="GTA content",
            processed_content="Processed GTA",
            category="trade",
            relevance_score=0.9,
            so_what_statement="GTA impact",
            affected_sectors=[ClientSector.MANUFACTURING],
            source_type="gta",
        )

        fred_item = IntelligenceItem(
            raw_content="FRED content",
            processed_content="Processed FRED",
            category="economic",
            relevance_score=0.75,
            so_what_statement="FRED impact",
            affected_sectors=[ClientSector.GOVERNMENT],
            source_type="fred",
        )

        merged = merger.merge_sources([ergomind_item], [gta_item], [fred_item])

        assert len(merged) == 3
        sources = {item.source_type for item in merged}
        assert "ergomind" in sources
        assert "gta" in sources
        assert "fred" in sources

    def test_merge_sorts_by_relevance(self, merger):
        """Test merged items are sorted by composite score"""
        items = [
            IntelligenceItem(
                raw_content="Low relevance",
                processed_content="Processed",
                category="test",
                relevance_score=0.3,
                so_what_statement="Impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="test",
            ),
            IntelligenceItem(
                raw_content="High relevance",
                processed_content="Processed",
                category="test",
                relevance_score=0.95,
                so_what_statement="Impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="test",
            ),
            IntelligenceItem(
                raw_content="Medium relevance",
                processed_content="Processed",
                category="test",
                relevance_score=0.6,
                so_what_statement="Impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="test",
            ),
        ]

        merged = merger.merge_sources(items)

        assert isinstance(merged, list)
        if len(merged) >= 2:
            assert merged[0].relevance_score >= merged[1].relevance_score
        if len(merged) >= 3:
            assert merged[1].relevance_score >= merged[2].relevance_score

    def test_organize_by_sector(self, merger):
        """Test organizing intelligence by client sector"""
        items = [
            IntelligenceItem(
                raw_content="Test content",
                processed_content="Test processed",
                category="test",
                relevance_score=0.8,
                so_what_statement="Test impact",
                affected_sectors=[ClientSector.MANUFACTURING],
                source_type="ergomind",
            )
        ]

        sector_intel = merger.organize_by_sector(items)

        assert len(sector_intel) > 0
        assert ClientSector.MANUFACTURING in sector_intel or ClientSector.GENERAL in sector_intel

    def test_organize_by_sector_empty(self, merger):
        """Test organizing empty list"""
        sector_intel = merger.organize_by_sector([])
        assert isinstance(sector_intel, dict)

    def test_organize_multiple_sectors(self, merger):
        """Test organizing items across multiple sectors"""
        items = [
            IntelligenceItem(
                raw_content="Tech news",
                processed_content="Technology update",
                category="technology",
                relevance_score=0.9,
                so_what_statement="Tech impact",
                affected_sectors=[ClientSector.MANUFACTURING],
                source_type="ergomind",
            ),
            IntelligenceItem(
                raw_content="Finance news",
                processed_content="Finance update",
                category="finance",
                relevance_score=0.85,
                so_what_statement="Finance impact",
                affected_sectors=[ClientSector.GOVERNMENT],
                source_type="ergomind",
            ),
        ]

        sector_intel = merger.organize_by_sector(items)

        assert isinstance(sector_intel, dict)
        assert len(sector_intel) > 0


class TestClientSectorEnum:
    """Test ClientSector enum"""

    def test_sector_values(self):
        """Test sector enum has expected values"""
        assert ClientSector.MANUFACTURING is not None
        assert ClientSector.GOVERNMENT is not None
        assert ClientSector.GENERAL is not None

    def test_sector_values_are_strings(self):
        """Test sector values are strings"""
        assert isinstance(ClientSector.MANUFACTURING.value, str)
        assert isinstance(ClientSector.GOVERNMENT.value, str)

    def test_all_sectors_defined(self):
        """Test all expected Grainger customer segments are defined"""
        expected_sectors = [
            "MANUFACTURING",
            "GOVERNMENT",
            "COMMERCIAL_FACILITIES",
            "CONTRACTORS",
            "GENERAL",
        ]

        for sector_name in expected_sectors:
            assert hasattr(ClientSector, sector_name), f"Missing sector: {sector_name}"
