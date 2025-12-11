"""
GTA (Global Trade Alert) Processor
Handles processing of trade intervention data
"""

import logging
from datetime import datetime
from typing import List

from solairus_intelligence.config.clients import ClientSector
from solairus_intelligence.core.processors.base import IntelligenceItem, BaseProcessor

logger = logging.getLogger(__name__)


class GTAProcessor(BaseProcessor):
    """Processor for Global Trade Alert intervention data"""

    # GTA sector taxonomy mapping to client sectors
    GTA_SECTOR_MAPPING = {
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
            'crude oil', 'natural gas'
        ],
        ClientSector.HEALTHCARE: [
            'healthcare', 'pharmaceutical', 'medical', 'health',
            'drugs', 'medicine', 'biotechnology', 'clinical'
        ]
    }

    def process_intervention(self, intervention, category: str = "trade_intervention") -> IntelligenceItem:
        """Convert a GTA intervention into an IntelligenceItem"""
        raw_content = intervention.description
        processed_content = intervention.get_short_description(400)
        relevance_score = self._calculate_relevance(intervention)
        so_what = self._generate_so_what(intervention)
        affected_sectors = self._map_to_sectors(intervention)
        action_items = self._generate_action_items(intervention, affected_sectors)
        confidence = 0.9 if intervention.sources else 0.8

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
            source_type="gta",
            gta_intervention_id=intervention.intervention_id,
            gta_implementing_countries=intervention.get_implementing_countries(),
            gta_affected_countries=intervention.get_affected_countries(),
            date_implemented=intervention.date_implemented,
            date_announced=intervention.date_announced
        )

    def _calculate_relevance(self, intervention) -> float:
        """Calculate relevance score for GTA intervention"""
        score = 0.5

        if intervention.gta_evaluation in ["Harmful", "Red"]:
            score += 0.3
        elif intervention.gta_evaluation == "Liberalising":
            score += 0.2

        # Check aviation relevance
        affected_sectors = intervention.affected_sectors if intervention.affected_sectors else []
        sector_strings = [str(s).lower() for s in affected_sectors if s]

        aviation_adjacent = ['aviation', 'aerospace', 'aircraft', 'petroleum', 'fuel',
                            'kerosene', 'air transport', 'airport', 'pilot']
        is_aviation_relevant = any(keyword in ' '.join(sector_strings) for keyword in aviation_adjacent)

        if is_aviation_relevant:
            score += 0.2

        # Freshness scoring
        if intervention.date_implemented:
            try:
                date_str = intervention.date_implemented
                impl_date = None

                for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                            "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        impl_date = datetime.strptime(
                            date_str.replace('Z', '').split('+')[0].split('.')[0],
                            fmt.replace('.%f', '').replace('Z', '').replace('%z', '')
                        )
                        break
                    except ValueError:
                        continue

                if impl_date is None:
                    impl_date = datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))

                days_old = (datetime.now() - impl_date).days

                if days_old < 30:
                    score += 0.3
                elif days_old < 60:
                    score += 0.2
                elif days_old < 90:
                    score += 0.1
                elif days_old < 180:
                    score += 0.0
                elif days_old < 365:
                    score += 0.0 if is_aviation_relevant else -0.1
                else:
                    score += 0.0 if is_aviation_relevant else -0.2

            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Could not parse GTA date '{intervention.date_implemented}': {e}")

        return min(score, 1.0)

    def _generate_so_what(self, intervention) -> str:
        """Generate 'So What' statement for GTA intervention"""
        impl_countries = intervention.get_implementing_countries()
        affected_countries = intervention.get_affected_countries()
        intervention_type_str = str(intervention.intervention_type) if intervention.intervention_type else ""
        intervention_type_lower = intervention_type_str.lower()

        if 'sanction' in intervention_type_lower or 'export' in intervention_type_lower:
            if impl_countries:
                return f"Trade restrictions from {', '.join(impl_countries[:2])} may affect supply chains, client operations, and routing decisions for affected regions."
            return "Export controls and sanctions require immediate compliance review and may impact client travel patterns."

        elif 'tariff' in intervention_type_lower or 'import' in intervention_type_lower:
            return "Tariff changes signal shifting trade relationships that may affect business aviation demand patterns and cross-border operations."

        elif 'capital' in intervention_type_lower:
            if affected_countries:
                return f"Capital controls in {', '.join(affected_countries[:2])} may restrict client financial flows and impact business travel demand from these markets."
            return "Financial restrictions may constrain client liquidity for aviation services and international operations."

        elif 'technology' in intervention_type_lower or 'local content' in intervention_type_lower:
            return "Technology sector restrictions directly impact Silicon Valley and tech clients' international operations and travel requirements."

        elif 'subsidy' in intervention_type_lower or 'grant' in intervention_type_lower:
            return "Government support measures signal economic policy direction and competitive landscape changes in affected sectors."

        else:
            if intervention.gta_evaluation == "Harmful":
                return "This trade intervention represents increased barriers to international business that may affect client operations and travel needs."
            elif intervention.gta_evaluation == "Liberalising":
                return "This liberalizing measure may create new business opportunities and increase demand for international travel services."
            return "This trade policy change warrants monitoring for potential impacts on client operations and aviation services."

    def _map_to_sectors(self, intervention) -> List[ClientSector]:
        """Map GTA intervention to affected client sectors"""
        sectors = set()
        affected_sectors = intervention.affected_sectors if intervention.affected_sectors else []
        sector_strings = [str(s) for s in affected_sectors if s]
        sector_text = ' '.join(sector_strings).lower()

        for client_sector, keywords in self.GTA_SECTOR_MAPPING.items():
            if any(kw in sector_text for kw in keywords):
                sectors.add(client_sector)

        if not sectors:
            sectors.add(ClientSector.GENERAL)

        return list(sectors)

    def _generate_action_items(self, intervention, sectors: List[ClientSector]) -> List[str]:
        """Generate actionable items based on GTA intervention"""
        actions = []
        intervention_type_str = str(intervention.intervention_type) if intervention.intervention_type else ""
        intervention_type_lower = intervention_type_str.lower()

        if 'sanction' in intervention_type_lower or 'export' in intervention_type_lower:
            actions.append("Conduct compliance review for all affected jurisdictions and update routing protocols")
            actions.append("Brief affected clients on travel restrictions and alternative routing options")
            actions.append("Review client list for exposure to sanctioned entities or regions")

        elif 'tariff' in intervention_type_lower:
            actions.append("Monitor for secondary impacts on client business operations and travel demand")
            actions.append("Assess potential effects on fuel costs and international operations")

        elif 'capital' in intervention_type_lower:
            actions.append("Review payment and billing procedures for affected jurisdictions")
            actions.append("Contact clients in affected markets to assess impact on travel budgets")

        elif 'technology' in intervention_type_lower:
            if ClientSector.TECHNOLOGY in sectors:
                actions.append("Proactively reach out to technology sector clients about operational impacts")
                actions.append("Monitor for changes in Silicon Valley travel patterns")

        if not actions:
            actions.append("Monitor situation and prepare briefing materials for affected clients")
            actions.append("Update market intelligence briefings with this development")

        return actions[:3]
