"""
Unit tests for AI Generator and related components
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from solairus_intelligence.ai.generator import (
    SecureAIGenerator,
    AIConfig,
    AIUsageTracker,
)
from solairus_intelligence.ai.pii_sanitizer import PIISanitizer
from solairus_intelligence.ai.fact_validator import FactValidator
from solairus_intelligence.core.processor import IntelligenceItem, ClientSector


class TestAIConfig:
    """Test AI configuration"""

    def test_config_creation(self):
        """Test creating AI config"""
        config = AIConfig(
            api_key="test_key",
            model="claude-opus-4-5-20251101",
            enabled=True
        )

        assert config.api_key == "test_key"
        assert config.enabled is True

    def test_config_defaults(self):
        """Test config default values"""
        config = AIConfig(api_key="test")

        assert config.model == "claude-opus-4-5-20251101"
        assert config.enabled is True
        assert config.max_tokens == 4000
        assert config.temperature == 0.3


class TestAIUsageTracker:
    """Test AI usage tracking"""

    @pytest.fixture
    def tracker(self):
        return AIUsageTracker()

    def test_tracker_initialization(self, tracker):
        """Test tracker initializes with zeros"""
        summary = tracker.get_summary()

        assert summary['total_requests'] == 0
        assert summary['successful_requests'] == 0
        assert summary['total_input_tokens'] == 0
        assert summary['total_output_tokens'] == 0

    def test_record_request(self, tracker):
        """Test recording a request"""
        tracker.log_request(
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        summary = tracker.get_summary()

        assert summary['total_requests'] == 1
        assert summary['successful_requests'] == 1
        assert summary['total_input_tokens'] == 100
        assert summary['total_output_tokens'] == 50

    def test_record_failed_request(self, tracker):
        """Test recording a failed request"""
        tracker.log_request(
            input_tokens=100,
            output_tokens=0,
            success=False
        )

        summary = tracker.get_summary()

        assert summary['total_requests'] == 1
        assert summary['successful_requests'] == 0
        assert summary['failed_requests'] == 1

    def test_cost_calculation(self, tracker):
        """Test cost calculation"""
        tracker.log_request(
            input_tokens=1000,
            output_tokens=500,
            success=True
        )

        summary = tracker.get_summary()

        assert summary['total_cost_usd'] > 0


class TestPIISanitizer:
    """Test PII sanitization"""

    @pytest.fixture
    def sanitizer(self):
        return PIISanitizer()

    def test_sanitizer_initialization(self, sanitizer):
        """Test sanitizer initializes correctly"""
        assert sanitizer is not None
        assert sanitizer.company_patterns is not None

    def test_sanitize_text_with_client_name(self, sanitizer):
        """Test sanitizing text containing client company names"""
        # Using a company from the client mapping
        text = "Cisco announced new security features"
        sanitized = sanitizer.sanitize_text(text)

        # Company name should be replaced
        assert "Cisco" not in sanitized or "[" in sanitized

    def test_sanitize_text_preserves_non_client(self, sanitizer):
        """Test that non-client companies are preserved"""
        text = "Apple and Google announced new products"
        sanitized = sanitizer.sanitize_text(text)

        # Non-client companies should be preserved
        assert "Apple" in sanitized
        assert "Google" in sanitized

    def test_sanitize_empty_text(self, sanitizer):
        """Test sanitizing empty text"""
        assert sanitizer.sanitize_text("") == ""
        assert sanitizer.sanitize_text(None) is None


class TestFactValidator:
    """Test fact validation"""

    @pytest.fixture
    def validator(self):
        return FactValidator()

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator is not None
        assert validator.factual_patterns is not None

    def test_extract_factual_claims(self, validator):
        """Test extracting factual claims from text"""
        text = "Inflation rose to 3.5% in Q4 2024, impacting $50 billion in trade"

        claims = validator.extract_factual_claims(text)

        # Claims should be returned (as set, list, or dict)
        assert claims is not None
        assert len(claims) > 0

    def test_validate_supported_claims(self, validator):
        """Test validating claims that are supported by sources"""
        source_items = [
            IntelligenceItem(
                raw_content="US inflation 3.5%",
                processed_content="US inflation rose to 3.5%",
                category="economic",
                relevance_score=0.9,
                so_what_statement="Higher costs expected",
                affected_sectors=[]
            )
        ]

        ai_text = "Inflation at 3.5% creates cost pressures"

        is_valid, unsupported = validator.validate_ai_output(
            ai_text, source_items, strict=False
        )

        # Should be valid since claim is supported
        assert is_valid or len(unsupported) == 0

    def test_detect_prohibited_content(self, validator):
        """Test detecting prohibited content patterns"""
        # Text with first-person language (prohibited)
        text = "I believe inflation will continue to rise"

        is_safe, violations = validator.check_for_prohibited_content(text)

        assert is_safe is False
        assert len(violations) > 0


class TestSecureAIGenerator:
    """Test secure AI generator"""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        """Create mock configuration"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
        monkeypatch.setenv("AI_ENABLED", "true")

    def test_generator_disabled_without_key(self, monkeypatch):
        """Test generator is disabled without API key"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("AI_ENABLED", "true")

        generator = SecureAIGenerator()

        assert generator.config.enabled is False

    def test_generator_respects_ai_enabled_flag(self, monkeypatch):
        """Test generator respects AI_ENABLED flag"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
        monkeypatch.setenv("AI_ENABLED", "false")

        generator = SecureAIGenerator()

        assert generator.config.enabled is False

    def test_usage_tracking(self, mock_config):
        """Test usage tracking is initialized"""
        generator = SecureAIGenerator()

        summary = generator.get_usage_summary()

        assert 'total_requests' in summary
        assert 'total_cost_usd' in summary


class TestExecutiveSummaryParsing:
    """Test parsing of executive summary responses"""

    @pytest.fixture
    def config(self):
        return AIConfig(api_key="test_key")

    @pytest.fixture
    def generator(self, config):
        return SecureAIGenerator(config)

    def test_parse_bottom_line_section(self, generator):
        """Test parsing bottom line section"""
        response = """
        BOTTOM LINE:
        - Key development affecting aviation
        - Monitor for operational impact
        """
        result = generator._parse_executive_summary_response(response)

        assert "bottom_line" in result
        assert len(result["bottom_line"]) > 0

    def test_parse_key_findings_section(self, generator):
        """Test parsing key findings section"""
        response = """
        KEY FINDINGS:
        - Trade policy changes affecting supply chain
        - Economic indicators showing weakness
        """
        result = generator._parse_executive_summary_response(response)

        assert "key_findings" in result
        assert len(result["key_findings"]) > 0

    def test_parse_watch_factors_section(self, generator):
        """Test parsing watch factors section"""
        response = """
        WATCH FACTORS:
        - Monitor geopolitical developments
        - Watch for regulatory changes
        """
        result = generator._parse_executive_summary_response(response)

        assert "watch_factors" in result
        assert len(result["watch_factors"]) > 0

    def test_parse_empty_response(self, generator):
        """Test parsing empty response"""
        result = generator._parse_executive_summary_response("")

        assert result["bottom_line"] == []
        assert result["key_findings"] == []
        assert result["watch_factors"] == []

    def test_parse_structured_key_finding(self, generator):
        """Test parsing structured key finding format"""
        response = """
        KEY FINDINGS:
        [SUBHEADER: Trade Policy]
        [CONTENT: New tariffs announced affecting imports]
        [BULLET: Supply chain disruption expected]
        [BULLET: Monitor price increases]
        """
        result = generator._parse_executive_summary_response(response)

        assert "key_findings" in result

    def test_parse_structured_watch_factor(self, generator):
        """Test parsing structured watch factor format"""
        response = """
        WATCH FACTORS:
        [INDICATOR: Geopolitical Risk]
        [WHAT_TO_WATCH: Regional tensions escalating]
        [WHY_IT_MATTERS: May impact aviation routes]
        """
        result = generator._parse_executive_summary_response(response)

        assert "watch_factors" in result

    def test_parse_mixed_format(self, generator):
        """Test parsing mixed format response"""
        response = """
        BOTTOM LINE:
        - Critical development requiring attention

        KEY FINDINGS:
        - Economic growth slowing
        - Trade tensions rising

        WATCH FACTORS:
        - Monitor inflation trends
        """
        result = generator._parse_executive_summary_response(response)

        assert len(result["bottom_line"]) >= 1
        assert len(result["key_findings"]) >= 2
        assert len(result["watch_factors"]) >= 1

    def test_parse_bullet_variations(self, generator):
        """Test parsing different bullet formats"""
        response = """
        KEY FINDINGS:
        - First finding with dash
        • Second finding with bullet
        """
        result = generator._parse_executive_summary_response(response)

        assert len(result["key_findings"]) >= 2


class TestPromptConstruction:
    """Test prompt construction for AI calls"""

    @pytest.fixture
    def config(self):
        return AIConfig(api_key="test_key")

    @pytest.fixture
    def generator(self, config):
        return SecureAIGenerator(config)

    @pytest.fixture
    def sample_items(self):
        return [
            IntelligenceItem(
                raw_content="Trade tensions",
                processed_content="US-China trade tensions escalating",
                category="geopolitical",
                relevance_score=0.9,
                confidence=0.85,
                so_what_statement="Monitor for supply chain impact",
                affected_sectors=[ClientSector.TECHNOLOGY],
            ),
            IntelligenceItem(
                raw_content="Economic data",
                processed_content="GDP growth at 2.5% in Q4",
                category="economic",
                relevance_score=0.8,
                confidence=0.9,
                so_what_statement="Watch for demand changes",
                affected_sectors=[ClientSector.FINANCE],
            ),
        ]

    def test_build_executive_summary_prompt(self, generator, sample_items):
        """Test building executive summary prompt"""
        prompt = generator._build_executive_summary_prompt(sample_items)

        assert prompt is not None
        assert len(prompt) > 0
        assert "BOTTOM LINE" in prompt or "intelligence" in prompt.lower()

    def test_build_so_what_prompt(self, generator, sample_items):
        """Test building so-what statement prompt"""
        item = sample_items[0]
        prompt = generator._build_so_what_prompt(item)

        assert prompt is not None
        assert len(prompt) > 0
        assert item.processed_content in prompt or "So What" in prompt
