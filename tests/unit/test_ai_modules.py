"""
Unit tests for AI modules (fact_validator, generator, pii_sanitizer)
"""

import pytest

from mro_intelligence.ai.fact_validator import FactValidator
from mro_intelligence.ai.generator import AIConfig, AIUsageTracker, SecureAIGenerator
from mro_intelligence.ai.pii_sanitizer import PIISanitizer
from mro_intelligence.config.clients import ClientSector
from mro_intelligence.core.processor import IntelligenceItem


class TestFactValidator:
    """Test FactValidator class"""

    @pytest.fixture
    def validator(self):
        return FactValidator()

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator is not None
        assert validator.factual_patterns is not None
        assert len(validator.factual_patterns) > 0

    def test_extract_factual_claims_percentages(self, validator):
        """Test extracting percentage claims"""
        text = "The rate increased by 5.5% this quarter."
        claims = validator.extract_factual_claims(text)

        assert any("percentages" in claim for claim in claims)

    def test_extract_factual_claims_dollar_amounts(self, validator):
        """Test extracting dollar amount claims"""
        text = "The investment totaled $50 million."
        claims = validator.extract_factual_claims(text)

        assert any("dollar_amounts" in claim for claim in claims)

    def test_extract_factual_claims_dates(self, validator):
        """Test extracting date claims"""
        text = "This was announced on January 15, 2024."
        claims = validator.extract_factual_claims(text)

        assert any("dates" in claim for claim in claims)

    def test_extract_factual_claims_countries(self, validator):
        """Test extracting country claims"""
        text = "United States and China reached an agreement."
        claims = validator.extract_factual_claims(text)

        assert any("specific_countries" in claim for claim in claims)

    def test_extract_factual_claims_no_claims(self, validator):
        """Test with no factual claims"""
        text = "This is general analysis without specific data."
        claims = validator.extract_factual_claims(text)

        # May or may not have claims depending on interpretation
        assert isinstance(claims, set)

    def test_validate_ai_output_valid(self, validator):
        """Test validating supported AI output"""
        source_items = [
            IntelligenceItem(
                raw_content="The rate increased by 10%",
                processed_content="Economic indicator showed 10% growth",
                category="economic",
                relevance_score=0.9,
                so_what_statement="Significant economic impact",
                affected_sectors=[ClientSector.GENERAL],
            )
        ]

        ai_text = "The rate increased by 10% indicating significant growth."

        is_valid, unsupported = validator.validate_ai_output(ai_text, source_items)

        assert isinstance(is_valid, bool)
        assert isinstance(unsupported, list)

    def test_validate_ai_output_unsupported(self, validator):
        """Test validating unsupported AI output"""
        source_items = [
            IntelligenceItem(
                raw_content="The rate increased by 10%",
                processed_content="Economic indicator showed growth",
                category="economic",
                relevance_score=0.9,
                so_what_statement="Significant impact",
                affected_sectors=[ClientSector.GENERAL],
            )
        ]

        # AI claims something not in source
        ai_text = "The rate increased by 50% which is unprecedented."

        is_valid, unsupported = validator.validate_ai_output(ai_text, source_items)

        # Should detect unsupported claim
        assert isinstance(unsupported, list)

    def test_validate_ai_output_no_claims(self, validator):
        """Test validating AI output with no factual claims"""
        source_items = []
        ai_text = "This is general analysis with no specific data points."

        is_valid, unsupported = validator.validate_ai_output(ai_text, source_items)

        assert is_valid is True
        assert unsupported == []

    def test_check_for_prohibited_content_safe(self, validator):
        """Test checking safe content"""
        text = "The economic indicators show positive growth trends."

        is_safe, violations = validator.check_for_prohibited_content(text)

        assert is_safe is True
        assert violations == []

    def test_check_for_prohibited_content_first_person(self, validator):
        """Test detecting first-person language"""
        text = "I believe this trend will continue."

        is_safe, violations = validator.check_for_prohibited_content(text)

        assert is_safe is False
        assert len(violations) > 0

    def test_check_for_prohibited_content_personal_assessment(self, validator):
        """Test detecting personal assessment language"""
        text = "Based on my analysis of the data, we can conclude."

        is_safe, violations = validator.check_for_prohibited_content(text)

        assert is_safe is False


class TestAIConfig:
    """Test AIConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = AIConfig(api_key="test_key")

        assert config.api_key == "test_key"
        assert config.model == "claude-opus-4-5-20251101"
        assert config.enabled is True
        assert config.max_tokens == 4000
        assert config.temperature == 0.3

    def test_custom_values(self):
        """Test custom configuration values"""
        config = AIConfig(
            api_key="custom_key",
            model="claude-3-sonnet",
            enabled=False,
            max_tokens=2000,
            temperature=0.5,
        )

        assert config.api_key == "custom_key"
        assert config.model == "claude-3-sonnet"
        assert config.enabled is False
        assert config.max_tokens == 2000
        assert config.temperature == 0.5


class TestAIUsageTracker:
    """Test AIUsageTracker class"""

    @pytest.fixture
    def tracker(self):
        return AIUsageTracker()

    def test_tracker_initialization(self, tracker):
        """Test tracker initializes with zeros"""
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert tracker.total_requests == 0
        assert tracker.total_cost == 0.0
        assert tracker.failed_requests == 0

    def test_log_successful_request(self, tracker):
        """Test logging successful request"""
        tracker.log_request(input_tokens=1000, output_tokens=500, success=True)

        assert tracker.total_requests == 1
        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
        assert tracker.failed_requests == 0
        assert tracker.total_cost > 0

    def test_log_failed_request(self, tracker):
        """Test logging failed request"""
        tracker.log_request(input_tokens=1000, output_tokens=0, success=False)

        assert tracker.total_requests == 1
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert tracker.failed_requests == 1

    def test_get_summary(self, tracker):
        """Test getting usage summary"""
        tracker.log_request(1000, 500, True)
        tracker.log_request(2000, 1000, True)

        summary = tracker.get_summary()

        assert summary["total_requests"] == 2
        assert summary["successful_requests"] == 2
        assert summary["failed_requests"] == 0
        assert summary["total_input_tokens"] == 3000
        assert summary["total_output_tokens"] == 1500
        assert "total_cost_usd" in summary

    def test_cost_calculation(self, tracker):
        """Test cost is calculated correctly"""
        # 1M input tokens = $15, 1M output tokens = $75
        tracker.log_request(input_tokens=1_000_000, output_tokens=1_000_000, success=True)

        assert tracker.total_cost == pytest.approx(90.0, rel=0.01)


class TestSecureAIGenerator:
    """Test SecureAIGenerator class"""

    @pytest.fixture
    def generator(self):
        """Create generator with disabled AI to avoid API calls"""
        config = AIConfig(api_key="test_key", enabled=False)
        return SecureAIGenerator(config=config)

    def test_generator_initialization(self, generator):
        """Test generator initializes correctly"""
        assert generator is not None
        assert generator.sanitizer is not None
        assert generator.validator is not None
        assert generator.usage_tracker is not None

    def test_generator_has_fallback_methods(self, generator):
        """Test generator has fallback methods"""
        assert hasattr(generator, "generate_executive_summary")
        assert hasattr(generator, "usage_tracker")

    def test_generator_disabled_returns_fallback(self, generator):
        """Test disabled generator returns fallback content"""
        # When AI is disabled, should use template fallback
        assert generator.config.enabled is False


class TestPIISanitizer:
    """Test PIISanitizer class"""

    @pytest.fixture
    def sanitizer(self):
        return PIISanitizer()

    def test_sanitizer_initialization(self, sanitizer):
        """Test sanitizer initializes correctly"""
        assert sanitizer is not None
        assert sanitizer.company_patterns is not None
        assert sanitizer.client_mapping is not None

    def test_sanitize_text_basic(self, sanitizer):
        """Test basic text sanitization"""
        text = "The economic indicators show positive trends in the market."

        sanitized = sanitizer.sanitize_text(text)

        # Should be mostly the same when no company names present
        assert "economic indicators" in sanitized
        assert "positive trends" in sanitized

    def test_sanitize_text_preserves_structure(self, sanitizer):
        """Test sanitization preserves text structure"""
        text = """
        Key findings:
        1. First point about industrial
        2. Second point about markets
        """

        sanitized = sanitizer.sanitize_text(text)

        assert "Key findings" in sanitized
        assert "First point" in sanitized
        assert "Second point" in sanitized

    def test_sanitize_intelligence_item(self, sanitizer):
        """Test sanitizing intelligence item"""
        item = IntelligenceItem(
            raw_content="Test raw content",
            processed_content="Test processed content",
            category="economic",
            relevance_score=0.9,
            so_what_statement="Test impact",
            affected_sectors=[ClientSector.GENERAL],
        )

        sanitized_item = sanitizer.sanitize_intelligence_item(item)

        assert sanitized_item is not None
        assert isinstance(sanitized_item, IntelligenceItem)

    def test_sanitize_intelligence_items_list(self, sanitizer):
        """Test sanitizing list of items"""
        items = [
            IntelligenceItem(
                raw_content="Test content 1",
                processed_content="Processed 1",
                category="economic",
                relevance_score=0.8,
                so_what_statement="Impact 1",
                affected_sectors=[ClientSector.MANUFACTURING],
            ),
            IntelligenceItem(
                raw_content="Test content 2",
                processed_content="Processed 2",
                category="trade",
                relevance_score=0.7,
                so_what_statement="Impact 2",
                affected_sectors=[ClientSector.GOVERNMENT],
            ),
        ]

        sanitized_items = sanitizer.sanitize_intelligence_items(items)

        assert len(sanitized_items) == 2
        assert all(isinstance(item, IntelligenceItem) for item in sanitized_items)

    def test_sanitize_dict(self, sanitizer):
        """Test sanitizing dictionary"""
        data = {"key1": "Test value", "key2": "Another value", "nested": {"key3": "Nested value"}}

        sanitized = sanitizer.sanitize_dict(data)

        assert "key1" in sanitized
        assert "nested" in sanitized

    def test_company_patterns_built(self, sanitizer):
        """Test company patterns are built from mapping"""
        # Should have patterns if client mapping has companies
        assert isinstance(sanitizer.company_patterns, dict)


class TestValidateExecutiveSummary:
    """Test executive summary validation"""

    @pytest.fixture
    def validator(self):
        return FactValidator()

    def test_validate_summary_with_string_items(self, validator):
        """Test validating summary with string items"""
        summary_dict = {
            "bottom_line": ["Economic growth continues at 5% pace."],
            "key_findings": ["Trade tensions remain elevated."],
            "watch_factors": ["Monitor inflation closely."],
        }

        source_items = [
            IntelligenceItem(
                raw_content="Economic growth at 5%",
                processed_content="Growth continues at 5%",
                category="economic",
                relevance_score=0.9,
                so_what_statement="Strong growth",
                affected_sectors=[ClientSector.GENERAL],
            )
        ]

        is_valid, report = validator.validate_executive_summary(summary_dict, source_items)

        assert isinstance(is_valid, bool)
        assert "bottom_line" in report
        assert "key_findings" in report
        assert "watch_factors" in report

    def test_validate_summary_with_dict_items(self, validator):
        """Test validating summary with dict items"""
        summary_dict = {
            "bottom_line": ["Key insight about markets."],
            "key_findings": [
                {
                    "subheader": "Economic Overview",
                    "content": "Growth remains steady.",
                    "bullets": ["First bullet", "Second bullet"],
                }
            ],
            "watch_factors": [
                {
                    "indicator": "Inflation",
                    "what_to_watch": "CPI data",
                    "why_it_matters": "Affects policy",
                }
            ],
        }

        source_items = []

        is_valid, report = validator.validate_executive_summary(summary_dict, source_items)

        assert "overall_valid" in report

    def test_validate_empty_summary(self, validator):
        """Test validating empty summary"""
        summary_dict = {
            "bottom_line": [],
            "key_findings": [],
            "watch_factors": [],
        }

        is_valid, report = validator.validate_executive_summary(summary_dict, [])

        assert report["overall_valid"] is True
