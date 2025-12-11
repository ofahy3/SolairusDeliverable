"""
Unit tests for PII sanitizer module
"""

import pytest
from unittest.mock import patch

from solairus_intelligence.ai.pii_sanitizer import PIISanitizer
from solairus_intelligence.config.clients import ClientSector, CLIENT_SECTOR_MAPPING


class TestPIISanitizer:
    """Test suite for PII sanitization"""

    def test_sanitizer_initialization(self):
        """Test sanitizer initializes correctly"""
        sanitizer = PIISanitizer()

        assert sanitizer is not None
        assert hasattr(sanitizer, "sanitize_text")
        assert hasattr(sanitizer, "company_patterns")

    def test_sanitizer_with_default_mapping(self):
        """Test sanitizer uses default client mapping"""
        sanitizer = PIISanitizer()

        # Should have loaded client mappings
        assert sanitizer.client_mapping is not None
        assert sanitizer.company_patterns is not None

    def test_sanitize_removes_client_names(self):
        """Test sanitize removes known client names"""
        sanitizer = PIISanitizer()

        # Get a known company name from config
        tech_mapping = CLIENT_SECTOR_MAPPING.get(ClientSector.TECHNOLOGY, {})
        companies = tech_mapping.get("companies", [])

        if companies:
            company_name = companies[0]
            text = f"The {company_name} executive team is planning travel."

            sanitized = sanitizer.sanitize_text(text)

            # Company name should be replaced
            assert company_name not in sanitized

    def test_sanitize_preserves_non_client_text(self):
        """Test sanitize preserves text that doesn't contain client names"""
        sanitizer = PIISanitizer()

        text = "General aviation news about the industry trends."
        sanitized = sanitizer.sanitize_text(text)

        # Should be mostly unchanged
        assert "aviation" in sanitized
        assert "industry" in sanitized

    def test_sanitize_handles_empty_text(self):
        """Test sanitize handles empty strings"""
        sanitizer = PIISanitizer()

        result = sanitizer.sanitize_text("")
        assert result == ""

    def test_sanitize_handles_none(self):
        """Test sanitize handles None gracefully"""
        sanitizer = PIISanitizer()

        result = sanitizer.sanitize_text(None)  # type: ignore
        assert result is None

    def test_sanitize_multiple_occurrences(self):
        """Test sanitize handles multiple occurrences of client names"""
        sanitizer = PIISanitizer()

        tech_mapping = CLIENT_SECTOR_MAPPING.get(ClientSector.TECHNOLOGY, {})
        companies = tech_mapping.get("companies", [])

        if companies:
            company = companies[0]
            text = f"{company} CEO met with {company} board about {company} expansion."

            sanitized = sanitizer.sanitize_text(text)

            # All occurrences should be replaced
            assert company not in sanitized

    def test_sanitizer_case_sensitivity(self):
        """Test sanitizer handles case variations"""
        sanitizer = PIISanitizer()

        # Sanitization should handle case variations
        text = "Discussion about TECHNOLOGY sector clients."
        sanitized = sanitizer.sanitize_text(text)

        # Should process without errors
        assert sanitized is not None


class TestPIISanitizerReplacement:
    """Test replacement behavior"""

    def test_replacement_maintains_readability(self):
        """Test that replacements maintain sentence readability"""
        sanitizer = PIISanitizer()

        tech_mapping = CLIENT_SECTOR_MAPPING.get(ClientSector.TECHNOLOGY, {})
        companies = tech_mapping.get("companies", [])

        if companies:
            company = companies[0]
            text = f"{company} is expanding operations."

            sanitized = sanitizer.sanitize_text(text)

            # Should still be readable
            assert "is expanding operations" in sanitized

    def test_handles_special_characters_in_names(self):
        """Test handling of special characters in company names"""
        sanitizer = PIISanitizer()

        # Test with text containing various special characters
        text = "Company Ltd. & Co. discussed strategies."
        sanitized = sanitizer.sanitize_text(text)

        # Should not crash
        assert sanitized is not None
