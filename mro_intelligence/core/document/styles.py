"""
Document Styles for MRO Intelligence Reports.

Contains Ergo brand colors, spacing constants, and style configuration.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt, RGBColor

# Ergo brand colors (full palette)
ERGO_COLORS: Dict[str, RGBColor] = {
    # Primary colors
    "primary_blue": RGBColor(27, 41, 70),  # #1B2946 (colorP1)
    "secondary_blue": RGBColor(2, 113, 195),  # #0271C3 (colorP2)
    "light_blue": RGBColor(148, 176, 201),  # #94B0C9 (colorP3)
    # Secondary colors
    "orange": RGBColor(232, 116, 73),  # #E87449 (colorS1)
    "teal": RGBColor(0, 221, 204),  # #00DDCC (colorS2)
    "dark_navy": RGBColor(19, 31, 51),  # #131F33 (colorS3)
    # Tertiary colors
    "deep_orange": RGBColor(196, 97, 60),  # #C4613C (colorT1)
    "light_gray": RGBColor(229, 234, 239),  # #E5EAEF (colorT2)
    "dark_teal": RGBColor(1, 185, 171),  # #01B9AB (colorT3)
    "dark_blue": RGBColor(1, 93, 162),  # #015DA2 (colorT4)
    # Base colors
    "dark_gray": RGBColor(100, 100, 100),
    "black": RGBColor(0, 0, 0),
    "white": RGBColor(255, 255, 255),
}


# Standardized spacing constants (in points) for consistent document layout
SPACING: Dict[str, int] = {
    "section_before": 18,  # Space before major section headings
    "section_after": 8,  # Space after section headings
    "subsection_before": 12,  # Space before subsection headings
    "subsection_after": 6,  # Space after subsection headings
    "paragraph": 8,  # Standard paragraph spacing
    "bullet": 4,  # Space after bullet items
    "table_after": 12,  # Space after tables
    "header_after": 6,  # Space after header elements
}


@dataclass
class FontConfig:
    """Font configuration for document elements"""

    name: str = "Calibri"
    heading_size: int = 14
    subheading_size: int = 12
    body_size: int = 10
    small_size: int = 9


class ErgoStyles:
    """
    Manages document styles for Ergo-branded reports.

    Provides methods to apply consistent styling across documents.
    """

    def __init__(self, font_config: Optional[FontConfig] = None):
        self.font_config = font_config or FontConfig()
        self.colors = ERGO_COLORS
        self.spacing = SPACING

    def apply_to_document(self, doc: Document) -> None:
        """Apply Ergo styles to a document"""
        self._setup_normal_style(doc)
        self._create_heading_styles(doc)

    def _setup_normal_style(self, doc: Document) -> None:
        """Configure the Normal style"""
        style = doc.styles["Normal"]
        font = style.font
        font.name = self.font_config.name
        font.size = Pt(self.font_config.body_size)
        font.color.rgb = self.colors["black"]

    def _create_heading_styles(self, doc: Document) -> None:
        """Create custom heading styles"""
        self._create_custom_heading_style(
            doc, "Section Heading", self.font_config.heading_size, bold=True
        )
        self._create_custom_heading_style(
            doc, "Subsection Heading", self.font_config.subheading_size, bold=True
        )

    def _create_custom_heading_style(self, doc: Document, name: str, size: int, bold: bool) -> None:
        """Create a custom heading style"""
        try:
            style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = doc.styles["Normal"]
            font = style.font
            font.name = self.font_config.name
            font.size = Pt(size)
            font.bold = bold
            font.color.rgb = self.colors["primary_blue"]
        except ValueError:
            # Style already exists
            pass

    def get_color(self, name: str) -> RGBColor:
        """Get a color by name"""
        return self.colors.get(name, self.colors["black"])

    def get_spacing(self, name: str) -> int:
        """Get a spacing value by name"""
        return self.spacing.get(name, self.spacing["paragraph"])
