"""
Intelligence Merger
Combines and deduplicates intelligence from multiple sources
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from solairus_intelligence.config.clients import ClientSector
from solairus_intelligence.core.processors.base import IntelligenceItem, SectorIntelligence

logger = logging.getLogger(__name__)


class IntelligenceMerger:
    """
    Intelligently merges multiple intelligence sources (ErgoMind, GTA, FRED)
    with deduplication and source priority handling
    """

    # Source weights for composite scoring
    SOURCE_WEIGHTS = {
        "ergomind": 1.15,  # 15% boost for narrative leadership
        "gta": 1.0,  # Neutral - valuable supporting data
        "fred": 0.95,  # Slight reduction to prevent top-score saturation
    }

    def merge_sources(self, *source_lists: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """
        Merge multiple intelligence sources with deduplication

        Args:
            *source_lists: Variable number of IntelligenceItem lists

        Returns:
            Merged and deduplicated list sorted by composite score
        """
        all_items = [item for source_list in source_lists for item in source_list]
        filtered_items = self._apply_freshness_filter(all_items)
        filtered_items.sort(key=self._calculate_composite_score, reverse=True)
        unique_items = self._deduplicate(filtered_items)
        prioritized_items = self._apply_source_priority(unique_items)

        return prioritized_items

    def _apply_freshness_filter(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Filter out stale data (6 months for GTA)"""
        six_months_ago = datetime.now() - timedelta(days=180)
        filtered = []

        for item in items:
            if item.source_type == "gta" and item.date_implemented:
                try:
                    impl_date = datetime.fromisoformat(
                        item.date_implemented.replace("Z", "+00:00").replace("T", " ")[:10]
                    )
                    if impl_date < six_months_ago:
                        continue
                except (ValueError, TypeError):
                    # Date parsing failed - include item anyway
                    pass

            filtered.append(item)

        return filtered

    def _calculate_composite_score(self, item: IntelligenceItem) -> float:
        """Calculate weighted score for sorting"""
        base_score = item.relevance_score * item.confidence
        source_weight = self.SOURCE_WEIGHTS.get(item.source_type, 1.0)

        # Freshness factor
        freshness_factor = 1.0
        if item.source_type == "gta" and item.date_implemented:
            try:
                impl_date = datetime.fromisoformat(item.date_implemented.replace("Z", "+00:00"))
                days_old = (datetime.now() - impl_date.replace(tzinfo=None)).days
                freshness_factor = 1.0 if days_old < 90 else 0.9
            except (ValueError, TypeError):
                pass  # Use default freshness_factor
        elif item.source_type == "fred" and item.fred_observation_date:
            try:
                obs_date = datetime.fromisoformat(item.fred_observation_date[:10])
                days_old = (datetime.now() - obs_date).days
                freshness_factor = 1.0 if days_old < 60 else 0.95
            except (ValueError, TypeError):
                pass  # Use default freshness_factor

        return base_score * freshness_factor * source_weight

    def _deduplicate(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Remove semantic duplicates"""
        unique_items: List[IntelligenceItem] = []
        seen_content_hashes: set[str] = set()

        for item in items:
            content_normalized = item.processed_content[:200].lower().strip()

            is_duplicate = False
            for existing_hash in seen_content_hashes:
                if self._calculate_similarity(content_normalized, existing_hash) > 0.75:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_items.append(item)
                seen_content_hashes.add(content_normalized)

        return unique_items

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate keyword-based similarity between two content strings"""
        stop_words = {"the", "and", "for", "this", "that", "with", "from", "have", "will", "are"}

        words1 = set(
            w.lower() for w in content1.split() if len(w) > 3 and w.lower() not in stop_words
        )
        words2 = set(
            w.lower() for w in content2.split() if len(w) > 3 and w.lower() not in stop_words
        )

        if not words1 or not words2:
            return 0.0

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
        economic_keywords = [
            "inflation",
            "interest rate",
            "gdp",
            "cpi",
            "federal reserve",
            "treasury",
            "mortgage",
        ]
        trade_keywords = ["tariff", "sanction", "export control", "trade barrier", "intervention"]

        prioritized_items: List[IntelligenceItem] = []
        topic_seen: Dict[str, set[str]] = {"economic": set(), "trade": set()}

        # First pass: Add high-priority sources for each topic
        for item in items:
            content_lower = item.processed_content.lower()

            if any(kw in content_lower for kw in economic_keywords):
                topic_key = "economic_" + content_lower[:50]
                if topic_key not in topic_seen["economic"]:
                    if item.source_type == "fred":
                        prioritized_items.append(item)
                        topic_seen["economic"].add(topic_key)

            elif any(kw in content_lower for kw in trade_keywords):
                topic_key = "trade_" + content_lower[:50]
                if topic_key not in topic_seen["trade"]:
                    if item.source_type == "gta":
                        prioritized_items.append(item)
                        topic_seen["trade"].add(topic_key)

            else:
                prioritized_items.append(item)

        # Second pass: Add remaining items
        for item in items:
            if item not in prioritized_items:
                prioritized_items.append(item)

        return prioritized_items

    def organize_by_sector(
        self, items: List[IntelligenceItem]
    ) -> Dict[ClientSector, SectorIntelligence]:
        """Organize intelligence items by client sector"""
        sector_intel = {}

        for sector in ClientSector:
            sector_items = [
                item
                for item in items
                if sector in item.affected_sectors or ClientSector.GENERAL in item.affected_sectors
            ]

            if sector_items:
                sector_items.sort(key=lambda x: x.relevance_score, reverse=True)

                summary = self._generate_sector_summary(sector, sector_items)
                risks = self._extract_risks(sector_items)
                opportunities = self._extract_opportunities(sector_items)

                sector_intel[sector] = SectorIntelligence(
                    sector=sector,
                    items=sector_items,
                    summary=summary,
                    key_risks=risks,
                    key_opportunities=opportunities,
                )

        return sector_intel

    def _generate_sector_summary(self, sector: ClientSector, items: List[IntelligenceItem]) -> str:
        """Generate a summary for a specific sector"""
        if not items:
            return "No significant developments identified this period."

        top_items = items[:3]
        summary_parts = [item.so_what_statement for item in top_items]
        return " ".join(summary_parts)

    def _extract_risks(self, items: List[IntelligenceItem]) -> List[str]:
        """Extract key risks from intelligence items"""
        risk_keywords = [
            "risk",
            "threat",
            "instability",
            "conflict",
            "sanctions",
            "crisis",
            "disruption",
            "uncertainty",
            "volatility",
            "tension",
        ]
        risks = []

        for item in items:
            text_lower = item.raw_content.lower()
            if any(kw in text_lower for kw in risk_keywords):
                if item.so_what_statement not in risks:
                    risks.append(item.so_what_statement)

        return risks[:3]

    def _extract_opportunities(self, items: List[IntelligenceItem]) -> List[str]:
        """Extract key opportunities from intelligence items"""
        opportunity_keywords = [
            "growth",
            "expansion",
            "opportunity",
            "emerging",
            "recovery",
            "improvement",
            "investment",
            "development",
            "innovation",
        ]
        opportunities = []

        for item in items:
            text_lower = item.raw_content.lower()
            if any(kw in text_lower for kw in opportunity_keywords):
                if item.so_what_statement not in opportunities:
                    opportunities.append(item.so_what_statement)

        return opportunities[:3]
