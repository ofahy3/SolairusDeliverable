"""
Base classes and data structures for intelligence processing
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from solairus_intelligence.config.clients import ClientSector


@dataclass
class IntelligenceItem:
    """A single piece of processed intelligence from ErgoMind, GTA, or FRED"""
    raw_content: str
    processed_content: str
    category: str
    relevance_score: float
    so_what_statement: str
    affected_sectors: List[ClientSector] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    confidence: float = 0.0
    sources: List[Dict] = field(default_factory=list)
    # Source type identifier
    source_type: str = "ergomind"  # "ergomind", "gta", or "fred"
    # GTA-specific fields
    gta_intervention_id: Optional[int] = None
    gta_implementing_countries: List[str] = field(default_factory=list)
    gta_affected_countries: List[str] = field(default_factory=list)
    date_implemented: Optional[str] = None
    date_announced: Optional[str] = None
    # FRED-specific fields
    fred_series_id: Optional[str] = None
    fred_observation_date: Optional[str] = None
    fred_units: Optional[str] = None
    fred_value: Optional[float] = None


@dataclass
class SectorIntelligence:
    """Intelligence organized by client sector"""
    sector: ClientSector
    items: List[IntelligenceItem] = field(default_factory=list)
    summary: str = ""
    key_risks: List[str] = field(default_factory=list)
    key_opportunities: List[str] = field(default_factory=list)


class BaseProcessor:
    """Base class for all intelligence processors"""

    # Keywords for relevance scoring
    RELEVANCE_KEYWORDS = {
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

    def calculate_base_relevance(self, text: str) -> float:
        """Calculate base relevance score (0-1) for Solairus"""
        score = 0.0
        text_lower = text.lower()

        # Direct aviation relevance (highest weight)
        aviation_matches = sum(1 for kw in self.RELEVANCE_KEYWORDS['aviation_direct']
                               if kw in text_lower)
        score += min(aviation_matches * 0.15, 0.4)

        # Indirect aviation relevance
        indirect_matches = sum(1 for kw in self.RELEVANCE_KEYWORDS['aviation_indirect']
                               if kw in text_lower)
        score += min(indirect_matches * 0.1, 0.2)

        # Business impact relevance
        business_matches = sum(1 for kw in self.RELEVANCE_KEYWORDS['business_impact']
                               if kw in text_lower)
        score += min(business_matches * 0.08, 0.2)

        # Risk/opportunity indicators
        risk_matches = sum(1 for kw in self.RELEVANCE_KEYWORDS['risk_indicators']
                           if kw in text_lower)
        opportunity_matches = sum(1 for kw in self.RELEVANCE_KEYWORDS['opportunity_indicators']
                                  if kw in text_lower)
        score += min((risk_matches + opportunity_matches) * 0.05, 0.2)

        return min(score, 1.0)
