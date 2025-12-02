"""
Document Generator for Solairus Intelligence Reports
Creates professional, Google Docs-compatible DOCX files with elegant formatting
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from solairus_intelligence.core.processor import ClientSector, IntelligenceItem, SectorIntelligence
from solairus_intelligence.utils.config import ENV_CONFIG, get_output_dir


class DocumentGenerator:
    """
    Generates professional DOCX reports optimized for Google Docs
    With optional AI-enhanced Executive Summary generation
    """

    def __init__(self):
        # Ergo brand colors (full palette)
        self.ergo_colors = {
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
        self.spacing = {
            "section_before": 18,  # Space before major section headings
            "section_after": 8,  # Space after section headings
            "subsection_before": 12,  # Space before subsection headings
            "subsection_after": 6,  # Space after subsection headings
            "paragraph": 8,  # Standard paragraph spacing
            "bullet": 4,  # Space after bullet items
            "table_after": 12,  # Space after tables
            "header_after": 6,  # Space after header elements
        }

        # Path to logo
        self.logo_path = (
            Path(__file__).parent.parent / "web" / "static" / "images" / "ergo_logo.png"
        )

        # Initialize AI generator if enabled
        self.ai_generator = None
        if ENV_CONFIG.ai_enabled:
            try:
                from solairus_intelligence.ai.generator import AIConfig, SecureAIGenerator

                config = AIConfig(
                    api_key=ENV_CONFIG.anthropic_api_key, model=ENV_CONFIG.ai_model, enabled=True
                )
                self.ai_generator = SecureAIGenerator(config)
                import logging

                logging.getLogger(__name__).info("✓ AI-enhanced Executive Summary enabled")
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(f"AI generator initialization failed: {e}")

    def create_report(
        self,
        solairus_items: List[IntelligenceItem],
        sector_intelligence: Dict[ClientSector, SectorIntelligence],
        report_month: Optional[str] = None,
    ) -> Document:
        """
        Create a complete two-page intelligence report
        """
        doc = Document()
        self._setup_document_properties(doc)
        self._apply_styles(doc)

        # Use current month if not specified
        if not report_month:
            report_month = datetime.now().strftime("%B %Y")

        # Page 1: Solairus Business Intelligence
        self._create_page_1(doc, solairus_items, report_month)

        # Page break
        doc.add_page_break()

        # Page 2: Client Sector Intelligence
        self._create_page_2(doc, sector_intelligence, report_month)

        return doc

    def _setup_document_properties(self, doc: Document):
        """Set up document properties for optimal Google Docs compatibility"""
        # Set page margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

    def _apply_styles(self, doc: Document):
        """Apply professional styling to the document"""
        # Modify default paragraph font
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Arial"  # Google Docs compatible
        font.size = Pt(11)
        font.color.rgb = self.ergo_colors["black"]

        # Create custom heading styles
        self._create_custom_heading_style(doc, "CustomHeading1", 16, True)
        self._create_custom_heading_style(doc, "CustomHeading2", 14, True)
        self._create_custom_heading_style(doc, "CustomHeading3", 12, False)

    def _create_custom_heading_style(self, doc: Document, name: str, size: int, bold: bool):
        """Create a custom heading style with standardized spacing"""
        styles = doc.styles
        if name not in styles:
            style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = styles["Normal"]
            font = style.font
            font.size = Pt(size)
            font.bold = bold
            font.color.rgb = self.ergo_colors["primary_blue"]
            paragraph_format = style.paragraph_format
            paragraph_format.space_before = Pt(self.spacing["section_before"])
            paragraph_format.space_after = Pt(self.spacing["section_after"])

    def _create_page_1(self, doc: Document, items: List[IntelligenceItem], month: str):
        """Create Page 1: Solairus Business Intelligence"""

        # Header
        self._add_header(doc, "FLASHPOINTS FORUM INTELLIGENCE BRIEF", month)

        # Executive Summary
        self._add_section_heading(doc, "EXECUTIVE SUMMARY")
        self._add_executive_summary(doc, items)

        # Economic Indicators - as a table
        self._add_section_heading(doc, "ECONOMIC INDICATORS FOR BUSINESS AVIATION")
        econ_items = [
            item
            for item in items
            if "economic" in item.category
            or "financial" in item.category
            or "market" in item.category
        ]
        self._add_economic_indicators_table(doc, econ_items)

        # Regional Risk Assessments
        self._add_section_heading(doc, "REGIONAL RISK ASSESSMENTS")
        regional_items = [
            item
            for item in items
            if any(region in item.category for region in ["america", "europe", "asia", "middle"])
        ]
        self._add_regional_assessment(doc, regional_items)

        # Regulatory Horizon
        self._add_section_heading(doc, "REGULATORY HORIZON")
        reg_items = [
            item
            for item in items
            if "regulation" in item.category
            or "compliance" in item.category
            or "policy" in item.category
        ]
        self._add_regulatory_outlook(doc, reg_items)

    def _create_page_2(
        self, doc: Document, sector_intel: Dict[ClientSector, SectorIntelligence], month: str
    ):
        """Create Page 2: Client Sector Intelligence"""

        # Header
        self._add_header(doc, "CLIENT SECTOR INTELLIGENCE", month)

        # Prioritize sectors with most intelligence
        sorted_sectors = sorted(sector_intel.items(), key=lambda x: len(x[1].items), reverse=True)

        # Add top sectors (limit to fit on one page)
        sectors_to_include = sorted_sectors[:4]

        for sector, intelligence in sectors_to_include:
            if intelligence.items:  # Only include if there's actual intelligence
                self._add_sector_section(doc, sector, intelligence)

    def _add_header(self, doc: Document, title: str, subtitle: str):
        """Add a professional header to the document with logo"""
        # Add logo if it exists
        if self.logo_path.exists():
            try:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run()
                run.add_picture(str(self.logo_path), width=Inches(2.0))
                p.paragraph_format.space_after = Pt(self.spacing["table_after"])
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(f"Could not add logo to document: {e}")

        # Title
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = self.ergo_colors["primary_blue"]

        # Subtitle (Month Year)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(subtitle)
        run.font.size = Pt(14)
        run.font.color.rgb = self.ergo_colors["secondary_blue"]

        # Add a subtle line using orange accent
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("_" * 50).font.color.rgb = self.ergo_colors["orange"]

    def _add_section_heading(self, doc: Document, heading: str):
        """Add a section heading"""
        p = doc.add_paragraph()
        p.style = "CustomHeading2"
        p.add_run(heading)

    def _add_executive_summary(self, doc: Document, items: List[IntelligenceItem]):
        """Generate sharp, actionable executive summary in Ergo analytical voice"""

        # Extract analytical judgments from top items
        insights = self._extract_analytical_insights(items)

        # Structure: BOTTOM LINE (2 max) + KEY FINDINGS (3-5) + WATCH FACTORS (2-3)
        bottom_line_items = insights.get("bottom_line", [])[:2]
        key_findings = insights.get("key_findings", [])[:5]
        watch_factors = insights.get("watch_factors", [])[:3]

        # Add BOTTOM LINE section if items exist
        if bottom_line_items:
            # Section header
            p = doc.add_paragraph()
            run = p.add_run("BOTTOM LINE")
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = self.ergo_colors["primary_blue"]
            p.space_after = Pt(self.spacing["header_after"])

            for item_text in bottom_line_items:
                p = doc.add_paragraph()
                p.add_run(item_text)
                p.paragraph_format.space_after = Pt(self.spacing["paragraph"])

        # Add KEY FINDINGS section
        if key_findings:
            p = doc.add_paragraph()
            run = p.add_run("KEY FINDINGS")
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = self.ergo_colors["primary_blue"]
            p.space_after = Pt(self.spacing["header_after"])

            for finding in key_findings:
                # Extract subheader and content from structured finding
                if isinstance(finding, dict):
                    subheader = finding.get("subheader", "")
                    content = finding.get("content", "")
                    bullets = finding.get("bullets", [])
                else:
                    # Legacy format - parse or use as-is
                    subheader, content, bullets = self._parse_key_finding(finding)

                # Add subheader (bold, slightly smaller than section header)
                if subheader:
                    p = doc.add_paragraph()
                    run = p.add_run(subheader)
                    run.font.bold = True
                    run.font.size = Pt(10)
                    run.font.color.rgb = self.ergo_colors["secondary_blue"]
                    p.paragraph_format.space_before = Pt(self.spacing["paragraph"])
                    p.paragraph_format.space_after = Pt(self.spacing["bullet"])

                # Add main paragraph content
                if content:
                    p = doc.add_paragraph()
                    p.add_run(content)
                    p.paragraph_format.space_after = Pt(self.spacing["bullet"])

                # Add supporting bullets
                for bullet in bullets:
                    p = doc.add_paragraph()
                    p.add_run(f"• {bullet}")
                    p.paragraph_format.left_indent = Inches(0.25)
                    p.paragraph_format.space_after = Pt(self.spacing["bullet"])

                # Add spacing after each finding
                if bullets:
                    doc.add_paragraph().paragraph_format.space_after = Pt(self.spacing["bullet"])

        # Add WATCH FACTORS section as a table
        if watch_factors:
            p = doc.add_paragraph()
            run = p.add_run("WATCH FACTORS")
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = self.ergo_colors["primary_blue"]
            p.space_after = Pt(self.spacing["header_after"])

            # Create table with columns: Indicator | What to Watch | Why It Matters
            # Ensure at least 3 rows
            num_rows = max(3, len(watch_factors))
            table = doc.add_table(rows=num_rows + 1, cols=3)  # +1 for header row
            table.style = "Table Grid"

            # Set column widths
            for row in table.rows:
                row.cells[0].width = Inches(1.8)
                row.cells[1].width = Inches(2.5)
                row.cells[2].width = Inches(2.2)

            # Header row
            header_cells = table.rows[0].cells
            headers = ["Indicator", "What to Watch", "Why It Matters"]
            for i, header_text in enumerate(headers):
                header_cells[i].text = header_text
                # Style header
                for paragraph in header_cells[i].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
                        run.font.size = Pt(10)
                        run.font.color.rgb = self.ergo_colors["white"]
                # Set header background color
                from docx.oxml import parse_xml
                from docx.oxml.ns import nsdecls

                shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="1B2946"/>')
                header_cells[i]._tc.get_or_add_tcPr().append(shading_elm)

            # Data rows
            for row_idx, factor in enumerate(watch_factors[:num_rows]):
                data_row = table.rows[row_idx + 1]  # +1 to skip header

                # Parse watch factor into components
                if isinstance(factor, dict):
                    indicator = factor.get("indicator", "")
                    what_to_watch = factor.get("what_to_watch", "")
                    why_it_matters = factor.get("why_it_matters", "")
                else:
                    # Legacy format - parse the string
                    indicator, what_to_watch, why_it_matters = self._parse_watch_factor(factor)

                data_row.cells[0].text = indicator
                data_row.cells[1].text = what_to_watch
                data_row.cells[2].text = why_it_matters

                # Style data cells
                for cell in data_row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(9)

            # Fill empty rows if we have fewer than 3 watch factors
            if len(watch_factors) < 3:
                for row_idx in range(len(watch_factors), 3):
                    data_row = table.rows[row_idx + 1]
                    # Generate placeholder content based on available intelligence
                    placeholder = self._generate_placeholder_watch_factor(row_idx, items)
                    if placeholder:
                        data_row.cells[0].text = placeholder.get("indicator", "TBD")
                        data_row.cells[1].text = placeholder.get(
                            "what_to_watch", "Monitoring in progress"
                        )
                        data_row.cells[2].text = placeholder.get(
                            "why_it_matters", "Analysis pending"
                        )

            # Add spacing after table
            doc.add_paragraph()

    def _extract_analytical_insights(self, items: List[IntelligenceItem]) -> dict:
        """Extract sharp analytical insights from intelligence items

        Note: Freshness filtering now handled globally in merge_intelligence_sources()
        to ensure consistency across entire report (not just Executive Summary)

        Uses AI-enhanced generation when available, with template fallback
        """
        # Try AI generation first if enabled
        if self.ai_generator:
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.info("Attempting AI-enhanced Executive Summary generation...")

                # Handle both running and new event loop scenarios
                try:
                    asyncio.get_running_loop()
                    # If there's a running loop, use a thread pool
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.ai_generator.generate_executive_summary(
                                items,
                                fallback_generator=lambda x: self._extract_insights_template(x),
                            ),
                        )
                        ai_summary = future.result(timeout=120)
                except RuntimeError:
                    # No running event loop - safe to use asyncio.run
                    ai_summary = asyncio.run(
                        self.ai_generator.generate_executive_summary(
                            items, fallback_generator=lambda x: self._extract_insights_template(x)
                        )
                    )

                if ai_summary and any(ai_summary.values()):
                    logger.info("✓ AI-enhanced Executive Summary generated successfully")
                    return ai_summary

            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(f"AI generation failed, using template: {e}")

        # Fallback to template-based extraction
        return self._extract_insights_template(items)

    def _extract_insights_template(self, items: List[IntelligenceItem]) -> dict:
        """
        Template-based extraction (original implementation)
        Used as fallback when AI is unavailable or fails validation
        """
        bottom_line = []
        key_findings = []
        watch_factors = []

        # Sort by composite score (relevance × confidence)
        # No need to filter stale data here - already done in merge logic
        #
        # Prioritize ErgoMind for narrative leadership in Executive Summary
        # Ensures ErgoMind narrative items appear first in BOTTOM LINE and KEY FINDINGS
        ergomind_items = [i for i in items if i.source_type == "ergomind"]
        other_items = [i for i in items if i.source_type != "ergomind"]

        # Sort each group by composite score
        ergomind_sorted = sorted(
            ergomind_items, key=lambda x: (x.relevance_score * x.confidence), reverse=True
        )
        other_sorted = sorted(
            other_items, key=lambda x: (x.relevance_score * x.confidence), reverse=True
        )

        # Prioritize ErgoMind: scan ErgoMind first (~20 items), then data sources for supporting evidence
        prioritized = ergomind_sorted + other_sorted

        # Track content to avoid duplication
        seen_themes = set()

        for item in prioritized[:30]:  # Review top 30 items
            text = item.processed_content.lower()
            so_what = item.so_what_statement

            # Create theme fingerprint for deduplication
            theme = self._extract_theme(text, so_what)
            if theme in seen_themes:
                continue
            seen_themes.add(theme)

            # BOTTOM LINE: Immediate threats requiring action
            if (
                any(
                    kw in text
                    for kw in ["sanction", "blocking", "full blocking", "export control", "ban"]
                )
                and item.relevance_score > 0.7
                and len(bottom_line) < 2
            ):
                insight = self._craft_bottom_line_statement(item)
                if insight:
                    bottom_line.append(insight)
                    continue

            # KEY FINDINGS: Specific, actionable intelligence
            if item.relevance_score > 0.6 and len(key_findings) < 5:
                insight = self._craft_key_finding_statement(item)
                if insight and insight not in key_findings:
                    key_findings.append(insight)
                    continue

            # WATCH FACTORS: Forward-looking indicators
            if (
                any(
                    kw in text
                    for kw in ["trend", "signal", "increase", "decrease", "shift", "emerging"]
                )
                and len(watch_factors) < 3
            ):
                insight = self._craft_watch_factor_statement(item)
                if insight and insight not in watch_factors:
                    watch_factors.append(insight)

        return {
            "bottom_line": bottom_line,
            "key_findings": key_findings,
            "watch_factors": watch_factors,
        }

    def _extract_theme(self, text: str, so_what: str) -> str:
        """Extract core theme for deduplication"""
        # Combine key words from both text and so_what
        combined = (text + " " + so_what.lower())[:200]

        # Extract theme based on key terms
        if "sanction" in combined:
            return "sanctions"
        elif "tariff" in combined or "trade" in combined:
            return "trade"
        elif "inflation" in combined or "interest rate" in combined:
            return "monetary"
        elif "china" in combined and "us" in combined:
            return "us-china"
        elif "russia" in combined:
            return "russia"
        elif "aviation" in combined:
            return "aviation-specific"
        elif "fuel" in combined or "oil" in combined:
            return "fuel-costs"
        elif "technology" in combined or "semiconductor" in combined:
            return "tech-sector"
        else:
            # Use first 30 chars as fallback theme
            return combined[:30].strip()

    def _craft_bottom_line_statement(self, item: IntelligenceItem) -> str:
        """Craft authoritative bottom-line statement"""
        text = item.processed_content.lower()

        # Extract specific, high-impact statements
        if "rosneft" in text or "lukoil" in text or ("russian oil" in text and "sanction" in text):
            return "US full blocking sanctions on Russian oil majors create immediate compliance risk for clients with Russian exposure or routes through sanctioned jurisdictions."

        if "export control" in text and (
            "china" in text or "semiconductor" in text or "technology" in text
        ):
            return "Expanded US export controls on advanced technology require immediate client screening for Silicon Valley and tech sector exposure to restricted jurisdictions."

        if "full blocking" in text or "sdn list" in text:
            return "New sanctions regime requires client exposure audit within 30 days - particularly technology, energy, and financial sector clients with international operations."

        # Dynamic extraction for other high-priority threats
        if "airspace closure" in text or "flight ban" in text:
            return "New airspace restrictions require immediate route review and client notification - operational impacts within 48-72 hours."

        if "compliance risk" in text and "immediate" in text:
            # Extract the specific risk if mentioned
            sentences = item.processed_content.split(".")
            for sent in sentences[:3]:
                if "compliance" in sent.lower() and len(sent) > 40:
                    return sent.strip() + "."

        return None

    def _craft_key_finding_statement(self, item: IntelligenceItem) -> str:
        """Craft analytical key finding in Ergo voice - lead with judgment, support with evidence

        Always returns content - uses processed_content as fallback if no specific pattern matches
        """
        text = item.processed_content.lower()
        original_text = item.processed_content

        # Ergo analytical patterns: "Ergo assesses...", "Ergo believes...", probability statements

        # US-China relations
        if "truce" in text and ("october" in text or "china" in text):
            return "Ergo assesses that the US-China strategic truce (October 30) will hold through Q1 2026, stabilizing cross-Pacific routing. However, underlying export controls on semiconductors and advanced technology remain in force, creating compliance burdens for technology sector clients with Asia-Pacific operations."

        # Inflation/monetary policy
        if "inflation" in text and any(d.isdigit() for d in text):
            if "3.5" in text or "3.5%" in text:
                return "Ergo expects US inflation to remain above 3.5% through 2025, driving continued Federal Reserve rate increases. Aircraft financing costs will likely rise 15-25 basis points per quarter, affecting charter operators' cost structures and client pricing."

        # Tariff/trade litigation
        if "supreme court" in text and "tariff" in text:
            return "Ergo believes Supreme Court review of IEEPA-based tariffs creates significant regulatory uncertainty for Q1 2026. A ruling against executive tariff authority could trigger retroactive refunds and destabilize cost projections for clients in manufacturing and trade-sensitive sectors."

        # Russia sanctions
        if ("rosneft" in text or "lukoil" in text or "russian oil" in text) and "sanction" in text:
            return "Ergo assesses that US full blocking sanctions on Russian oil majors (Rosneft, Lukoil) create immediate compliance risk for energy sector clients. Operators must audit client exposure to sanctioned entities and routes through affected jurisdictions within 30 days."

        # China stimulus
        if "china" in text and ("stimulus" in text or "trillion" in text):
            # Extract specific amount if present
            amount_match = None
            if "$3" in text or "3 trillion" in text:
                amount_match = "$3+ trillion"

            if amount_match:
                return f"Ergo judges that China's {amount_match} stimulus package will stabilize domestic demand through mid-2026, supporting business aviation activity for clients with mainland operations. However, export-oriented sectors face persistent uncertainty from ongoing US-China tech restrictions."

        # EU fiscal constraints
        if "eu" in text and ("loan" in text or "fiscal" in text or "140" in text):
            return "Ergo assesses that EU fiscal constraints, evidenced by delays in the €140 billion Ukraine loan scheme, signal tightening corporate travel budgets across European clients in 2026. Public sector and cost-sensitive private clients will likely reduce discretionary aviation expenditures."

        # Fallback: Extract analytical sentences from original content
        sentences = original_text.split(".")
        for sent in sentences[:8]:
            sent_lower = sent.lower()
            # Look for Ergo assessments or expert-sourced statements
            if (
                "ergo assess" in sent_lower
                or "ergo believes" in sent_lower
                or "ergo expects" in sent_lower
                or "ergo judges" in sent_lower
            ):
                if len(sent) > 80 and len(sent) < 300:
                    return sent.strip() + "."

            # Look for probabilistic analytical statements
            if (
                any(
                    kw in sent_lower
                    for kw in ["likely", "unlikely", "probable", "expects", "believes"]
                )
                and len(sent) > 80
                and len(sent) < 250
            ):
                return sent.strip() + "."

        # ALWAYS return content - use the processed content directly if no specific pattern matches
        # Truncate at sentence boundary if needed
        if len(original_text) > 300:
            sentences = original_text.split(". ")
            truncated = ""
            for sent in sentences:
                if len(truncated) + len(sent) + 2 < 280:
                    truncated += sent + ". "
                else:
                    break
            if truncated:
                return truncated.strip()
            else:
                return sentences[0] + "." if sentences else original_text[:280]

        return original_text

    def _craft_watch_factor_statement(self, item: IntelligenceItem) -> str:
        """Craft forward-looking watch factor - always returns content"""
        text = item.processed_content.lower()
        original_text = item.processed_content

        if "data center" in text:
            return "Monitor corporate data center expansion in Middle America - signals sustained business aviation demand for project deployment and executive travel."

        if "eu" in text and "loan" in text:
            return "Track EU loan scheme execution (€140B target) - delays indicate fiscal constraints affecting European corporate travel budgets."

        if "supply chain" in text and ("china" in text or "asia" in text):
            return "Watch US-China supply chain decoupling velocity - accelerating separation drives increased site visit requirements for tech and manufacturing clients."

        if "inflation" in text or "interest rate" in text:
            return "Monitor Federal Reserve rate decisions and inflation trajectory - direct impact on aircraft financing costs and client budget decisions."

        if "sanction" in text:
            return "Track OFAC sanctions updates and enforcement actions - compliance requirements may change rapidly for international operations."

        if "china" in text:
            return "Watch US-China policy developments and diplomatic signals - sets tone for cross-Pacific business climate and travel demand."

        if "oil" in text or "fuel" in text or "energy" in text:
            return "Monitor crude oil and jet fuel price volatility - direct impact on operating costs and charter pricing."

        if "tariff" in text or "trade" in text:
            return "Track trade policy developments and tariff announcements - affects supply chain patterns and client travel requirements."

        if "technology" in text or "semiconductor" in text:
            return "Monitor tech sector export controls and regulatory changes - impacts Silicon Valley client compliance and travel patterns."

        # Fallback: Create generic watch factor from content
        # Extract first sentence and format as watch factor
        first_sentence = original_text.split(".")[0] if "." in original_text else original_text
        if len(first_sentence) > 80:
            first_sentence = first_sentence[:80]
        return (
            f"Monitor: {first_sentence} - potential implications for business aviation operations."
        )

    def _parse_key_finding(self, finding_text: str) -> tuple:
        """
        Parse a legacy key finding string into structured components.
        Returns (subheader, content, bullets) tuple.
        """
        text = finding_text.strip()

        # Try to extract a thematic subheader based on content analysis
        text_lower = text.lower()

        # Determine subheader based on key themes
        if "sanction" in text_lower or "blocking" in text_lower:
            subheader = "Sanctions & compliance risk"
        elif "china" in text_lower and (
            "us" in text_lower or "trade" in text_lower or "truce" in text_lower
        ):
            subheader = "US-China relations"
        elif (
            "inflation" in text_lower
            or "interest rate" in text_lower
            or "federal reserve" in text_lower
        ):
            subheader = "Monetary policy & financing"
        elif "tariff" in text_lower or "trade" in text_lower:
            subheader = "Trade policy & tariffs"
        elif (
            "technology" in text_lower
            or "semiconductor" in text_lower
            or "export control" in text_lower
        ):
            subheader = "Technology sector restrictions"
        elif "eu" in text_lower or "europe" in text_lower:
            subheader = "European regulatory landscape"
        elif "stimulus" in text_lower or "fiscal" in text_lower:
            subheader = "Fiscal policy & economic stimulus"
        elif "aviation" in text_lower or "aircraft" in text_lower or "fuel" in text_lower:
            subheader = "Aviation industry outlook"
        elif "regulation" in text_lower or "compliance" in text_lower or "policy" in text_lower:
            subheader = "Regulatory developments"
        else:
            # Extract first key phrase as subheader
            subheader = "Strategic development"

        # Split content into main paragraph and supporting bullets
        # Look for sentence boundaries to create bullets
        sentences = text.split(". ")

        if len(sentences) >= 3:
            # First 1-2 sentences as main content
            content = ". ".join(sentences[:2]) + "."
            # Remaining sentences as bullets
            bullets = [
                s.strip() + ("." if not s.strip().endswith(".") else "")
                for s in sentences[2:]
                if s.strip()
            ]
        elif len(sentences) == 2:
            content = sentences[0] + "."
            bullets = [
                sentences[1].strip() + ("." if not sentences[1].strip().endswith(".") else "")
            ]
        else:
            content = text
            bullets = []

        # Generate contextual bullets if we don't have enough
        if len(bullets) < 2:
            bullets.extend(
                self._generate_contextual_bullets(text_lower, subheader, 2 - len(bullets))
            )

        return (subheader, content, bullets[:3])  # Limit to 3 bullets max

    def _generate_contextual_bullets(self, text_lower: str, subheader: str, count: int) -> list:
        """Generate contextual supporting bullets based on content theme"""
        bullets = []

        if "sanction" in text_lower or "compliance" in subheader.lower():
            bullets.extend(
                [
                    "Immediate client exposure audit recommended for affected jurisdictions.",
                    "Operations teams should review routing through sanctioned airspace or territories.",
                    "Legal counsel consultation advised for high-exposure clients.",
                ]
            )
        elif "china" in text_lower or "us-china" in subheader.lower():
            bullets.extend(
                [
                    "Technology sector clients face heightened compliance requirements for cross-border operations.",
                    "Routing adjustments may be required for Asia-Pacific destinations.",
                    "Monitor for escalation signals that could affect bilateral flight agreements.",
                ]
            )
        elif "inflation" in text_lower or "monetary" in subheader.lower():
            bullets.extend(
                [
                    "Aircraft financing costs expected to increase, affecting lease and purchase decisions.",
                    "Operating cost increases may require pricing adjustments for charter services.",
                    "Budget-conscious clients may reduce discretionary travel frequency.",
                ]
            )
        elif "tariff" in text_lower or "trade" in subheader.lower():
            bullets.extend(
                [
                    "Manufacturing sector clients may adjust site visit patterns based on supply chain shifts.",
                    "Import-dependent businesses face cost pressures affecting travel budgets.",
                    "Monitor for retaliatory measures affecting additional sectors.",
                ]
            )
        elif "technology" in text_lower or subheader.lower() == "technology sector restrictions":
            bullets.extend(
                [
                    "Silicon Valley and tech corridor clients require enhanced compliance screening.",
                    "Data sovereignty regulations may affect international operations.",
                    "Export control awareness briefings recommended for affected clients.",
                ]
            )
        else:
            bullets.extend(
                [
                    "Continuous monitoring recommended for operational implications.",
                    "Client briefings should address sector-specific exposure.",
                    "Coordinate with operations team on contingency planning.",
                ]
            )

        return bullets[:count]

    def _parse_watch_factor(self, factor_text: str) -> tuple:
        """
        Parse a legacy watch factor string into table components.
        Returns (indicator, what_to_watch, why_it_matters) tuple.
        """
        text = factor_text.strip()
        text_lower = text.lower()

        # Extract indicator keyword
        if "data center" in text_lower:
            indicator = "Data Center Expansion"
            what_to_watch = "Corporate data center construction activity in Middle America"
            why_it_matters = "Signals sustained business aviation demand for project deployment and executive travel"
        elif "eu" in text_lower and "loan" in text_lower:
            indicator = "EU Fiscal Execution"
            what_to_watch = "EU loan scheme execution progress (€140B target)"
            why_it_matters = (
                "Delays indicate fiscal constraints affecting European corporate travel budgets"
            )
        elif "supply chain" in text_lower:
            indicator = "Supply Chain Decoupling"
            what_to_watch = "US-China supply chain separation velocity"
            why_it_matters = (
                "Accelerating separation drives increased site visit requirements for tech clients"
            )
        elif "inflation" in text_lower or "interest" in text_lower:
            indicator = "Interest Rate Trajectory"
            what_to_watch = "Federal Reserve rate decisions and inflation data"
            why_it_matters = "Affects aircraft financing costs and client budget decisions"
        elif "sanction" in text_lower:
            indicator = "Sanctions Enforcement"
            what_to_watch = "OFAC enforcement actions and SDN list updates"
            why_it_matters = (
                "Compliance requirements may change rapidly for international operations"
            )
        elif "china" in text_lower:
            indicator = "China Policy Signals"
            what_to_watch = "Beijing policy announcements and US diplomatic engagement"
            why_it_matters = "Sets tone for cross-Pacific business climate and travel demand"
        elif "oil" in text_lower or "fuel" in text_lower:
            indicator = "Fuel Price Volatility"
            what_to_watch = "Crude oil prices and refining capacity indicators"
            why_it_matters = "Direct impact on operating costs and charter pricing"
        else:
            # Generic parsing - try to split on common delimiters
            if " - " in text:
                parts = text.split(" - ", 1)
                indicator = parts[0][:30]  # Truncate indicator
                remainder = parts[1] if len(parts) > 1 else ""
                what_to_watch = remainder[:80] if remainder else "Monitor for developments"
                why_it_matters = "Potential impact on business aviation operations"
            else:
                indicator = text[:25] + "..." if len(text) > 25 else text
                what_to_watch = text[:80] if len(text) > 80 else text
                why_it_matters = "Relevance to aviation sector operations"

        return (indicator, what_to_watch, why_it_matters)

    def _generate_placeholder_watch_factor(self, index: int, items: List[IntelligenceItem]) -> dict:
        """Generate placeholder watch factors when fewer than 3 are available"""
        placeholders = [
            {
                "indicator": "Economic Indicators",
                "what_to_watch": "Key macro indicators including GDP growth, PMI, and consumer confidence",
                "why_it_matters": "Leading indicators of corporate travel demand and budget trends",
            },
            {
                "indicator": "Regulatory Changes",
                "what_to_watch": "Aviation regulatory updates from FAA, EASA, and international authorities",
                "why_it_matters": "Compliance requirements and operational flexibility",
            },
            {
                "indicator": "Geopolitical Developments",
                "what_to_watch": "Regional stability indicators and diplomatic developments",
                "why_it_matters": "Route availability and client travel safety assessments",
            },
        ]

        # Try to generate based on available intelligence items
        if items and index < len(items):
            item = items[index]
            text_lower = item.processed_content.lower()

            if "technology" in text_lower or "semiconductor" in text_lower:
                return {
                    "indicator": "Tech Sector Activity",
                    "what_to_watch": "Silicon Valley business activity and venture capital flows",
                    "why_it_matters": "Tech executive travel demand indicator",
                }
            elif "finance" in text_lower or "banking" in text_lower:
                return {
                    "indicator": "Financial Sector Health",
                    "what_to_watch": "Banking sector stability and M&A activity levels",
                    "why_it_matters": "Financial sector client demand signals",
                }

        return placeholders[index] if index < len(placeholders) else placeholders[0]

    def _add_economic_indicators_table(self, doc: Document, items: List[IntelligenceItem]):
        """Add economic indicators as a professional table"""
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml
        from docx.oxml.ns import nsdecls

        # Filter to get FRED economic data items
        fred_items = [item for item in items if item.source_type == "fred"]

        # If no FRED items, use any economic items
        if not fred_items:
            fred_items = items[:5]

        if not fred_items:
            p = doc.add_paragraph("No economic indicator data available for this period.")
            p.paragraph_format.space_after = Pt(self.spacing["header_after"])
            return

        # Create table with 4 columns: Indicator, Current Value, Trend, Aviation Impact
        table = doc.add_table(rows=1, cols=4)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Set column widths
        widths = [Inches(1.8), Inches(1.2), Inches(1.0), Inches(2.5)]
        for i, width in enumerate(widths):
            table.columns[i].width = width

        # Header row
        header_cells = table.rows[0].cells
        headers = ["Indicator", "Current Value", "Trend", "Aviation Impact"]
        for i, header in enumerate(headers):
            header_cells[i].text = header
            # Style header
            for paragraph in header_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(10)
            # Add shading to header
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="1F4E79"/>')
            header_cells[i]._tc.get_or_add_tcPr().append(shading)
            for paragraph in header_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = RGBColor(255, 255, 255)

        # Add data rows
        for item in fred_items[:5]:  # Limit to 5 indicators
            row = table.add_row()
            cells = row.cells

            # Extract indicator name from content
            indicator_name = self._extract_indicator_name(item)
            cells[0].text = indicator_name

            # Extract current value
            current_value = self._extract_value(item)
            cells[1].text = current_value

            # Determine trend
            trend = self._determine_trend(item)
            cells[2].text = trend

            # Aviation impact - use so_what statement or generate one
            impact = (
                item.so_what_statement
                if item.so_what_statement
                else self._generate_economic_impact(item)
            )
            # Truncate if too long
            if len(impact) > 120:
                impact = impact[:117] + "..."
            cells[3].text = impact

            # Style data cells
            for cell in cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9)

        # Add spacing after table
        doc.add_paragraph()

    def _strip_markdown(self, text: str) -> str:
        """Remove markdown formatting artifacts from text for clean document rendering"""
        import re

        if not text:
            return text

        # Remove bold/italic markers (* and _)
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)  # ***bold*** -> bold
        text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)  # ___italic___ -> italic

        # Remove markdown headers (# ## ### etc)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove markdown links [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove markdown images ![alt](url)
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

        # Remove bullet point markers at start of lines
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)

        # Remove numbered list markers
        text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Remove code backticks
        text = re.sub(r"`{1,3}([^`]+)`{1,3}", r"\1", text)

        # Remove blockquote markers
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

        # Replace en-dash and em-dash with regular hyphen or remove
        text = text.replace("–", "-").replace("—", "-")

        # Remove bracketed numbers like [1], [2], (1), (2) - citation artifacts
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"\(\d+\)", "", text)

        # Remove standalone numbers in brackets at word boundaries
        text = re.sub(r"\s*\[\d+(?:,\s*\d+)*\]\s*", " ", text)

        # Remove parenthetical asides that are just numbers or short codes
        text = re.sub(r"\s*\([A-Z]{2,4}\d*\)\s*", " ", text)

        # Remove HTML tags if any
        text = re.sub(r"<[^>]+>", "", text)

        # Fix common grammar issues
        # Remove orphaned punctuation
        text = re.sub(r"\s+([,;:])", r"\1", text)
        text = re.sub(r"([,;:])\s*([,;:])", r"\1", text)

        # Fix double periods
        text = re.sub(r"\.\.+", ".", text)

        # Fix spacing around hyphens used as dashes (keep compound words intact)
        text = re.sub(r"\s+-\s+", " - ", text)

        # Clean up extra whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        return text

    def _extract_indicator_name(self, item: IntelligenceItem) -> str:
        """Extract a clean indicator name from the item"""
        content = item.processed_content.lower()

        # Try to identify common economic indicators
        if "gdp" in content:
            return "GDP Growth"
        elif "inflation" in content or "cpi" in content:
            return "Inflation Rate"
        elif "unemployment" in content or "jobs" in content:
            return "Unemployment"
        elif "interest rate" in content or "fed" in content or "federal reserve" in content:
            return "Interest Rate"
        elif "oil" in content or "petroleum" in content or "energy" in content:
            return "Oil/Energy"
        elif "jet fuel" in content or "fuel" in content:
            return "Jet Fuel"
        elif "dollar" in content or "currency" in content or "exchange" in content:
            return "USD Index"
        elif "consumer" in content or "spending" in content:
            return "Consumer Spending"
        elif "manufacturing" in content or "pmi" in content:
            return "Manufacturing PMI"
        elif "trade" in content or "export" in content or "import" in content:
            return "Trade Balance"
        else:
            # Use first few words of category or content
            words = item.processed_content.split()[:3]
            return " ".join(words)[:25]

    def _extract_value(self, item: IntelligenceItem) -> str:
        """Extract the current value from content"""
        import re

        content = item.processed_content

        # Look for percentage patterns
        pct_match = re.search(r"(\d+\.?\d*)\s*%", content)
        if pct_match:
            return f"{pct_match.group(1)}%"

        # Look for dollar amounts
        dollar_match = re.search(
            r"\$(\d+\.?\d*)\s*(billion|million|trillion)?", content, re.IGNORECASE
        )
        if dollar_match:
            amount = dollar_match.group(1)
            unit = dollar_match.group(2) or ""
            return f"${amount}{unit[0].upper() if unit else ''}"

        # Look for just numbers with context
        num_match = re.search(r"(\d+\.?\d*)\s*(points?|bps|basis points)?", content)
        if num_match:
            return num_match.group(0)

        return "See details"

    def _determine_trend(self, item: IntelligenceItem) -> str:
        """Determine trend direction from content"""
        content = item.processed_content.lower()

        up_words = ["increase", "rose", "rising", "grew", "growth", "higher", "up", "gain", "surge"]
        down_words = ["decrease", "fell", "falling", "decline", "lower", "down", "drop", "slump"]
        stable_words = ["stable", "unchanged", "flat", "steady", "maintained"]

        if any(word in content for word in up_words):
            return "Rising"
        elif any(word in content for word in down_words):
            return "Falling"
        elif any(word in content for word in stable_words):
            return "Stable"
        else:
            return "Monitor"

    def _generate_economic_impact(self, item: IntelligenceItem) -> str:
        """Generate an aviation impact statement for economic data"""
        content = item.processed_content.lower()

        if "fuel" in content or "oil" in content or "energy" in content:
            return "Directly affects operating costs and charter pricing"
        elif "interest" in content or "fed" in content:
            return "Influences aircraft financing and client capital allocation"
        elif "inflation" in content:
            return "Impacts operating margins and pricing strategy"
        elif "gdp" in content or "growth" in content:
            return "Indicator of business travel demand trajectory"
        elif "unemployment" in content or "jobs" in content:
            return "Correlates with corporate travel budgets"
        elif "consumer" in content or "spending" in content:
            return "Signals leisure charter demand patterns"
        elif "dollar" in content or "currency" in content:
            return "Affects international charter competitiveness"
        elif "trade" in content:
            return "Influences cross-border business travel needs"
        else:
            return "Monitor for potential aviation sector impact"

    def _add_intelligence_items(self, doc: Document, items: List[IntelligenceItem]):
        """Add intelligence items with smart truncation at sentence boundaries"""
        for item in items:
            if item.relevance_score < 0.5:  # Skip low relevance items
                continue

            # Main finding - clean paragraph without bullets
            p = doc.add_paragraph()

            # Smart truncation at sentence boundaries - strip markdown artifacts
            content = self._strip_markdown(item.processed_content)
            if len(content) > 400:
                # Try to truncate at sentence boundary
                sentences = content.split(". ")
                truncated = ""
                for sentence in sentences:
                    # Check if adding this sentence would exceed limit
                    if len(truncated) + len(sentence) + 2 < 380:  # Leave room for ". "
                        truncated += sentence + ". "
                    else:
                        break

                # Only use complete sentences - no ellipsis
                if truncated and len(truncated) > 100:
                    content = truncated.rstrip()
                else:
                    # Fallback: extract first sentence only
                    first_period = content.find(". ")
                    if first_period > 50:  # Reasonable sentence length
                        content = content[: first_period + 1]
                    else:
                        # If no good sentence boundary, take first 300 chars at word boundary
                        content = content[:300]
                        last_space = content.rfind(" ")
                        if last_space > 250:
                            content = content[:last_space] + "."

            p.add_run(content)
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(self.spacing["bullet"])

            # Add source citation - differentiate between ErgoMind and GTA
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.space_after = Pt(self.spacing["bullet"])

            if item.source_type == "gta":
                # GTA source with intervention ID and dates
                source_text = "   📊 GTA Data"
                if item.gta_intervention_id:
                    source_text += f" (ID: {item.gta_intervention_id})"
                if item.date_implemented:
                    source_text += f" | Implemented: {item.date_implemented}"

                run = p.add_run(source_text)
                run.font.size = Pt(9)
                run.font.color.rgb = self.ergo_colors["secondary_blue"]  # Blue for GTA
                run.font.italic = True

                # Add geographic data if available
                if item.gta_implementing_countries or item.gta_affected_countries:
                    p = doc.add_paragraph()
                    geo_text = "   "
                    if item.gta_implementing_countries:
                        geo_text += (
                            f"Implementing: {', '.join(item.gta_implementing_countries[:3])}"
                        )
                    if item.gta_affected_countries:
                        if item.gta_implementing_countries:
                            geo_text += " | "
                        geo_text += f"Affected: {', '.join(item.gta_affected_countries[:3])}"

                    run = p.add_run(geo_text)
                    run.font.size = Pt(8)
                    run.font.color.rgb = self.ergo_colors["dark_gray"]
                    run.font.italic = True
                    p.paragraph_format.left_indent = Inches(0.5)
                    p.paragraph_format.space_after = Pt(self.spacing["bullet"])
            elif item.source_type == "fred":
                # FRED source with series ID and observation date
                source_text = "   📊 FRED Economic Data"
                if item.fred_series_id:
                    source_text += f" ({item.fred_series_id})"
                if item.fred_observation_date:
                    source_text += f" | {item.fred_observation_date}"

                run = p.add_run(source_text)
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0, 100, 0)  # Green for FRED (Federal Reserve)
                run.font.italic = True
            else:
                # ErgoMind source (existing format)
                if item.sources:
                    source_count = len(item.sources)
                    source_text = f"   Sources: Based on {source_count} source{'s' if source_count > 1 else ''}"
                    run = p.add_run(source_text)
                    run.font.size = Pt(9)
                    run.font.color.rgb = self.ergo_colors["dark_gray"]
                    run.font.italic = True

            # Add "So What" in italics - clean format without arrows
            if item.so_what_statement:
                p = doc.add_paragraph()
                run1 = p.add_run("Impact: ")
                run1.font.italic = True
                run1.font.size = Pt(10)
                run2 = p.add_run(item.so_what_statement)
                run2.font.italic = True
                run2.font.size = Pt(10)
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.space_after = Pt(self.spacing["paragraph"])

    def _add_regional_assessment(self, doc: Document, regional_items: List[IntelligenceItem]):
        """Add regional risk assessments with actual content"""
        regions = {"North America": [], "Europe": [], "Asia-Pacific": [], "Middle East": []}

        # Track which items we've already assigned to prevent duplication
        assigned_items = set()

        # Categorize items by PRIMARY region only - check both category and content
        for item in regional_items:
            # Skip if already assigned
            item_id = id(item)
            if item_id in assigned_items:
                continue

            text_lower = item.processed_content.lower()
            category_lower = item.category.lower()

            # Prioritize more specific regional mentions
            # Use GTA country data if available for more precise mapping
            primary_region = None

            if item.source_type == "gta":
                # Use GTA geographic data for precise regional assignment
                countries = item.gta_implementing_countries + item.gta_affected_countries
                countries_text = " ".join(countries).lower()

                if any(c in countries_text for c in ["united states", "canada", "mexico"]):
                    primary_region = "North America"
                elif any(
                    c in countries_text
                    for c in ["china", "japan", "india", "korea", "singapore", "australia"]
                ):
                    primary_region = "Asia-Pacific"
                elif any(
                    c in countries_text
                    for c in [
                        "germany",
                        "france",
                        "uk",
                        "united kingdom",
                        "italy",
                        "spain",
                        "european union",
                    ]
                ):
                    primary_region = "Europe"
                elif any(
                    c in countries_text
                    for c in ["saudi", "uae", "qatar", "israel", "iran", "kuwait"]
                ):
                    primary_region = "Middle East"

            # Fallback to content-based detection
            if not primary_region:
                if any(
                    kw in text_lower or kw in category_lower
                    for kw in ["united states", "u.s.", "america", "canada", "mexico"]
                ):
                    primary_region = "North America"
                elif any(
                    kw in text_lower or kw in category_lower
                    for kw in ["china", "japan", "india", "asia", "pacific"]
                ):
                    primary_region = "Asia-Pacific"
                elif any(
                    kw in text_lower or kw in category_lower
                    for kw in ["europe", "eu", "britain", "france", "germany", "uk"]
                ):
                    primary_region = "Europe"
                elif any(
                    kw in text_lower or kw in category_lower
                    for kw in ["middle east", "saudi", "uae", "qatar", "israel"]
                ):
                    primary_region = "Middle East"

            if primary_region:
                regions[primary_region].append(item)
                assigned_items.add(item_id)

        # Add regional summaries with actual content - use top 2-3 items per region
        for region, items in regions.items():
            if items:
                p = doc.add_paragraph()
                run = p.add_run(f"{region}: ")
                run.font.bold = True
                run.font.color.rgb = self.ergo_colors["primary_blue"]

                # Get top item sorted by relevance - use single best source for clarity
                top_item = sorted(items, key=lambda x: x.relevance_score, reverse=True)[0]

                # Generate clean regional assessment
                assessment = self._craft_regional_assessment(region, top_item, items)
                p.add_run(assessment)
                p.paragraph_format.space_after = Pt(self.spacing["header_after"])

    def _craft_regional_assessment(
        self, region: str, primary_item: IntelligenceItem, all_items: List[IntelligenceItem]
    ) -> str:
        """Craft a clean, professional regional assessment in Ergo analytical voice"""
        # Strip markdown and clean the content
        content = self._strip_markdown(primary_item.processed_content)
        content_lower = content.lower()

        # Region-specific assessment templates based on content analysis
        if region == "North America":
            if "tariff" in content_lower or "trade" in content_lower:
                return self._build_assessment_sentence(
                    "Trade policy developments continue to shape the business environment.",
                    content,
                    primary_item,
                )
            elif "sanction" in content_lower or "restriction" in content_lower:
                return self._build_assessment_sentence(
                    "Regulatory changes require ongoing compliance monitoring for operators.",
                    content,
                    primary_item,
                )
            elif (
                "inflation" in content_lower
                or "economic" in content_lower
                or "fed" in content_lower
            ):
                return self._build_assessment_sentence(
                    "Economic conditions remain a key factor for business aviation demand.",
                    content,
                    primary_item,
                )
            else:
                return self._build_assessment_sentence(
                    "Market conditions present both opportunities and considerations for operators.",
                    content,
                    primary_item,
                )

        elif region == "Europe":
            if "eu" in content_lower or "regulation" in content_lower:
                return self._build_assessment_sentence(
                    "EU regulatory developments warrant attention from operators serving European destinations.",
                    content,
                    primary_item,
                )
            elif "fiscal" in content_lower or "budget" in content_lower:
                return self._build_assessment_sentence(
                    "Fiscal constraints across the region may affect corporate travel budgets.",
                    content,
                    primary_item,
                )
            else:
                return self._build_assessment_sentence(
                    "Regional dynamics continue to evolve with implications for aviation operations.",
                    content,
                    primary_item,
                )

        elif region == "Asia-Pacific":
            if "china" in content_lower:
                if "stimulus" in content_lower or "growth" in content_lower:
                    return self._build_assessment_sentence(
                        "Chinese economic policy developments influence regional business aviation demand.",
                        content,
                        primary_item,
                    )
                elif "trade" in content_lower or "export" in content_lower:
                    return self._build_assessment_sentence(
                        "US-China trade dynamics continue to affect cross-Pacific business operations.",
                        content,
                        primary_item,
                    )
            elif "technology" in content_lower or "semiconductor" in content_lower:
                return self._build_assessment_sentence(
                    "Technology sector developments shape travel patterns across the region.",
                    content,
                    primary_item,
                )
            else:
                return self._build_assessment_sentence(
                    "Regional economic activity presents opportunities for business aviation growth.",
                    content,
                    primary_item,
                )

        elif region == "Middle East":
            if "oil" in content_lower or "energy" in content_lower:
                return self._build_assessment_sentence(
                    "Energy market dynamics continue to influence regional aviation activity.",
                    content,
                    primary_item,
                )
            elif "conflict" in content_lower or "security" in content_lower:
                return self._build_assessment_sentence(
                    "Security considerations require ongoing route assessment for regional operations.",
                    content,
                    primary_item,
                )
            else:
                return self._build_assessment_sentence(
                    "Regional developments present evolving considerations for aviation operations.",
                    content,
                    primary_item,
                )

        # Default fallback - extract clean first sentence
        return self._build_assessment_sentence(
            "Developments in this region warrant continued monitoring.", content, primary_item
        )

    def _build_assessment_sentence(
        self, template: str, content: str, item: IntelligenceItem
    ) -> str:
        """Build a clean assessment sentence, incorporating source content when appropriate"""
        import re

        # Try to extract a clean, complete sentence from the content
        sentences = content.split(". ")
        clean_sentence = None

        for sent in sentences:
            sent = sent.strip()
            # Skip if too short, starts with lowercase (fragment), or has artifacts
            if len(sent) < 40:
                continue
            if sent and sent[0].islower():
                continue
            if re.search(r"\[\d+\]|\(\d+\)|^\d+\s", sent):
                continue
            # Check for complete sentence structure
            if sent and sent[0].isupper():
                # Ensure it ends properly
                if not sent.endswith("."):
                    sent = sent + "."
                clean_sentence = sent
                break

        # If we found a good sentence from source, use it
        if clean_sentence and len(clean_sentence) > 50 and len(clean_sentence) < 250:
            return clean_sentence

        # Otherwise, use the template with so_what if available
        if item.so_what_statement and len(item.so_what_statement) > 30:
            so_what = self._strip_markdown(item.so_what_statement)
            # Ensure proper capitalization and punctuation
            if so_what and so_what[0].islower():
                so_what = so_what[0].upper() + so_what[1:]
            if so_what and not so_what.endswith("."):
                so_what = so_what + "."
            return so_what

        return template

    def _add_regulatory_outlook(self, doc: Document, reg_items: List[IntelligenceItem]):
        """Add regulatory outlook section"""
        if not reg_items:
            p = doc.add_paragraph()
            p.add_run("No significant regulatory changes identified this period.")
            return

        # Combine action items from regulatory intelligence
        all_actions = []
        for item in reg_items[:3]:
            all_actions.extend(item.action_items)

        # Deduplicate and add top actions
        unique_actions = list(dict.fromkeys(all_actions))
        for action in unique_actions[:4]:
            p = doc.add_paragraph()
            p.add_run(action)
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.space_after = Pt(self.spacing["bullet"])

    def _add_sector_section(
        self, doc: Document, sector: ClientSector, intelligence: SectorIntelligence
    ):
        """Add a section for a specific client sector"""
        # Sector heading
        sector_name = sector.value.replace("_", " ").upper()
        if sector == ClientSector.TECHNOLOGY:
            sector_name = "TECHNOLOGY SECTOR CLIENTS"
        elif sector == ClientSector.FINANCE:
            sector_name = "FINANCIAL SECTOR CLIENTS"
        elif sector == ClientSector.REAL_ESTATE:
            sector_name = "REAL ESTATE SECTOR CLIENTS"
        elif sector == ClientSector.ENTERTAINMENT:
            sector_name = "ENTERTAINMENT & MEDIA SECTOR CLIENTS"

        self._add_section_heading(doc, sector_name)

        # Critical Developments
        p = doc.add_paragraph()
        run = p.add_run("Critical Developments:")
        run.font.bold = True
        run.font.color.rgb = self.ergo_colors["dark_gray"]

        # Add top 2 items for this sector - complete sentences only
        for item in intelligence.items[:2]:
            p = doc.add_paragraph()
            content = item.processed_content

            # Truncate to complete sentences if needed
            if len(content) > 250:
                sentences = content.split(". ")
                truncated = ""
                for sentence in sentences:
                    if len(truncated) + len(sentence) + 2 <= 250:
                        truncated += sentence + ". "
                    else:
                        break
                content = truncated.rstrip() if truncated else sentences[0] + "."

            p.add_run(content)
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.space_after = Pt(self.spacing["bullet"])

            # Add source citation for sector items - differentiate sources
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.75)
            p.paragraph_format.space_after = Pt(self.spacing["bullet"])

            if item.source_type == "gta":
                source_text = "   📊 GTA"
                if item.gta_intervention_id:
                    source_text += f" (ID: {item.gta_intervention_id})"
                run = p.add_run(source_text)
                run.font.size = Pt(9)
                run.font.color.rgb = self.ergo_colors["secondary_blue"]
                run.font.italic = True
            elif item.sources:
                source_count = len(item.sources)
                run = p.add_run(
                    f"   Based on {source_count} source{'s' if source_count > 1 else ''}"
                )
                run.font.size = Pt(9)
                run.font.color.rgb = self.ergo_colors["dark_gray"]
                run.font.italic = True

        # Action Items - enhanced with sector-specific filtering
        if any(item.action_items for item in intelligence.items):
            p = doc.add_paragraph()
            run = p.add_run("Action Items:")
            run.font.bold = True
            run.font.color.rgb = self.ergo_colors["dark_gray"]

            # Collect unique action items - filter out generic ones
            generic_patterns = [
                "Monitor situation and prepare briefing",
                "Update market intelligence briefings",
                "Conduct immediate review of affected routes and file alternative flight plans",
            ]

            all_actions = []
            for item in intelligence.items[:3]:  # Top 3 items only
                for action in item.action_items:
                    # Skip generic actions
                    is_generic = any(
                        pattern.lower() in action.lower() for pattern in generic_patterns
                    )
                    if not is_generic and action not in all_actions:
                        all_actions.append(action)

            # If we filtered out everything, generate sector-specific actions
            if not all_actions:
                all_actions = self._generate_sector_specific_actions(sector, intelligence.items[:2])

            for action in all_actions[:3]:
                p = doc.add_paragraph()
                p.add_run(action)
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.space_after = Pt(self.spacing["bullet"])

        # Add spacing between sectors
        doc.add_paragraph()

    def _generate_sector_specific_actions(
        self, sector: ClientSector, items: List[IntelligenceItem]
    ) -> List[str]:
        """Generate sector-specific action items when generic ones are filtered out"""
        actions = []

        if sector == ClientSector.TECHNOLOGY:
            actions = [
                "Proactively reach out to technology sector clients about export control impacts",
                "Monitor Silicon Valley travel patterns for early demand signals",
                "Brief tech executives on cross-border data sovereignty requirements",
            ]
        elif sector == ClientSector.FINANCE:
            actions = [
                "Schedule check-ins with financial sector clients to discuss market volatility impacts",
                "Position for relationship-critical travel during M&A activity periods",
                "Monitor capital flow restrictions affecting client budgets",
            ]
        elif sector == ClientSector.REAL_ESTATE:
            actions = [
                "Alert real estate clients to regional market developments affecting property tours",
                "Track construction material costs impact on development timelines",
                "Coordinate with clients on site visit scheduling around market conditions",
            ]
        elif sector == ClientSector.ENTERTAINMENT:
            actions = [
                "Coordinate with entertainment clients on production schedule changes",
                "Monitor content regulation impacts on international filming locations",
                "Track talent mobility restrictions affecting casting and production",
            ]
        elif sector == ClientSector.ENERGY:
            actions = [
                "Brief energy sector clients on trade restrictions affecting operations",
                "Monitor oil price volatility impacts on client travel budgets",
                "Track sanctions affecting energy sector international operations",
            ]
        else:
            # Generate based on item content
            if items:
                item_content = " ".join([i.processed_content.lower() for i in items])
                if "sanction" in item_content or "restriction" in item_content:
                    actions.append("Review client operations for exposure to trade restrictions")
                if "regulation" in item_content or "compliance" in item_content:
                    actions.append("Update compliance protocols and brief affected clients")
                if "market" in item_content or "economic" in item_content:
                    actions.append("Assess market conditions impact on client travel demand")

        return actions[:3]

    def save_report(self, doc: Document, filename: Optional[str] = None) -> str:
        """Save the report to a file"""
        if not filename:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            month = datetime.now().strftime("%B%Y")
            filename = f"Solairus_Intelligence_Report_{month}_{timestamp}.docx"

        # Get environment-appropriate output directory
        output_dir = get_output_dir()

        filepath = output_dir / filename
        doc.save(str(filepath))

        return str(filepath)


def test_document_generator():
    """Test the document generator with sample data"""
    from intelligence_processor import ClientSector, IntelligenceItem, SectorIntelligence

    # Create sample intelligence items
    sample_items = [
        IntelligenceItem(
            raw_content="Test content",
            processed_content="The Federal Reserve raised interest rates by 25 basis points, signaling continued monetary tightening.",
            category="economic_indicators",
            relevance_score=0.8,
            so_what_statement="Aircraft financing costs will increase, affecting purchase decisions and lease rates.",
            affected_sectors=[ClientSector.FINANCE],
            action_items=["Review financing arrangements", "Update cost projections"],
            confidence=0.9,
        ),
        IntelligenceItem(
            raw_content="Test content",
            processed_content="New EU regulations on sustainable aviation fuel mandate 5% SAF blend by 2025.",
            category="regulation",
            relevance_score=0.9,
            so_what_statement="Operators must plan for increased fuel costs and ensure SAF availability at European destinations.",
            affected_sectors=[ClientSector.GENERAL],
            action_items=["Establish SAF supply contracts", "Update fuel cost models"],
            confidence=0.85,
        ),
    ]

    # Create sample sector intelligence
    sector_intel = {
        ClientSector.TECHNOLOGY: SectorIntelligence(
            sector=ClientSector.TECHNOLOGY,
            items=sample_items,
            summary="Technology sector facing increased scrutiny on data sovereignty.",
            key_risks=["Export control restrictions"],
            key_opportunities=["Growing demand for tech executive travel"],
        )
    }

    # Generate document
    generator = DocumentGenerator()
    doc = generator.create_report(sample_items, sector_intel)
    filepath = generator.save_report(doc, "test_report.docx")

    print(f"Test report generated: {filepath}")
    return filepath


if __name__ == "__main__":
    test_document_generator()
