"""
FRED (Federal Reserve Economic Data) Processor
Handles processing of economic indicator data
"""

import logging
from typing import List

from solairus_intelligence.config.clients import ClientSector
from solairus_intelligence.core.processors.base import IntelligenceItem, BaseProcessor

logger = logging.getLogger(__name__)


class FREDProcessor(BaseProcessor):
    """Processor for Federal Reserve Economic Data observations"""

    def process_observation(self, observation, category: str) -> IntelligenceItem:
        """Convert FRED economic data observation to IntelligenceItem"""
        formatted_value = self._format_value(observation)
        processed_content = f"{observation.series_name}: {formatted_value} as of {observation.date}"
        relevance_score = self._calculate_relevance(observation)
        so_what = self._generate_so_what(observation)
        affected_sectors = self._map_to_sectors(observation)
        action_items = self._generate_action_items(observation, affected_sectors)

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
            fred_value=observation.value,
        )

    def _format_value(self, observation) -> str:
        """Format FRED value based on series type"""
        series_id = observation.series_id
        value = observation.value

        if series_id in ["DFF", "DGS10", "MORTGAGE30US", "A191RL1Q225SBEA", "UNRATE"]:
            return f"{value:.2f}%"

        elif series_id in ["WJFUELUSGULF", "DCOILWTICO", "GASREGW"]:
            return (
                f"${value:.2f}/gallon"
                if "gallon" in observation.units.lower()
                else f"${value:.2f}/barrel"
            )

        elif "CPI" in series_id or "PCE" in series_id:
            return f"{value:.1f} (Index)"

        elif "GDP" in series_id:
            if value > 1000:
                return f"${value/1000:.2f}T"
            else:
                return f"${value:.1f}B"

        elif series_id == "PAYEMS":
            return f"{value/1000:.1f}M employees"

        return f"{value:.2f}"

    def _calculate_relevance(self, observation) -> float:
        """Calculate relevance score for FRED data"""
        series_id = observation.series_id
        category = observation.category
        score = 0.5

        if series_id == "WJFUELUSGULF":
            score += 0.4
        elif category == "interest_rates":
            score += 0.3
        elif category == "inflation":
            score += 0.25
        elif category == "gdp_growth":
            score += 0.2
        elif category == "employment":
            score += 0.15
        elif series_id in ["DCOILWTICO", "GASREGW"]:
            score += 0.25

        return min(score, 1.0)

    def _generate_so_what(self, observation) -> str:
        """Generate contextual impact statement for FRED economic data"""
        series_id = observation.series_id
        value = observation.value

        if series_id == "WJFUELUSGULF":
            if value > 3.00:
                return "Elevated jet fuel costs require immediate pricing strategy review and fuel hedging assessment to protect margins."
            elif value < 2.00:
                return "Lower jet fuel costs create opportunity for competitive pricing and margin expansion."
            else:
                return "Moderate jet fuel costs support current pricing models and operational budgets."

        elif series_id == "DCOILWTICO":
            if value > 90:
                return "High crude oil prices signal upcoming jet fuel cost pressure - monitor hedging opportunities."
            else:
                return "Stable crude oil prices support predictable operational cost structure."

        elif series_id == "DFF":
            if value > 5.0:
                return "Elevated interest rates increase aircraft financing costs, affecting acquisition timing and lease rate negotiations."
            else:
                return "Lower interest rates create favorable environment for aircraft acquisitions and refinancing."

        elif series_id == "DGS10":
            return "Treasury rate movements affect long-term aircraft financing costs and client capital allocation decisions."

        elif series_id == "MORTGAGE30US":
            return "Mortgage rate trends signal real estate sector activity levels, affecting property tour and site visit demand."

        elif "CPI" in series_id:
            if value > 300:
                return "Persistent inflation pressures will impact operational costs, requiring dynamic pricing strategies and contract adjustments."
            else:
                return "Inflation trends affect operational cost structure and client budget planning for business aviation."

        elif "GDP" in series_id:
            return "GDP trends signal overall business activity levels and corporate travel demand across all client sectors."

        elif series_id == "UNRATE":
            if value < 4.0:
                return "Low unemployment indicates strong economy and high business activity, supporting aviation demand."
            elif value > 6.0:
                return "Rising unemployment may signal reduced corporate travel budgets and discretionary aviation spending."
            else:
                return "Employment trends reflect economic health and business aviation demand patterns."

        return (
            "Economic indicator warrants monitoring for potential operational and demand impacts."
        )

    def _map_to_sectors(self, observation) -> List[ClientSector]:
        """Map FRED data to affected client sectors"""
        series_id = observation.series_id

        if series_id == "WJFUELUSGULF":
            return [ClientSector.GENERAL, ClientSector.ENERGY]
        elif series_id in ["DFF", "DGS10"]:
            return [ClientSector.FINANCE, ClientSector.REAL_ESTATE, ClientSector.GENERAL]
        elif series_id == "MORTGAGE30US":
            return [ClientSector.REAL_ESTATE, ClientSector.FINANCE]
        elif "CPI" in series_id or "PCE" in series_id:
            return [ClientSector.GENERAL]
        elif "GDP" in series_id:
            return [ClientSector.GENERAL]
        elif series_id in ["UNRATE", "PAYEMS"]:
            return [ClientSector.GENERAL]
        elif series_id == "DCOILWTICO":
            return [ClientSector.ENERGY, ClientSector.GENERAL]
        elif series_id == "GASREGW":
            return [ClientSector.GENERAL]

        return [ClientSector.GENERAL]

    def _generate_action_items(self, observation, sectors: List[ClientSector]) -> List[str]:
        """Generate action items based on FRED data"""
        series_id = observation.series_id
        actions = []

        if series_id == "WJFUELUSGULF":
            actions.append("Review fuel hedging strategy and pricing models")
            actions.append("Update cost projections for charter operations")
            actions.append("Brief clients on fuel cost trends affecting pricing")

        elif series_id in ["DFF", "DGS10"]:
            actions.append("Assess aircraft financing and refinancing opportunities")
            actions.append("Update financial projections for rate environment")
            if ClientSector.FINANCE in sectors:
                actions.append("Brief finance sector clients on capital cost impacts")

        elif series_id == "MORTGAGE30US":
            actions.append("Monitor real estate sector travel demand indicators")
            actions.append("Engage real estate clients on property tour scheduling")

        elif "CPI" in series_id:
            actions.append("Review operational cost structure and pricing strategy")
            actions.append("Update client contracts to reflect cost environment")

        elif "GDP" in series_id:
            actions.append("Adjust demand forecasts based on economic growth trends")
            actions.append("Review capacity planning for projected activity levels")

        elif series_id == "UNRATE":
            actions.append("Monitor corporate travel budget trends")
            actions.append("Adjust marketing strategy for economic environment")

        if not actions:
            actions.append("Monitor economic indicator for operational impacts")
            actions.append("Brief relevant client sectors on trend implications")

        return actions[:3]
