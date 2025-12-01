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
