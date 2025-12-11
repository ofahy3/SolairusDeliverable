"""
GTA (Global Trade Alert) Processor
Handles processing of trade intervention data for MRO market intelligence
"""

import logging
from datetime import datetime
from typing import List

from mro_intelligence.config.clients import ClientSector
from mro_intelligence.core.processors.base import BaseProcessor, IntelligenceItem

logger = logging.getLogger(__name__)


class GTAProcessor(BaseProcessor):
    """Processor for Global Trade Alert intervention data - Grainger MRO focused"""

    # GTA sector taxonomy mapping to Grainger's customer segments
    GTA_SECTOR_MAPPING = {
        ClientSector.MANUFACTURING: [
            "manufacturing",
            "industrial",
            "machinery",
            "equipment",
            "metal",
            "steel",
            "aluminum",
            "fabricated metal",
            "machine tools",
            "automation",
            "robotics",
            "automotive",
            "semiconductor",
            "electronic",
            "electrical equipment",
            "motors",
            "bearings",
            "pumps",
            "valves",
            "factory",
            "production",
        ],
        ClientSector.GOVERNMENT: [
            "defense",
            "military",
            "government",
            "federal",
            "public sector",
            "procurement",
            "national security",
            "security",
            "strategic",
            "infrastructure",
            "public works",
        ],
        ClientSector.COMMERCIAL_FACILITIES: [
            "commercial real estate",
            "office",
            "retail",
            "hospitality",
            "hotel",
            "hospital",
            "healthcare",
            "facility",
            "property management",
            "building maintenance",
            "hvac",
            "lighting",
            "janitorial",
        ],
        ClientSector.CONTRACTORS: [
            "construction",
            "building",
            "infrastructure",
            "cement",
            "concrete",
            "steel",
            "lumber",
            "timber",
            "wood",
            "plumbing",
            "electrical",
            "housing",
            "contractor",
            "renovation",
            "trades",
        ],
    }

    def process_intervention(
        self, intervention, category: str = "trade_intervention"
    ) -> IntelligenceItem:
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
            date_announced=intervention.date_announced,
        )

    def _calculate_relevance(self, intervention) -> float:
        """Calculate relevance score for GTA intervention - MRO focused"""
        score = 0.5

        if intervention.gta_evaluation in ["Harmful", "Red"]:
            score += 0.3
        elif intervention.gta_evaluation == "Liberalising":
            score += 0.2

        # Check MRO industrial relevance
        affected_sectors = intervention.affected_sectors if intervention.affected_sectors else []
        sector_strings = [str(s).lower() for s in affected_sectors if s]

        # MRO-relevant keywords
        mro_adjacent = [
            "industrial",
            "manufacturing",
            "machinery",
            "equipment",
            "steel",
            "metal",
            "construction",
            "building",
            "energy",
            "petroleum",
            "fuel",
            "transportation",
            "logistics",
            "agriculture",
            "farming",
        ]
        is_mro_relevant = any(
            keyword in " ".join(sector_strings) for keyword in mro_adjacent
        )

        if is_mro_relevant:
            score += 0.2

        # Freshness scoring
        if intervention.date_implemented:
            try:
                date_str = intervention.date_implemented
                impl_date = None

                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%d",
                    "%d/%m/%Y",
                    "%m/%d/%Y",
                ]:
                    try:
                        impl_date = datetime.strptime(
                            date_str.replace("Z", "").split("+")[0].split(".")[0],
                            fmt.replace(".%f", "").replace("Z", "").replace("%z", ""),
                        )
                        break
                    except ValueError:
                        continue

                if impl_date is None:
                    impl_date = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00").replace("+00:00", "")
                    )

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
                    score += 0.0 if is_mro_relevant else -0.1
                else:
                    score += 0.0 if is_mro_relevant else -0.2

            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Could not parse GTA date '{intervention.date_implemented}': {e}")

        return min(score, 1.0)

    def _generate_so_what(self, intervention) -> str:
        """Generate 'So What' statement for GTA intervention - MRO market focused"""
        impl_countries = intervention.get_implementing_countries()
        affected_countries = intervention.get_affected_countries()
        intervention_type_str = (
            str(intervention.intervention_type) if intervention.intervention_type else ""
        )
        intervention_type_lower = intervention_type_str.lower()

        if "sanction" in intervention_type_lower or "export" in intervention_type_lower:
            if impl_countries:
                return f"Trade restrictions from {', '.join(impl_countries[:2])} may disrupt industrial supply chains and require alternative sourcing strategies."
            return "Export controls may affect availability and pricing of industrial components and equipment."

        elif "tariff" in intervention_type_lower or "import" in intervention_type_lower:
            return "Tariff changes will affect import costs for industrial products - review pricing and inventory strategies for affected categories."

        elif "capital" in intervention_type_lower:
            if affected_countries:
                return f"Capital controls in {', '.join(affected_countries[:2])} may affect supplier payments and cross-border procurement operations."
            return "Financial restrictions may impact supplier relationships and international procurement."

        elif "steel" in intervention_type_lower or "metal" in intervention_type_lower:
            return "Steel and metals trade restrictions directly impact manufacturing and construction supply costs - monitor for pricing adjustments."

        elif "subsidy" in intervention_type_lower or "grant" in intervention_type_lower:
            return "Government support measures may shift competitive dynamics in affected industrial sectors."

        elif "local content" in intervention_type_lower:
            return "Local content requirements may affect sourcing strategies for products sold in or sourced from affected markets."

        else:
            if intervention.gta_evaluation == "Harmful":
                return "This trade barrier may increase costs or limit availability for industrial products in affected markets."
            elif intervention.gta_evaluation == "Liberalising":
                return "This trade liberalization may reduce costs or improve availability for industrial products."
            return "This trade policy change warrants monitoring for potential supply chain and pricing impacts."

    def _map_to_sectors(self, intervention) -> List[ClientSector]:
        """Map GTA intervention to affected MRO client sectors"""
        sectors = set()
        affected_sectors = intervention.affected_sectors if intervention.affected_sectors else []
        sector_strings = [str(s) for s in affected_sectors if s]
        sector_text = " ".join(sector_strings).lower()

        for client_sector, keywords in self.GTA_SECTOR_MAPPING.items():
            if any(kw in sector_text for kw in keywords):
                sectors.add(client_sector)

        if not sectors:
            sectors.add(ClientSector.GENERAL)

        return list(sectors)

    def _generate_action_items(self, intervention, sectors: List[ClientSector]) -> List[str]:
        """Generate actionable items based on GTA intervention for MRO market"""
        actions = []
        intervention_type_str = (
            str(intervention.intervention_type) if intervention.intervention_type else ""
        )
        intervention_type_lower = intervention_type_str.lower()

        if "sanction" in intervention_type_lower or "export" in intervention_type_lower:
            actions.append(
                "Review supplier exposure to affected regions and identify alternative sources"
            )
            actions.append(
                "Assess inventory levels for products that may be affected by restrictions"
            )
            actions.append("Update procurement compliance procedures for new requirements")

        elif "tariff" in intervention_type_lower:
            actions.append(
                "Analyze cost impact on affected product categories and adjust pricing if needed"
            )
            actions.append("Review supplier contracts for tariff pass-through clauses")
            actions.append("Evaluate alternative sourcing options to mitigate tariff exposure")

        elif "capital" in intervention_type_lower:
            actions.append("Review payment terms with suppliers in affected markets")
            actions.append("Assess currency and payment risk for ongoing contracts")

        elif "steel" in intervention_type_lower or "metal" in intervention_type_lower:
            actions.append("Review pricing strategy for metal-intensive product categories")
            actions.append("Assess domestic sourcing alternatives for affected materials")

        # Sector-specific actions for Grainger's customer segments
        if ClientSector.MANUFACTURING in sectors:
            actions.append(
                "Brief manufacturing sector customers on potential supply chain impacts"
            )

        if ClientSector.GOVERNMENT in sectors:
            actions.append(
                "Assess impact on federal/defense procurement and GSA contracts"
            )

        if ClientSector.COMMERCIAL_FACILITIES in sectors:
            actions.append(
                "Monitor building maintenance product availability and pricing"
            )

        if ClientSector.CONTRACTORS in sectors:
            actions.append(
                "Monitor construction materials pricing for downstream effects"
            )

        if not actions:
            actions.append("Monitor developments and prepare customer communications if needed")
            actions.append("Update market intelligence tracking for this intervention")

        return actions[:3]
