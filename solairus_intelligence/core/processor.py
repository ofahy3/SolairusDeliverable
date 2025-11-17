"""
Intelligence Processing Engine
Transforms raw ErgoMind responses into actionable insights for Solairus and clients
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class ClientSector(Enum):
    """Client industry sectors"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    ENTERTAINMENT = "entertainment"
    ENERGY = "energy"
    HEALTHCARE = "healthcare"
    GENERAL = "general"

@dataclass
class IntelligenceItem:
    """A single piece of processed intelligence from ErgoMind or GTA"""
    raw_content: str
    processed_content: str
    category: str
    relevance_score: float
    so_what_statement: str
    affected_sectors: List[ClientSector] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    confidence: float = 0.0
    sources: List[Dict] = field(default_factory=list)
    # NEW: Multi-source support fields
    source_type: str = "ergomind"  # "ergomind", "gta", or "fred"
    # GTA-specific fields
    gta_intervention_id: Optional[int] = None  # Link to GTA intervention
    gta_implementing_countries: List[str] = field(default_factory=list)  # For GTA interventions
    gta_affected_countries: List[str] = field(default_factory=list)  # For GTA interventions
    date_implemented: Optional[str] = None  # For GTA: when intervention took effect
    date_announced: Optional[str] = None  # For GTA: when intervention was announced
    # FRED-specific fields
    fred_series_id: Optional[str] = None  # FRED series identifier (e.g., "CPIAUCSL")
    fred_observation_date: Optional[str] = None  # Date of observation
    fred_units: Optional[str] = None  # Units of measurement
    fred_value: Optional[float] = None  # Numeric value

@dataclass
class SectorIntelligence:
    """Intelligence organized by client sector"""
    sector: ClientSector
    items: List[IntelligenceItem] = field(default_factory=list)
    summary: str = ""
    key_risks: List[str] = field(default_factory=list)
    key_opportunities: List[str] = field(default_factory=list)

class IntelligenceProcessor:
    """
    Core intelligence processing engine that transforms raw ErgoMind data
    into actionable insights with "So What" analysis
    With optional AI-enhanced "So What" statement generation
    """

    def __init__(self):
        self.client_mapping = self._initialize_client_mapping()
        self.relevance_keywords = self._initialize_relevance_keywords()

        # Initialize AI generator if enabled
        self.ai_generator = None
        try:
            from solairus_intelligence.utils.config import ENV_CONFIG
            if ENV_CONFIG.ai_enabled:
                from solairus_intelligence.ai.generator import SecureAIGenerator, AIConfig
                config = AIConfig(
                    api_key=ENV_CONFIG.anthropic_api_key,
                    model=ENV_CONFIG.ai_model,
                    enabled=True
                )
                self.ai_generator = SecureAIGenerator(config)
                import logging
                logging.getLogger(__name__).info("✓ AI-enhanced 'So What' generation enabled")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"AI generator initialization failed: {e}")
        
    def _initialize_client_mapping(self) -> Dict[ClientSector, Dict]:
        """Initialize client sector mappings with Solairus client data"""
        return {
            ClientSector.TECHNOLOGY: {
                'companies': ['Cisco', 'Palantir', 'NantWorks', 'Pluralsight'],
                'keywords': [
                    'technology', 'silicon valley', 'semiconductor', 'AI', 'cyber',
                    'data', 'software', 'cloud', 'digital', 'innovation', 'startup'
                ],
                'geopolitical_triggers': [
                    'US-China', 'export controls', 'data sovereignty', 'CHIPS Act',
                    'technology transfer', 'intellectual property', 'sanctions'
                ]
            },
            ClientSector.FINANCE: {
                'companies': ['ICONIQ Capital', 'Vista Equity', 'Affinius Capital', 
                            'Ribbit Management', 'ArcLight Capital'],
                'keywords': [
                    'financial', 'investment', 'private equity', 'capital markets',
                    'interest rates', 'inflation', 'banking', 'credit', 'currency',
                    'M&A', 'IPO', 'valuation'
                ],
                'geopolitical_triggers': [
                    'central bank', 'Federal Reserve', 'ECB', 'monetary policy',
                    'Basel', 'financial regulation', 'capital controls', 'sovereign debt'
                ]
            },
            ClientSector.REAL_ESTATE: {
                'companies': ['Presidium Development', 'Restoration Hardware', 
                            'Grassy Creek', 'Bay Grove Capital'],
                'keywords': [
                    'real estate', 'construction', 'property', 'development',
                    'infrastructure', 'urban', 'commercial', 'residential', 'REIT'
                ],
                'geopolitical_triggers': [
                    'zoning', 'housing policy', 'infrastructure spending',
                    'construction costs', 'supply chain', 'materials', 'labor'
                ]
            },
            ClientSector.ENTERTAINMENT: {
                'companies': ['WME IMG', 'Anheuser-Busch InBev'],
                'keywords': [
                    'entertainment', 'media', 'sports', 'content', 'streaming',
                    'production', 'talent', 'broadcasting', 'gaming'
                ],
                'geopolitical_triggers': [
                    'content regulation', 'censorship', 'cultural policy',
                    'international co-production', 'talent mobility', 'visa'
                ]
            },
            ClientSector.ENERGY: {
                'companies': ['ArcLight Capital Partners'],
                'keywords': [
                    'energy', 'oil', 'gas', 'renewable', 'solar', 'wind',
                    'petroleum', 'electricity', 'power', 'utilities', 'carbon'
                ],
                'geopolitical_triggers': [
                    'OPEC', 'energy security', 'pipeline', 'sanctions', 'climate',
                    'Paris Agreement', 'energy transition', 'grid', 'LNG'
                ]
            }
        }
        
    def _initialize_relevance_keywords(self) -> Dict[str, List[str]]:
        """Keywords that indicate relevance to aviation and business travel"""
        return {
            'aviation_direct': [
                'aviation', 'aircraft', 'flight', 'pilot', 'airline', 'airport',
                'FAA', 'EASA', 'ICAO', 'air travel', 'business jet', 'FBO'
            ],
            'aviation_indirect': [
                'travel', 'mobility', 'transportation', 'logistics', 'customs',
                'visa', 'border', 'immigration', 'security', 'fuel prices'
            ],
            'business_impact': [
                'corporate', 'executive', 'business travel', 'global business',
                'international', 'cross-border', 'multinational', 'supply chain'
            ],
            'risk_indicators': [
                'risk', 'threat', 'instability', 'conflict', 'sanctions', 'crisis',
                'disruption', 'uncertainty', 'volatility', 'tension'
            ],
            'opportunity_indicators': [
                'growth', 'expansion', 'opportunity', 'emerging', 'recovery',
                'improvement', 'investment', 'development', 'innovation'
            ]
        }
        
    def process_intelligence(self, raw_text: str, category: str = "general") -> IntelligenceItem:
        """
        Process a single piece of raw intelligence with optional AI enhancement
        """
        # Clean and structure the content
        processed_content = self._clean_and_structure(raw_text)

        # Calculate relevance score
        relevance_score = self._calculate_relevance(raw_text)

        # Identify affected sectors
        affected_sectors = self._identify_affected_sectors(raw_text)

        # Generate action items
        action_items = self._generate_action_items(raw_text, affected_sectors)

        # Calculate confidence
        confidence = self._calculate_confidence(processed_content)

        # Create initial item (without "So What" yet)
        item = IntelligenceItem(
            raw_content=raw_text,
            processed_content=processed_content,
            category=category,
            relevance_score=relevance_score,
            so_what_statement="",  # Temporary
            affected_sectors=affected_sectors,
            action_items=action_items,
            confidence=confidence,
            source_type="ergomind"  # Explicit source type instead of relying on default
        )

        # Generate "So What" statement (with AI if available, using full item context)
        so_what = self._generate_so_what(raw_text, category, item=item)

        # Update the item with the generated "So What"
        from dataclasses import replace
        item = replace(item, so_what_statement=so_what)

        return item
        
    def _clean_and_structure(self, text: str) -> str:
        """Clean and structure raw text for presentation"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix common formatting issues
        text = text.replace('..', '.')
        text = re.sub(r'\.{3,}', '...', text)
        
        # Ensure proper sentence capitalization
        sentences = text.split('. ')
        sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
        text = '. '.join(sentences)

        # Remove hedging/negative statements - this is a tailored intelligence deliverable
        # If we don't have relevant information, we omit it rather than stating what we don't know
        hedging_patterns = [
            'has not identified',
            'have not identified',
            'no evidence of',
            'does not appear',
            'not identified',
            'no significant new',
            'no major new',
            'unclear whether',
            'insufficient data',
            'cannot determine',
            'remains unclear'
        ]

        # Filter out sentences containing hedging language
        sentences = text.split('. ')
        filtered_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if not any(pattern in sentence_lower for pattern in hedging_patterns):
                filtered_sentences.append(sentence)

        if filtered_sentences:
            text = '. '.join(filtered_sentences)
            # Clean up any double periods
            text = re.sub(r'\.{2,}', '.', text)

        # Add structure if it's a long paragraph - use clean prose without bullets
        if len(text) > 500 and '•' not in text:
            # Try to identify key points and structure them
            sentences = text.split('. ')
            if len(sentences) > 3:
                # Extract key sentences and format as clean prose
                key_sentences = self._extract_key_sentences(sentences)
                if key_sentences:
                    # Join sentences with proper spacing
                    structured = " ".join([f"{sentence}." for sentence in key_sentences])
                    return structured
                    
        return text
        
    def _extract_key_sentences(self, sentences: List[str]) -> List[str]:
        """Extract the most important sentences from a list"""
        key_sentences = []
        
        # Prioritize sentences with key indicators
        priority_indicators = [
            'significant', 'major', 'critical', 'important', 'key',
            'forecast', 'expect', 'likely', 'will', 'could',
            'increase', 'decrease', 'rise', 'fall', 'growth'
        ]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in priority_indicators):
                key_sentences.append(sentence)
                
        # Limit to top 3-5 sentences
        return key_sentences[:5] if len(key_sentences) > 5 else key_sentences
        
    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score (0-1) for Solairus"""
        score = 0.0
        text_lower = text.lower()
        
        # Direct aviation relevance (highest weight)
        aviation_matches = sum(1 for kw in self.relevance_keywords['aviation_direct'] 
                              if kw in text_lower)
        score += min(aviation_matches * 0.15, 0.4)
        
        # Indirect aviation relevance
        indirect_matches = sum(1 for kw in self.relevance_keywords['aviation_indirect'] 
                              if kw in text_lower)
        score += min(indirect_matches * 0.1, 0.2)
        
        # Business impact relevance
        business_matches = sum(1 for kw in self.relevance_keywords['business_impact'] 
                              if kw in text_lower)
        score += min(business_matches * 0.08, 0.2)
        
        # Risk/opportunity indicators
        risk_matches = sum(1 for kw in self.relevance_keywords['risk_indicators'] 
                          if kw in text_lower)
        opportunity_matches = sum(1 for kw in self.relevance_keywords['opportunity_indicators'] 
                                 if kw in text_lower)
        score += min((risk_matches + opportunity_matches) * 0.05, 0.2)
        
        return min(score, 1.0)
        
    def _generate_so_what(self, text: str, category: str, item: Optional[IntelligenceItem] = None) -> str:
        """
        Enhanced "So What" generator with AI-powered generation and template fallback

        Args:
            text: Content text
            category: Intelligence category
            item: Full intelligence item (for AI generation)

        Returns:
            "So What" statement
        """
        # Try AI generation if enabled and item is provided
        if self.ai_generator and item:
            try:
                import asyncio
                import logging
                logger = logging.getLogger(__name__)

                # Run AI generation asynchronously
                loop = asyncio.get_event_loop()
                ai_so_what = loop.run_until_complete(
                    self.ai_generator.generate_so_what_statement(
                        item,
                        fallback_generator=lambda x: self._generate_so_what_template(x.processed_content, x.category)
                    )
                )

                if ai_so_what and len(ai_so_what) > 20:  # Validate minimum length
                    return ai_so_what

            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"AI 'So What' generation failed, using template: {e}")

        # Fallback to template-based generation
        return self._generate_so_what_template(text, category)

    def _generate_so_what_template(self, text: str, category: str) -> str:
        """
        Template-based "So What" generator (original implementation)
        Used as fallback when AI is unavailable or fails
        """
        text_lower = text.lower()

        # Economic indicators - varies by specific topic
        if 'economic' in category or 'inflation' in text_lower:
            if 'inflation' in text_lower:
                return "Higher operating costs will impact charter pricing and may require contract adjustments with key clients."
            elif 'interest rate' in text_lower:
                return "Aircraft financing costs will adjust, affecting acquisition timing and lease rate negotiations."
            elif 'gdp' in text_lower or 'growth' in text_lower:
                return "Market demand shifts expected - strengthen presence in growth regions while monitoring declining markets."
            else:
                return "Economic volatility requires dynamic pricing strategies and flexible capacity planning."

        # Geopolitical - varies by region and type
        elif 'geopolitical' in category or 'sanctions' in text_lower or 'political' in text_lower:
            if 'sanctions' in text_lower:
                return "Immediate review of client exposure to sanctioned entities and route adjustments may be necessary."
            elif 'china' in text_lower or 'asia' in text_lower:
                return "Asia-Pacific travel patterns may shift - coordinate with clients on alternative routing and destinations."
            elif 'russia' in text_lower or 'ukraine' in text_lower:
                return "European airspace constraints continue - flight planning complexity increases for transatlantic operations."
            elif 'middle east' in text_lower:
                return "Regional security protocols require updating - brief crews and clients on enhanced procedures."
            else:
                return "Geopolitical shifts demand proactive client communication and operational contingency planning."

        # Regulatory - varies by jurisdiction
        elif 'regulation' in category or 'compliance' in text_lower:
            if 'europe' in text_lower or 'eu' in text_lower:
                return "EU regulatory changes require operational procedure updates and potential crew retraining."
            elif 'faa' in text_lower or 'united states' in text_lower:
                return "FAA compliance adjustments needed - schedule regulatory review and update SOPs accordingly."
            elif 'sustainability' in text_lower or 'environmental' in text_lower:
                return "Environmental compliance costs rising - evaluate SAF adoption timeline and carbon offset strategies."
            else:
                return "New compliance requirements necessitate legal review and operational procedure modifications."

        # Aviation-specific
        elif 'aviation' in text_lower or 'aircraft' in text_lower:
            if 'fuel' in text_lower or 'saf' in text_lower:
                return "Fuel strategy requires reassessment - balance cost management with sustainability commitments."
            elif 'airport' in text_lower or 'fbo' in text_lower:
                return "Ground services landscape changing - review preferred vendor agreements and service levels."
            elif 'safety' in text_lower:
                return "Safety protocols demand immediate attention - convene safety committee and update procedures."
            else:
                return "Industry dynamics shifting - competitive positioning and service differentiation become critical."

        # Technology sector
        elif 'technology' in text_lower or 'cyber' in text_lower:
            if 'restriction' in text_lower or 'export' in text_lower:
                return "Technology sector clients face new travel constraints - proactive coordination on international itineraries essential."
            elif 'cyber' in text_lower or 'security' in text_lower:
                return "Cybersecurity concerns escalating - evaluate onboard connectivity security and client data protection."
            else:
                return "Tech industry disruption affects executive travel patterns - maintain flexibility in service offerings."

        # Finance sector
        elif 'financial' in text_lower or 'market' in text_lower or 'investment' in text_lower:
            if 'market volatility' in text_lower or 'stock' in text_lower:
                return "Market turbulence may compress private aviation budgets - emphasize value proposition to financial clients."
            elif 'banking' in text_lower:
                return "Banking sector dynamics shift executive travel priorities - position for relationship-critical trips."
            else:
                return "Financial sector developments influence client liquidity - monitor closely for demand signals."

        # Supply chain
        elif 'supply chain' in text_lower:
            return "Parts availability concerns require proactive inventory management and vendor diversification strategies."

        # Default - but make it specific to the category
        else:
            if 'security' in category:
                return "Security posture requires updating - assess threat levels and adjust protocols for affected destinations."
            elif 'economic' in category:
                return "Economic indicators suggest demand pattern changes - adjust capacity and marketing focus accordingly."
            else:
                return "Situation warrants monitoring - prepare contingency plans and maintain client communication readiness."
            
    def _identify_affected_sectors(self, text: str) -> List[ClientSector]:
        """Identify which client sectors are affected by this intelligence"""
        affected = []
        text_lower = text.lower()
        
        for sector, mapping in self.client_mapping.items():
            # Check for direct mentions
            sector_score = 0
            
            # Check keywords
            for keyword in mapping['keywords']:
                if keyword in text_lower:
                    sector_score += 1
                    
            # Check geopolitical triggers
            for trigger in mapping['geopolitical_triggers']:
                if trigger.lower() in text_lower:
                    sector_score += 2  # Higher weight for specific triggers
                    
            # If score is high enough, add to affected sectors
            if sector_score >= 2:
                affected.append(sector)
                
        # If no specific sectors identified but it's important, mark as general
        if not affected and self._calculate_relevance(text) > 0.5:
            affected.append(ClientSector.GENERAL)
            
        return affected
        
    def _generate_action_items(self, text: str, sectors: List[ClientSector]) -> List[str]:
        """
        Generate sector-specific and context-aware action items
        """
        action_items = []
        text_lower = text.lower()

        # Aviation operational actions
        if any(kw in text_lower for kw in ['sanction', 'restriction', 'ban']):
            action_items.append("Conduct immediate review of affected routes and file alternative flight plans")
            action_items.append("Audit client list for exposure to sanctioned entities or regions")

        if any(kw in text_lower for kw in ['fuel', 'oil price', 'energy cost', 'saf']):
            action_items.append("Revise fuel hedging strategy with finance team by end of quarter")
            action_items.append("Update client proposals to reflect current fuel cost projections")

        if any(kw in text_lower for kw in ['regulation', 'compliance', 'faa', 'easa']):
            action_items.append("Schedule regulatory compliance meeting with operations and legal teams")
            action_items.append("Update crew training modules to incorporate new regulatory requirements")

        if any(kw in text_lower for kw in ['safety', 'security', 'risk']):
            action_items.append("Convene safety committee to assess threat and update protocols")
            action_items.append("Brief flight crews on enhanced security procedures for affected regions")

        # Sector-specific actions with detail
        if ClientSector.TECHNOLOGY in sectors:
            if 'export' in text_lower or 'restriction' in text_lower:
                action_items.append("Proactively contact technology sector clients to discuss international travel implications")
            elif 'cyber' in text_lower:
                action_items.append("Review and enhance cybersecurity protocols for technology executive flights")
            else:
                action_items.append("Prepare briefing for technology sector clients on industry-specific developments")

        if ClientSector.FINANCE in sectors:
            if 'market' in text_lower or 'volatility' in text_lower:
                action_items.append("Monitor financial sector client booking patterns for early demand signals")
            elif 'banking' in text_lower:
                action_items.append("Strengthen relationships with banking clients - position for relationship-critical travel")
            else:
                action_items.append("Schedule check-ins with financial sector clients to discuss market impact on travel needs")

        if ClientSector.REAL_ESTATE in sectors:
            action_items.append("Alert real estate clients to regional market developments affecting property tours")

        if ClientSector.ENTERTAINMENT in sectors:
            action_items.append("Coordinate with entertainment sector clients on production schedule and location changes")

        # Strategic business actions
        if any(kw in text_lower for kw in ['economic growth', 'gdp', 'expansion']):
            action_items.append("Evaluate market expansion opportunities in high-growth regions")

        if any(kw in text_lower for kw in ['downturn', 'recession', 'slowdown']):
            action_items.append("Strengthen value proposition messaging and client retention programs")

        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in action_items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)

        return unique_items[:3]  # Return top 3 most relevant actions
        
    def _calculate_confidence(self, processed_content: str) -> float:
        """
        Calculate confidence in the processed intelligence

        ErgoMind confidence boosted to 0.7-1.0 range to ensure narrative leadership
        in composite scoring vs FRED (0.95) and GTA (0.8-0.9)
        """
        confidence = 0.7  # Base confidence (boosted from 0.5 to strengthen ErgoMind)

        # Increase for structured content
        if '•' in processed_content or '\n' in processed_content:
            confidence += 0.1

        # Increase for specific details
        if any(char.isdigit() for char in processed_content):
            confidence += 0.1

        # Increase for proper length
        if 100 < len(processed_content) < 1000:
            confidence += 0.1  # Reduced from 0.2 since base is higher
        elif len(processed_content) >= 1000:
            confidence += 0.05  # Reduced from 0.1

        return min(confidence, 1.0)
        
    def organize_by_sector(self, items: List[IntelligenceItem]) -> Dict[ClientSector, SectorIntelligence]:
        """Organize intelligence items by client sector"""
        sector_intel = {}
        
        for sector in ClientSector:
            # Find all items affecting this sector
            sector_items = [
                item for item in items 
                if sector in item.affected_sectors or ClientSector.GENERAL in item.affected_sectors
            ]
            
            if sector_items:
                # Sort by relevance
                sector_items.sort(key=lambda x: x.relevance_score, reverse=True)
                
                # Generate sector summary
                summary = self._generate_sector_summary(sector, sector_items)
                
                # Extract key risks and opportunities
                risks = self._extract_risks(sector_items)
                opportunities = self._extract_opportunities(sector_items)
                
                sector_intel[sector] = SectorIntelligence(
                    sector=sector,
                    items=sector_items,
                    summary=summary,
                    key_risks=risks,
                    key_opportunities=opportunities
                )
                
        return sector_intel
        
    def _generate_sector_summary(self, sector: ClientSector, items: List[IntelligenceItem]) -> str:
        """Generate a summary for a specific sector"""
        if not items:
            return "No significant developments identified this period."
            
        top_items = items[:3]  # Focus on top 3 most relevant
        
        summary_parts = []
        for item in top_items:
            summary_parts.append(item.so_what_statement)
            
        return " ".join(summary_parts)
        
    def _extract_risks(self, items: List[IntelligenceItem]) -> List[str]:
        """Extract key risks from intelligence items"""
        risks = []
        
        for item in items:
            text_lower = item.raw_content.lower()
            if any(kw in text_lower for kw in self.relevance_keywords['risk_indicators']):
                # Extract the risk statement
                risk = item.so_what_statement
                if risk not in risks:
                    risks.append(risk)
                    
        return risks[:3]  # Top 3 risks
        
    def _extract_opportunities(self, items: List[IntelligenceItem]) -> List[str]:
        """Extract key opportunities from intelligence items"""
        opportunities = []

        for item in items:
            text_lower = item.raw_content.lower()
            if any(kw in text_lower for kw in self.relevance_keywords['opportunity_indicators']):
                # Extract the opportunity
                opportunity = item.so_what_statement
                if opportunity not in opportunities:
                    opportunities.append(opportunity)

        return opportunities[:3]  # Top 3 opportunities

    # =====================================================================
    # GTA (Global Trade Alert) Processing Methods
    # =====================================================================

    def process_gta_intervention(self, intervention, category: str = "trade_intervention") -> IntelligenceItem:
        """
        Convert a GTA intervention into an IntelligenceItem

        Args:
            intervention: GTAIntervention object from gta_client
            category: Category to assign (defaults to trade_intervention)

        Returns:
            IntelligenceItem with GTA-specific fields populated
        """
        # Import here to avoid circular dependency
        from gta_client import GTAIntervention

        # Extract raw and processed content
        raw_content = intervention.description
        processed_content = intervention.get_short_description(400)

        # Calculate relevance based on intervention evaluation and type
        relevance_score = self._calculate_gta_relevance(intervention)

        # Generate context-aware "So What" statement
        so_what = self._generate_gta_so_what(intervention)

        # Identify affected client sectors
        affected_sectors = self._map_gta_to_sectors(intervention)

        # Generate action items based on intervention type
        action_items = self._generate_gta_action_items(intervention, affected_sectors)

        # Calculate confidence (GTA data is highly reliable as it's from official sources)
        confidence = 0.9 if intervention.sources else 0.8

        # Create IntelligenceItem with GTA-specific fields
        return IntelligenceItem(
            raw_content=raw_content,
            processed_content=processed_content,
            category=category,
            relevance_score=relevance_score,
            so_what_statement=so_what,
            affected_sectors=affected_sectors,
            action_items=action_items,
            confidence=confidence,
            sources=intervention.sources,
            # GTA-specific fields
            source_type="gta",
            gta_intervention_id=intervention.intervention_id,
            gta_implementing_countries=intervention.get_implementing_countries(),
            gta_affected_countries=intervention.get_affected_countries(),
            date_implemented=intervention.date_implemented,
            date_announced=intervention.date_announced
        )

    def _calculate_gta_relevance(self, intervention) -> float:
        """Calculate relevance score for GTA intervention"""
        score = 0.5  # Base score

        # Harmful interventions are highly relevant
        if intervention.gta_evaluation in ["Harmful", "Red"]:
            score += 0.3
        elif intervention.gta_evaluation == "Liberalising":
            score += 0.2

        # Check if aviation-relevant FIRST (before time penalties)
        # Handle affected_sectors as strings or ints
        affected_sectors = intervention.affected_sectors if intervention.affected_sectors else []
        sector_strings = [str(s).lower() for s in affected_sectors if s]

        # Aviation-adjacent sectors for broader relevance
        aviation_adjacent = ['aviation', 'aerospace', 'aircraft', 'petroleum', 'fuel',
                            'kerosene', 'air transport', 'airport', 'pilot']
        is_aviation_relevant = any(keyword in ' '.join(sector_strings) for keyword in aviation_adjacent)

        if is_aviation_relevant:
            score += 0.2  # Aviation sector boost

        # Recent interventions are more relevant - SOFTENED penalties for old data
        # Aviation-relevant interventions exempt from penalties
        if intervention.date_implemented:
            try:
                from datetime import datetime
                impl_date = datetime.fromisoformat(intervention.date_implemented.replace('Z', '+00:00'))
                days_old = (datetime.now() - impl_date.replace(tzinfo=None)).days

                if days_old < 30:
                    score += 0.3  # Very recent - highly relevant
                elif days_old < 60:
                    score += 0.2
                elif days_old < 90:
                    score += 0.1
                elif days_old < 180:
                    score += 0.0  # Neutral
                elif days_old < 365:
                    # Softened penalty: 0.0 instead of -0.2 for aviation-relevant
                    score += 0.0 if is_aviation_relevant else -0.1
                else:
                    # Data older than 1 year: softened from -0.5 to -0.2
                    # Aviation-relevant items get no penalty
                    score += 0.0 if is_aviation_relevant else -0.2
            except:
                pass

        return min(score, 1.0)

    def _generate_gta_so_what(self, intervention) -> str:
        """Generate 'So What' statement for GTA intervention"""
        impl_countries = intervention.get_implementing_countries()
        affected_countries = intervention.get_affected_countries()

        # Handle intervention_type as string or int
        intervention_type_str = str(intervention.intervention_type) if intervention.intervention_type else ""
        intervention_type_lower = intervention_type_str.lower()

        # Sanctions and export controls
        if 'sanction' in intervention_type_lower or 'export' in intervention_type_lower:
            if impl_countries:
                return f"Trade restrictions from {', '.join(impl_countries[:2])} may affect supply chains, client operations, and routing decisions for affected regions."
            return "Export controls and sanctions require immediate compliance review and may impact client travel patterns."

        # Tariffs and import restrictions
        elif 'tariff' in intervention_type_lower or 'import' in intervention_type_lower:
            return "Tariff changes signal shifting trade relationships that may affect business aviation demand patterns and cross-border operations."

        # Capital controls
        elif 'capital' in intervention_type_lower:
            if affected_countries:
                return f"Capital controls in {', '.join(affected_countries[:2])} may restrict client financial flows and impact business travel demand from these markets."
            return "Financial restrictions may constrain client liquidity for aviation services and international operations."

        # Technology restrictions
        elif 'technology' in intervention_type_lower or 'local content' in intervention_type_lower:
            return "Technology sector restrictions directly impact Silicon Valley and tech clients' international operations and travel requirements."

        # Subsidies and government support
        elif 'subsidy' in intervention_type_lower or 'grant' in intervention_type_lower:
            return "Government support measures signal economic policy direction and competitive landscape changes in affected sectors."

        # Generic for other types
        else:
            if intervention.gta_evaluation == "Harmful":
                return "This trade intervention represents increased barriers to international business that may affect client operations and travel needs."
            elif intervention.gta_evaluation == "Liberalising":
                return "This liberalizing measure may create new business opportunities and increase demand for international travel services."
            return "This trade policy change warrants monitoring for potential impacts on client operations and aviation services."

    def _map_gta_to_sectors(self, intervention) -> List[ClientSector]:
        """
        Map GTA intervention to affected client sectors using taxonomy alignment

        GTA uses different sector taxonomy than ClientSector enum, so we map:
        - "Computer and electronic products" → TECHNOLOGY
        - "Semiconductors" → TECHNOLOGY
        - "Petroleum products" → ENERGY (aviation-relevant for jet fuel)
        - etc.
        """
        sectors = set()

        # Check affected sectors - handle various types (str, int, list)
        affected_sectors = intervention.affected_sectors if intervention.affected_sectors else []
        # Convert all elements to strings
        sector_strings = [str(s) for s in affected_sectors if s]
        sector_text = ' '.join(sector_strings).lower()

        # GTA Taxonomy Mapping - expanded for better coverage
        gta_sector_mapping = {
            ClientSector.TECHNOLOGY: [
                'technology', 'software', 'semiconductor', 'computer', 'electronic',
                'information', 'telecommunications', 'data processing', 'internet',
                'chips', 'integrated circuits'
            ],
            ClientSector.FINANCE: [
                'finance', 'financial', 'banking', 'capital', 'insurance',
                'securities', 'investment', 'credit', 'monetary'
            ],
            ClientSector.REAL_ESTATE: [
                'real estate', 'construction', 'property', 'building',
                'housing', 'infrastructure', 'cement', 'steel'
            ],
            ClientSector.ENTERTAINMENT: [
                'entertainment', 'media', 'broadcasting', 'film',
                'television', 'music', 'cultural', 'recreation'
            ],
            ClientSector.ENERGY: [
                'energy', 'oil', 'gas', 'petroleum', 'fuel', 'kerosene',
                'coal', 'electricity', 'power generation', 'renewable energy',
                'crude oil', 'natural gas'  # Aviation-relevant
            ],
            ClientSector.HEALTHCARE: [
                'healthcare', 'pharmaceutical', 'medical', 'health',
                'drugs', 'medicine', 'biotechnology', 'clinical'
            ]
        }

        # Apply mapping
        for client_sector, keywords in gta_sector_mapping.items():
            if any(kw in sector_text for kw in keywords):
                sectors.add(client_sector)

        # If no specific sectors identified, mark as general
        if not sectors:
            sectors.add(ClientSector.GENERAL)

        return list(sectors)

    def _generate_gta_action_items(self, intervention, sectors: List[ClientSector]) -> List[str]:
        """Generate actionable items based on GTA intervention"""
        actions = []

        # Handle intervention_type as string or int
        intervention_type_str = str(intervention.intervention_type) if intervention.intervention_type else ""
        intervention_type_lower = intervention_type_str.lower()

        # Sanctions/export controls
        if 'sanction' in intervention_type_lower or 'export' in intervention_type_lower:
            actions.append("Conduct compliance review for all affected jurisdictions and update routing protocols")
            actions.append("Brief affected clients on travel restrictions and alternative routing options")
            actions.append("Review client list for exposure to sanctioned entities or regions")

        # Tariffs
        elif 'tariff' in intervention_type_lower:
            actions.append("Monitor for secondary impacts on client business operations and travel demand")
            actions.append("Assess potential effects on fuel costs and international operations")

        # Capital controls
        elif 'capital' in intervention_type_lower:
            actions.append("Review payment and billing procedures for affected jurisdictions")
            actions.append("Contact clients in affected markets to assess impact on travel budgets")

        # Technology restrictions
        elif 'technology' in intervention_type_lower:
            if ClientSector.TECHNOLOGY in sectors:
                actions.append("Proactively reach out to technology sector clients about operational impacts")
                actions.append("Monitor for changes in Silicon Valley travel patterns")

        # Generic actions
        if not actions:
            actions.append("Monitor situation and prepare briefing materials for affected clients")
            actions.append("Update market intelligence briefings with this development")

        return actions[:3]

    def process_fred_observation(
        self,
        observation,  # FREDObservation from fred_client
        category: str
    ) -> IntelligenceItem:
        """
        Convert FRED economic data observation to IntelligenceItem

        Args:
            observation: FREDObservation with series data
            category: Category name (inflation, interest_rate, fuel_cost, etc.)

        Returns:
            IntelligenceItem with economic data
        """
        from fred_client import FREDObservation

        # Format value based on category and units
        formatted_value = self._format_fred_value(observation)

        # Create processed content
        processed_content = f"{observation.series_name}: {formatted_value} as of {observation.date}"

        # Calculate relevance based on series and value
        relevance_score = self._calculate_fred_relevance(observation)

        # Generate contextual "So What" statement
        so_what = self._generate_fred_so_what(observation)

        # Map to affected sectors
        affected_sectors = self._map_fred_to_sectors(observation)

        # Generate action items
        action_items = self._generate_fred_action_items(observation, affected_sectors)

        return IntelligenceItem(
            raw_content=f"{observation.series_id}: {observation.value}",
            processed_content=processed_content,
            category=f"economic_{category}",
            relevance_score=relevance_score,
            so_what_statement=so_what,
            affected_sectors=affected_sectors,
            action_items=action_items,
            confidence=0.95,  # FRED data is highly reliable
            source_type="fred",
            fred_series_id=observation.series_id,
            fred_observation_date=observation.date,
            fred_units=observation.units,
            fred_value=observation.value
        )

    def _format_fred_value(self, observation) -> str:
        """Format FRED value based on series type"""
        series_id = observation.series_id
        value = observation.value

        # Percentages (rates, growth)
        if series_id in ['DFF', 'DGS10', 'MORTGAGE30US', 'A191RL1Q225SBEA', 'UNRATE']:
            return f"{value:.2f}%"

        # Prices (dollars per gallon, dollars per barrel)
        elif series_id in ['WJFUELUSGULF', 'DCOILWTICO', 'GASREGW']:
            return f"${value:.2f}/gallon" if 'gallon' in observation.units.lower() else f"${value:.2f}/barrel"

        # Index values (CPI, etc.)
        elif 'CPI' in series_id or 'PCE' in series_id:
            return f"{value:.1f} (Index)"

        # GDP (billions/trillions)
        elif 'GDP' in series_id:
            if value > 1000:
                return f"${value/1000:.2f}T"
            else:
                return f"${value:.1f}B"

        # Employment (thousands)
        elif series_id == 'PAYEMS':
            return f"{value/1000:.1f}M employees"

        # Default
        return f"{value:.2f}"

    def _calculate_fred_relevance(self, observation) -> float:
        """Calculate relevance score for FRED data"""
        series_id = observation.series_id
        category = observation.category

        # Base score
        score = 0.5

        # Aviation-specific indicators (highest relevance)
        if series_id == 'WJFUELUSGULF':  # Jet fuel price
            score += 0.4

        # Interest rates (aircraft financing)
        elif category == 'interest_rates':
            score += 0.3

        # Inflation (operational costs)
        elif category == 'inflation':
            score += 0.25

        # GDP growth (demand indicators)
        elif category == 'gdp_growth':
            score += 0.2

        # Employment (business activity)
        elif category == 'employment':
            score += 0.15

        # Fuel costs (operational)
        elif series_id in ['DCOILWTICO', 'GASREGW']:
            score += 0.25

        return min(score, 1.0)

    def _generate_fred_so_what(self, observation) -> str:
        """Generate contextual impact statement for FRED economic data"""
        series_id = observation.series_id
        value = observation.value

        # Jet fuel prices
        if series_id == 'WJFUELUSGULF':
            if value > 3.00:
                return "Elevated jet fuel costs require immediate pricing strategy review and fuel hedging assessment to protect margins."
            elif value < 2.00:
                return "Lower jet fuel costs create opportunity for competitive pricing and margin expansion."
            else:
                return "Moderate jet fuel costs support current pricing models and operational budgets."

        # Crude oil (correlates with jet fuel)
        elif series_id == 'DCOILWTICO':
            if value > 90:
                return "High crude oil prices signal upcoming jet fuel cost pressure - monitor hedging opportunities."
            else:
                return "Stable crude oil prices support predictable operational cost structure."

        # Federal Funds Rate
        elif series_id == 'DFF':
            if value > 5.0:
                return "Elevated interest rates increase aircraft financing costs, affecting acquisition timing and lease rate negotiations."
            else:
                return "Lower interest rates create favorable environment for aircraft acquisitions and refinancing."

        # 10-Year Treasury
        elif series_id == 'DGS10':
            return "Treasury rate movements affect long-term aircraft financing costs and client capital allocation decisions."

        # Mortgage rates (real estate sector proxy)
        elif series_id == 'MORTGAGE30US':
            return "Mortgage rate trends signal real estate sector activity levels, affecting property tour and site visit demand."

        # CPI (inflation)
        elif 'CPI' in series_id:
            if value > 300:  # High CPI level
                return "Persistent inflation pressures will impact operational costs, requiring dynamic pricing strategies and contract adjustments."
            else:
                return "Inflation trends affect operational cost structure and client budget planning for business aviation."

        # GDP growth
        elif 'GDP' in series_id:
            return "GDP trends signal overall business activity levels and corporate travel demand across all client sectors."

        # Unemployment
        elif series_id == 'UNRATE':
            if value < 4.0:
                return "Low unemployment indicates strong economy and high business activity, supporting aviation demand."
            elif value > 6.0:
                return "Rising unemployment may signal reduced corporate travel budgets and discretionary aviation spending."
            else:
                return "Employment trends reflect economic health and business aviation demand patterns."

        # Default
        return "Economic indicator warrants monitoring for potential operational and demand impacts."

    def _map_fred_to_sectors(self, observation) -> List[ClientSector]:
        """
        Map FRED data to affected client sectors

        Note: Restricted jet fuel to GENERAL + ENERGY only (was appearing in all sectors)
        """
        series_id = observation.series_id
        sectors = []

        # Jet fuel - GENERAL operational concern + ENERGY sector
        # (Restricted from appearing in all sector sections to reduce redundancy)
        if series_id == 'WJFUELUSGULF':
            return [ClientSector.GENERAL, ClientSector.ENERGY]

        # Interest rates - finance and real estate (aircraft financing, property development)
        elif series_id in ['DFF', 'DGS10']:
            sectors = [ClientSector.FINANCE, ClientSector.REAL_ESTATE, ClientSector.GENERAL]

        # Mortgage rates - real estate specific
        elif series_id == 'MORTGAGE30US':
            sectors = [ClientSector.REAL_ESTATE, ClientSector.FINANCE]

        # Inflation - all sectors (general operational concern)
        elif 'CPI' in series_id or 'PCE' in series_id:
            sectors = [ClientSector.GENERAL]

        # GDP - all sectors (economic health indicator)
        elif 'GDP' in series_id:
            sectors = [ClientSector.GENERAL]

        # Employment - general business activity
        elif series_id in ['UNRATE', 'PAYEMS']:
            sectors = [ClientSector.GENERAL]

        # Crude oil - energy sector + operational
        elif series_id == 'DCOILWTICO':
            sectors = [ClientSector.ENERGY, ClientSector.GENERAL]

        # Regular gas - general operational costs
        elif series_id == 'GASREGW':
            sectors = [ClientSector.GENERAL]

        return sectors if sectors else [ClientSector.GENERAL]

    def _generate_fred_action_items(self, observation, sectors: List[ClientSector]) -> List[str]:
        """Generate action items based on FRED data"""
        series_id = observation.series_id
        actions = []

        # Jet fuel specific
        if series_id == 'WJFUELUSGULF':
            actions.append("Review fuel hedging strategy and pricing models")
            actions.append("Update cost projections for charter operations")
            actions.append("Brief clients on fuel cost trends affecting pricing")

        # Interest rates
        elif series_id in ['DFF', 'DGS10']:
            actions.append("Assess aircraft financing and refinancing opportunities")
            actions.append("Update financial projections for rate environment")
            if ClientSector.FINANCE in sectors:
                actions.append("Brief finance sector clients on capital cost impacts")

        # Mortgage rates / real estate
        elif series_id == 'MORTGAGE30US':
            actions.append("Monitor real estate sector travel demand indicators")
            actions.append("Engage real estate clients on property tour scheduling")

        # Inflation
        elif 'CPI' in series_id:
            actions.append("Review operational cost structure and pricing strategy")
            actions.append("Update client contracts to reflect cost environment")

        # GDP
        elif 'GDP' in series_id:
            actions.append("Adjust demand forecasts based on economic growth trends")
            actions.append("Review capacity planning for projected activity levels")

        # Unemployment
        elif series_id == 'UNRATE':
            actions.append("Monitor corporate travel budget trends")
            actions.append("Adjust marketing strategy for economic environment")

        # Default
        if not actions:
            actions.append("Monitor economic indicator for operational impacts")
            actions.append("Brief relevant client sectors on trend implications")

        return actions[:3]

    def merge_intelligence_sources(
        self,
        *source_lists: List[IntelligenceItem]
    ) -> List[IntelligenceItem]:
        """
        Intelligently merge multiple intelligence sources (ErgoMind, GTA, FRED)

        Features:
        - Semantic deduplication (not just first 100 chars)
        - Source priority for overlapping topics (FRED > GTA > ErgoMind for economics)
        - Composite scoring: relevance × confidence × freshness
        - Global freshness filtering (6 months for GTA)

        Args:
            *source_lists: Variable number of IntelligenceItem lists from different sources

        Returns:
            Merged and deduplicated intelligence list, sorted by composite score
        """
        from datetime import datetime, timedelta

        # Flatten all source lists into single list
        all_items = [item for source_list in source_lists for item in source_list]

        # Apply global freshness filter (6 months for GTA)
        six_months_ago = datetime.now() - timedelta(days=180)
        filtered_items = []

        for item in all_items:
            # Filter stale GTA data
            if item.source_type == "gta" and item.date_implemented:
                try:
                    impl_date = datetime.fromisoformat(item.date_implemented.replace('Z', '+00:00').replace('T', ' ')[:10])
                    if impl_date < six_months_ago:
                        continue  # Skip stale GTA data
                except:
                    pass  # Keep if we can't parse date

            filtered_items.append(item)

        # Calculate composite score for sorting: relevance × confidence × freshness × source_weight
        def calculate_composite_score(item: IntelligenceItem) -> float:
            """
            Calculate weighted score considering multiple factors

            Source weights ensure ErgoMind narrative leads while keeping data sources valuable:
            - ErgoMind: 1.15x (narrative leadership)
            - GTA: 1.0x (data support)
            - FRED: 0.95x (prevents economic data dominance)
            """
            base_score = item.relevance_score * item.confidence

            # Source weighting to ensure ErgoMind dominance
            source_weights = {
                'ergomind': 1.15,  # 15% boost for narrative leadership
                'gta': 1.0,        # Neutral - valuable supporting data
                'fred': 0.95       # Slight reduction to prevent top-score saturation
            }
            source_weight = source_weights.get(item.source_type, 1.0)

            # Freshness factor (GTA and FRED have dates, ErgoMind is always "current")
            freshness_factor = 1.0
            if item.source_type == "gta" and item.date_implemented:
                try:
                    impl_date = datetime.fromisoformat(item.date_implemented.replace('Z', '+00:00'))
                    days_old = (datetime.now() - impl_date.replace(tzinfo=None)).days
                    # Gentle freshness boost: 1.0 for <90 days, 0.9 for 90-180 days
                    freshness_factor = 1.0 if days_old < 90 else 0.9
                except:
                    pass
            elif item.source_type == "fred" and item.fred_observation_date:
                try:
                    obs_date = datetime.fromisoformat(item.fred_observation_date[:10])
                    days_old = (datetime.now() - obs_date).days
                    # FRED data freshness: 1.0 for <60 days, 0.95 for older
                    freshness_factor = 1.0 if days_old < 60 else 0.95
                except:
                    pass

            return base_score * freshness_factor * source_weight

        # Sort by composite score
        filtered_items.sort(key=calculate_composite_score, reverse=True)

        # Enhanced deduplication with semantic similarity
        unique_items = []
        seen_content_hashes = set()

        for item in filtered_items:
            # Create content fingerprint (first 200 chars + key terms)
            content_normalized = item.processed_content[:200].lower().strip()

            # Check for semantic duplicates
            is_duplicate = False
            for existing_hash in seen_content_hashes:
                # Calculate keyword overlap (simple semantic similarity)
                if self._calculate_content_similarity(content_normalized, existing_hash) > 0.75:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_items.append(item)
                seen_content_hashes.add(content_normalized)

        # Apply source priority for overlapping topics
        unique_items = self._apply_source_priority(unique_items)

        return unique_items

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple keyword-based similarity between two content strings"""
        # Extract keywords (words longer than 3 chars, excluding common words)
        stop_words = {'the', 'and', 'for', 'this', 'that', 'with', 'from', 'have', 'will', 'are'}

        words1 = set(w.lower() for w in content1.split() if len(w) > 3 and w.lower() not in stop_words)
        words2 = set(w.lower() for w in content2.split() if len(w) > 3 and w.lower() not in stop_words)

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity: intersection / union
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _apply_source_priority(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """
        Apply source priority for overlapping topics:
        - FRED > GTA > ErgoMind for economic indicators
        - GTA > FRED > ErgoMind for trade policy
        - ErgoMind leads for narrative/geopolitical analysis
        """
        # Group by topic clusters
        economic_keywords = ['inflation', 'interest rate', 'gdp', 'cpi', 'federal reserve', 'treasury', 'mortgage']
        trade_keywords = ['tariff', 'sanction', 'export control', 'trade barrier', 'intervention']

        prioritized_items = []
        topic_seen = {'economic': set(), 'trade': set()}

        # First pass: Add high-priority sources for each topic
        for item in items:
            content_lower = item.processed_content.lower()

            # Economic topic
            if any(kw in content_lower for kw in economic_keywords):
                topic_key = 'economic_' + content_lower[:50]
                if topic_key not in topic_seen['economic']:
                    # Prefer FRED for economic data
                    if item.source_type == 'fred':
                        prioritized_items.append(item)
                        topic_seen['economic'].add(topic_key)

            # Trade topic
            elif any(kw in content_lower for kw in trade_keywords):
                topic_key = 'trade_' + content_lower[:50]
                if topic_key not in topic_seen['trade']:
                    # Prefer GTA for trade data
                    if item.source_type == 'gta':
                        prioritized_items.append(item)
                        topic_seen['trade'].add(topic_key)

            # Geopolitical/narrative
            else:
                prioritized_items.append(item)

        # Second pass: Add remaining items that weren't filtered
        for item in items:
            if item not in prioritized_items:
                prioritized_items.append(item)

        return prioritized_items
