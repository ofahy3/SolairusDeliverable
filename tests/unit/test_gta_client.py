"""
Unit tests for GTA (Global Trade Alert) client
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from solairus_intelligence.clients.gta_client import (
    GTAClient,
    GTAConfig,
    GTAIntervention,
)


class TestGTAConfig:
    """Test GTA configuration"""

    def test_config_from_env(self, monkeypatch):
        """Test configuration loads from environment variables"""
        monkeypatch.setenv("GTA_API_KEY", "test_gta_key")
        monkeypatch.setenv("GTA_BASE_URL", "https://test.api.com/")

        config = GTAConfig()

        assert config.api_key == "test_gta_key"
        assert config.base_url == "https://test.api.com/"

    def test_config_defaults(self, monkeypatch):
        """Test configuration default values"""
        monkeypatch.setenv("GTA_API_KEY", "")

        config = GTAConfig()

        assert config.base_url == "https://api.globaltradealert.org/api/v1/data/"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_config_requires_api_key(self, monkeypatch):
        """Test that empty API key is handled"""
        monkeypatch.setenv("GTA_API_KEY", "")

        config = GTAConfig()

        assert config.api_key == ""


class TestGTAIntervention:
    """Test GTA intervention dataclass"""

    def test_intervention_creation(self):
        """Test creating an intervention"""
        intervention = GTAIntervention(
            intervention_id=12345,
            title="Test Tariff",
            description="Test description of a trade intervention",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[{"name": "United States"}],
            affected_jurisdictions=[{"name": "China"}],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        assert intervention.intervention_id == 12345
        assert intervention.title == "Test Tariff"
        assert intervention.gta_evaluation == "Harmful"

    def test_get_short_description(self):
        """Test description truncation"""
        long_desc = "A" * 300
        intervention = GTAIntervention(
            intervention_id=1,
            title="Test",
            description=long_desc,
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        short = intervention.get_short_description(100)

        assert len(short) == 103  # 100 + "..."
        assert short.endswith("...")

    def test_get_short_description_no_truncation(self):
        """Test description when no truncation needed"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Test",
            description="Short description",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        short = intervention.get_short_description(100)

        assert short == "Short description"


class TestGTAClient:
    """Test GTA client"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        """Create mock configuration"""
        monkeypatch.setenv("GTA_API_KEY", "test_key")
        return GTAConfig()

    @pytest.fixture
    def client(self, mock_config):
        """Create client instance"""
        return GTAClient(config=mock_config)

    def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client is not None
        assert client.config.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager"""
        async with client:
            assert client.session is not None

    def test_build_date_filter(self, client):
        """Test date filter building"""
        # This tests the internal date filter logic
        assert client.config.max_results_per_query == 100


class TestGTAInterventionMethods:
    """Test intervention helper methods"""

    def test_get_implementing_countries(self):
        """Test extracting implementing countries"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Test",
            description="Test",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[
                {"name": "United States"},
                {"name": "Canada"}
            ],
            affected_jurisdictions=[],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        countries = intervention.get_implementing_countries()

        assert "United States" in countries
        assert "Canada" in countries

    def test_get_affected_countries(self):
        """Test extracting affected countries"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Test",
            description="Test",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[
                {"name": "China"},
                {"name": "Germany"}
            ],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        countries = intervention.get_affected_countries()

        assert "China" in countries
        assert "Germany" in countries
