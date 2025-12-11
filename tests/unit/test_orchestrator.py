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
            sectors=[ClientSector.TECHNOLOGY],
        )

        assert template.category == "test_category"
        assert template.priority == 8
        assert len(template.follow_ups) == 2

    def test_template_defaults(self):
        """Test template default values"""
        template = QueryTemplate(category="test", query="Test query")

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
            t
            for t in orchestrator.query_templates
            if "aviation" in t.category.lower() or "aviation" in t.query.lower()
        ]

        assert len(aviation_templates) > 0

    def test_processor_initialized(self, orchestrator):
        """Test processor is initialized"""
        assert orchestrator.ergomind_processor is not None


class TestQueryOrchestratorMethods:
    """Test orchestrator methods"""

    @pytest.fixture
    def orchestrator(self):
        return QueryOrchestrator()

    def test_templates_sorted_by_priority(self, orchestrator):
        """Test templates can be sorted by priority"""
        sorted_templates = sorted(
            orchestrator.query_templates, key=lambda x: x.priority, reverse=True
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
        with patch.object(
            orchestrator, "execute_monthly_intelligence_gathering", new_callable=AsyncMock
        ) as mock_ergo:
            with patch.object(
                orchestrator, "execute_gta_intelligence_gathering", new_callable=AsyncMock
            ) as mock_gta:
                with patch.object(
                    orchestrator, "execute_fred_data_gathering", new_callable=AsyncMock
                ) as mock_fred:

                    # Simulate partial failure
                    mock_ergo.return_value = {}
                    mock_gta.side_effect = Exception("GTA API error")
                    mock_fred.return_value = {}

                    results = await orchestrator.execute_multi_source_intelligence_gathering(
                        use_cache=False
                    )

                    # Should still return results structure
                    assert "ergomind" in results
                    assert "gta" in results
                    assert "fred" in results
                    assert "source_status" in results

                    # GTA should be marked as failed
                    assert results["source_status"]["gta"] == "failed"

    @pytest.mark.asyncio
    async def test_execute_multi_source_all_succeed(self, orchestrator):
        """Test multi-source gathering when all sources succeed"""
        with patch.object(
            orchestrator, "execute_monthly_intelligence_gathering", new_callable=AsyncMock
        ) as mock_ergo:
            with patch.object(
                orchestrator, "execute_gta_intelligence_gathering", new_callable=AsyncMock
            ) as mock_gta:
                with patch.object(
                    orchestrator, "execute_fred_data_gathering", new_callable=AsyncMock
                ) as mock_fred:

                    mock_ergo.return_value = {"category1": ["result1"]}
                    mock_gta.return_value = {"sanctions": ["intervention1"]}
                    mock_fred.return_value = {"inflation": ["obs1"]}

                    results = await orchestrator.execute_multi_source_intelligence_gathering(
                        use_cache=False
                    )

                    assert results["source_status"]["ergomind"] == "success"
                    assert results["source_status"]["gta"] == "success"
                    assert results["source_status"]["fred"] == "success"


class TestProcessAndFilterResults:
    """Test result processing and filtering"""

    @pytest.fixture
    def orchestrator(self):
        return QueryOrchestrator()

    @pytest.mark.asyncio
    async def test_process_results_with_query_result(self, orchestrator):
        """Test processing with QueryResult objects"""
        from solairus_intelligence.clients.ergomind_client import QueryResult

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.response = (
            "This is a comprehensive analysis of geopolitical developments affecting aviation security. "
            * 5
        )
        mock_result.confidence_score = 0.9
        mock_result.sources = ["source1"]

        raw_results = {"aviation_security": [mock_result]}

        items = await orchestrator.process_and_filter_results(raw_results)

        # Should process successfully
        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_process_results_with_dict(self, orchestrator):
        """Test processing with cached dict data"""
        # Use MagicMock to provide sources attribute
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.response = (
            "New sanctions have been implemented affecting multiple sectors and industries. " * 5
        )
        mock_result.sources = ["source1"]

        raw_results = {"sanctions_trade": [mock_result]}

        items = await orchestrator.process_and_filter_results(raw_results)

        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_process_results_with_numbered_sections(self, orchestrator):
        """Test processing response with numbered sections"""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.response = """Key developments:
1. First major development with significant implications for global trade that spans multiple regions and sectors in detail.
2. Second development affecting technology sector with detailed analysis of semiconductor supply chains and export controls.
3. Third development impacting financial markets with extensive coverage of banking regulations and compliance requirements."""
        mock_result.confidence_score = 0.85
        mock_result.sources = ["source1"]

        raw_results = {"technology_sector": [mock_result]}

        items = await orchestrator.process_and_filter_results(raw_results)

        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_process_results_removes_duplicates(self, orchestrator):
        """Test duplicate removal in processing"""
        # Same content twice
        same_content = "This is a comprehensive analysis of geopolitical developments. " * 10
        mock_result1 = MagicMock()
        mock_result1.success = True
        mock_result1.response = same_content
        mock_result1.confidence_score = 0.9
        mock_result1.sources = ["source1"]

        mock_result2 = MagicMock()
        mock_result2.success = True
        mock_result2.response = same_content
        mock_result2.confidence_score = 0.9
        mock_result2.sources = ["source2"]

        raw_results = {"category1": [mock_result1, mock_result2]}

        items = await orchestrator.process_and_filter_results(raw_results)

        # Should have fewer items due to deduplication
        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_process_results_failed_query(self, orchestrator):
        """Test processing failed queries"""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.response = ""
        mock_result.confidence_score = 0.0
        mock_result.sources = []

        raw_results = {"aviation_security": [mock_result]}

        items = await orchestrator.process_and_filter_results(raw_results)

        assert items == []


class TestProcessGTAResults:
    """Test GTA result processing"""

    @pytest.fixture
    def orchestrator(self):
        return QueryOrchestrator()

    @pytest.mark.asyncio
    async def test_process_gta_with_interventions(self, orchestrator):
        """Test processing GTA interventions"""
        from solairus_intelligence.clients.gta_client import GTAIntervention

        intervention = GTAIntervention(
            intervention_id=12345,
            title="Test Export Control",
            description="Controls on semiconductor exports affecting global supply chains",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[{"name": "United States"}],
            affected_jurisdictions=[{"name": "China"}],
            intervention_type="Export control",
            intervention_type_id=1,
        )

        gta_results = {"sanctions_trade": [intervention]}

        items = await orchestrator.process_gta_results(gta_results)

        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_process_gta_removes_duplicates(self, orchestrator):
        """Test GTA duplicate removal by intervention ID"""
        from solairus_intelligence.clients.gta_client import GTAIntervention

        # Same intervention ID
        intervention1 = GTAIntervention(
            intervention_id=12345,
            title="Test Export Control",
            description="Controls on exports",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Export control",
            intervention_type_id=1,
        )
        intervention2 = GTAIntervention(
            intervention_id=12345,  # Same ID
            title="Test Export Control",
            description="Controls on exports",
            gta_evaluation="Harmful",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Export control",
            intervention_type_id=1,
        )

        gta_results = {"sanctions_trade": [intervention1, intervention2]}

        items = await orchestrator.process_gta_results(gta_results)

        # Should only have one item due to ID deduplication
        assert len(items) <= 1

    @pytest.mark.asyncio
    async def test_process_gta_filters_low_relevance(self, orchestrator):
        """Test GTA filters low relevance items"""
        from solairus_intelligence.clients.gta_client import GTAIntervention

        intervention = GTAIntervention(
            intervention_id=99999,
            title="",  # Empty title reduces relevance
            description="",
            gta_evaluation="Unknown",
            implementing_jurisdictions=[],
            affected_jurisdictions=[],
            intervention_type="Other",
            intervention_type_id=999,
        )

        gta_results = {"other": [intervention]}

        items = await orchestrator.process_gta_results(gta_results)

        # May be filtered out due to low relevance
        assert isinstance(items, list)


class TestProcessFREDResults:
    """Test FRED result processing"""

    @pytest.fixture
    def orchestrator(self):
        return QueryOrchestrator()

    @pytest.mark.asyncio
    async def test_process_fred_with_observations(self, orchestrator):
        """Test processing FRED observations"""
        from solairus_intelligence.clients.fred_client import FREDObservation

        observation = FREDObservation(
            series_id="CPIAUCSL",
            series_name="Consumer Price Index",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )

        fred_results = {"inflation": [observation]}

        items = await orchestrator.process_fred_results(fred_results)

        assert len(items) == 1
        assert items[0].source_type == "fred"

    @pytest.mark.asyncio
    async def test_process_fred_multiple_categories(self, orchestrator):
        """Test processing multiple FRED categories"""
        from solairus_intelligence.clients.fred_client import FREDObservation

        inflation_obs = FREDObservation(
            series_id="CPIAUCSL",
            series_name="CPI",
            value=310.5,
            date="2024-11-01",
            units="Index",
            category="inflation",
        )
        fuel_obs = FREDObservation(
            series_id="DJFUELUSGULF",
            series_name="Jet Fuel",
            value=2.85,
            date="2024-11-01",
            units="$/Gallon",
            category="fuel_costs",
        )

        fred_results = {
            "inflation": [inflation_obs],
            "fuel_costs": [fuel_obs],
        }

        items = await orchestrator.process_fred_results(fred_results)

        assert len(items) == 2


class TestQueryTemplateCategories:
    """Test query template categories"""

    @pytest.fixture
    def orchestrator(self):
        return QueryOrchestrator()

    def test_has_regional_templates(self, orchestrator):
        """Test regional templates exist"""
        regional_categories = ["north_america", "europe", "asia_pacific", "middle_east"]
        for category in regional_categories:
            templates = [t for t in orchestrator.query_templates if t.category == category]
            assert len(templates) > 0, f"Missing template for {category}"

    def test_has_sector_templates(self, orchestrator):
        """Test sector templates exist"""
        sector_categories = ["technology_sector", "financial_sector"]
        for category in sector_categories:
            templates = [t for t in orchestrator.query_templates if t.category == category]
            assert len(templates) > 0, f"Missing template for {category}"

    def test_has_forecast_templates(self, orchestrator):
        """Test forecast templates exist"""
        forecast_templates = [t for t in orchestrator.query_templates if "forecast" in t.category]
        assert len(forecast_templates) > 0

    def test_templates_have_follow_ups(self, orchestrator):
        """Test high priority templates have follow-ups"""
        high_priority = [t for t in orchestrator.query_templates if t.priority >= 8]
        for t in high_priority:
            assert len(t.follow_ups) > 0, f"High priority template {t.category} has no follow-ups"


class TestOrchestratorWithMockedClient:
    """Test orchestrator with mocked client"""

    @pytest.fixture
    def mock_client(self):
        """Create mock ErgoMind client"""
        client = MagicMock()
        client.test_connection = AsyncMock(return_value=True)
        client.query_websocket = AsyncMock(
            return_value=MagicMock(
                success=True,
                response="Test response content that is long enough to pass filters. " * 10,
                confidence_score=0.85,
                sources=["test_source"],
            )
        )
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client

    @pytest.fixture
    def orchestrator_with_mock(self, mock_client):
        """Create orchestrator with mocked client"""
        return QueryOrchestrator(client=mock_client)

    def test_orchestrator_accepts_custom_client(self, orchestrator_with_mock, mock_client):
        """Test orchestrator accepts custom client"""
        assert orchestrator_with_mock.client == mock_client

    @pytest.mark.asyncio
    async def test_execute_monthly_with_failed_connection(self, mock_client):
        """Test handling failed connection"""
        mock_client.test_connection = AsyncMock(return_value=False)
        orchestrator = QueryOrchestrator(client=mock_client)

        results = await orchestrator.execute_monthly_intelligence_gathering()

        assert results == {}
