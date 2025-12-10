"""
Unit tests for the public API module
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from datetime import datetime

from solairus_intelligence.api import (
    generate_report,
    generate_report_sync,
    ReportConfig,
)


class TestReportConfig:
    """Test suite for ReportConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ReportConfig()

        assert config.month is None
        assert config.sources == ["ergomind", "gta", "fred"]
        assert config.output_format == "docx"
        assert config.output_dir is None
        assert config.test_mode is False

    def test_custom_config(self):
        """Test custom configuration values"""
        config = ReportConfig(
            month="December 2024",
            sources=["ergomind", "gta"],
            output_format="docx",
            output_dir=Path("/tmp"),
            test_mode=True
        )

        assert config.month == "December 2024"
        assert config.sources == ["ergomind", "gta"]
        assert config.output_dir == Path("/tmp")
        assert config.test_mode is True


class TestGenerateReport:
    """Test suite for generate_report function"""

    @pytest.mark.asyncio
    async def test_generate_report_returns_path(self):
        """Test generate_report returns a Path object"""
        with patch('solairus_intelligence.api.SolairusIntelligenceGenerator') as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": True, "errors": []})
            )
            MockGen.return_value = mock_generator

            result = await generate_report(month="December 2024", test_mode=True)

            assert isinstance(result, Path)
            assert str(result) == "/tmp/report.docx"

    @pytest.mark.asyncio
    async def test_generate_report_default_month(self):
        """Test generate_report uses current month when not specified"""
        with patch('solairus_intelligence.api.SolairusIntelligenceGenerator') as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": True, "errors": []})
            )
            MockGen.return_value = mock_generator

            result = await generate_report(test_mode=True)

            assert isinstance(result, Path)

    @pytest.mark.asyncio
    async def test_generate_report_raises_on_failure(self):
        """Test generate_report raises RuntimeError on failure"""
        with patch('solairus_intelligence.api.SolairusIntelligenceGenerator') as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": False, "errors": ["Test error"]})
            )
            MockGen.return_value = mock_generator

            with pytest.raises(RuntimeError, match="Test error"):
                await generate_report(test_mode=True)

    @pytest.mark.asyncio
    async def test_generate_report_accepts_sources(self):
        """Test generate_report accepts sources parameter"""
        with patch('solairus_intelligence.api.SolairusIntelligenceGenerator') as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": True, "errors": []})
            )
            MockGen.return_value = mock_generator

            result = await generate_report(
                sources=["ergomind", "gta"],
                test_mode=True
            )

            assert isinstance(result, Path)


class TestGenerateReportSync:
    """Test suite for generate_report_sync function"""

    def test_sync_wrapper_returns_path(self):
        """Test sync wrapper returns correct result"""
        with patch('solairus_intelligence.api.SolairusIntelligenceGenerator') as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": True, "errors": []})
            )
            MockGen.return_value = mock_generator

            result = generate_report_sync(test_mode=True)

            assert isinstance(result, Path)
            assert str(result) == "/tmp/report.docx"

    def test_sync_wrapper_raises_on_failure(self):
        """Test sync wrapper raises on failure"""
        with patch('solairus_intelligence.api.SolairusIntelligenceGenerator') as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": False, "errors": ["Failed"]})
            )
            MockGen.return_value = mock_generator

            with pytest.raises(RuntimeError):
                generate_report_sync(test_mode=True)


class TestPublicAPIExports:
    """Test that public API exports correctly"""

    def test_imports_from_package(self):
        """Test imports from package root"""
        from solairus_intelligence import generate_report, generate_report_sync, ReportConfig

        assert callable(generate_report)
        assert callable(generate_report_sync)
        assert ReportConfig is not None

    def test_version_exported(self):
        """Test version is exported"""
        from solairus_intelligence import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0
