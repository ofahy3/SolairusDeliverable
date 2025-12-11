"""
Main Document Generator for Solairus Intelligence Reports.

Orchestrates the document generation process using focused modules.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.shared import Inches

from solairus_intelligence.core.document.content import ContentExtractor
from solairus_intelligence.core.document.sections import (
    EconomicIndicatorsBuilder,
    ExecutiveSummaryBuilder,
    HeaderBuilder,
    RegionalAssessmentBuilder,
    SectorSectionBuilder,
)
from solairus_intelligence.core.document.styles import ERGO_COLORS, ErgoStyles
from solairus_intelligence.core.processor import (
    ClientSector,
    IntelligenceItem,
    SectorIntelligence,
)
from solairus_intelligence.utils.config import ENV_CONFIG, get_output_dir

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """
    Generates professional DOCX reports optimized for Google Docs.

    Uses a modular architecture with separate components for:
    - Styles: Brand colors and formatting
    - Content: Data extraction and parsing
    - Sections: Individual report section builders
    """

    def __init__(self):
        # Initialize components
        self.styles = ErgoStyles()
        self.content_extractor = ContentExtractor()

        # Path to logo
        self.logo_path = str(
            Path(__file__).parent.parent.parent / "web" / "static" / "images" / "ergo_logo.png"
        )

        # Initialize AI generator if enabled
        self.ai_generator: Optional[Any] = None
        if ENV_CONFIG.ai_enabled:
            self._init_ai_generator()

        # Initialize section builders
        self.header_builder = HeaderBuilder(self.styles, self.logo_path)
        self.exec_summary_builder = ExecutiveSummaryBuilder(
            self.styles, self.content_extractor, self.ai_generator
        )
        self.econ_indicators_builder = EconomicIndicatorsBuilder(
            self.styles, self.content_extractor
        )
        self.regional_builder = RegionalAssessmentBuilder(self.styles, self.content_extractor)
        self.sector_builder = SectorSectionBuilder(self.styles, self.content_extractor)

        # Backwards compatibility attributes
        self.ergo_colors = ERGO_COLORS
        self.output_dir = get_output_dir()

    def _init_ai_generator(self) -> None:
        """Initialize AI generator for enhanced summaries"""
        try:
            from solairus_intelligence.ai.generator import AIConfig, SecureAIGenerator

            api_key = ENV_CONFIG.anthropic_api_key
            if not api_key:
                logger.info("AI generation disabled: no API key configured")
                return

            config = AIConfig(api_key=api_key, model=ENV_CONFIG.ai_model, enabled=True)
            self.ai_generator = SecureAIGenerator(config)
            logger.info("✓ AI-enhanced Executive Summary enabled")
        except Exception as e:
            logger.warning(f"AI generator initialization failed: {e}")

    def create_report(
        self,
        solairus_items: List[IntelligenceItem],
        sector_intelligence: Dict[ClientSector, SectorIntelligence],
        report_month: Optional[str] = None,
    ) -> Document:
        """
        Create a complete intelligence report.

        Args:
            solairus_items: List of intelligence items
            sector_intelligence: Dictionary of sector-specific intelligence
            report_month: Month for the report (e.g., "December 2024")

        Returns:
            Generated Document object
        """
        doc = Document()
        self._setup_document(doc)

        # Use current month if not specified
        if not report_month:
            report_month = datetime.now().strftime("%B %Y")

        # Build Page 1: Business Intelligence Overview
        self._create_page_1(doc, solairus_items, report_month)

        # Add page break
        doc.add_page_break()

        # Build Page 2: Sector Analysis
        self._create_page_2(doc, sector_intelligence, report_month)

        return doc

    def _setup_document(self, doc: Document) -> None:
        """Set up document properties and styles"""
        # Document properties
        core_props = doc.core_properties
        core_props.author = "Ergo Intelligence"
        core_props.title = "Monthly Intelligence Report"

        # Apply styles
        self.styles.apply_to_document(doc)

        # Set margins
        for section in doc.sections:
            section.page_width = Inches(8.5)
            section.page_height = Inches(11)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)

    def _create_page_1(self, doc: Document, items: List[IntelligenceItem], month: str) -> None:
        """Create page 1: Business Intelligence Overview"""
        # Header
        self.header_builder.add_header(doc, "Solairus Business Intelligence", month)

        # Executive Summary
        self.exec_summary_builder.add_executive_summary(doc, items)

        # Economic Indicators
        self.econ_indicators_builder.add_economic_indicators_table(doc, items)

        # Regional Assessment
        self.regional_builder.add_regional_assessment(doc, items)

    def _create_page_2(
        self, doc: Document, sector_intelligence: Dict[ClientSector, SectorIntelligence], month: str
    ) -> None:
        """Create page 2: Sector Analysis"""
        # Header
        self.header_builder.add_header(doc, "Sector Intelligence Analysis", month)

        # Add each sector
        for sector, intelligence in sector_intelligence.items():
            if intelligence.items:
                self.sector_builder.add_sector_section(doc, sector, intelligence)

    def save_report(self, doc: Document, filename: Optional[str] = None) -> str:
        """
        Save the report to a file.

        Args:
            doc: Document to save
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            month = datetime.now().strftime("%B_%Y")
            filename = f"Intelligence_Report_{month}_{timestamp}.docx"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        filepath = self.output_dir / filename
        doc.save(str(filepath))

        logger.info(f"Report saved: {filepath}")
        return str(filepath)

    # Backwards compatibility methods
    def _apply_styles(self, doc: Document) -> None:
        """Backwards compatible style application"""
        self.styles.apply_to_document(doc)

    def _setup_document_properties(self, doc: Document) -> None:
        """Backwards compatible setup"""
        self._setup_document(doc)
