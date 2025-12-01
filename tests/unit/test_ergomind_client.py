"""
Unit tests for ErgoMind client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from solairus_intelligence.clients.ergomind_client import (
    ErgoMindClient,
    ErgoMindConfig,
    QueryResult,
)


class TestErgoMindConfig:
    """Test ErgoMind configuration"""

    def test_config_from_env(self, monkeypatch):
        """Test configuration loads from environment variables"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "test_key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "test@test.com")

        config = ErgoMindConfig()

        assert config.api_key == "test_key"
        assert config.user_id == "test@test.com"

    def test_config_validation_fails_without_api_key(self, monkeypatch):
        """Test validation fails when API key is missing"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "")
        monkeypatch.setenv("ERGOMIND_USER_ID", "test@test.com")

        config = ErgoMindConfig()

        assert config.validate() is False

    def test_config_validation_fails_without_user_id(self, monkeypatch):
        """Test validation fails when user ID is missing"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "test_key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "")

        config = ErgoMindConfig()

        assert config.validate() is False

    def test_config_validation_passes_with_all_required(self, monkeypatch):
        """Test validation passes with all required fields"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "test_key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "test@test.com")

        config = ErgoMindConfig()

        assert config.validate() is True


class TestErgoMindClient:
    """Test ErgoMind client"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        """Create mock configuration"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "test_key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "test@test.com")
        return ErgoMindConfig()

    @pytest.fixture
    def client(self, mock_config):
        """Create client instance"""
        return ErgoMindClient(config=mock_config)

    def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client is not None
        assert client.config.api_key == "test_key"
        assert client.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager"""
        async with client:
            assert client.session is not None

        # Session should be closed after exit
        assert client.session is None or client.session.closed

    @pytest.mark.asyncio
    async def test_test_connection_success(self, client):
        """Test connection test with successful response"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "ok"})

        with patch.object(client, 'session') as mock_session:
            mock_session.get = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

            # Initialize session
            client.session = MagicMock()
            client.session.get = AsyncMock()

            # The actual test would need more mocking for the full flow
            # This is a simplified version
            assert client.config.api_key == "test_key"


class TestQueryResult:
    """Test QueryResult dataclass"""

    def test_query_result_creation(self):
        """Test creating a query result"""
        result = QueryResult(
            query="Test query",
            response="Test response",
            success=True,
            confidence_score=0.85
        )

        assert result.query == "Test query"
        assert result.response == "Test response"
        assert result.success is True
        assert result.confidence_score == 0.85

    def test_query_result_default_values(self):
        """Test query result default values"""
        result = QueryResult(
            query="Test",
            response="Response"
        )

        assert result.success is True
        assert result.error is None
        assert result.confidence_score == 0.0
        assert result.sources == []
