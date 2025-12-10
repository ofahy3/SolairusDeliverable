"""
Document Generator for Solairus Intelligence Reports.

This module provides backwards compatibility by re-exporting from the
refactored document package. The actual implementation is now in:
- solairus_intelligence.core.document.generator
- solairus_intelligence.core.document.styles
- solairus_intelligence.core.document.content
- solairus_intelligence.core.document.sections
"""

# Re-export the main class for backwards compatibility
from solairus_intelligence.core.document.generator import DocumentGenerator
from solairus_intelligence.core.document.styles import (
    ErgoStyles,
    ERGO_COLORS,
    SPACING,
    FontConfig,
)
from solairus_intelligence.core.document.content import ContentExtractor
from solairus_intelligence.core.document.sections import (
    HeaderBuilder,
    ExecutiveSummaryBuilder,
    EconomicIndicatorsBuilder,
    RegionalAssessmentBuilder,
    SectorSectionBuilder,
)

__all__ = [
    'DocumentGenerator',
    'ErgoStyles',
    'ERGO_COLORS',
    'SPACING',
    'FontConfig',
    'ContentExtractor',
    'HeaderBuilder',
    'ExecutiveSummaryBuilder',
    'EconomicIndicatorsBuilder',
    'RegionalAssessmentBuilder',
    'SectorSectionBuilder',
]
