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
        assert hasattr(gen, 'merger')
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


class TestQualityAssessment:
    """Test quality assessment logic"""

    @pytest.fixture
    def generator(self):
        return SolairusIntelligenceGenerator()

    @pytest.fixture
    def sample_items(self):
        from solairus_intelligence.core.processor import IntelligenceItem
        from solairus_intelligence.config.clients import ClientSector

        return [
            IntelligenceItem(
                raw_content="Test content 1",
                processed_content="Processed content 1",
                category="geopolitical",
                relevance_score=0.9,
                confidence=0.85,
                so_what_statement="Monitor this development",
                affected_sectors=[ClientSector.GENERAL],
                action_items=["Review impact", "Update clients"],
            ),
            IntelligenceItem(
                raw_content="Test content 2",
                processed_content="Processed content 2",
                category="economic",
                relevance_score=0.8,
                confidence=0.9,
                so_what_statement="Budget implications",
                affected_sectors=[ClientSector.FINANCE],
                action_items=["Check costs"],
            ),
            IntelligenceItem(
                raw_content="Test content 3",
                processed_content="Processed content 3",
                category="trade",
                relevance_score=0.75,
                confidence=0.8,
                so_what_statement="Supply chain impact",
                affected_sectors=[ClientSector.TECHNOLOGY],
                action_items=["Monitor supply"],
            ),
            IntelligenceItem(
                raw_content="Test content 4",
                processed_content="Processed content 4",
                category="regulatory",
                relevance_score=0.85,
                confidence=0.88,
                so_what_statement="Compliance review needed",
                affected_sectors=[ClientSector.HEALTHCARE],
                action_items=["Legal review"],
            ),
            IntelligenceItem(
                raw_content="Test content 5",
                processed_content="Processed content 5",
                category="geopolitical",
                relevance_score=0.7,
                confidence=0.75,
                so_what_statement="Watch for escalation",
                affected_sectors=[ClientSector.GENERAL],
                action_items=["Track developments"],
            ),
        ]

    @pytest.fixture
    def sample_sector_intel(self, sample_items):
        from solairus_intelligence.config.clients import ClientSector
        from solairus_intelligence.core.processor import SectorIntelligence

        return {
            ClientSector.GENERAL: SectorIntelligence(
                sector=ClientSector.GENERAL,
                items=[sample_items[0], sample_items[4]],
                summary="General sector summary",
            ),
            ClientSector.FINANCE: SectorIntelligence(
                sector=ClientSector.FINANCE,
                items=[sample_items[1]],
                summary="Finance sector summary",
            ),
            ClientSector.TECHNOLOGY: SectorIntelligence(
                sector=ClientSector.TECHNOLOGY,
                items=[sample_items[2]],
                summary="Technology sector summary",
            ),
            ClientSector.HEALTHCARE: SectorIntelligence(
                sector=ClientSector.HEALTHCARE,
                items=[sample_items[3]],
                summary="Healthcare sector summary",
            ),
        }

    def test_quality_score_with_good_data(self, generator, sample_items, sample_sector_intel):
        """Test quality assessment with good quality data"""
        score = generator._assess_quality(sample_items, sample_sector_intel)

        assert score > 0.5
        assert score <= 1.0

    def test_quality_score_empty_items(self, generator):
        """Test quality assessment with empty items list"""
        score = generator._assess_quality([], {})

        assert score == 0.0

    def test_quality_score_few_items(self, generator, sample_items, sample_sector_intel):
        """Test quality assessment with few items"""
        few_items = sample_items[:2]
        score = generator._assess_quality(few_items, sample_sector_intel)

        # Should be lower due to fewer items
        assert 0.0 <= score <= 1.0

    def test_quality_score_high_relevance(self, generator, sample_items, sample_sector_intel):
        """Test quality assessment considers relevance scores"""
        # All items have relevance > 0.7
        score = generator._assess_quality(sample_items, sample_sector_intel)

        # Should get credit for high relevance items
        assert score > 0.3


class TestStatusManagement:
    """Test status tracking and persistence"""

    @pytest.fixture
    def generator(self):
        return SolairusIntelligenceGenerator()

    def test_status_initialization(self, generator):
        """Test initial status is None"""
        assert generator.last_run_status is None

    def test_save_status(self, generator, tmp_path, monkeypatch):
        """Test status saving to file"""
        # Mock the status file path
        status_file = tmp_path / "status.json"
        monkeypatch.setattr(
            "solairus_intelligence.cli.get_status_file_path",
            lambda: str(status_file)
        )

        status = {
            'success': True,
            'queries_executed': 10,
            'items_processed': 5,
        }

        generator._save_status(status)

        assert status_file.exists()

        import json
        with open(status_file) as f:
            saved_status = json.load(f)

        assert saved_status['success'] is True
        assert saved_status['queries_executed'] == 10


class TestPrintSummary:
    """Test summary printing"""

    @pytest.fixture
    def generator(self):
        return SolairusIntelligenceGenerator()

    def test_print_summary_success(self, generator, capsys):
        """Test printing summary for successful run"""
        status = {
            'success': True,
            'queries_executed': 15,
            'items_processed': 10,
            'sectors_covered': ['general', 'finance', 'technology'],
            'quality_score': 0.85,
            'report_path': '/tmp/test_report.docx',
            'errors': [],
        }
        start_time = datetime.now()

        generator._print_summary(status, start_time)

        captured = capsys.readouterr()
        assert 'SUCCESS' in captured.out
        assert '15' in captured.out  # queries
        assert '10' in captured.out  # items
        assert '85' in captured.out  # quality score percentage

    def test_print_summary_with_errors(self, generator, capsys):
        """Test printing summary with errors"""
        status = {
            'success': False,
            'queries_executed': 5,
            'items_processed': 0,
            'sectors_covered': [],
            'quality_score': 0.0,
            'report_path': None,
            'errors': ['Connection failed', 'Timeout error'],
        }
        start_time = datetime.now()

        generator._print_summary(status, start_time)

        captured = capsys.readouterr()
        assert 'FAILED' in captured.out
        assert 'Connection failed' in captured.out
        assert 'Timeout error' in captured.out

    def test_print_summary_with_source_status(self, generator, capsys):
        """Test printing summary with source status"""
        status = {
            'success': True,
            'queries_executed': 20,
            'items_processed': 15,
            'sectors_covered': ['general'],
            'quality_score': 0.7,
            'report_path': '/tmp/report.docx',
            'errors': [],
            'source_status': {
                'ergomind': 'success',
                'gta': 'success',
                'fred': 'failed',
            },
        }
        start_time = datetime.now()

        generator._print_summary(status, start_time)

        captured = capsys.readouterr()
        assert 'ErgoMind' in captured.out
        assert 'GTA' in captured.out
        assert 'FRED' in captured.out

    def test_print_summary_with_ai_usage(self, generator, capsys):
        """Test printing summary with AI usage stats"""
        status = {
            'success': True,
            'queries_executed': 10,
            'items_processed': 8,
            'sectors_covered': ['general'],
            'quality_score': 0.8,
            'report_path': '/tmp/report.docx',
            'errors': [],
            'ai_usage': {
                'total_requests': 5,
                'successful_requests': 5,
                'total_input_tokens': 1000,
                'total_output_tokens': 500,
                'total_cost_usd': 0.0123,
            },
        }
        start_time = datetime.now()

        generator._print_summary(status, start_time)

        captured = capsys.readouterr()
        assert 'AI Enhancement' in captured.out
        assert '5' in captured.out  # API calls
        assert '1,000' in captured.out or '1000' in captured.out  # tokens
