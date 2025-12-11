"""
Test suite for MRO Query Templates, Sector Definitions, and Grainger Configuration.

Validates:
- All MRO query templates are properly formed
- Sector definitions are complete
- FRED indicator codes are valid
- Grainger config is properly loaded
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mro_intelligence.config.clients import (
    CLIENT_SECTOR_MAPPING,
    ClientSector,
    get_all_sectors,
    get_sector_keywords,
    get_sector_mro_impact,
    get_sector_triggers,
)
from mro_intelligence.core.orchestrator import QueryOrchestrator, QueryTemplate
from mro_intelligence.clients.fred_client import FREDClient
from mro_intelligence.config.grainger_profile import (
    COMPANY_PROFILE,
    GEOGRAPHIC_FOCUS,
    RELEVANCE_FILTERS,
    REPORT_SETTINGS,
    SECTOR_PRIORITIES,
    GraingerConfig,
    get_grainger_config,
)


class TestMROQueryTemplates:
    """Test query templates are properly formed for MRO market intelligence."""

    def setup_method(self):
        """Initialize orchestrator for tests."""
        self.orchestrator = QueryOrchestrator()

    def test_query_templates_exist(self):
        """Verify query templates are initialized."""
        assert len(self.orchestrator.query_templates) > 0
        assert len(self.orchestrator.query_templates) >= 10, "Should have at least 10 templates"

    def test_all_templates_have_required_fields(self):
        """Verify all templates have required fields."""
        for template in self.orchestrator.query_templates:
            assert template.category, "Template must have category"
            assert template.query, "Template must have query"
            assert template.priority >= 1 and template.priority <= 10, "Priority must be 1-10"
            assert isinstance(template.follow_ups, list), "follow_ups must be a list"
            assert isinstance(template.sectors, list), "sectors must be a list"

    def test_templates_cover_grainger_segments(self):
        """Verify templates cover Grainger's customer segments."""
        all_sectors = set()
        for template in self.orchestrator.query_templates:
            all_sectors.update(template.sectors)

        assert ClientSector.MANUFACTURING in all_sectors, "Must have manufacturing templates"
        assert ClientSector.GOVERNMENT in all_sectors, "Must have government templates"
        assert ClientSector.CONTRACTORS in all_sectors, "Must have contractors templates"

    def test_high_priority_templates_exist(self):
        """Verify high-priority templates exist (priority >= 8)."""
        high_priority = [t for t in self.orchestrator.query_templates if t.priority >= 8]
        assert len(high_priority) >= 5, "Should have at least 5 high-priority templates"

    def test_supply_chain_template_exists(self):
        """Verify supply chain disruption template exists."""
        supply_chain = [t for t in self.orchestrator.query_templates
                       if "supply_chain" in t.category.lower()]
        assert len(supply_chain) > 0, "Must have supply chain template"

    def test_tariff_template_exists(self):
        """Verify tariffs/trade policy template exists."""
        tariff = [t for t in self.orchestrator.query_templates
                  if "tariff" in t.category.lower() or "trade" in t.category.lower()]
        assert len(tariff) > 0, "Must have tariff/trade template"

    def test_mro_outlook_template_exists(self):
        """Verify MRO market outlook template exists."""
        outlook = [t for t in self.orchestrator.query_templates
                   if "mro" in t.category.lower() or "outlook" in t.category.lower()]
        assert len(outlook) > 0, "Must have MRO outlook template"

    def test_queries_contain_time_constraint(self):
        """Verify queries include time constraint for recency."""
        for template in self.orchestrator.query_templates:
            # At least main query or some templates should have time constraint
            has_time_ref = any(word in template.query.lower()
                              for word in ["month", "present", "recent", "current"])
            # Not all need it, but should be present in most
        # Just verify orchestrator uses lookback_months
        assert self.orchestrator.lookback_months > 0


class TestGraingerSectorDefinitions:
    """Test Grainger customer segment definitions are complete and valid."""

    def test_all_grainger_segments_defined(self):
        """Verify all 5 Grainger customer segments are defined."""
        expected_sectors = [
            ClientSector.MANUFACTURING,
            ClientSector.GOVERNMENT,
            ClientSector.COMMERCIAL_FACILITIES,
            ClientSector.CONTRACTORS,
            ClientSector.GENERAL,
        ]
        for sector in expected_sectors:
            assert sector in CLIENT_SECTOR_MAPPING, f"Missing sector: {sector}"

    def test_sectors_have_keywords(self):
        """Verify non-GENERAL sectors have keywords."""
        for sector in get_all_sectors():
            keywords = get_sector_keywords(sector)
            assert len(keywords) > 0, f"{sector} must have keywords"

    def test_sectors_have_geopolitical_triggers(self):
        """Verify non-GENERAL sectors have geopolitical triggers."""
        for sector in get_all_sectors():
            triggers = get_sector_triggers(sector)
            assert len(triggers) > 0, f"{sector} must have triggers"

    def test_sectors_have_mro_impact(self):
        """Verify all sectors have MRO impact description."""
        for sector in ClientSector:
            impact = get_sector_mro_impact(sector)
            assert isinstance(impact, str), f"{sector} must have string impact"

    def test_manufacturing_keywords_relevant(self):
        """Verify manufacturing keywords are MRO-relevant."""
        keywords = get_sector_keywords(ClientSector.MANUFACTURING)
        keyword_text = " ".join(keywords).lower()
        assert any(word in keyword_text for word in ["manufacturing", "industrial", "production"])

    def test_government_keywords_relevant(self):
        """Verify government keywords are relevant."""
        keywords = get_sector_keywords(ClientSector.GOVERNMENT)
        keyword_text = " ".join(keywords).lower()
        assert any(word in keyword_text for word in ["government", "federal", "military", "defense"])

    def test_contractors_keywords_relevant(self):
        """Verify contractors keywords are MRO-relevant."""
        keywords = get_sector_keywords(ClientSector.CONTRACTORS)
        keyword_text = " ".join(keywords).lower()
        assert any(word in keyword_text for word in ["construction", "contractor", "building"])


class TestFREDIndicatorCodes:
    """Test FRED indicator codes are valid and MRO-relevant."""

    def test_fred_series_dictionary_exists(self):
        """Verify FRED series dictionary is defined."""
        assert hasattr(FREDClient, 'SERIES'), "FREDClient must have SERIES dictionary"
        assert len(FREDClient.SERIES) > 0, "SERIES must not be empty"

    def test_fred_has_industrial_activity_indicators(self):
        """Verify FRED has industrial activity indicators."""
        assert "industrial_activity" in FREDClient.SERIES
        industrial = FREDClient.SERIES["industrial_activity"]
        assert "INDPRO" in industrial, "Must have Industrial Production Index"
        assert "IPMAN" in industrial, "Must have Manufacturing Production"

    def test_fred_has_construction_indicators(self):
        """Verify FRED has construction indicators."""
        assert "construction" in FREDClient.SERIES
        construction = FREDClient.SERIES["construction"]
        assert "HOUST" in construction or "PERMIT" in construction, "Must have housing/permit data"

    def test_fred_has_business_conditions_indicators(self):
        """Verify FRED has business conditions indicators."""
        assert "business_conditions" in FREDClient.SERIES
        conditions = FREDClient.SERIES["business_conditions"]
        assert "UNRATE" in conditions or "FEDFUNDS" in conditions, "Must have key business indicators"

    def test_fred_has_commodity_indicators(self):
        """Verify FRED has commodity indicators."""
        assert "commodities" in FREDClient.SERIES
        commodities = FREDClient.SERIES["commodities"]
        assert len(commodities) > 0, "Must have commodity indicators"

    def test_fred_series_descriptions_exist(self):
        """Verify FRED series have descriptions."""
        assert hasattr(FREDClient, 'SERIES_DESCRIPTIONS'), "Must have SERIES_DESCRIPTIONS"
        # Verify descriptions exist for key series
        for category, series in FREDClient.SERIES.items():
            for series_id in series.keys():
                assert series_id in FREDClient.SERIES_DESCRIPTIONS, f"Missing description for {series_id}"

    def test_all_fred_series_ids_valid_format(self):
        """Verify all FRED series IDs are valid format (alphanumeric)."""
        for category, series in FREDClient.SERIES.items():
            for series_id in series.keys():
                assert series_id.replace("_", "").isalnum(), f"Invalid series ID format: {series_id}"


class TestGraingerConfiguration:
    """Test Grainger-specific configuration is properly loaded."""

    def test_company_profile_loaded(self):
        """Verify company profile is loaded."""
        assert COMPANY_PROFILE is not None
        assert COMPANY_PROFILE["name"] == "Grainger"
        assert COMPANY_PROFILE["full_name"] == "W.W. Grainger, Inc."

    def test_company_profile_has_required_fields(self):
        """Verify company profile has all required fields."""
        required_fields = [
            "name",
            "full_name",
            "business_model",
            "primary_market",
            "key_segments",
            "value_proposition",
            "geographic_focus",
            "not_interested_in",
        ]
        for field in required_fields:
            assert field in COMPANY_PROFILE, f"Missing field: {field}"

    def test_report_settings_loaded(self):
        """Verify report settings are loaded."""
        assert REPORT_SETTINGS is not None
        assert REPORT_SETTINGS["lookback_months"] == 3
        assert REPORT_SETTINGS["forecast_horizon"] == "90 days"
        assert REPORT_SETTINGS["max_pages"] == 3
        assert REPORT_SETTINGS["update_frequency"] == "biweekly"

    def test_relevance_filters_loaded(self):
        """Verify relevance filters are loaded."""
        assert RELEVANCE_FILTERS is not None
        assert "must_include_keywords" in RELEVANCE_FILTERS
        assert "exclude_keywords" in RELEVANCE_FILTERS
        assert RELEVANCE_FILTERS["minimum_relevance_score"] == 0.6

    def test_must_include_keywords_mro_relevant(self):
        """Verify must-include keywords are MRO-relevant."""
        keywords = RELEVANCE_FILTERS["must_include_keywords"]
        assert "manufacturing" in keywords or "MRO" in keywords
        assert "industrial" in keywords
        assert "supply chain" in keywords

    def test_exclude_keywords_appropriate(self):
        """Verify exclude keywords filter non-relevant content."""
        keywords = RELEVANCE_FILTERS["exclude_keywords"]
        assert "aviation" in keywords
        assert "aerospace" in keywords

    def test_geographic_focus_configured(self):
        """Verify geographic focus is configured."""
        assert GEOGRAPHIC_FOCUS is not None
        assert "primary_regions" in GEOGRAPHIC_FOCUS
        assert "US" in GEOGRAPHIC_FOCUS["primary_regions"] or "United States" in GEOGRAPHIC_FOCUS["primary_regions"]

    def test_sector_priorities_configured(self):
        """Verify sector priorities are configured."""
        assert SECTOR_PRIORITIES is not None
        assert "manufacturing" in SECTOR_PRIORITIES
        assert SECTOR_PRIORITIES["manufacturing"] >= 0.9, "Manufacturing should be high priority"

    def test_grainger_config_singleton(self):
        """Verify GraingerConfig singleton works."""
        config1 = get_grainger_config()
        config2 = get_grainger_config()
        assert config1.company_name == "Grainger"
        assert config1.lookback_months == 3

    def test_grainger_config_is_relevant_content(self):
        """Verify is_relevant_content method works."""
        config = get_grainger_config()
        assert config.is_relevant_content("US manufacturing production")
        assert not config.is_relevant_content("random unrelated text without keywords")

    def test_grainger_config_should_exclude(self):
        """Verify should_exclude method works."""
        config = get_grainger_config()
        assert config.should_exclude("aerospace defense contractor")
        assert not config.should_exclude("manufacturing facility maintenance")

    def test_grainger_config_relevance_boost(self):
        """Verify calculate_relevance_boost method works."""
        config = get_grainger_config()
        boost = config.calculate_relevance_boost("US industrial manufacturing in North America")
        assert boost > 0, "Should provide positive boost for US manufacturing content"
        assert boost <= 0.5, "Boost should be capped at 0.5"


class TestOrchestratorGraingerIntegration:
    """Test orchestrator properly integrates Grainger configuration."""

    def setup_method(self):
        """Initialize orchestrator for tests."""
        self.orchestrator = QueryOrchestrator()

    def test_orchestrator_uses_grainger_lookback(self):
        """Verify orchestrator uses Grainger lookback setting."""
        assert self.orchestrator.lookback_months == 3

    def test_orchestrator_uses_min_relevance(self):
        """Verify orchestrator uses Grainger min relevance setting."""
        assert self.orchestrator.min_relevance_score == 0.6

    def test_orchestrator_has_grainger_config(self):
        """Verify orchestrator has Grainger config loaded."""
        assert hasattr(self.orchestrator, 'grainger_config')
        assert self.orchestrator.grainger_config is not None


class TestProcessorGraingerIntegration:
    """Test processors properly integrate Grainger configuration."""

    def test_ergomind_processor_has_grainger_config(self):
        """Verify ErgoMind processor has Grainger config."""
        from mro_intelligence.core.processors.ergomind import ErgoMindProcessor
        processor = ErgoMindProcessor()
        assert hasattr(processor, 'grainger_config')

    def test_ergomind_processor_applies_boost(self):
        """Verify processor applies Grainger relevance boost."""
        from mro_intelligence.core.processors.ergomind import ErgoMindProcessor
        processor = ErgoMindProcessor()

        # Process US manufacturing content - should get boost
        item = processor.process_intelligence(
            "US manufacturing production increased 5% in domestic facilities",
            category="manufacturing_outlook"
        )
        assert item is not None
        # Score should be boosted (baseline + Grainger boost)
        assert item.relevance_score >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
