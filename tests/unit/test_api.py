"""Unit tests for the public API module"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mro_intelligence.api import generate_report, generate_report_sync


class TestGenerateReport:
    """Test suite for generate_report function"""

    @pytest.mark.asyncio
    async def test_generate_report_returns_path(self):
        """Test generate_report returns a Path object"""
        with patch("mro_intelligence.api.MROIntelligenceGenerator") as MockGen:
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
        with patch("mro_intelligence.api.MROIntelligenceGenerator") as MockGen:
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
        with patch("mro_intelligence.api.MROIntelligenceGenerator") as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": False, "errors": ["Test error"]})
            )
            MockGen.return_value = mock_generator

            with pytest.raises(RuntimeError, match="Test error"):
                await generate_report(test_mode=True)


class TestGenerateReportSync:
    """Test suite for generate_report_sync function"""

    def test_sync_wrapper_returns_path(self):
        """Test sync wrapper returns correct result"""
        with patch("mro_intelligence.api.MROIntelligenceGenerator") as MockGen:
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
        with patch("mro_intelligence.api.MROIntelligenceGenerator") as MockGen:
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
        from mro_intelligence import generate_report, generate_report_sync

        assert callable(generate_report)
        assert callable(generate_report_sync)

    def test_version_exported(self):
        """Test version is exported"""
        from mro_intelligence import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0
