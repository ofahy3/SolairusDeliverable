"""
Unit tests for document styles module
"""

import pytest
from docx import Document
from docx.shared import RGBColor, Pt

from solairus_intelligence.core.document.styles import (
    ERGO_COLORS,
    SPACING,
    FontConfig,
    ErgoStyles,
)


class TestErgoColors:
    """Test suite for ERGO_COLORS constant"""

    def test_colors_defined(self):
        """Test colors dictionary is defined"""
        assert ERGO_COLORS is not None
        assert isinstance(ERGO_COLORS, dict)

    def test_primary_colors_present(self):
        """Test primary colors are present"""
        assert "primary_blue" in ERGO_COLORS
        assert "secondary_blue" in ERGO_COLORS
        assert "light_blue" in ERGO_COLORS

    def test_secondary_colors_present(self):
        """Test secondary colors are present"""
        assert "orange" in ERGO_COLORS
        assert "teal" in ERGO_COLORS
        assert "dark_navy" in ERGO_COLORS

    def test_base_colors_present(self):
        """Test base colors are present"""
        assert "black" in ERGO_COLORS
        assert "white" in ERGO_COLORS
        assert "dark_gray" in ERGO_COLORS

    def test_colors_are_rgb(self):
        """Test colors are RGBColor objects"""
        for name, color in ERGO_COLORS.items():
            assert isinstance(color, RGBColor), f"{name} is not RGBColor"


class TestSpacing:
    """Test suite for SPACING constant"""

    def test_spacing_defined(self):
        """Test spacing dictionary is defined"""
        assert SPACING is not None
        assert isinstance(SPACING, dict)

    def test_section_spacing(self):
        """Test section spacing values"""
        assert "section_before" in SPACING
        assert "section_after" in SPACING

    def test_paragraph_spacing(self):
        """Test paragraph spacing"""
        assert "paragraph" in SPACING
        assert "bullet" in SPACING

    def test_spacing_values_are_integers(self):
        """Test spacing values are integers"""
        for name, value in SPACING.items():
            assert isinstance(value, int), f"{name} is not int"


class TestFontConfig:
    """Test suite for FontConfig"""

    def test_default_config(self):
        """Test default font configuration"""
        config = FontConfig()

        assert config.name == "Calibri"
        assert config.heading_size == 14
        assert config.subheading_size == 12
        assert config.body_size == 10
        assert config.small_size == 9

    def test_custom_config(self):
        """Test custom font configuration"""
        config = FontConfig(name="Arial", heading_size=16, body_size=11)

        assert config.name == "Arial"
        assert config.heading_size == 16
        assert config.body_size == 11


class TestErgoStyles:
    """Test suite for ErgoStyles"""

    @pytest.fixture
    def styles(self):
        """Create ErgoStyles instance"""
        return ErgoStyles()

    def test_initialization(self, styles):
        """Test styles initialize correctly"""
        assert styles is not None
        assert styles.font_config is not None
        assert styles.colors is not None
        assert styles.spacing is not None

    def test_custom_font_config(self):
        """Test styles with custom font config"""
        config = FontConfig(name="Times New Roman")
        styles = ErgoStyles(font_config=config)

        assert styles.font_config.name == "Times New Roman"

    def test_apply_to_document(self, styles):
        """Test styles can be applied to document"""
        doc = Document()
        styles.apply_to_document(doc)

        # Check Normal style was modified
        normal = doc.styles["Normal"]
        assert normal.font.name == "Calibri"

    def test_get_color(self, styles):
        """Test get_color method"""
        color = styles.get_color("primary_blue")

        assert isinstance(color, RGBColor)

    def test_get_color_fallback(self, styles):
        """Test get_color returns black for unknown color"""
        color = styles.get_color("nonexistent_color")

        assert color == ERGO_COLORS["black"]

    def test_get_spacing(self, styles):
        """Test get_spacing method"""
        spacing = styles.get_spacing("section_before")

        assert isinstance(spacing, int)

    def test_get_spacing_fallback(self, styles):
        """Test get_spacing returns paragraph for unknown"""
        spacing = styles.get_spacing("nonexistent_spacing")

        assert spacing == SPACING["paragraph"]
