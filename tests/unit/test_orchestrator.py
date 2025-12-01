"""
Unit tests for Query Orchestrator
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from solairus_intelligence.core.orchestrator import (
    QueryOrchestrator,
    QueryTemplate,
)
from solairus_intelligence.core.processor import ClientSector


class TestQueryTemplate:
    """Test query template dataclass"""

    def test_template_creation(self):
        """Test creating a query template"""
        template = QueryTemplate(
            category="test_category",
            query="What are the latest developments?",
            follow_ups=["Follow up 1", "Follow up 2"],
            priority=8,
            sectors=[ClientSector.TECHNOLOGY]
        )

        assert template.category == "test_category"
        assert template.priority == 8
        assert len(template.follow_ups) == 2

    def test_template_defaults(self):
        """Test template default values"""
        template = QueryTemplate(
            category="test",
            query="Test query"
        )

        assert template.priority == 5
        assert template.follow_ups == []
        assert template.sectors == []


class TestQueryOrchestrator:
    """Test query orchestrator"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return QueryOrchestrator()

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator is not None
        assert orchestrator.query_templates is not None
        assert len(orchestrator.query_templates) > 0

    def test_query_templates_loaded(self, orchestrator):
        """Test that query templates are loaded"""
        templates = orchestrator.query_templates

        # Should have multiple templates
        assert len(templates) >= 5

        # Should have high-priority templates
        high_priority = [t for t in templates if t.priority >= 8]
        assert len(high_priority) > 0

    def test_query_templates_have_required_fields(self, orchestrator):
        """Test all templates have required fields"""
        for template in orchestrator.query_templates:
            assert template.category is not None
            assert template.query is not None
            assert len(template.query) > 10  # Meaningful query
            assert 1 <= template.priority <= 10

    def test_aviation_templates_exist(self, orchestrator):
        """Test aviation-related templates exist"""
        aviation_templates = [
            t for t in orchestrator.query_templates
            if "aviation" in t.category.lower() or "aviation" in t.query.lower()
        ]

        assert len(aviation_templates) > 0

    def test_processor_initialized(self, orchestrator):
        """Test processor is initialized"""
        assert orchestrator.processor is not None


class TestQueryOrchestratorMethods:
    """Test orchestrator methods"""

    @pytest.fixture
    def orchestrator(self):
        return QueryOrchestrator()

    def test_templates_sorted_by_priority(self, orchestrator):
        """Test templates can be sorted by priority"""
        sorted_templates = sorted(
            orchestrator.query_templates,
            key=lambda x: x.priority,
            reverse=True
        )

        # Highest priority should be first
        assert sorted_templates[0].priority >= sorted_templates[-1].priority

    @pytest.mark.asyncio
    async def test_process_and_filter_results_empty(self, orchestrator):
        """Test processing empty results"""
        empty_results = {}

        items = await orchestrator.process_and_filter_results(empty_results)

        assert items == []

    @pytest.mark.asyncio
    async def test_process_gta_results_empty(self, orchestrator):
        """Test processing empty GTA results"""
        empty_results = {}

        items = await orchestrator.process_gta_results(empty_results)

        assert items == []

    @pytest.mark.asyncio
    async def test_process_fred_results_empty(self, orchestrator):
        """Test processing empty FRED results"""
        empty_results = {}

        items = await orchestrator.process_fred_results(empty_results)

        assert items == []


class TestMultiSourceGathering:
    """Test multi-source intelligence gathering"""

    @pytest.fixture
    def orchestrator(self):
        return QueryOrchestrator()

    @pytest.mark.asyncio
    async def test_execute_multi_source_handles_failures(self, orchestrator):
        """Test multi-source gathering handles source failures gracefully"""
        # Mock the individual gathering methods to simulate failures
        with patch.object(orchestrator, 'execute_monthly_intelligence_gathering',
                         new_callable=AsyncMock) as mock_ergo:
            with patch.object(orchestrator, 'execute_gta_intelligence_gathering',
                             new_callable=AsyncMock) as mock_gta:
                with patch.object(orchestrator, 'execute_fred_data_gathering',
                                 new_callable=AsyncMock) as mock_fred:

                    # Simulate partial failure
                    mock_ergo.return_value = {}
                    mock_gta.side_effect = Exception("GTA API error")
                    mock_fred.return_value = {}

                    results = await orchestrator.execute_multi_source_intelligence_gathering(
                        use_cache=False
                    )

                    # Should still return results structure
                    assert 'ergomind' in results
                    assert 'gta' in results
                    assert 'fred' in results
                    assert 'source_status' in results

                    # GTA should be marked as failed
                    assert results['source_status']['gta'] == 'failed'
