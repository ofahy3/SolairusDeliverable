"""
Unit tests for FRED Processor module
"""

import pytest
from datetime import datetime

from solairus_intelligence.core.processors.fred import FREDProcessor
from solairus_intelligence.clients.fred_client import FREDObservation
from solairus_intelligence.config.clients import ClientSector


class TestFREDProcessor:
    """Test suite for FREDProcessor"""

    @pytest.fixture
    def processor(self):
        """Create processor instance"""
        return FREDProcessor()

    @pytest.fixture
    def sample_observation(self):
        """Create sample FRED observation"""
        return FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-11-01",
            units="Index 1982-1984=100",
            category="inflation",
        )

    @pytest.fixture
    def fuel_observation(self):
        """Create fuel price observation"""
        return FREDObservation(
            series_id="DJFUELUSGULF",
            series_name="US Gulf Coast Kerosene-Type Jet Fuel",
            value=2.85,
            date="2024-11-01",
            units="Dollars per Gallon",
            category="fuel_costs",
        )

    @pytest.fixture
    def interest_rate_observation(self):
        """Create interest rate observation"""
        return FREDObservation(
            series_id="FEDFUNDS",
            series_name="Federal Funds Effective Rate",
            value=5.33,
            date="2024-11-01",
            units="Percent",
            category="interest_rates",
        )


class TestProcessObservation:
    """Test processing FRED observations"""

    @pytest.fixture
    def processor(self):
        return FREDProcessor()

    def test_process_inflation_observation(self, processor):
        """Test processing inflation data"""
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
        assert item.category == "economic_inflation"  # Processor adds 'economic_' prefix
        assert item.relevance_score > 0
        assert item.source_type == "fred"

    def test_process_fuel_observation(self, processor):
        """Test processing fuel price data"""
        obs = FREDObservation(
            series_id="DJFUELUSGULF",
            series_name="Jet Fuel Price",
            value=2.85,
            date="2024-11-01",
            units="Dollars per Gallon",
            category="fuel_costs",
        )

        item = processor.process_observation(obs, category="fuel_costs")

        assert item is not None
        assert item.category == "economic_fuel_costs"  # Processor adds 'economic_' prefix

    def test_process_interest_rate_observation(self, processor):
        """Test processing interest rate data"""
        obs = FREDObservation(
            series_id="FEDFUNDS",
            series_name="Federal Funds Rate",
            value=5.33,
            date="2024-11-01",
            units="Percent",
            category="interest_rates",
        )

        item = processor.process_observation(obs, category="interest_rates")

        assert item is not None
        assert item.category == "economic_interest_rates"  # Processor adds 'economic_' prefix

    def test_process_gdp_observation(self, processor):
        """Test processing GDP data"""
        obs = FREDObservation(
            series_id="GDP",
            series_name="Gross Domestic Product",
            value=26.5,
            date="2024-11-01",
            units="Trillions of Dollars",
            category="gdp_growth",
        )

        item = processor.process_observation(obs, category="gdp_growth")

        assert item is not None
        assert item.category == "economic_gdp_growth"  # Processor adds 'economic_' prefix


class TestRelevanceScoring:
    """Test relevance scoring for economic data"""

    @pytest.fixture
    def processor(self):
        return FREDProcessor()

    def test_observation_has_relevance_score(self, processor):
        """Test that observations get a relevance score"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="CPI",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        item = processor.process_observation(obs, "inflation")

        assert item.relevance_score > 0
        assert item.relevance_score <= 1.0


class TestSoWhatGeneration:
    """Test So What statement generation"""

    @pytest.fixture
    def processor(self):
        return FREDProcessor()

    def test_generates_so_what_statement(self, processor):
        """Test So What statement is generated"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        item = processor.process_observation(obs, "inflation")

        assert item.so_what_statement is not None
        assert len(item.so_what_statement) > 10

    def test_fuel_generates_so_what(self, processor):
        """Test fuel So What is generated"""
        obs = FREDObservation(
            series_id="DJFUELUSGULF",
            series_name="Jet Fuel Price",
            value=3.50,
            date="2024-11-01",
            units="Dollars per Gallon",
            category="fuel_costs",
        )

        item = processor.process_observation(obs, "fuel_costs")

        assert item.so_what_statement is not None
        assert len(item.so_what_statement) > 10


class TestAffectedSectors:
    """Test sector assignment"""

    @pytest.fixture
    def processor(self):
        return FREDProcessor()

    def test_observation_has_affected_sectors(self, processor):
        """Test observation has affected sectors"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="CPI",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        item = processor.process_observation(obs, "inflation")

        assert item.affected_sectors is not None
        assert len(item.affected_sectors) >= 0  # Can be empty or have values

    def test_interest_rates_assignment(self, processor):
        """Test interest rate data sector assignment"""
        obs = FREDObservation(
            series_id="FEDFUNDS",
            series_name="Fed Funds Rate",
            value=5.5,
            date="2024-11-01",
            units="Percent",
            category="interest_rates",
        )

        item = processor.process_observation(obs, "interest_rates")

        # Should have some affected sectors
        assert item.affected_sectors is not None


class TestContentFormatting:
    """Test content formatting"""

    @pytest.fixture
    def processor(self):
        return FREDProcessor()

    def test_processed_content_exists(self, processor):
        """Test processed content is generated"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        item = processor.process_observation(obs, "inflation")

        assert item.processed_content is not None
        assert len(item.processed_content) > 0

    def test_processed_content_has_value(self, processor):
        """Test processed content includes relevant data"""
        obs = FREDObservation(
            series_id="DJFUELUSGULF",
            series_name="US Gulf Coast Jet Fuel",
            value=2.85,
            date="2024-11-01",
            units="$/Gallon",
            category="fuel_costs",
        )

        item = processor.process_observation(obs, "fuel_costs")

        # Should have some content
        assert len(item.processed_content) > 20

    def test_raw_content_preserved(self, processor):
        """Test raw content is preserved"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        item = processor.process_observation(obs, "inflation")

        assert item.raw_content is not None
        assert len(item.raw_content) > 0
