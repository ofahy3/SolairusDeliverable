"""Solairus Intelligence Report Generator API"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from solairus_intelligence.cli import SolairusIntelligenceGenerator


async def generate_report(
    month: Optional[str] = None,
    test_mode: bool = False,
) -> Path:
    """
    Generate an intelligence report.

    Args:
        month: Report month (e.g., "December 2024"). Defaults to current month.
        test_mode: If True, uses limited queries for faster testing.

    Returns:
        Path to the generated report file.

    Raises:
        RuntimeError: If report generation fails.
    """
    if month is None:
        month = datetime.now().strftime("%B %Y")

    generator = SolairusIntelligenceGenerator()
    report_path, status = await generator.generate_monthly_report(test_mode=test_mode)

    if not status.get("success", False):
        errors = status.get("errors", ["Unknown error"])
        raise RuntimeError(f"Report generation failed: {'; '.join(errors)}")

    return Path(report_path)


def generate_report_sync(
    month: Optional[str] = None,
    test_mode: bool = False,
) -> Path:
    """
    Generate an intelligence report synchronously.

    Args:
        month: Report month (e.g., "December 2024"). Defaults to current month.
        test_mode: If True, uses limited queries for faster testing.

    Returns:
        Path to the generated report file.
    """
    return asyncio.run(generate_report(month=month, test_mode=test_mode))
