"""
Document generation package for Solairus Intelligence Reports.

This package splits the document generation logic into focused modules:
- styles: Document styling, colors, and formatting
- content: Content extraction and insight parsing
- sections: Section builders (executive summary, regional assessment, etc.)
- generator: Main DocumentGenerator class that orchestrates everything
"""

from solairus_intelligence.core.document.generator import DocumentGenerator
from solairus_intelligence.core.document.styles import ErgoStyles, ERGO_COLORS, SPACING

__all__ = [
    "DocumentGenerator",
    "ErgoStyles",
    "ERGO_COLORS",
    "SPACING",
]
