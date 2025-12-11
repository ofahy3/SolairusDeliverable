"""
Test suite for Grainger-specific requirements alignment.

Validates that the codebase properly implements Grainger's specific requirements
per the client dossier and Jenna Anderson's explicit questions.

Tests:
- Query templates address Jenna's specific questions
- Sectors match Grainger's actual customer base
- Geographic focus is US/USMCA only
- Critical commodities (steel, aluminum) are tracked
- China tariff exposure is monitored
- Report structure supports Jenna's newsletter workflow
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
    get_sector_triggers,
)
from mro_intelligence.core.orchestrator import QueryOrchestrator, QueryTemplate
from mro_intelligence.clients.fred_client import FREDClient
from mro_intelligence.config.grainger_profile import (
    COMPANY_PROFILE,
    GEOGRAPHIC_FOCUS,
    RELEVANCE_FILTERS,
    REPORT_SETTINGS,
    REPORT_STRUCTURE,
    SECTOR_PRIORITIES,
    SO_WHAT_PROMPT,
    GraingerConfig,
    get_grainger_config,
    filter_for_geographic_relevance,
)


class TestJennaQuestionsAddressed:
    """Ensure query templates address Jenna Anderson's specific questions."""

    def setup_method(self):
        """Initialize orchestrator for tests."""
        self.orchestrator = QueryOrchestrator()

    def test_tariff_mro_impact_query_exists(self):
        """Verify tariff MRO impact query exists (Jenna's explicit ask)."""
        tariff_queries = [
            t for t in self.orchestrator.query_templates
            if "tariff" in t.category.lower() or "tariff" in t.query.lower()
        ]
        assert len(tariff_queries) > 0, "Must have tariff impact queries"
        # Should be high priority (Jenna's explicit ask)
        assert any(t.priority >= 9 for t in tariff_queries), "Tariff queries should be high priority"

    def test_us_mro_outlook_query_exists(self):
        """Verify US MRO outlook query exists (Jenna's explicit ask)."""
        outlook_queries = [
            t for t in self.orchestrator.query_templates
            if "mro" in t.query.lower() and "outlook" in t.query.lower()
        ]
        assert len(outlook_queries) > 0, "Must have MRO outlook query"

    def test_steel_mro_demand_query_exists(self):
        """Verify steel-MRO demand query exists (Jenna's explicit ask)."""
        steel_queries = [
            t for t in self.orchestrator.query_templates
            if "steel" in t.category.lower() or "steel" in t.query.lower()
        ]
        assert len(steel_queries) > 0, "Must have steel-MRO demand query"
        # Should be high priority (Jenna's explicit ask)
        assert any(t.priority >= 9 for t in steel_queries), "Steel queries should be high priority"

    def test_pricing_strategy_query_exists(self):
        """Verify pricing pass-through query exists (Jenna's explicit ask)."""
        pricing_queries = [
            t for t in self.orchestrator.query_templates
            if "pricing" in t.category.lower() or "pricing" in t.query.lower()
        ]
        assert len(pricing_queries) > 0, "Must have pricing strategy query"

    def test_china_tariff_exposure_query_exists(self):
        """Verify China tariff exposure query exists (20% COGS exposure)."""
        china_queries = [
            t for t in self.orchestrator.query_templates
            if "china" in t.category.lower() or "china" in t.query.lower()
        ]
        assert len(china_queries) > 0, "Must have China tariff exposure query"


class TestSectorsMatchGraingerCustomers:
    """Ensure sectors match Grainger's actual customer base."""

    def test_valid_sectors_defined(self):
        """Verify only Grainger's actual customer segments are defined."""
        valid_sectors = {
            ClientSector.MANUFACTURING,
            ClientSector.GOVERNMENT,
            ClientSector.COMMERCIAL_FACILITIES,
            ClientSector.CONTRACTORS,
            ClientSector.GENERAL,
        }
        actual_sectors = set(ClientSector)
        assert actual_sectors == valid_sectors, f"Sectors should match Grainger customers, got: {actual_sectors}"

    def test_manufacturing_sector_exists(self):
        """Verify manufacturing sector exists (Grainger's largest segment)."""
        assert ClientSector.MANUFACTURING in CLIENT_SECTOR_MAPPING

    def test_government_sector_exists(self):
        """Verify government sector exists ($2B+ in Grainger revenue)."""
        assert ClientSector.GOVERNMENT in CLIENT_SECTOR_MAPPING
        gov_mapping = CLIENT_SECTOR_MAPPING[ClientSector.GOVERNMENT]
        assert "defense" in " ".join(gov_mapping.get("keywords", [])).lower() or \
               "military" in " ".join(gov_mapping.get("keywords", [])).lower(), \
               "Government sector should include defense/military keywords"

    def test_commercial_facilities_sector_exists(self):
        """Verify commercial facilities sector exists."""
        assert ClientSector.COMMERCIAL_FACILITIES in CLIENT_SECTOR_MAPPING

    def test_contractors_sector_exists(self):
        """Verify contractors sector exists."""
        assert ClientSector.CONTRACTORS in CLIENT_SECTOR_MAPPING
        contractor_mapping = CLIENT_SECTOR_MAPPING[ClientSector.CONTRACTORS]
        keywords = " ".join(contractor_mapping.get("keywords", [])).lower()
        assert "construction" in keywords or "contractor" in keywords, \
            "Contractors sector should include construction keywords"

    def test_no_old_sectors_exist(self):
        """Verify old sectors (ENERGY, AGRICULTURE, etc.) are removed."""
        sector_names = [s.name for s in ClientSector]
        assert "ENERGY" not in sector_names, "ENERGY sector should be removed"
        assert "AGRICULTURE" not in sector_names, "AGRICULTURE sector should be removed"
        assert "TRANSPORTATION_LOGISTICS" not in sector_names, "TRANSPORTATION_LOGISTICS should be removed"
        assert "CONSTRUCTION" not in sector_names, "CONSTRUCTION should be renamed to CONTRACTORS"


class TestGeographicFocus:
    """Ensure output focuses on US/USMCA, not global."""

    def test_primary_regions_include_us(self):
        """Verify US is in primary regions."""
        primary = GEOGRAPHIC_FOCUS["primary_regions"]
        assert any(
            region in ["US", "USA", "United States", "America"]
            for region in primary
        ), "Primary regions must include US"

    def test_secondary_regions_include_usmca(self):
        """Verify USMCA regions are secondary."""
        secondary = GEOGRAPHIC_FOCUS["secondary_regions"]
        assert "Canada" in secondary or "Mexico" in secondary, \
            "Secondary regions should include Canada/Mexico"

    def test_excluded_regions_defined(self):
        """Verify non-USMCA regions are excluded."""
        excluded = GEOGRAPHIC_FOCUS["exclude_regions"]
        assert "Europe" in excluded or "EU" in excluded, "Should exclude Europe"
        assert "APAC" in excluded or "Asia Pacific" in excluded, "Should exclude Asia Pacific"

    def test_filter_includes_us_content(self):
        """Verify filter includes US-focused content."""
        assert filter_for_geographic_relevance("US manufacturing production increased")
        assert filter_for_geographic_relevance("United States industrial output")
        assert filter_for_geographic_relevance("domestic supply chain")

    def test_filter_includes_trade_related_international(self):
        """Verify filter includes international content if trade-related to US."""
        assert filter_for_geographic_relevance("China tariffs affecting US imports")
        assert filter_for_geographic_relevance("APAC supply chain disruption impacting US sourcing")

    def test_filter_excludes_irrelevant_international(self):
        """Verify filter excludes purely international content with no US connection."""
        # Content that's purely about Europe with no US trade connection
        result = filter_for_geographic_relevance(
            "European Union manufacturing output increased in Germany and France"
        )
        # This should be excluded as it has no US/trade relevance
        assert not result, "Should exclude purely European content without US trade relevance"


class TestCriticalCommoditiesTracked:
    """Verify Grainger-critical commodities are tracked in FRED indicators."""

    def test_steel_indicators_exist(self):
        """Verify steel indicators exist (Jenna: 'steel is really important')."""
        all_series = {}
        for category, series in FREDClient.SERIES.items():
            all_series.update(series)

        steel_series = [s for s in all_series.keys() if "steel" in s.lower() or "WPU101" in s]
        assert len(steel_series) > 0 or "WPU101" in all_series, \
            "Must have steel price indicators"

    def test_aluminum_indicators_exist(self):
        """Verify aluminum indicators exist (Jenna: 'aluminum is really important to our business')."""
        all_series = {}
        for category, series in FREDClient.SERIES.items():
            all_series.update(series)

        aluminum_series = [
            s for s in all_series.keys()
            if "aluminum" in s.lower() or "WPU102501" in s or "PALUM" in s
        ]
        assert len(aluminum_series) > 0, "Must have aluminum price indicators"

    def test_grainger_commodities_category_exists(self):
        """Verify grainger_commodities category exists in FRED series."""
        assert "grainger_commodities" in FREDClient.SERIES, \
            "Must have grainger_commodities category in FRED series"

    def test_government_spending_indicators_exist(self):
        """Verify government spending indicators exist (Grainger $2B+ gov business)."""
        assert "government" in FREDClient.SERIES, \
            "Must have government spending category in FRED series"


class TestReportStructureForJenna:
    """Verify report structure supports Jenna's newsletter workflow."""

    def test_report_structure_exists(self):
        """Verify REPORT_STRUCTURE is defined."""
        assert REPORT_STRUCTURE is not None
        assert isinstance(REPORT_STRUCTURE, dict)

    def test_executive_summary_section_exists(self):
        """Verify executive summary section exists for newsletter excerpts."""
        assert "executive_summary" in REPORT_STRUCTURE
        exec_summary = REPORT_STRUCTURE["executive_summary"]
        assert "format" in exec_summary, "Executive summary should specify format"

    def test_pricing_section_exists(self):
        """Verify pricing section exists (Jenna's pricing pass-through question)."""
        assert "pricing_section" in REPORT_STRUCTURE
        pricing = REPORT_STRUCTURE["pricing_section"]
        assert "jenna_question" in pricing, "Should reference Jenna's question"

    def test_demand_section_exists(self):
        """Verify demand section exists (Jenna's MRO outlook question)."""
        assert "demand_section" in REPORT_STRUCTURE

    def test_risk_section_exists(self):
        """Verify risk section exists (Jenna's tariff question)."""
        assert "risk_section" in REPORT_STRUCTURE

    def test_report_max_pages_is_three(self):
        """Verify report is limited to 3 pages as specified."""
        assert REPORT_SETTINGS["max_pages"] == 3


class TestSoWhatPromptGraingerSpecific:
    """Verify So What analysis prompt is Grainger-specific."""

    def test_so_what_prompt_exists(self):
        """Verify SO_WHAT_PROMPT is defined."""
        assert SO_WHAT_PROMPT is not None
        assert len(SO_WHAT_PROMPT) > 100, "SO_WHAT_PROMPT should be substantial"

    def test_so_what_mentions_mro_demand(self):
        """Verify prompt asks about MRO demand impact."""
        assert "mro demand" in SO_WHAT_PROMPT.lower()

    def test_so_what_mentions_supply_costs(self):
        """Verify prompt asks about supply costs."""
        assert "supply" in SO_WHAT_PROMPT.lower() and "cost" in SO_WHAT_PROMPT.lower()

    def test_so_what_mentions_pricing(self):
        """Verify prompt asks about pricing implications."""
        assert "pricing" in SO_WHAT_PROMPT.lower()

    def test_so_what_mentions_customer_segments(self):
        """Verify prompt references Grainger's customer segments."""
        prompt_lower = SO_WHAT_PROMPT.lower()
        assert "manufacturing" in prompt_lower
        assert "government" in prompt_lower
        assert "contractor" in prompt_lower

    def test_so_what_mentions_china_exposure(self):
        """Verify prompt mentions China sourcing exposure."""
        assert "china" in SO_WHAT_PROMPT.lower() or "20%" in SO_WHAT_PROMPT


class TestCompanyProfileComplete:
    """Verify company profile has required Grainger-specific information."""

    def test_supply_chain_exposure_defined(self):
        """Verify supply chain exposure is defined (20% COGS from China)."""
        assert "supply_chain_exposure" in COMPANY_PROFILE
        exposure = COMPANY_PROFILE["supply_chain_exposure"]
        assert "china_cogs_percent" in exposure
        assert exposure["china_cogs_percent"] == 20

    def test_critical_commodities_defined(self):
        """Verify critical commodities are defined."""
        exposure = COMPANY_PROFILE.get("supply_chain_exposure", {})
        commodities = exposure.get("critical_commodities", [])
        assert "steel" in commodities
        assert "aluminum" in commodities

    def test_competitive_context_defined(self):
        """Verify competitive context (Amazon Business) is defined."""
        assert "competitive_context" in COMPANY_PROFILE
        competitive = COMPANY_PROFILE["competitive_context"]
        assert "amazon" in competitive.get("primary_threat", "").lower()


class TestQueryTemplatePriorities:
    """Verify query template priorities align with Grainger requirements."""

    def setup_method(self):
        """Initialize orchestrator for tests."""
        self.orchestrator = QueryOrchestrator()

    def test_high_priority_queries_exist(self):
        """Verify high-priority queries (>=9) exist for Jenna's explicit asks."""
        high_priority = [
            t for t in self.orchestrator.query_templates
            if t.priority >= 9
        ]
        assert len(high_priority) >= 4, "Should have at least 4 high-priority queries (Jenna's asks)"

    def test_tariff_queries_high_priority(self):
        """Verify tariff queries are high priority."""
        tariff_queries = [
            t for t in self.orchestrator.query_templates
            if "tariff" in t.query.lower()
        ]
        for q in tariff_queries:
            assert q.priority >= 9, f"Tariff query should be priority >=9, got {q.priority}"

    def test_government_sector_queries_exist(self):
        """Verify government sector queries exist ($2B+ segment)."""
        gov_queries = [
            t for t in self.orchestrator.query_templates
            if ClientSector.GOVERNMENT in t.sectors
        ]
        assert len(gov_queries) > 0, "Must have government sector queries"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
