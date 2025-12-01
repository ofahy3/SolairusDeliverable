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
