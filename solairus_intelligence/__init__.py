"""
Solairus Intelligence Report Generator

Usage:
    from solairus_intelligence import generate_report
    report = await generate_report()
"""

from solairus_intelligence.api import generate_report, generate_report_sync

__version__ = "1.0.0"
__all__ = ["generate_report", "generate_report_sync", "__version__"]
