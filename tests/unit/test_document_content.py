"""
Unit tests for document content extraction module
"""

import pytest
from datetime import datetime

from solairus_intelligence.core.document.content import ContentExtractor
from solairus_intelligence.core.processor import IntelligenceItem
from solairus_intelligence.config.clients import ClientSector


class TestContentExtractor:
    """Test suite for ContentExtractor"""

    @pytest.fixture
    def extractor(self):
        """Create ContentExtractor instance"""
        return ContentExtractor()

    @pytest.fixture
    def sample_items(self):
        """Create sample intelligence items"""
        return [
            IntelligenceItem(
                raw_content="Raw geopolitical content",
                processed_content="Rising tensions in Eastern Europe affecting aviation routes",
                category="geopolitical",
                relevance_score=0.9,
                confidence=0.85,
                so_what_statement="Monitor for route changes and insurance costs",
                affected_sectors=[ClientSector.GENERAL],
            ),
            IntelligenceItem(
                raw_content="Raw economic content",
                processed_content="Inflation increased to 3.2% this quarter",
                category="economic",
                relevance_score=0.75,
                confidence=0.92,
                so_what_statement="Budget for higher operating costs",
                affected_sectors=[ClientSector.FINANCE],
            ),
            IntelligenceItem(
                raw_content="Raw trade content",
                processed_content="New tariffs on aviation parts announced",
                category="trade",
                relevance_score=0.65,
                confidence=0.78,
                so_what_statement="Watch for supply chain impact",
                affected_sectors=[ClientSector.GENERAL],
            ),
        ]

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes correctly"""
        assert extractor is not None

    def test_extract_analytical_insights(self, extractor, sample_items):
        """Test insight extraction"""
        insights = extractor.extract_analytical_insights(sample_items)

        assert "bottom_line" in insights
        assert "key_findings" in insights
        assert "watch_factors" in insights

    def test_insights_structure(self, extractor, sample_items):
        """Test insights have correct structure"""
        insights = extractor.extract_analytical_insights(sample_items)

        assert isinstance(insights["bottom_line"], list)
        assert isinstance(insights["key_findings"], list)
        assert isinstance(insights["watch_factors"], list)

    def test_insights_limits(self, extractor, sample_items):
        """Test insights respect limits"""
        insights = extractor.extract_analytical_insights(sample_items)

        assert len(insights["bottom_line"]) <= 3
        assert len(insights["key_findings"]) <= 5
        assert len(insights["watch_factors"]) <= 3


class TestThemeExtraction:
    """Test theme extraction functionality"""

    @pytest.fixture
    def extractor(self):
        return ContentExtractor()

    def test_extract_geopolitical_theme(self, extractor):
        """Test geopolitical theme detection"""
        theme = extractor.extract_theme(
            "Military tensions escalating in the region",
            "Monitor conflict developments"
        )

        assert theme == "Geopolitical Risk"

    def test_extract_economic_theme(self, extractor):
        """Test economic theme detection"""
        theme = extractor.extract_theme(
            "GDP growth slowed in Q4",
            "Economic indicators weakening"
        )

        assert theme == "Economic Pressure"

    def test_extract_trade_theme(self, extractor):
        """Test trade theme detection"""
        theme = extractor.extract_theme(
            "New tariffs announced on imports",
            "Trade policy affecting supply"
        )

        assert theme == "Trade Policy"

    def test_extract_default_theme(self, extractor):
        """Test default theme for unrecognized content"""
        theme = extractor.extract_theme(
            "General update on situation",
            "Standard business impact"
        )

        assert theme == "Strategic Development"


class TestStatementCrafting:
    """Test statement crafting methods"""

    @pytest.fixture
    def extractor(self):
        return ContentExtractor()

    @pytest.fixture
    def sample_item(self):
        return IntelligenceItem(
            raw_content="Test content",
            processed_content="Important development affecting operations",
            category="test",
            relevance_score=0.8,
            confidence=0.9,
            so_what_statement="Take immediate action",
            affected_sectors=[ClientSector.GENERAL],
        )

    def test_craft_bottom_line(self, extractor, sample_item):
        """Test bottom line crafting"""
        statement = extractor.craft_bottom_line_statement(sample_item)

        assert statement is not None
        assert len(statement) > 0
        assert statement.endswith('.')

    def test_craft_key_finding(self, extractor, sample_item):
        """Test key finding crafting"""
        statement = extractor.craft_key_finding_statement(sample_item)

        assert statement is not None
        assert len(statement) > 0

    def test_craft_watch_factor(self, extractor, sample_item):
        """Test watch factor crafting"""
        statement = extractor.craft_watch_factor_statement(sample_item)

        assert statement is not None
        assert "Monitor:" in statement


class TestParsing:
    """Test parsing methods"""

    @pytest.fixture
    def extractor(self):
        return ContentExtractor()

    def test_parse_key_finding(self, extractor):
        """Test key finding parsing"""
        header, desc, bullets = extractor.parse_key_finding(
            "Trade Policy: New tariffs affecting imports"
        )

        assert header == "Trade Policy"
        assert "tariffs" in desc.lower()
        assert isinstance(bullets, list)

    def test_parse_key_finding_without_colon(self, extractor):
        """Test parsing finding without colon"""
        header, desc, bullets = extractor.parse_key_finding(
            "Simple finding without structured format"
        )

        assert header == "Key Development"
        assert len(desc) > 0

    def test_parse_watch_factor(self, extractor):
        """Test watch factor parsing"""
        title, desc, bullets = extractor.parse_watch_factor(
            "Emerging Risk: New developments to monitor"
        )

        assert title == "Emerging Risk"
        assert len(desc) > 0


class TestUtilities:
    """Test utility methods"""

    @pytest.fixture
    def extractor(self):
        return ContentExtractor()

    def test_strip_markdown_bold(self, extractor):
        """Test bold markdown removal"""
        result = extractor.strip_markdown("This is **bold** text")
        assert result == "This is bold text"

    def test_strip_markdown_italic(self, extractor):
        """Test italic markdown removal"""
        result = extractor.strip_markdown("This is *italic* text")
        assert result == "This is italic text"

    def test_strip_markdown_headers(self, extractor):
        """Test header markdown removal"""
        result = extractor.strip_markdown("## Heading\nContent")
        assert "##" not in result

    def test_strip_markdown_empty(self, extractor):
        """Test empty string handling"""
        result = extractor.strip_markdown("")
        assert result == ""

    def test_strip_markdown_none(self, extractor):
        """Test None handling"""
        result = extractor.strip_markdown(None)  # type: ignore
        assert result == ""


class TestEconomicIndicators:
    """Test economic indicator methods"""

    @pytest.fixture
    def extractor(self):
        return ContentExtractor()

    @pytest.fixture
    def econ_item(self):
        return IntelligenceItem(
            raw_content="Economic data",
            processed_content="Inflation rate reached 3.5% in November",
            category="inflation",
            relevance_score=0.85,
            confidence=0.95,
            so_what_statement="Higher costs expected",
            affected_sectors=[ClientSector.GENERAL],
            source_type="fred",
        )

    def test_extract_indicator_name(self, extractor, econ_item):
        """Test indicator name extraction"""
        name = extractor.extract_indicator_name(econ_item)
        assert name == "CPI Inflation"

    def test_extract_value(self, extractor, econ_item):
        """Test value extraction"""
        value = extractor.extract_value(econ_item)
        assert "3.5" in value or "%" in value

    def test_determine_trend_up(self, extractor):
        """Test upward trend detection"""
        item = IntelligenceItem(
            raw_content="Test",
            processed_content="Values increased by 5%",
            category="test",
            relevance_score=0.8,
            so_what_statement="Costs rising",
            affected_sectors=[],
        )
        trend = extractor.determine_trend(item)
        assert trend == "↑"

    def test_determine_trend_down(self, extractor):
        """Test downward trend detection"""
        item = IntelligenceItem(
            raw_content="Test",
            processed_content="Values decreased significantly",
            category="test",
            relevance_score=0.8,
            so_what_statement="Costs falling",
            affected_sectors=[],
        )
        trend = extractor.determine_trend(item)
        assert trend == "↓"

    def test_determine_trend_stable(self, extractor):
        """Test stable trend detection"""
        item = IntelligenceItem(
            raw_content="Test",
            processed_content="Values remained steady",
            category="test",
            relevance_score=0.8,
            so_what_statement="Stable outlook",
            affected_sectors=[],
        )
        trend = extractor.determine_trend(item)
        assert trend == "→"

    def test_generate_economic_impact(self, extractor, econ_item):
        """Test impact generation"""
        impact = extractor.generate_economic_impact(econ_item)
        assert len(impact) > 0
