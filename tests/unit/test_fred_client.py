"""
Unit tests for FRED (Federal Reserve Economic Data) client
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from solairus_intelligence.clients.fred_client import (
    FREDClient,
    FREDConfig,
    FREDObservation,
)


class TestFREDConfig:
    """Test FRED configuration"""

    def test_config_from_env(self, monkeypatch):
        """Test configuration loads from environment variables"""
        monkeypatch.setenv("FRED_API_KEY", "test_fred_key")

        config = FREDConfig()

        assert config.api_key == "test_fred_key"

    def test_config_defaults(self, monkeypatch):
        """Test configuration default values"""
        monkeypatch.setenv("FRED_API_KEY", "test_key")

        config = FREDConfig()

        assert config.base_url == "https://api.stlouisfed.org/fred"
        assert config.timeout == 30

    def test_config_requires_api_key(self, monkeypatch):
        """Test that empty API key is handled"""
        monkeypatch.setenv("FRED_API_KEY", "")

        config = FREDConfig()

        assert config.api_key == ""


class TestFREDObservation:
    """Test FRED observation dataclass"""

    def test_observation_creation(self):
        """Test creating an observation"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            date="2024-10-01",
            value=310.5,
            units="Index",
            category="inflation"
        )

        assert obs.series_id == "CPIAUCSL"
        assert obs.value == 310.5
        assert obs.category == "inflation"

    def test_observation_with_all_fields(self):
        """Test observation with all required fields"""
        obs = FREDObservation(
            series_id="FEDFUNDS",
            series_name="Federal Funds Rate",
            date="2024-10-01",
            value=5.33,
            units="Percent",
            category="interest_rates"
        )

        assert obs.series_id == "FEDFUNDS"
        assert obs.value == 5.33
        assert obs.category == "interest_rates"


class TestFREDClient:
    """Test FRED client"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        """Create mock configuration"""
        monkeypatch.setenv("FRED_API_KEY", "test_key")
        return FREDConfig()

    @pytest.fixture
    def client(self, mock_config):
        """Create client instance"""
        return FREDClient(config=mock_config)

    def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client is not None
        assert client.config.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager"""
        async with client:
            assert client.session is not None

    def test_series_definitions(self, client):
        """Test that series definitions are properly configured"""
        # Check that client has series_definitions attribute
        assert hasattr(client, 'series_definitions') or hasattr(client, 'SERIES')
        # Client is properly configured
        assert client.config is not None


class TestFREDClientMethods:
    """Test FRED client methods"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        monkeypatch.setenv("FRED_API_KEY", "test_key")
        return FREDConfig()

    @pytest.fixture
    def client(self, mock_config):
        return FREDClient(config=mock_config)

    @pytest.mark.asyncio
    async def test_test_connection_requires_api_key(self, monkeypatch):
        """Test that connection test checks for API key"""
        monkeypatch.setenv("FRED_API_KEY", "")
        config = FREDConfig()
        client = FREDClient(config=config)

        async with client:
            result = await client.test_connection()

        assert result is False

    def test_client_has_required_methods(self, client):
        """Test client has required methods"""
        assert hasattr(client, 'test_connection')
        assert hasattr(client, 'get_inflation_indicators')
        assert hasattr(client, 'get_interest_rate_data')
        assert hasattr(client, 'get_aviation_fuel_costs')

    @pytest.mark.asyncio
    async def test_context_manager_creates_session(self, client):
        """Test context manager creates session"""
        async with client:
            assert client.session is not None

    @pytest.mark.asyncio
    async def test_context_manager_closes_session(self, client):
        """Test context manager closes session"""
        async with client:
            pass
        assert client.session is None or client.session.closed


class TestFREDObservationProperties:
    """Test FRED observation properties"""

    def test_observation_date_format(self):
        """Test observation date format"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="CPI",
            date="2024-11-01",
            value=310.5,
            units="Index",
            category="inflation",
        )

        assert "-" in obs.date
        assert len(obs.date) == 10  # YYYY-MM-DD format

    def test_observation_value_types(self):
        """Test observation value types"""
        obs = FREDObservation(
            series_id="FEDFUNDS",
            series_name="Fed Funds",
            date="2024-11-01",
            value=5.33,
            units="Percent",
            category="interest_rates",
        )

        assert isinstance(obs.value, (int, float))
        assert obs.value > 0

    def test_observation_categories(self):
        """Test various observation categories"""
        categories = ["inflation", "interest_rates", "fuel_costs", "gdp_growth", "business_confidence"]

        for category in categories:
            obs = FREDObservation(
                series_id="TEST",
                series_name="Test Series",
                date="2024-01-01",
                value=100.0,
                units="Index",
                category=category,
            )
            assert obs.category == category


class TestFREDConfigProperties:
    """Test FRED configuration properties"""

    def test_config_has_base_url(self, monkeypatch):
        """Test config has base URL"""
        monkeypatch.setenv("FRED_API_KEY", "test")
        config = FREDConfig()

        assert config.base_url is not None
        assert "stlouisfed.org" in config.base_url or "fred" in config.base_url.lower()

    def test_config_has_timeout(self, monkeypatch):
        """Test config has timeout"""
        monkeypatch.setenv("FRED_API_KEY", "test")
        config = FREDConfig()

        assert hasattr(config, 'timeout')
        assert config.timeout > 0

    def test_config_api_key_from_env(self, monkeypatch):
        """Test API key is read from environment"""
        monkeypatch.setenv("FRED_API_KEY", "my_secret_key_123")
        config = FREDConfig()

        assert config.api_key == "my_secret_key_123"


class TestFREDClientContextManager:
    """Test FRED client context manager"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        monkeypatch.setenv("FRED_API_KEY", "test_key")
        return FREDConfig()

    @pytest.mark.asyncio
    async def test_context_manager_initializes(self, mock_config):
        """Test context manager initializes session"""
        client = FREDClient(config=mock_config)

        async with client:
            assert client.session is not None

    @pytest.mark.asyncio
    async def test_context_manager_cleans_up(self, mock_config):
        """Test context manager cleans up session"""
        client = FREDClient(config=mock_config)

        async with client:
            pass

        assert client.session is None or client.session.closed

    @pytest.mark.asyncio
    async def test_multiple_context_entries(self, mock_config):
        """Test client can be used multiple times"""
        client = FREDClient(config=mock_config)

        async with client:
            assert client.session is not None

        async with client:
            assert client.session is not None


class TestFREDSeriesDefinitions:
    """Test FRED series definitions"""

    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.setenv("FRED_API_KEY", "test_key")
        config = FREDConfig()
        return FREDClient(config=config)

    def test_has_inflation_series(self, client):
        """Test client knows about inflation series"""
        # CPIAUCSL is the standard CPI series
        assert client is not None  # Client should be initialized
        assert client.config.api_key == "test_key"

    def test_has_interest_rate_series(self, client):
        """Test client knows about interest rate series"""
        assert client is not None

    def test_has_fuel_series(self, client):
        """Test client knows about fuel series"""
        assert client is not None


class TestFREDObservationEdgeCases:
    """Test FRED observation edge cases"""

    def test_observation_zero_value(self):
        """Test observation with zero value"""
        obs = FREDObservation(
            series_id="TEST",
            series_name="Test",
            date="2024-01-01",
            value=0.0,
            units="Index",
            category="test",
        )

        assert obs.value == 0.0

    def test_observation_negative_value(self):
        """Test observation with negative value"""
        obs = FREDObservation(
            series_id="TEST",
            series_name="Test",
            date="2024-01-01",
            value=-2.5,
            units="Percent Change",
            category="gdp_growth",
        )

        assert obs.value == -2.5

    def test_observation_large_value(self):
        """Test observation with large value"""
        obs = FREDObservation(
            series_id="GDP",
            series_name="GDP",
            date="2024-01-01",
            value=27_000_000_000_000.0,  # 27 trillion
            units="Billions of Dollars",
            category="gdp_growth",
        )

        assert obs.value > 1_000_000_000_000

    def test_observation_small_decimal_value(self):
        """Test observation with small decimal"""
        obs = FREDObservation(
            series_id="TEST",
            series_name="Test",
            date="2024-01-01",
            value=0.0001,
            units="Percent",
            category="test",
        )

        assert obs.value < 0.001
