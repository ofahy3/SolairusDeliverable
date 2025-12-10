"""
Simple Public API for Solairus Intelligence

This module provides a clean, Stripe-style API for generating intelligence reports.
Designed to make complex functionality accessible in just a few lines of code.

Usage:
    from solairus_intelligence import generate_report

    # Generate a report (async)
    report_path = await generate_report(month="December 2024")

    # Generate with options
    report_path = await generate_report(
        month="December 2024",
        sources=["ergomind", "gta", "fred"],
        output_format="docx"
    )
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal

from solairus_intelligence.cli import SolairusIntelligenceGenerator
from solairus_intelligence.utils.config import get_output_dir


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    month: Optional[str] = None  # e.g., "December 2024" - defaults to current month
    sources: List[Literal["ergomind", "gta", "fred"]] = field(
        default_factory=lambda: ["ergomind", "gta", "fred"]
    )
    output_format: Literal["docx"] = "docx"
    output_dir: Optional[Path] = None
    test_mode: bool = False  # Use limited queries for testing


async def generate_report(
    month: Optional[str] = None,
    sources: Optional[List[str]] = None,
    output_format: str = "docx",
    output_dir: Optional[Path] = None,
    test_mode: bool = False,
) -> Path:
    """
    Generate an intelligence report asynchronously.

    This is the primary API for generating Solairus intelligence reports.
    It handles all the complexity internally and returns the path to the
    generated report.

    Args:
        month: Report month (e.g., "December 2024"). Defaults to current month.
        sources: Data sources to use. Options: ["ergomind", "gta", "fred"].
                 Defaults to all three.
        output_format: Output format. Currently only "docx" is supported.
        output_dir: Custom output directory. Defaults to ./outputs/ or
                    /mnt/user-data/outputs/ in Docker.
        test_mode: If True, uses limited queries for faster testing.

    Returns:
        Path to the generated report file.

    Raises:
        RuntimeError: If report generation fails.

    Example:
        >>> from solairus_intelligence import generate_report
        >>> report = await generate_report(month="December 2024")
        >>> print(f"Report saved to: {report}")
    """
    # Set defaults
    if month is None:
        month = datetime.now().strftime("%B %Y")

    if sources is None:
        sources = ["ergomind", "gta", "fred"]

    if output_dir is None:
        output_dir = get_output_dir()

    # Create generator and run
    generator = SolairusIntelligenceGenerator()

    # Generate the report
    report_path, status = await generator.generate_monthly_report(
        test_mode=test_mode
    )

    if not status.get("success", False):
        errors = status.get("errors", ["Unknown error"])
        raise RuntimeError(f"Report generation failed: {'; '.join(errors)}")

    return Path(report_path)


def generate_report_sync(
    month: Optional[str] = None,
    sources: Optional[List[str]] = None,
    output_format: str = "docx",
    output_dir: Optional[Path] = None,
    test_mode: bool = False,
) -> Path:
    """
    Generate an intelligence report synchronously.

    This is a convenience wrapper around generate_report() for use in
    synchronous code contexts.

    Args:
        month: Report month (e.g., "December 2024"). Defaults to current month.
        sources: Data sources to use. Options: ["ergomind", "gta", "fred"].
        output_format: Output format. Currently only "docx" is supported.
        output_dir: Custom output directory.
        test_mode: If True, uses limited queries for faster testing.

    Returns:
        Path to the generated report file.

    Example:
        >>> from solairus_intelligence import generate_report_sync
        >>> report = generate_report_sync(month="December 2024")
        >>> print(f"Report saved to: {report}")
    """
    return asyncio.run(
        generate_report(
            month=month,
            sources=sources,
            output_format=output_format,
            output_dir=output_dir,
            test_mode=test_mode,
        )
    )


# Convenience aliases
create_report = generate_report
create_report_sync = generate_report_sync
