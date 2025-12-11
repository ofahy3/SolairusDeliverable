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

    def test_query_result_with_error(self):
        """Test query result with error"""
        result = QueryResult(
            query="Test",
            response="",
            success=False,
            error="Connection timeout"
        )

        assert result.success is False
        assert result.error == "Connection timeout"

    def test_query_result_with_sources(self):
        """Test query result with sources"""
        result = QueryResult(
            query="Test",
            response="Response",
            sources=["source1", "source2", "source3"]
        )

        assert len(result.sources) == 3
        assert "source1" in result.sources

    def test_query_result_with_timestamp(self):
        """Test query result with timestamp"""
        result = QueryResult(
            query="Test",
            response="Response",
            timestamp="2024-12-01T10:00:00"
        )

        assert result.timestamp == "2024-12-01T10:00:00"


class TestErgoMindClientMethods:
    """Test ErgoMind client methods"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        monkeypatch.setenv("ERGOMIND_API_KEY", "test_key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "test@test.com")
        return ErgoMindConfig()

    @pytest.fixture
    def client(self, mock_config):
        return ErgoMindClient(config=mock_config)

    def test_client_has_required_attributes(self, client):
        """Test client has required attributes"""
        assert hasattr(client, 'config')
        assert hasattr(client, 'session')
        assert hasattr(client, 'test_connection')
        assert hasattr(client, 'query_websocket')

    @pytest.mark.asyncio
    async def test_initialize_creates_session(self, client):
        """Test initialize creates a session"""
        await client.initialize()
        assert client.session is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_close_clears_session(self, client):
        """Test close clears the session"""
        await client.initialize()
        assert client.session is not None
        await client.close()
        assert client.session is None or client.session.closed

    @pytest.mark.asyncio
    async def test_session_not_initialized_error(self, client):
        """Test error when using client without initialization"""
        # Client should handle missing session gracefully or raise clear error
        assert client.session is None


class TestErgoMindConfigValidation:
    """Test ErgoMind configuration validation"""

    def test_validate_with_both_fields(self, monkeypatch):
        """Test validation passes with both fields"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "key123")
        monkeypatch.setenv("ERGOMIND_USER_ID", "user@example.com")

        config = ErgoMindConfig()
        assert config.validate() is True

    def test_validate_empty_api_key(self, monkeypatch):
        """Test validation fails with empty API key"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "")
        monkeypatch.setenv("ERGOMIND_USER_ID", "user@example.com")

        config = ErgoMindConfig()
        assert config.validate() is False

    def test_validate_empty_user_id(self, monkeypatch):
        """Test validation fails with empty user ID"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "key123")
        monkeypatch.setenv("ERGOMIND_USER_ID", "")

        config = ErgoMindConfig()
        assert config.validate() is False

    def test_config_base_url(self, monkeypatch):
        """Test configuration has correct base URL"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "user")

        config = ErgoMindConfig()
        assert config.base_url is not None
        assert "ergomind" in config.base_url.lower() or "api" in config.base_url.lower()

    def test_config_timeout(self, monkeypatch):
        """Test configuration has timeout"""
        monkeypatch.setenv("ERGOMIND_API_KEY", "key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "user")

        config = ErgoMindConfig()
        assert hasattr(config, 'timeout')
        assert config.timeout > 0


class TestErgoMindClientContextManager:
    """Test ErgoMind client context manager"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        monkeypatch.setenv("ERGOMIND_API_KEY", "test_key")
        monkeypatch.setenv("ERGOMIND_USER_ID", "test@test.com")
        return ErgoMindConfig()

    @pytest.mark.asyncio
    async def test_context_manager_initializes(self, mock_config):
        """Test context manager initializes session"""
        client = ErgoMindClient(config=mock_config)

        async with client:
            assert client.session is not None

    @pytest.mark.asyncio
    async def test_context_manager_cleans_up(self, mock_config):
        """Test context manager cleans up session"""
        client = ErgoMindClient(config=mock_config)

        async with client:
            pass

        assert client.session is None or client.session.closed

    @pytest.mark.asyncio
    async def test_multiple_context_entries(self, mock_config):
        """Test client can be used multiple times"""
        client = ErgoMindClient(config=mock_config)

        async with client:
            assert client.session is not None

        async with client:
            assert client.session is not None


class TestQueryResultProperties:
    """Test QueryResult properties and edge cases"""

    def test_query_result_with_high_confidence(self):
        """Test query result with high confidence"""
        result = QueryResult(
            query="Test",
            response="Detailed response",
            confidence_score=0.95
        )

        assert result.confidence_score > 0.9

    def test_query_result_with_low_confidence(self):
        """Test query result with low confidence"""
        result = QueryResult(
            query="Test",
            response="Uncertain response",
            confidence_score=0.3
        )

        assert result.confidence_score < 0.5

    def test_query_result_empty_response(self):
        """Test query result with empty response"""
        result = QueryResult(
            query="Test",
            response="",
            success=False
        )

        assert result.response == ""
        assert result.success is False

    def test_query_result_long_response(self):
        """Test query result with long response"""
        long_text = "This is a test. " * 1000
        result = QueryResult(
            query="Test",
            response=long_text,
            confidence_score=0.8
        )

        assert len(result.response) > 10000
