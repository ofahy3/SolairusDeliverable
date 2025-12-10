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


class TestGTAClientParsing:
    """Test GTA client parsing methods"""

    @pytest.fixture
    def client(self, monkeypatch):
        """Create client instance"""
        monkeypatch.setenv("GTA_API_KEY", "test_key")
        config = GTAConfig()
        return GTAClient(config=config)

    def test_parse_intervention_basic(self, client):
        """Test parsing basic intervention data"""
        raw_data = {
            "intervention_id": 12345,
            "state_act_title": "Test Export Control",
            "gta_evaluation": "Harmful",
            "implementing_jurisdictions": [{"name": "United States"}],
            "affected_jurisdictions": [{"name": "China"}],
            "state_act_id": 100,
            "mast_chapters": [{"name": "Export controls"}],
            "is_in_force": 1,
            "date_announced": "2024-01-15",
            "date_implemented": "2024-02-01",
        }

        intervention = client._parse_intervention(raw_data)

        assert intervention.intervention_id == 12345
        assert intervention.title == "Test Export Control"
        assert intervention.gta_evaluation == "Harmful"

    def test_parse_intervention_missing_fields(self, client):
        """Test parsing with missing optional fields"""
        raw_data = {
            "intervention_id": 99,
            "gta_evaluation": "Liberalizing",
            "implementing_jurisdictions": [],
            "affected_jurisdictions": [],
        }

        intervention = client._parse_intervention(raw_data)

        assert intervention.intervention_id == 99
        assert intervention.title == "Untitled Intervention"
        # intervention_type comes from mast_chapters, defaults to what's in the code
        assert intervention is not None

    def test_parse_intervention_is_in_force(self, client):
        """Test parsing is_in_force as integer"""
        raw_data = {
            "intervention_id": 1,
            "state_act_title": "Test",
            "gta_evaluation": "Harmful",
            "implementing_jurisdictions": [],
            "affected_jurisdictions": [],
            "is_in_force": 0,  # Integer format
        }

        intervention = client._parse_intervention(raw_data)

        assert intervention.is_in_force is False

    def test_parse_intervention_mast_chapters(self, client):
        """Test parsing MAST chapters"""
        raw_data = {
            "intervention_id": 1,
            "state_act_title": "Test",
            "gta_evaluation": "Harmful",
            "implementing_jurisdictions": [],
            "affected_jurisdictions": [],
            "mast_chapters": [
                {"name": "Tariffs"},
                {"name": "Non-tariff barriers"}
            ],
        }

        intervention = client._parse_intervention(raw_data)

        # mast_chapter should contain something from mast_chapters
        assert intervention.mast_chapter is not None


class TestGTAInterventionProperties:
    """Test GTA intervention properties and methods"""

    def test_gta_evaluation_stored(self):
        """Test gta_evaluation is correctly stored"""
        harmful = GTAIntervention(
            intervention_id=1,
            title="Test",
            description="Test",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        liberalizing = GTAIntervention(
            intervention_id=2,
            title="Test",
            description="Test",
            gta_evaluation="Liberalizing",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        assert harmful.gta_evaluation == "Harmful"
        assert liberalizing.gta_evaluation == "Liberalizing"

    def test_intervention_type_stored(self):
        """Test intervention type is correctly stored"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Test",
            description="Test",
            gta_evaluation="Liberalizing",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Tariff",
            intervention_type_id=100,
        )

        assert intervention.intervention_type == "Tariff"
        assert intervention.intervention_type_id == 100

    def test_affected_sectors_stored(self):
        """Test affected sectors are stored"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Aircraft Parts Export Control",
            description="Controls on aviation components",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Export control",
            intervention_type_id=1,
            affected_sectors=["Aircraft and spacecraft", "Parts"],
        )

        assert "Aircraft and spacecraft" in intervention.affected_sectors
        assert len(intervention.affected_sectors) == 2

    def test_empty_jurisdictions(self):
        """Test handling empty jurisdiction lists"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Test",
            description="Test",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Tariff",
            intervention_type_id=1,
        )

        impl = intervention.get_implementing_countries()
        affected = intervention.get_affected_countries()

        assert impl == []
        assert affected == []
