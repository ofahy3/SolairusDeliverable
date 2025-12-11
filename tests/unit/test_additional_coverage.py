"""
Additional tests for coverage improvement
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Test AI Generator additional coverage
from solairus_intelligence.ai.generator import AIConfig, AIUsageTracker, SecureAIGenerator


class TestAIGeneratorAdditional:
    """Additional tests for AI generator"""

    @pytest.fixture
    def disabled_generator(self):
        """Create generator with AI disabled"""
        config = AIConfig(api_key="test_key", enabled=False)
        return SecureAIGenerator(config)

    def test_generator_creates_validator(self, disabled_generator):
        """Test generator creates fact validator"""
        assert disabled_generator.validator is not None

    def test_generator_creates_sanitizer(self, disabled_generator):
        """Test generator creates PII sanitizer"""
        assert disabled_generator.sanitizer is not None

    def test_generator_has_generate_methods(self, disabled_generator):
        """Test generator has expected methods"""
        assert hasattr(disabled_generator, "generate_executive_summary")
        assert callable(disabled_generator.generate_executive_summary)


class TestUsageTrackerAdditional:
    """Additional tests for usage tracker"""

    @pytest.fixture
    def tracker(self):
        return AIUsageTracker()

    def test_multiple_requests(self, tracker):
        """Test logging multiple requests"""
        for i in range(5):
            tracker.log_request(100, 50, True)

        assert tracker.total_requests == 5
        assert tracker.total_input_tokens == 500
        assert tracker.total_output_tokens == 250

    def test_summary_keys(self, tracker):
        """Test summary contains expected keys"""
        tracker.log_request(100, 50, True)
        summary = tracker.get_summary()

        assert "total_requests" in summary
        assert "successful_requests" in summary
        assert "failed_requests" in summary
        assert "total_input_tokens" in summary
        assert "total_output_tokens" in summary
        assert "total_cost_usd" in summary


from solairus_intelligence.config.clients import ClientSector

# Test processor module additional coverage
from solairus_intelligence.core.processors.base import IntelligenceItem, SectorIntelligence


class TestIntelligenceItemAdditional:
    """Additional tests for IntelligenceItem"""

    def test_item_with_all_fields(self):
        """Test creating item with all fields"""
        item = IntelligenceItem(
            raw_content="Raw content here",
            processed_content="Processed content",
            category="economic",
            relevance_score=0.9,
            so_what_statement="This is important",
            affected_sectors=[ClientSector.TECHNOLOGY, ClientSector.FINANCE],
            confidence=0.95,
            source_type="ergomind",
            action_items=["Action 1", "Action 2"],
        )

        assert item.raw_content == "Raw content here"
        assert item.confidence == 0.95
        assert len(item.affected_sectors) == 2
        assert len(item.action_items) == 2

    def test_item_default_confidence(self):
        """Test item default confidence"""
        item = IntelligenceItem(
            raw_content="Raw",
            processed_content="Processed",
            category="test",
            relevance_score=0.5,
            so_what_statement="Impact",
            affected_sectors=[ClientSector.GENERAL],
        )
        # Check that confidence exists (may or may not be 0)
        assert hasattr(item, "confidence")


class TestSectorIntelligenceAdditional:
    """Additional tests for SectorIntelligence"""

    def test_sector_intelligence_empty(self):
        """Test sector intelligence with no items"""
        intel = SectorIntelligence(
            sector=ClientSector.TECHNOLOGY,
            items=[],
            summary="",
        )

        assert len(intel.items) == 0
        assert intel.summary == ""

    def test_sector_intelligence_full(self):
        """Test sector intelligence with items"""
        items = [
            IntelligenceItem(
                raw_content="Item 1",
                processed_content="Processed 1",
                category="tech",
                relevance_score=0.8,
                so_what_statement="Impact 1",
                affected_sectors=[ClientSector.TECHNOLOGY],
            )
        ]
        intel = SectorIntelligence(
            sector=ClientSector.TECHNOLOGY,
            items=items,
            summary="Tech sector summary",
            key_risks=["Risk 1"],
            key_opportunities=["Opportunity 1"],
        )

        assert len(intel.items) == 1
        assert intel.summary == "Tech sector summary"
        assert len(intel.key_risks) == 1
        assert len(intel.key_opportunities) == 1


# Test CLI module
from solairus_intelligence.cli import SolairusIntelligenceGenerator


class TestCLIAdditional:
    """Additional CLI tests"""

    def test_generator_initialization(self):
        """Test SolairusIntelligenceGenerator initializes"""
        gen = SolairusIntelligenceGenerator()
        assert gen is not None
        assert gen.client is not None
        assert gen.orchestrator is not None
        assert gen.merger is not None
        assert gen.generator is not None

    def test_generator_has_generate_method(self):
        """Test generator has generate method"""
        gen = SolairusIntelligenceGenerator()
        assert hasattr(gen, "generate_monthly_report")
        assert callable(gen.generate_monthly_report)

    def test_generator_initial_status(self):
        """Test generator initial status is None"""
        gen = SolairusIntelligenceGenerator()
        assert gen.last_run_status is None


# Test config module additional coverage
from solairus_intelligence.utils.config import (
    ENV_CONFIG,
    EnvironmentConfig,
    get_config,
    get_output_dir,
)


class TestConfigAdditional:
    """Additional config tests"""

    def test_get_config_returns_env_config(self):
        """Test get_config returns EnvironmentConfig"""
        config = get_config()
        assert isinstance(config, EnvironmentConfig)

    def test_output_dir_creates_path(self):
        """Test output dir returns Path object"""
        from pathlib import Path

        output_dir = get_output_dir()
        assert isinstance(output_dir, Path)

    def test_env_config_global(self):
        """Test ENV_CONFIG global is EnvironmentConfig"""
        assert isinstance(ENV_CONFIG, EnvironmentConfig)


# Test orchestrator module additional coverage
from solairus_intelligence.core.orchestrator import QueryTemplate


class TestQueryTemplateAdditional:
    """Additional tests for QueryTemplate"""

    def test_query_template_categories(self):
        """Test query template categories"""
        assert QueryTemplate is not None

    def test_create_aviation_template(self):
        """Test creating aviation template"""
        template = QueryTemplate(
            category="aviation",
            query="aviation safety",
            priority=1,
        )
        assert template.category == "aviation"
        assert template.priority == 1

    def test_create_economic_template(self):
        """Test creating economic template"""
        template = QueryTemplate(
            category="economic",
            query="inflation rates",
            priority=2,
        )
        assert template.category == "economic"


# Test FRED client additional coverage
from solairus_intelligence.clients.fred_client import FREDClient, FREDConfig, FREDObservation


class TestFREDClientAdditional:
    """Additional FRED client tests"""

    def test_fred_config_defaults(self):
        """Test FRED config defaults"""
        config = FREDConfig()
        assert "api.stlouisfed.org" in config.base_url
        assert config.timeout > 0

    def test_fred_observation_creation(self):
        """Test creating FRED observation"""
        obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-01-01",
            units="Index",
            category="inflation",
        )
        assert obs.series_id == "CPIAUCSL"
        assert obs.value == 310.5
        assert obs.category == "inflation"

    @pytest.mark.asyncio
    async def test_fred_client_context_manager(self):
        """Test FRED client context manager"""
        config = FREDConfig(api_key="test_key")
        client = FREDClient(config)
        async with client:
            assert client.session is not None


# Test ergomind client additional coverage
from solairus_intelligence.clients.ergomind_client import ErgoMindClient, ErgoMindConfig


class TestErgoMindClientAdditional:
    """Additional ErgoMind client tests"""

    def test_ergomind_config_defaults(self):
        """Test ErgoMind config defaults"""
        config = ErgoMindConfig()
        assert config.timeout > 0
        assert config.max_retries > 0

    def test_ergomind_config_custom(self):
        """Test ErgoMind config with custom values"""
        config = ErgoMindConfig(
            api_key="test_key",
            user_id="test_user",
            timeout=60,
            max_retries=5,
        )
        assert config.api_key == "test_key"
        assert config.timeout == 60

    @pytest.mark.asyncio
    async def test_ergomind_client_context_manager(self):
        """Test ErgoMind client context manager"""
        config = ErgoMindConfig(api_key="test_key", user_id="test_user")
        client = ErgoMindClient(config)
        async with client:
            assert client.session is not None
