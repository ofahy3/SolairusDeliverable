"""
Integration tests for the Intelligence Processor pipeline
Tests the complete flow from raw data to processed intelligence
"""

import pytest
from unittest.mock import MagicMock, patch

from solairus_intelligence.core.processors.ergomind import ErgoMindProcessor
from solairus_intelligence.core.processors.gta import GTAProcessor
from solairus_intelligence.core.processors.fred import FREDProcessor
from solairus_intelligence.core.processors.merger import IntelligenceMerger
from solairus_intelligence.core.processors.base import IntelligenceItem
from solairus_intelligence.config.clients import ClientSector


class TestErgoMindProcessorIntegration:
    """Integration tests for the complete ErgoMind processor pipeline"""

    @pytest.fixture
    def processor(self):
        """Create a processor with AI disabled for testing"""
        with patch.dict('os.environ', {'AI_ENABLED': 'false'}):
            return ErgoMindProcessor()

    def test_ergomind_processing_pipeline(self, processor):
        """Test complete ErgoMind processing from raw text to IntelligenceItem"""
        raw_text = """
        The Federal Reserve announced a 25 basis point increase in interest rates,
        citing persistent inflation concerns. This marks the fifth consecutive rate hike
        and brings the federal funds rate to 5.5%. Markets reacted with increased volatility,
        and analysts expect continued pressure on corporate borrowing costs through Q4 2024.
        """

        result = processor.process_intelligence(raw_text, category="economic")

        assert isinstance(result, IntelligenceItem)
        assert result.source_type == "ergomind"
        assert result.relevance_score > 0
        assert result.confidence > 0
        assert len(result.so_what_statement) > 0
        assert len(result.affected_sectors) > 0
        assert ClientSector.FINANCE in result.affected_sectors or ClientSector.GENERAL in result.affected_sectors

    def test_aviation_relevance_scoring(self, processor):
        """Test that aviation-related content gets higher relevance scores"""
        aviation_text = """
        New FAA regulations require all Part 135 operators to implement enhanced
        safety management systems by January 2025. The rule affects business jet
        operators and FBOs across the United States, with significant compliance
        costs expected for smaller operators.
        """

        non_aviation_text = """
        The European Central Bank maintained its current interest rate stance,
        citing stable inflation expectations across the Eurozone. Manufacturing
        indices showed modest improvement in Germany and France.
        """

        aviation_result = processor.process_intelligence(aviation_text, category="regulatory")
        non_aviation_result = processor.process_intelligence(non_aviation_text, category="economic")

        assert aviation_result.relevance_score > non_aviation_result.relevance_score

    def test_sector_identification(self, processor):
        """Test that sectors are correctly identified from content"""
        tech_text = """
        US export controls on advanced semiconductors continue to impact
        technology companies. Cisco and other Silicon Valley firms are
        adjusting their supply chains in response to restrictions on
        chip exports to China.
        """

        result = processor.process_intelligence(tech_text, category="geopolitical")

        assert ClientSector.TECHNOLOGY in result.affected_sectors

    def test_action_items_generation(self, processor):
        """Test that appropriate action items are generated"""
        sanctions_text = """
        New sanctions imposed on Russian entities affect banking and
        energy sectors. Companies with exposure to sanctioned parties
        must review compliance immediately.
        """

        result = processor.process_intelligence(sanctions_text, category="geopolitical")

        assert len(result.action_items) > 0
        assert any('compliance' in action.lower() or 'review' in action.lower()
                   for action in result.action_items)

    @pytest.mark.asyncio
    async def test_async_processing(self, processor):
        """Test async processing method"""
        raw_text = "Aviation security concerns rising in Middle East region"

        result = await processor.process_intelligence_async(raw_text, category="security")

        assert isinstance(result, IntelligenceItem)
        assert result.source_type == "ergomind"
        assert len(result.so_what_statement) > 0


class TestGTAProcessorIntegration:
    """Integration tests for GTA processing"""

    @pytest.fixture
    def processor(self):
        with patch.dict('os.environ', {'AI_ENABLED': 'false'}):
            return GTAProcessor()

    def test_gta_intervention_processing(self, processor):
        """Test GTA intervention processing"""
        mock_intervention = MagicMock()
        mock_intervention.intervention_id = 12345
        mock_intervention.description = "Export restrictions on semiconductor equipment"
        mock_intervention.gta_evaluation = "Harmful"
        mock_intervention.intervention_type = "Export restriction"
        mock_intervention.affected_sectors = ["Semiconductors", "Electronics"]
        mock_intervention.sources = [{"url": "https://example.com"}]
        mock_intervention.date_implemented = "2024-01-15"
        mock_intervention.date_announced = "2024-01-10"
        mock_intervention.get_short_description = MagicMock(return_value="Export restrictions on semiconductor equipment")
        mock_intervention.get_implementing_countries = MagicMock(return_value=["United States"])
        mock_intervention.get_affected_countries = MagicMock(return_value=["China"])

        result = processor.process_intervention(mock_intervention)

        assert isinstance(result, IntelligenceItem)
        assert result.source_type == "gta"
        assert result.gta_intervention_id == 12345
        assert len(result.gta_implementing_countries) > 0
        assert len(result.so_what_statement) > 0


class TestFREDProcessorIntegration:
    """Integration tests for FRED processing"""

    @pytest.fixture
    def processor(self):
        with patch.dict('os.environ', {'AI_ENABLED': 'false'}):
            return FREDProcessor()

    def test_fred_observation_processing(self, processor):
        """Test FRED observation processing"""
        mock_observation = MagicMock()
        mock_observation.series_id = "WJFUELUSGULF"
        mock_observation.series_name = "Gulf Coast Kerosene-Type Jet Fuel Spot Price"
        mock_observation.value = 2.85
        mock_observation.date = "2024-01-15"
        mock_observation.units = "Dollars per Gallon"
        mock_observation.category = "fuel_costs"

        result = processor.process_observation(mock_observation, "fuel_costs")

        assert isinstance(result, IntelligenceItem)
        assert result.source_type == "fred"
        assert result.fred_series_id == "WJFUELUSGULF"
        assert result.fred_value == 2.85
        assert "jet fuel" in result.so_what_statement.lower() or "fuel" in result.so_what_statement.lower()


class TestMergerIntegration:
    """Integration tests for intelligence merging"""

    @pytest.fixture
    def merger(self):
        return IntelligenceMerger()

    def test_multi_source_merge(self, merger):
        """Test merging intelligence from multiple sources"""
        ergomind_items = [
            IntelligenceItem(
                raw_content="Interest rates rising",
                processed_content="Federal Reserve raises rates",
                category="economic",
                relevance_score=0.7,
                so_what_statement="Financing costs increasing",
                confidence=0.8,
                source_type="ergomind"
            )
        ]

        fred_items = [
            IntelligenceItem(
                raw_content="DFF: 5.5",
                processed_content="Federal Funds Rate: 5.50%",
                category="economic_interest_rates",
                relevance_score=0.8,
                so_what_statement="Higher rates affect financing",
                confidence=0.95,
                source_type="fred",
                fred_series_id="DFF",
                fred_value=5.5
            )
        ]

        merged = merger.merge_sources(ergomind_items, fred_items)

        assert len(merged) >= 1
        source_types = set(item.source_type for item in merged)
        assert len(source_types) >= 1

    def test_sector_organization(self, merger):
        """Test organizing items by sector"""
        items = [
            IntelligenceItem(
                raw_content="Tech sector news",
                processed_content="Technology developments",
                category="technology",
                relevance_score=0.8,
                so_what_statement="Tech impact",
                confidence=0.85,
                source_type="ergomind",
                affected_sectors=[ClientSector.TECHNOLOGY]
            ),
            IntelligenceItem(
                raw_content="Finance sector news",
                processed_content="Financial developments",
                category="finance",
                relevance_score=0.75,
                so_what_statement="Finance impact",
                confidence=0.8,
                source_type="ergomind",
                affected_sectors=[ClientSector.FINANCE]
            )
        ]

        organized = merger.organize_by_sector(items)

        assert ClientSector.TECHNOLOGY in organized
        assert ClientSector.FINANCE in organized
        assert len(organized[ClientSector.TECHNOLOGY].items) > 0
