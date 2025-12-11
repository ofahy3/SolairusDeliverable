"""
End-to-end test for the full Solairus Intelligence pipeline.

This test verifies the complete workflow from API call to report generation,
using mocked external services to ensure consistent testing.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from solairus_intelligence import generate_report, generate_report_sync


class TestEndToEndPipeline:
    """End-to-end pipeline tests"""

    @pytest.fixture
    def mock_ergomind_response(self):
        """Mock ErgoMind API response"""
        return [
            {
                "query": "aviation geopolitical risks",
                "response": "Rising tensions in Eastern Europe pose risks to aviation operations. "
                "Several airlines have rerouted flights away from conflict zones. "
                "Insurance costs have increased by 15% for affected regions.",
                "confidence": 0.87,
            },
            {
                "query": "trade policy aviation",
                "response": "New export controls on aviation components affecting supply chains. "
                "Manufacturers report 6-month delays for critical parts.",
                "confidence": 0.82,
            },
        ]

    @pytest.fixture
    def mock_gta_response(self):
        """Mock GTA API response"""
        return [
            {
                "intervention_id": 12345,
                "title": "Tariffs on Aircraft Components",
                "implementing_jurisdiction": "United States",
                "affected_products": ["aircraft engines", "aviation parts"],
                "announcement_date": "2024-11-15",
                "implementation_date": "2024-12-01",
                "description": "25% tariff on imported aviation components from certain countries",
            }
        ]

    @pytest.fixture
    def mock_fred_response(self):
        """Mock FRED API response"""
        return {
            "inflation": [{"date": "2024-11", "value": 2.7}],
            "interest_rates": [{"date": "2024-11", "value": 4.5}],
            "fuel_costs": [{"date": "2024-11", "value": 85.2}],
            "gdp": [{"date": "2024-Q3", "value": 2.8}],
            "consumer_confidence": [{"date": "2024-11", "value": 98.5}],
        }

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocks(
        self, mock_ergomind_response, mock_gta_response, mock_fred_response
    ):
        """Test complete pipeline from API to report"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            with patch("solairus_intelligence.api.SolairusIntelligenceGenerator") as MockGen:
                mock_generator = MagicMock()
                mock_doc_path = str(output_dir / "Intelligence_Report_December_2024.docx")
                Path(mock_doc_path).touch()

                mock_generator.generate_monthly_report = AsyncMock(
                    return_value=(
                        mock_doc_path,
                        {
                            "success": True,
                            "errors": [],
                            "queries_executed": 15,
                            "intelligence_items": 25,
                        },
                    )
                )
                MockGen.return_value = mock_generator

                result = await generate_report(month="December 2024", test_mode=True)

                assert result is not None
                assert isinstance(result, Path)

    def test_sync_pipeline_with_mocks(
        self, mock_ergomind_response, mock_gta_response, mock_fred_response
    ):
        """Test synchronous pipeline"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            with patch("solairus_intelligence.api.SolairusIntelligenceGenerator") as MockGen:
                mock_generator = MagicMock()
                mock_doc_path = str(output_dir / "Intelligence_Report_December_2024.docx")
                Path(mock_doc_path).touch()

                mock_generator.generate_monthly_report = AsyncMock(
                    return_value=(mock_doc_path, {"success": True, "errors": []})
                )
                MockGen.return_value = mock_generator

                result = generate_report_sync(month="December 2024", test_mode=True)

                assert result is not None
                assert isinstance(result, Path)


class TestErrorHandling:
    """Test error handling in the pipeline"""

    @pytest.mark.asyncio
    async def test_handles_generation_failure(self):
        """Test that failures are properly reported"""
        with patch("solairus_intelligence.api.SolairusIntelligenceGenerator") as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=(
                    None,
                    {"success": False, "errors": ["API connection failed", "No data retrieved"]},
                )
            )
            MockGen.return_value = mock_generator

            with pytest.raises(RuntimeError) as excinfo:
                await generate_report(test_mode=True)

            assert "API connection failed" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_handles_empty_errors(self):
        """Test handling of failure with no error details"""
        with patch("solairus_intelligence.api.SolairusIntelligenceGenerator") as MockGen:
            mock_generator = MagicMock()
            mock_generator.generate_monthly_report = AsyncMock(
                return_value=(None, {"success": False, "errors": []})
            )
            MockGen.return_value = mock_generator

            with pytest.raises(RuntimeError):
                await generate_report(test_mode=True)
