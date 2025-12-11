"""
Unit tests for GTA client module
"""

from unittest.mock import AsyncMock, patch

import pytest

from mro_intelligence.clients.gta_client import GTAClient, GTAConfig, GTAIntervention


class TestGTAConfig:
    """Test GTAConfig dataclass"""

    def test_default_values(self):
        """Test default configuration"""
        config = GTAConfig()

        assert "globaltradealert.org" in config.base_url
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.max_results_per_query == 100

    def test_custom_values(self):
        """Test custom configuration"""
        config = GTAConfig(
            base_url="https://custom-api.com", api_key="test_key", timeout=60, max_retries=5
        )

        assert config.base_url == "https://custom-api.com"
        assert config.api_key == "test_key"
        assert config.timeout == 60
        assert config.max_retries == 5


class TestGTAIntervention:
    """Test GTAIntervention dataclass"""

    @pytest.fixture
    def sample_intervention(self):
        return GTAIntervention(
            intervention_id=12345,
            title="Test Trade Intervention",
            description="Test description of a trade intervention that is fairly long and might need to be truncated for display purposes",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[
                {"name": "United States", "code": "US"},
                {"name": "Canada", "code": "CA"},
            ],
            affected_jurisdictions=[
                {"name": "China", "code": "CN"},
                {"name": "Japan", "code": "JP"},
            ],
            intervention_type="Tariff increase",
            intervention_type_id=47,
            mast_chapter="Trade Restrictions",
            affected_sectors=["technology", "semiconductors"],
            date_announced="2024-01-01",
            date_implemented="2024-02-01",
            is_in_force=True,
        )

    def test_intervention_attributes(self, sample_intervention):
        """Test intervention has all attributes"""
        assert sample_intervention.intervention_id == 12345
        assert sample_intervention.title == "Test Trade Intervention"
        assert sample_intervention.gta_evaluation == "Harmful"
        assert sample_intervention.is_in_force is True

    def test_get_short_description_full(self, sample_intervention):
        """Test short description for short text"""
        short = sample_intervention.get_short_description(max_length=500)
        assert short == sample_intervention.description

    def test_get_short_description_truncated(self, sample_intervention):
        """Test short description truncation"""
        short = sample_intervention.get_short_description(max_length=20)
        assert len(short) == 23  # 20 + "..."
        assert short.endswith("...")

    def test_get_implementing_countries(self, sample_intervention):
        """Test extracting implementing countries"""
        countries = sample_intervention.get_implementing_countries()
        assert "United States" in countries
        assert "Canada" in countries
        assert len(countries) == 2

    def test_get_affected_countries(self, sample_intervention):
        """Test extracting affected countries"""
        countries = sample_intervention.get_affected_countries()
        assert "China" in countries
        assert "Japan" in countries
        assert len(countries) == 2

    def test_intervention_default_values(self):
        """Test intervention with minimal required fields"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Minimal",
            description="Desc",
            gta_evaluation="Unclear",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Unknown",
            intervention_type_id=0,
        )
        assert intervention.mast_chapter is None
        assert intervention.affected_sectors == []
        assert intervention.date_announced is None
        assert intervention.is_in_force is True

    def test_get_countries_with_missing_name(self):
        """Test extracting countries when name is missing"""
        intervention = GTAIntervention(
            intervention_id=1,
            title="Test",
            description="Desc",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[{"code": "US"}],
            affected_jurisdictions=[{"id": 123}],
            intervention_type="Test",
            intervention_type_id=0,
        )
        impl_countries = intervention.get_implementing_countries()
        affected_countries = intervention.get_affected_countries()

        assert "Unknown" in impl_countries
        assert "Unknown" in affected_countries


class TestGTAClient:
    """Test GTAClient class"""

    @pytest.fixture
    def client(self):
        config = GTAConfig(api_key="test_api_key")
        return GTAClient(config)

    def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client is not None
        assert client.config is not None
        assert client.session is None

    def test_client_initialization_no_api_key(self):
        """Test client warns when no API key"""
        config = GTAConfig(api_key="")
        client = GTAClient(config)
        assert client.config.api_key == ""

    @pytest.mark.asyncio
    async def test_context_manager_entry(self, client):
        """Test async context manager entry"""
        async with client:
            assert client.session is not None

    @pytest.mark.asyncio
    async def test_context_manager_exit(self, client):
        """Test async context manager exit closes session"""
        async with client:
            pass

    @pytest.mark.asyncio
    async def test_test_connection_no_api_key(self):
        """Test connection fails without API key"""
        config = GTAConfig(api_key="")
        client = GTAClient(config)
        async with client:
            result = await client.test_connection()
        assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_no_session(self, client):
        """Test connection fails without session"""
        result = await client.test_connection()
        assert result is False

    def test_parse_intervention(self, client):
        """Test parsing raw intervention data"""
        raw_data = {
            "intervention_id": 12345,
            "state_act_title": "Test Intervention",
            "gta_evaluation": "Harmful",
            "implementing_jurisdictions": [{"name": "US"}],
            "affected_jurisdictions": [{"name": "China"}],
            "intervention_type": "Tariff",
            "state_act_id": 100,
            "mast_chapter": "Trade",
            "is_in_force": 1,
        }
        intervention = client._parse_intervention(raw_data)

        assert intervention.intervention_id == 12345
        assert intervention.title == "Test Intervention"
        assert intervention.gta_evaluation == "Harmful"
        assert intervention.is_in_force is True

    def test_parse_intervention_minimal(self, client):
        """Test parsing intervention with minimal data"""
        raw_data = {}
        intervention = client._parse_intervention(raw_data)

        assert intervention.intervention_id == 0
        assert intervention.title == "Untitled Intervention"
        assert intervention.gta_evaluation == "Unclear"

    def test_parse_intervention_is_in_force_false(self, client):
        """Test parsing intervention not in force"""
        raw_data = {"is_in_force": 0}
        intervention = client._parse_intervention(raw_data)
        assert intervention.is_in_force is False

    def test_parse_intervention_null_intervention_id(self, client):
        """Test parsing intervention with null ID"""
        raw_data = {"intervention_id": None}
        intervention = client._parse_intervention(raw_data)
        assert intervention.intervention_id == 0

    @pytest.mark.asyncio
    async def test_query_interventions_success(self, client):
        """Test querying interventions successfully"""
        mock_response = [
            {
                "intervention_id": 1,
                "state_act_title": "Test",
                "gta_evaluation": "Harmful",
                "implementing_jurisdictions": [],
                "affected_jurisdictions": [],
                "intervention_type": "Tariff",
            }
        ]

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            async with client:
                interventions = await client.query_interventions({})

        assert len(interventions) == 1
        assert isinstance(interventions[0], GTAIntervention)

    @pytest.mark.asyncio
    async def test_query_interventions_with_limit(self, client):
        """Test querying interventions with limit"""
        mock_response = [{"intervention_id": i} for i in range(10)]

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            async with client:
                interventions = await client.query_interventions({}, limit=5)

        assert len(interventions) == 5

    @pytest.mark.asyncio
    async def test_query_interventions_failure(self, client):
        """Test querying interventions handles errors"""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("API Error")
            async with client:
                interventions = await client.query_interventions({})

        assert interventions == []

    @pytest.mark.asyncio
    async def test_get_recent_harmful_interventions(self, client):
        """Test getting harmful interventions"""
        mock_response = [
            {
                "intervention_id": 1,
                "gta_evaluation": "Harmful",
                "implementing_jurisdictions": [],
                "affected_jurisdictions": [],
            }
        ]

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            async with client:
                interventions = await client.get_recent_harmful_interventions(days=30)

        assert len(interventions) == 1

    @pytest.mark.asyncio
    async def test_get_recent_harmful_with_sectors(self, client):
        """Test getting harmful interventions with sector filter"""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            async with client:
                await client.get_recent_harmful_interventions(days=30, sectors=["technology"])

        mock_request.assert_called_once()
        call_args = mock_request.call_args[0][0]
        assert "affected_sectors" in call_args

    @pytest.mark.asyncio
    async def test_get_sanctions_and_export_controls(self, client):
        """Test getting sanctions"""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            async with client:
                result = await client.get_sanctions_and_export_controls(days=60)

        assert result == []
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_capital_controls(self, client):
        """Test getting capital controls"""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            async with client:
                result = await client.get_capital_controls(days=60)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_capital_controls_with_countries(self, client):
        """Test getting capital controls with country filter"""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            async with client:
                await client.get_capital_controls(affected_countries=[1, 2, 3])

        call_args = mock_request.call_args[0][0]
        assert "affected" in call_args

    @pytest.mark.asyncio
    async def test_get_technology_restrictions(self, client):
        """Test getting tech restrictions"""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            async with client:
                result = await client.get_technology_restrictions(days=60)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_industrial_sector_interventions(self, client):
        """Test getting industrial sector interventions"""
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            async with client:
                result = await client.get_industrial_sector_interventions(days=90)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_immigration_visa_restrictions(self, client):
        """Test getting immigration restrictions"""
        mock_response = [
            {
                "intervention_id": 1,
                "state_act_title": "Visa Restriction",
                "mast_chapter": "Migration measures",
                "intervention_type": "Labour market",
                "implementing_jurisdictions": [],
                "affected_jurisdictions": [],
            },
            {
                "intervention_id": 2,
                "state_act_title": "Trade tariff",
                "mast_chapter": "Tariffs",
                "intervention_type": "Tariff",
                "implementing_jurisdictions": [],
                "affected_jurisdictions": [],
            },
        ]

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            async with client:
                result = await client.get_immigration_visa_restrictions(days=365)

        # Should filter to only migration-related
        assert len(result) == 1
        assert "Visa" in result[0].title

    @pytest.mark.asyncio
    async def test_make_request_no_session(self, client):
        """Test _make_request fails without session"""
        with pytest.raises(RuntimeError, match="session not initialized"):
            await client._make_request({})


class TestGTAClientIntegration:
    """Integration-style tests for GTA client"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow with mocked responses"""
        config = GTAConfig(api_key="test_key")
        client = GTAClient(config)

        mock_interventions = [
            {
                "intervention_id": 1,
                "state_act_title": "US-China Tariff",
                "gta_evaluation": "Harmful",
                "implementing_jurisdictions": [{"name": "United States"}],
                "affected_jurisdictions": [{"name": "China"}],
                "intervention_type": "Tariff increase",
                "mast_chapter": "Tariffs",
                "is_in_force": 1,
            }
        ]

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_interventions

            async with client:
                interventions = await client.get_recent_harmful_interventions(days=30)

                assert len(interventions) == 1
                intervention = interventions[0]
                assert intervention.title == "US-China Tariff"
                assert intervention.gta_evaluation == "Harmful"
                assert "United States" in intervention.get_implementing_countries()
                assert "China" in intervention.get_affected_countries()
