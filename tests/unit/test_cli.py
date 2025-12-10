"""
Unit tests for CLI module
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from datetime import datetime

from solairus_intelligence.cli import SolairusIntelligenceGenerator


class TestSolairusIntelligenceGenerator:
    """Test suite for the main CLI generator"""

    def test_generator_initialization(self):
        """Test generator initializes correctly"""
        gen = SolairusIntelligenceGenerator()

        assert gen is not None
        assert hasattr(gen, 'orchestrator')
        assert hasattr(gen, 'generator')  # DocumentGenerator is named 'generator'
        assert hasattr(gen, 'processor')
        assert hasattr(gen, 'client')

    def test_generator_has_required_methods(self):
        """Test generator has required interface methods"""
        gen = SolairusIntelligenceGenerator()

        assert hasattr(gen, 'generate_monthly_report')
        assert callable(gen.generate_monthly_report)

    def test_generator_has_last_run_status(self):
        """Test generator tracks last run status"""
        gen = SolairusIntelligenceGenerator()

        assert hasattr(gen, 'last_run_status')


class TestCLIHelpers:
    """Test CLI helper functions"""

    def test_month_format(self):
        """Test month formatting for report titles"""
        now = datetime.now()
        month_str = now.strftime("%B %Y")

        # Should be format like "December 2024"
        assert len(month_str.split()) == 2
        assert month_str.split()[0] in [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]


class TestCLIConfiguration:
    """Test CLI configuration"""

    def test_default_config(self):
        """Test generator uses default config when none provided"""
        gen = SolairusIntelligenceGenerator()

        assert gen.config is not None

    def test_custom_config(self):
        """Test generator accepts custom config"""
        from solairus_intelligence.clients.ergomind_client import ErgoMindConfig

        custom_config = ErgoMindConfig()
        gen = SolairusIntelligenceGenerator(config=custom_config)

        assert gen.config is custom_config
