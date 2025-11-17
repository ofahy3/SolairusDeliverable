"""
Document Generator for Solairus Intelligence Reports
Creates professional, Google Docs-compatible DOCX files with elegant formatting
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

from solairus_intelligence.core.processor import (
    IntelligenceItem,
    SectorIntelligence,
    ClientSector
)
from solairus_intelligence.utils.config import get_output_dir, ENV_CONFIG
import asyncio

class DocumentGenerator:
    """
    Generates professional DOCX reports optimized for Google Docs
    With optional AI-enhanced Executive Summary generation
    """

    def __init__(self):
        self.ergo_colors = {
            'primary_blue': RGBColor(27, 41, 70),      # #1B2946
            'secondary_blue': RGBColor(2, 113, 195),   # #0271C3
            'light_blue': RGBColor(148, 176, 201),     # #94B0C9
            'dark_gray': RGBColor(100, 100, 100),
            'black': RGBColor(0, 0, 0),
            'white': RGBColor(255, 255, 255)
        }

        # Initialize AI generator if enabled
        self.ai_generator = None
        if ENV_CONFIG.ai_enabled:
            try:
                from solairus_intelligence.ai.generator import SecureAIGenerator, AIConfig
                config = AIConfig(
                    api_key=ENV_CONFIG.anthropic_api_key,
                    model=ENV_CONFIG.ai_model,
                    enabled=True
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
        report_month: Optional[str] = None
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
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Arial'  # Google Docs compatible
        font.size = Pt(11)
        font.color.rgb = self.ergo_colors['black']
        
        # Create custom heading styles
        self._create_custom_heading_style(doc, 'CustomHeading1', 16, True)
        self._create_custom_heading_style(doc, 'CustomHeading2', 14, True)
        self._create_custom_heading_style(doc, 'CustomHeading3', 12, False)
        
    def _create_custom_heading_style(self, doc: Document, name: str, size: int, bold: bool):
        """Create a custom heading style"""
        styles = doc.styles
        if name not in styles:
            style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = styles['Normal']
            font = style.font
            font.size = Pt(size)
            font.bold = bold
            font.color.rgb = self.ergo_colors['primary_blue']
            paragraph_format = style.paragraph_format
            paragraph_format.space_before = Pt(12)
            paragraph_format.space_after = Pt(6)
            
    def _create_page_1(self, doc: Document, items: List[IntelligenceItem], month: str):
        """Create Page 1: Solairus Business Intelligence"""
        
        # Header
        self._add_header(doc, "FLASHPOINTS FORUM INTELLIGENCE BRIEF", month)
        
        # Executive Summary
        self._add_section_heading(doc, "EXECUTIVE SUMMARY")
        self._add_executive_summary(doc, items)
        
        # Geopolitical Developments
        self._add_section_heading(doc, "GEOPOLITICAL DEVELOPMENTS IMPACTING AVIATION")
        geo_items = [item for item in items if 'geopolitical' in item.category or 
                     'sanctions' in item.category or 'security' in item.category]
        self._add_intelligence_items(doc, geo_items[:3])
        
        # Economic Indicators
        self._add_section_heading(doc, "ECONOMIC INDICATORS FOR BUSINESS AVIATION")
        econ_items = [item for item in items if 'economic' in item.category or 
                      'financial' in item.category or 'market' in item.category]
        self._add_intelligence_items(doc, econ_items[:3])
        
        # Regional Risk Assessments
        self._add_section_heading(doc, "REGIONAL RISK ASSESSMENTS")
        regional_items = [item for item in items if any(region in item.category for region in 
                          ['america', 'europe', 'asia', 'middle'])]
        self._add_regional_assessment(doc, regional_items)
        
        # Regulatory Horizon
        self._add_section_heading(doc, "REGULATORY HORIZON")
        reg_items = [item for item in items if 'regulation' in item.category or 
                     'compliance' in item.category or 'policy' in item.category]
        self._add_regulatory_outlook(doc, reg_items)
        
    def _create_page_2(self, doc: Document, sector_intel: Dict[ClientSector, SectorIntelligence], month: str):
        """Create Page 2: Client Sector Intelligence"""
        
        # Header
        self._add_header(doc, "CLIENT SECTOR INTELLIGENCE", month)
        
        # Prioritize sectors with most intelligence
        sorted_sectors = sorted(
            sector_intel.items(),
            key=lambda x: len(x[1].items),
            reverse=True
        )
        
        # Add top sectors (limit to fit on one page)
        sectors_to_include = sorted_sectors[:4]
        
        for sector, intelligence in sectors_to_include:
            if intelligence.items:  # Only include if there's actual intelligence
                self._add_sector_section(doc, sector, intelligence)
                
    def _add_header(self, doc: Document, title: str, subtitle: str):
        """Add a professional header to the document"""
        # Title
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = self.ergo_colors['primary_blue']
        
        # Subtitle (Month Year)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(subtitle)
        run.font.size = Pt(14)
        run.font.color.rgb = self.ergo_colors['secondary_blue']
        
        # Add a subtle line
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("_" * 50).font.color.rgb = self.ergo_colors['light_blue']
        
    def _add_section_heading(self, doc: Document, heading: str):
        """Add a section heading"""
        p = doc.add_paragraph()
        p.style = 'CustomHeading2'
        p.add_run(heading)
        
    def _add_executive_summary(self, doc: Document, items: List[IntelligenceItem]):
        """Generate sharp, actionable executive summary in Ergo analytical voice"""

        # Extract analytical judgments from top items
        insights = self._extract_analytical_insights(items)

        # Structure: BOTTOM LINE (2 max) + KEY FINDINGS (3-5) + WATCH FACTORS (2-3)
        bottom_line_items = insights.get('bottom_line', [])[:2]
        key_findings = insights.get('key_findings', [])[:5]
        watch_factors = insights.get('watch_factors', [])[:3]

        # Add BOTTOM LINE section if items exist
        if bottom_line_items:
            # Section header
            p = doc.add_paragraph()
            run = p.add_run('BOTTOM LINE')
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = self.ergo_colors['primary_blue']
            p.space_after = Pt(6)

            for item_text in bottom_line_items:
                p = doc.add_paragraph()
                p.add_run(item_text)
                p.paragraph_format.space_after = Pt(8)

        # Add KEY FINDINGS section
        if key_findings:
            p = doc.add_paragraph()
            run = p.add_run('KEY FINDINGS')
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = self.ergo_colors['primary_blue']
            p.space_after = Pt(6)

            for item_text in key_findings:
                p = doc.add_paragraph()
                p.add_run(item_text)
                p.paragraph_format.space_after = Pt(8)

        # Add WATCH FACTORS section
        if watch_factors:
            p = doc.add_paragraph()
            run = p.add_run('WATCH FACTORS')
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = self.ergo_colors['primary_blue']
            p.space_after = Pt(6)

            for item_text in watch_factors:
                p = doc.add_paragraph()
                p.add_run(item_text)
                p.paragraph_format.space_after = Pt(8)

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

                # Run AI generation asynchronously
                loop = asyncio.get_event_loop()
                ai_summary = loop.run_until_complete(
                    self.ai_generator.generate_executive_summary(
                        items,
                        fallback_generator=lambda x: self._extract_insights_template(x)
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
        ergomind_items = [i for i in items if i.source_type == 'ergomind']
        other_items = [i for i in items if i.source_type != 'ergomind']

        # Sort each group by composite score
        ergomind_sorted = sorted(ergomind_items, key=lambda x: (x.relevance_score * x.confidence), reverse=True)
        other_sorted = sorted(other_items, key=lambda x: (x.relevance_score * x.confidence), reverse=True)

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
            if (any(kw in text for kw in ['sanction', 'blocking', 'full blocking', 'export control', 'ban']) and
                item.relevance_score > 0.7 and len(bottom_line) < 2):
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
            if (any(kw in text for kw in ['trend', 'signal', 'increase', 'decrease', 'shift', 'emerging']) and
                len(watch_factors) < 3):
                insight = self._craft_watch_factor_statement(item)
                if insight and insight not in watch_factors:
                    watch_factors.append(insight)

        return {
            'bottom_line': bottom_line,
            'key_findings': key_findings,
            'watch_factors': watch_factors
        }

    def _extract_theme(self, text: str, so_what: str) -> str:
        """Extract core theme for deduplication"""
        # Combine key words from both text and so_what
        combined = (text + ' ' + so_what.lower())[:200]

        # Extract theme based on key terms
        if 'sanction' in combined:
            return 'sanctions'
        elif 'tariff' in combined or 'trade' in combined:
            return 'trade'
        elif 'inflation' in combined or 'interest rate' in combined:
            return 'monetary'
        elif 'china' in combined and 'us' in combined:
            return 'us-china'
        elif 'russia' in combined:
            return 'russia'
        elif 'aviation' in combined:
            return 'aviation-specific'
        elif 'fuel' in combined or 'oil' in combined:
            return 'fuel-costs'
        elif 'technology' in combined or 'semiconductor' in combined:
            return 'tech-sector'
        else:
            # Use first 30 chars as fallback theme
            return combined[:30].strip()

    def _craft_bottom_line_statement(self, item: IntelligenceItem) -> str:
        """Craft authoritative bottom-line statement"""
        text = item.processed_content.lower()

        # Extract specific, high-impact statements
        if 'rosneft' in text or 'lukoil' in text or ('russian oil' in text and 'sanction' in text):
            return "US full blocking sanctions on Russian oil majors create immediate compliance risk for clients with Russian exposure or routes through sanctioned jurisdictions."

        if 'export control' in text and ('china' in text or 'semiconductor' in text or 'technology' in text):
            return "Expanded US export controls on advanced technology require immediate client screening for Silicon Valley and tech sector exposure to restricted jurisdictions."

        if 'full blocking' in text or 'sdn list' in text:
            return "New sanctions regime requires client exposure audit within 30 days - particularly technology, energy, and financial sector clients with international operations."

        # Dynamic extraction for other high-priority threats
        if 'airspace closure' in text or 'flight ban' in text:
            return "New airspace restrictions require immediate route review and client notification - operational impacts within 48-72 hours."

        if 'compliance risk' in text and 'immediate' in text:
            # Extract the specific risk if mentioned
            sentences = item.processed_content.split('.')
            for sent in sentences[:3]:
                if 'compliance' in sent.lower() and len(sent) > 40:
                    return sent.strip() + '.'

        return None

    def _craft_key_finding_statement(self, item: IntelligenceItem) -> str:
        """Craft analytical key finding in Ergo voice - lead with judgment, support with evidence"""
        text = item.processed_content.lower()
        original_text = item.processed_content

        # Ergo analytical patterns: "Ergo assesses...", "Ergo believes...", probability statements

        # US-China relations
        if 'truce' in text and ('october' in text or 'china' in text):
            return "Ergo assesses that the US-China strategic truce (October 30) will hold through Q1 2026, stabilizing cross-Pacific routing. However, underlying export controls on semiconductors and advanced technology remain in force, creating compliance burdens for technology sector clients with Asia-Pacific operations."

        # Inflation/monetary policy
        if 'inflation' in text and any(d.isdigit() for d in text):
            if '3.5' in text or '3.5%' in text:
                return "Ergo expects US inflation to remain above 3.5% through 2025, driving continued Federal Reserve rate increases. Aircraft financing costs will likely rise 15-25 basis points per quarter, affecting charter operators' cost structures and client pricing."

        # Tariff/trade litigation
        if 'supreme court' in text and 'tariff' in text:
            return "Ergo believes Supreme Court review of IEEPA-based tariffs creates significant regulatory uncertainty for Q1 2026. A ruling against executive tariff authority could trigger retroactive refunds and destabilize cost projections for clients in manufacturing and trade-sensitive sectors."

        # Russia sanctions
        if ('rosneft' in text or 'lukoil' in text or 'russian oil' in text) and 'sanction' in text:
            return "Ergo assesses that US full blocking sanctions on Russian oil majors (Rosneft, Lukoil) create immediate compliance risk for energy sector clients. Operators must audit client exposure to sanctioned entities and routes through affected jurisdictions within 30 days."

        # China stimulus
        if 'china' in text and ('stimulus' in text or 'trillion' in text):
            # Extract specific amount if present
            amount_match = None
            if '$3' in text or '3 trillion' in text:
                amount_match = "$3+ trillion"

            if amount_match:
                return f"Ergo judges that China's {amount_match} stimulus package will stabilize domestic demand through mid-2026, supporting business aviation activity for clients with mainland operations. However, export-oriented sectors face persistent uncertainty from ongoing US-China tech restrictions."

        # EU fiscal constraints
        if 'eu' in text and ('loan' in text or 'fiscal' in text or '140' in text):
            return "Ergo assesses that EU fiscal constraints, evidenced by delays in the €140 billion Ukraine loan scheme, signal tightening corporate travel budgets across European clients in 2026. Public sector and cost-sensitive private clients will likely reduce discretionary aviation expenditures."

        # Fallback: Extract analytical sentences from original content
        sentences = original_text.split('.')
        for sent in sentences[:8]:
            sent_lower = sent.lower()
            # Look for Ergo assessments or expert-sourced statements
            if ('ergo assess' in sent_lower or 'ergo believes' in sent_lower or
                'ergo expects' in sent_lower or 'ergo judges' in sent_lower):
                if len(sent) > 80 and len(sent) < 300:
                    return sent.strip() + '.'

            # Look for probabilistic analytical statements
            if (any(kw in sent_lower for kw in ['likely', 'unlikely', 'probable', 'expects', 'believes']) and
                len(sent) > 80 and len(sent) < 250):
                return sent.strip() + '.'

        return None

    def _craft_watch_factor_statement(self, item: IntelligenceItem) -> str:
        """Craft forward-looking watch factor"""
        text = item.processed_content.lower()

        if 'data center' in text:
            return "Monitor corporate data center expansion in Middle America - signals sustained business aviation demand for project deployment and executive travel."

        if 'eu' in text and 'loan' in text:
            return "Track EU loan scheme execution (€140B target) - delays indicate fiscal constraints affecting European corporate travel budgets."

        if 'supply chain' in text and ('china' in text or 'asia' in text):
            return "Watch US-China supply chain decoupling velocity - accelerating separation drives increased site visit requirements for tech and manufacturing clients."

        return None
            
    def _add_intelligence_items(self, doc: Document, items: List[IntelligenceItem]):
        """Add intelligence items with smart truncation at sentence boundaries"""
        for item in items:
            if item.relevance_score < 0.5:  # Skip low relevance items
                continue

            # Main finding - clean paragraph without bullets
            p = doc.add_paragraph()

            # Smart truncation at sentence boundaries
            content = item.processed_content
            if len(content) > 400:
                # Try to truncate at sentence boundary
                sentences = content.split('. ')
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
                    first_period = content.find('. ')
                    if first_period > 50:  # Reasonable sentence length
                        content = content[:first_period + 1]
                    else:
                        # If no good sentence boundary, take first 300 chars at word boundary
                        content = content[:300]
                        last_space = content.rfind(' ')
                        if last_space > 250:
                            content = content[:last_space] + "."

            p.add_run(content)
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(4)

            # Add source citation - differentiate between ErgoMind and GTA
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.space_after = Pt(2)

            if item.source_type == "gta":
                # GTA source with intervention ID and dates
                source_text = f"   📊 GTA Data"
                if item.gta_intervention_id:
                    source_text += f" (ID: {item.gta_intervention_id})"
                if item.date_implemented:
                    source_text += f" | Implemented: {item.date_implemented}"

                run = p.add_run(source_text)
                run.font.size = Pt(9)
                run.font.color.rgb = self.ergo_colors['secondary_blue']  # Blue for GTA
                run.font.italic = True

                # Add geographic data if available
                if item.gta_implementing_countries or item.gta_affected_countries:
                    p = doc.add_paragraph()
                    geo_text = "   "
                    if item.gta_implementing_countries:
                        geo_text += f"Implementing: {', '.join(item.gta_implementing_countries[:3])}"
                    if item.gta_affected_countries:
                        if item.gta_implementing_countries:
                            geo_text += " | "
                        geo_text += f"Affected: {', '.join(item.gta_affected_countries[:3])}"

                    run = p.add_run(geo_text)
                    run.font.size = Pt(8)
                    run.font.color.rgb = self.ergo_colors['dark_gray']
                    run.font.italic = True
                    p.paragraph_format.left_indent = Inches(0.5)
                    p.paragraph_format.space_after = Pt(2)
            elif item.source_type == "fred":
                # FRED source with series ID and observation date
                source_text = f"   📊 FRED Economic Data"
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
                    run.font.color.rgb = self.ergo_colors['dark_gray']
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
                p.paragraph_format.space_after = Pt(8)
                
    def _add_regional_assessment(self, doc: Document, regional_items: List[IntelligenceItem]):
        """Add regional risk assessments with actual content"""
        regions = {
            'North America': [],
            'Europe': [],
            'Asia-Pacific': [],
            'Middle East': []
        }

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
                countries_text = ' '.join(countries).lower()

                if any(c in countries_text for c in ['united states', 'canada', 'mexico']):
                    primary_region = 'North America'
                elif any(c in countries_text for c in ['china', 'japan', 'india', 'korea', 'singapore', 'australia']):
                    primary_region = 'Asia-Pacific'
                elif any(c in countries_text for c in ['germany', 'france', 'uk', 'united kingdom', 'italy', 'spain', 'european union']):
                    primary_region = 'Europe'
                elif any(c in countries_text for c in ['saudi', 'uae', 'qatar', 'israel', 'iran', 'kuwait']):
                    primary_region = 'Middle East'

            # Fallback to content-based detection
            if not primary_region:
                if any(kw in text_lower or kw in category_lower for kw in ['united states', 'u.s.', 'america', 'canada', 'mexico']):
                    primary_region = 'North America'
                elif any(kw in text_lower or kw in category_lower for kw in ['china', 'japan', 'india', 'asia', 'pacific']):
                    primary_region = 'Asia-Pacific'
                elif any(kw in text_lower or kw in category_lower for kw in ['europe', 'eu', 'britain', 'france', 'germany', 'uk']):
                    primary_region = 'Europe'
                elif any(kw in text_lower or kw in category_lower for kw in ['middle east', 'saudi', 'uae', 'qatar', 'israel']):
                    primary_region = 'Middle East'

            if primary_region:
                regions[primary_region].append(item)
                assigned_items.add(item_id)

        # Add regional summaries with actual content - use top 2-3 items per region
        for region, items in regions.items():
            if items:
                p = doc.add_paragraph()
                run = p.add_run(f"{region}: ")
                run.font.bold = True
                run.font.color.rgb = self.ergo_colors['primary_blue']

                # Get top 2-3 items sorted by relevance for multi-perspective analysis
                top_items = sorted(items, key=lambda x: x.relevance_score, reverse=True)[:min(3, len(items))]

                # Combine insights from multiple items for richer assessment
                combined_insights = []
                seen_content = set()

                for item in top_items:
                    content = item.processed_content

                    # Skip if too similar to already added content
                    content_hash = content[:60].lower()
                    if content_hash in seen_content:
                        continue
                    seen_content.add(content_hash)

                    # Smart truncation - complete sentences only
                    if len(content) > 120:
                        sentences = content.split('. ')
                        truncated = ""
                        for sentence in sentences:
                            if len(truncated) + len(sentence) + 2 < 100:
                                truncated += sentence + ". "
                            else:
                                break
                        # Only use truncated if we got at least one sentence
                        if truncated and len(truncated) > 50:
                            content = truncated.rstrip()
                        else:
                            # Use first sentence only
                            content = sentences[0] + "." if sentences and len(sentences[0]) > 30 else content[:100]

                    combined_insights.append(content)

                # Join insights with clean separator
                full_content = " ".join(combined_insights)
                p.add_run(full_content)
                p.paragraph_format.space_after = Pt(6)
                
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
            p.paragraph_format.space_after = Pt(4)
            
    def _add_sector_section(self, doc: Document, sector: ClientSector, intelligence: SectorIntelligence):
        """Add a section for a specific client sector"""
        # Sector heading
        sector_name = sector.value.replace('_', ' ').upper()
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
        run.font.color.rgb = self.ergo_colors['dark_gray']
        
        # Add top 2 items for this sector - complete sentences only
        for item in intelligence.items[:2]:
            p = doc.add_paragraph()
            content = item.processed_content

            # Truncate to complete sentences if needed
            if len(content) > 250:
                sentences = content.split('. ')
                truncated = ""
                for sentence in sentences:
                    if len(truncated) + len(sentence) + 2 <= 250:
                        truncated += sentence + ". "
                    else:
                        break
                content = truncated.rstrip() if truncated else sentences[0] + "."

            p.add_run(content)
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.space_after = Pt(2)

            # Add source citation for sector items - differentiate sources
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.75)
            p.paragraph_format.space_after = Pt(4)

            if item.source_type == "gta":
                source_text = f"   📊 GTA"
                if item.gta_intervention_id:
                    source_text += f" (ID: {item.gta_intervention_id})"
                run = p.add_run(source_text)
                run.font.size = Pt(9)
                run.font.color.rgb = self.ergo_colors['secondary_blue']
                run.font.italic = True
            elif item.sources:
                source_count = len(item.sources)
                run = p.add_run(f"   Based on {source_count} source{'s' if source_count > 1 else ''}")
                run.font.size = Pt(9)
                run.font.color.rgb = self.ergo_colors['dark_gray']
                run.font.italic = True
            
        # Action Items - enhanced with sector-specific filtering
        if any(item.action_items for item in intelligence.items):
            p = doc.add_paragraph()
            run = p.add_run("Action Items:")
            run.font.bold = True
            run.font.color.rgb = self.ergo_colors['dark_gray']

            # Collect unique action items - filter out generic ones
            generic_patterns = [
                "Monitor situation and prepare briefing",
                "Update market intelligence briefings",
                "Conduct immediate review of affected routes and file alternative flight plans"
            ]

            all_actions = []
            for item in intelligence.items[:3]:  # Top 3 items only
                for action in item.action_items:
                    # Skip generic actions
                    is_generic = any(pattern.lower() in action.lower() for pattern in generic_patterns)
                    if not is_generic and action not in all_actions:
                        all_actions.append(action)

            # If we filtered out everything, generate sector-specific actions
            if not all_actions:
                all_actions = self._generate_sector_specific_actions(sector, intelligence.items[:2])

            for action in all_actions[:3]:
                p = doc.add_paragraph()
                p.add_run(action)
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.space_after = Pt(4)
                
        # Add spacing between sectors
        doc.add_paragraph()

    def _generate_sector_specific_actions(self, sector: ClientSector, items: List[IntelligenceItem]) -> List[str]:
        """Generate sector-specific action items when generic ones are filtered out"""
        actions = []

        if sector == ClientSector.TECHNOLOGY:
            actions = [
                "Proactively reach out to technology sector clients about export control impacts",
                "Monitor Silicon Valley travel patterns for early demand signals",
                "Brief tech executives on cross-border data sovereignty requirements"
            ]
        elif sector == ClientSector.FINANCE:
            actions = [
                "Schedule check-ins with financial sector clients to discuss market volatility impacts",
                "Position for relationship-critical travel during M&A activity periods",
                "Monitor capital flow restrictions affecting client budgets"
            ]
        elif sector == ClientSector.REAL_ESTATE:
            actions = [
                "Alert real estate clients to regional market developments affecting property tours",
                "Track construction material costs impact on development timelines",
                "Coordinate with clients on site visit scheduling around market conditions"
            ]
        elif sector == ClientSector.ENTERTAINMENT:
            actions = [
                "Coordinate with entertainment clients on production schedule changes",
                "Monitor content regulation impacts on international filming locations",
                "Track talent mobility restrictions affecting casting and production"
            ]
        elif sector == ClientSector.ENERGY:
            actions = [
                "Brief energy sector clients on trade restrictions affecting operations",
                "Monitor oil price volatility impacts on client travel budgets",
                "Track sanctions affecting energy sector international operations"
            ]
        else:
            # Generate based on item content
            if items:
                item_content = ' '.join([i.processed_content.lower() for i in items])
                if 'sanction' in item_content or 'restriction' in item_content:
                    actions.append("Review client operations for exposure to trade restrictions")
                if 'regulation' in item_content or 'compliance' in item_content:
                    actions.append("Update compliance protocols and brief affected clients")
                if 'market' in item_content or 'economic' in item_content:
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
    from intelligence_processor import IntelligenceItem, SectorIntelligence, ClientSector
    
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
            confidence=0.9
        ),
        IntelligenceItem(
            raw_content="Test content",
            processed_content="New EU regulations on sustainable aviation fuel mandate 5% SAF blend by 2025.",
            category="regulation",
            relevance_score=0.9,
            so_what_statement="Operators must plan for increased fuel costs and ensure SAF availability at European destinations.",
            affected_sectors=[ClientSector.GENERAL],
            action_items=["Establish SAF supply contracts", "Update fuel cost models"],
            confidence=0.85
        )
    ]
    
    # Create sample sector intelligence
    sector_intel = {
        ClientSector.TECHNOLOGY: SectorIntelligence(
            sector=ClientSector.TECHNOLOGY,
            items=sample_items,
            summary="Technology sector facing increased scrutiny on data sovereignty.",
            key_risks=["Export control restrictions"],
            key_opportunities=["Growing demand for tech executive travel"]
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
