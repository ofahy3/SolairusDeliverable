"""
Document generation package for MRO Intelligence Reports.

This package splits the document generation logic into focused modules:
- styles: Document styling, colors, and formatting
- content: Content extraction and insight parsing
- sections: Section builders (executive summary, regional assessment, etc.)
- generator: Main DocumentGenerator class that orchestrates everything
"""

from mro_intelligence.core.document.generator import DocumentGenerator
from mro_intelligence.core.document.styles import ERGO_COLORS, SPACING, ErgoStyles

__all__ = [
    "DocumentGenerator",
    "ErgoStyles",
    "ERGO_COLORS",
    "SPACING",
]
