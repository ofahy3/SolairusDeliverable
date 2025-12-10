"""
Solairus Intelligence Report Generator

A simple, elegant API for generating intelligence reports.

Usage:
    from solairus_intelligence import generate_report

    # Async usage (recommended)
    report_path = await generate_report(month="December 2024")

    # Sync usage
    report_path = generate_report_sync(month="December 2024")
"""

from solairus_intelligence.api import (
    generate_report,
    generate_report_sync,
    ReportConfig,
)

__version__ = "1.0.0"
__all__ = ["generate_report", "generate_report_sync", "ReportConfig", "__version__"]
