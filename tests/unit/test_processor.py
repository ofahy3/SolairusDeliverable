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

    def test_sector_intel_multiple_items(self):
        """Test sector intelligence with multiple items"""
        items = [
            IntelligenceItem(
                raw_content="Test 1",
                processed_content="Processed 1",
                category="test",
                relevance_score=0.9,
                so_what_statement="Impact 1",
                affected_sectors=[ClientSector.FINANCE]
            ),
            IntelligenceItem(
                raw_content="Test 2",
                processed_content="Processed 2",
                category="test",
                relevance_score=0.85,
                so_what_statement="Impact 2",
                affected_sectors=[ClientSector.FINANCE]
            ),
        ]

        sector_intel = SectorIntelligence(
            sector=ClientSector.FINANCE,
            items=items,
            summary="Finance sector update"
        )

        assert len(sector_intel.items) == 2

    def test_sector_intel_empty_items(self):
        """Test sector intelligence with no items"""
        sector_intel = SectorIntelligence(
            sector=ClientSector.GENERAL,
            items=[],
            summary="No items this period"
        )

        assert len(sector_intel.items) == 0
        assert sector_intel.summary is not None


class TestProcessIntelligence:
    """Test intelligence processing"""

    @pytest.fixture
    def processor(self):
        return IntelligenceProcessor()

    def test_process_intelligence_basic(self, processor):
        """Test basic intelligence processing"""
        content = """
        The Federal Reserve announced interest rate changes that will impact
        corporate borrowing costs and business aviation financing.
        """

        item = processor.process_intelligence(content, category="economic")

        assert item is not None
        assert item.raw_content is not None
        assert item.processed_content is not None
        assert item.category == "economic"

    def test_process_intelligence_aviation(self, processor):
        """Test processing aviation-related content"""
        content = """
        New FAA regulations affecting business jet operations in controlled airspace.
        Flight safety requirements updated for private aviation operators.
        """

        item = processor.process_intelligence(content, category="aviation_security")

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
        Aviation security threat assessment indicates increased risk for business
        jet operations in Middle East airspace due to ongoing conflicts.
        """

        low_relevance_content = "General weather patterns observed."

        high_item = processor.process_intelligence(high_relevance_content, category="aviation_security")
        low_item = processor.process_intelligence(low_relevance_content, category="other")

        assert high_item.relevance_score >= low_item.relevance_score


class TestProcessGTAIntervention:
    """Test GTA intervention processing"""

    @pytest.fixture
    def processor(self):
        return IntelligenceProcessor()

    def test_process_gta_intervention(self, processor):
        """Test processing GTA intervention"""
        from solairus_intelligence.clients.gta_client import GTAIntervention

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

        item = processor.process_gta_intervention(intervention, category="sanctions_trade")

        assert item is not None
        assert item.source_type == "gta"
        assert item.gta_intervention_id == 12345

    def test_process_gta_harmful_intervention(self, processor):
        """Test processing harmful intervention"""
        from solairus_intelligence.clients.gta_client import GTAIntervention

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

        item = processor.process_gta_intervention(intervention, category="sanctions_trade")

        assert item is not None
        # Harmful interventions should have higher relevance
        assert item.relevance_score > 0


class TestProcessFREDObservation:
    """Test FRED observation processing"""

    @pytest.fixture
    def processor(self):
        return IntelligenceProcessor()

    def test_process_fred_observation(self, processor):
        """Test processing FRED observation"""
        from solairus_intelligence.clients.fred_client import FREDObservation

        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        item = processor.process_fred_observation(obs, category="inflation")

        assert item is not None
        assert item.source_type == "fred"

    def test_process_fred_fuel_observation(self, processor):
        """Test processing fuel price observation"""
        from solairus_intelligence.clients.fred_client import FREDObservation

        obs = FREDObservation(
            series_id="DJFUELUSGULF",
            series_name="US Gulf Coast Jet Fuel",
            value=2.85,
            date="2024-11-01",
            units="$/Gallon",
            category="fuel_costs",
        )

        item = processor.process_fred_observation(obs, category="fuel_costs")

        assert item is not None
        assert "fuel" in item.category.lower() or "economic" in item.category.lower()


class TestMergeIntelligenceSources:
    """Test merging intelligence from multiple sources"""

    @pytest.fixture
    def processor(self):
        return IntelligenceProcessor()

    def test_merge_multiple_sources(self, processor):
        """Test merging items from different sources"""
        ergomind_item = IntelligenceItem(
            raw_content="ErgoMind content",
            processed_content="Processed ErgoMind",
            category="geopolitical",
            relevance_score=0.85,
            so_what_statement="ErgoMind impact",
            affected_sectors=[ClientSector.GENERAL],
            source_type="ergomind"
        )

        gta_item = IntelligenceItem(
            raw_content="GTA content",
            processed_content="Processed GTA",
            category="trade",
            relevance_score=0.9,
            so_what_statement="GTA impact",
            affected_sectors=[ClientSector.TECHNOLOGY],
            source_type="gta"
        )

        fred_item = IntelligenceItem(
            raw_content="FRED content",
            processed_content="Processed FRED",
            category="economic",
            relevance_score=0.75,
            so_what_statement="FRED impact",
            affected_sectors=[ClientSector.FINANCE],
            source_type="fred"
        )

        merged = processor.merge_intelligence_sources([ergomind_item], [gta_item], [fred_item])

        assert len(merged) == 3
        sources = {item.source_type for item in merged}
        assert "ergomind" in sources
        assert "gta" in sources
        assert "fred" in sources

    def test_merge_sorts_by_relevance(self, processor):
        """Test merged items are sorted by relevance"""
        items = [
            IntelligenceItem(
                raw_content="Low relevance",
                processed_content="Processed",
                category="test",
                relevance_score=0.3,
                so_what_statement="Impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="test"
            ),
            IntelligenceItem(
                raw_content="High relevance",
                processed_content="Processed",
                category="test",
                relevance_score=0.95,
                so_what_statement="Impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="test"
            ),
            IntelligenceItem(
                raw_content="Medium relevance",
                processed_content="Processed",
                category="test",
                relevance_score=0.6,
                so_what_statement="Impact",
                affected_sectors=[ClientSector.GENERAL],
                source_type="test"
            ),
        ]

        merged = processor.merge_intelligence_sources(items)

        # Should return items
        assert isinstance(merged, list)
        # If items returned, check they are sorted
        if len(merged) >= 2:
            assert merged[0].relevance_score >= merged[1].relevance_score
        if len(merged) >= 3:
            assert merged[1].relevance_score >= merged[2].relevance_score


class TestOrganizeBySector:
    """Test organizing intelligence by sector"""

    @pytest.fixture
    def processor(self):
        return IntelligenceProcessor()

    def test_organize_multiple_sectors(self, processor):
        """Test organizing items across multiple sectors"""
        items = [
            IntelligenceItem(
                raw_content="Tech news",
                processed_content="Technology update",
                category="technology",
                relevance_score=0.9,
                so_what_statement="Tech impact",
                affected_sectors=[ClientSector.TECHNOLOGY],
                source_type="ergomind"
            ),
            IntelligenceItem(
                raw_content="Finance news",
                processed_content="Finance update",
                category="finance",
                relevance_score=0.85,
                so_what_statement="Finance impact",
                affected_sectors=[ClientSector.FINANCE],
                source_type="ergomind"
            ),
        ]

        sector_intel = processor.organize_by_sector(items)

        assert isinstance(sector_intel, dict)
        # Should have items organized by sector
        assert len(sector_intel) > 0

    def test_organize_item_multiple_sectors(self, processor):
        """Test item affecting multiple sectors"""
        item = IntelligenceItem(
            raw_content="Cross-sector news",
            processed_content="Cross-sector update",
            category="general",
            relevance_score=0.8,
            so_what_statement="Multi-sector impact",
            affected_sectors=[ClientSector.TECHNOLOGY, ClientSector.FINANCE],
            source_type="ergomind"
        )

        sector_intel = processor.organize_by_sector([item])

        # Item should appear in both sectors or in general
        assert len(sector_intel) >= 1


class TestClientSectorEnum:
    """Test ClientSector enum"""

    def test_sector_values(self):
        """Test sector enum has expected values"""
        assert ClientSector.TECHNOLOGY is not None
        assert ClientSector.FINANCE is not None
        assert ClientSector.GENERAL is not None

    def test_sector_values_are_strings(self):
        """Test sector values are strings"""
        assert isinstance(ClientSector.TECHNOLOGY.value, str)
        assert isinstance(ClientSector.FINANCE.value, str)

    def test_all_sectors_defined(self):
        """Test all expected sectors are defined"""
        expected_sectors = ["TECHNOLOGY", "FINANCE", "GENERAL", "HEALTHCARE",
                          "ENERGY", "ENTERTAINMENT", "REAL_ESTATE"]

        for sector_name in expected_sectors:
            assert hasattr(ClientSector, sector_name), f"Missing sector: {sector_name}"
