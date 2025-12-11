"""
FRED (Federal Reserve Economic Data) Processor
Handles processing of economic indicator data for MRO market intelligence
"""

import logging
from typing import List

from mro_intelligence.config.clients import ClientSector
from mro_intelligence.core.processors.base import BaseProcessor, IntelligenceItem

logger = logging.getLogger(__name__)


class FREDProcessor(BaseProcessor):
    """Processor for Federal Reserve Economic Data observations - MRO market focused"""

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

        # Percentage values
        if series_id in ["DFF", "DGS10", "MORTGAGE30US", "FEDFUNDS", "UNRATE", "A191RL1Q225SBEA", "PCEPILFE", "T10Y2Y"]:
            return f"{value:.2f}%"

        # Dollar per barrel (crude oil)
        elif series_id == "DCOILWTICO":
            return f"${value:.2f}/barrel"

        # Index values
        elif series_id in ["INDPRO", "IPMAN", "PPIACO", "WPU101"]:
            return f"{value:.1f} (Index)"

        # Housing/permits (thousands of units)
        elif series_id in ["HOUST", "PERMIT"]:
            return f"{value:.0f}K units"

        # Construction spending (millions)
        elif series_id in ["TLRESCONS", "TLNRESCONS"]:
            return f"${value/1000:.1f}B"

        # Durable goods orders (millions)
        elif series_id == "DGORDER":
            return f"${value/1000:.1f}B"

        # Manufacturing sales
        elif series_id == "CMRMTSPL":
            return f"${value/1000:.1f}B"

        # GDP values
        elif series_id == "GDP":
            if value > 1000:
                return f"${value/1000:.2f}T"
            else:
                return f"${value:.1f}B"

        # Employment (thousands)
        elif series_id in ["PAYEMS", "MANEMP", "USCONS"]:
            return f"{value/1000:.1f}M workers"

        # Business confidence (centered at 0)
        elif series_id == "BSCICP02USM460S":
            if value > 0:
                return f"+{value:.2f} (optimistic)"
            elif value < 0:
                return f"{value:.2f} (pessimistic)"
            else:
                return "0.00 (neutral)"

        return f"{value:.2f}"

    def _calculate_relevance(self, observation) -> float:
        """Calculate relevance score for FRED data based on MRO market importance"""
        series_id = observation.series_id
        category = observation.category
        score = 0.5

        # Tier 1: Highest relevance - Direct MRO demand indicators
        if series_id in ["INDPRO", "IPMAN", "DGORDER"]:
            score += 0.4  # Industrial production directly drives MRO demand

        # Tier 2: High relevance - Construction and employment
        elif series_id in ["TLNRESCONS", "HOUST", "PERMIT", "MANEMP", "USCONS"]:
            score += 0.35

        # Tier 3: Important - Cost and inflation indicators
        elif series_id in ["PPIACO", "WPU101", "DCOILWTICO", "PCEPILFE"]:
            score += 0.3

        # Tier 4: Relevant - Interest rates and business conditions
        elif series_id in ["FEDFUNDS", "DFF", "DGS10", "MORTGAGE30US", "UNRATE", "T10Y2Y"]:
            score += 0.25

        # Tier 5: General economic indicators
        elif series_id in ["GDP", "A191RL1Q225SBEA", "PAYEMS", "CMRMTSPL"]:
            score += 0.2

        # Category-based adjustments
        if category == "industrial_activity":
            score += 0.1
        elif category == "construction":
            score += 0.1
        elif category == "commodities":
            score += 0.05

        return min(score, 1.0)

    def _generate_so_what(self, observation) -> str:
        """Generate contextual MRO market impact statement for FRED economic data"""
        series_id = observation.series_id
        value = observation.value

        # Industrial Activity Indicators
        if series_id == "INDPRO":
            return "Industrial Production Index directly reflects manufacturing activity - changes signal corresponding shifts in MRO consumables, spare parts, and maintenance supply demand."

        elif series_id == "IPMAN":
            return "Manufacturing production levels drive core MRO demand for industrial supplies, safety equipment, and plant maintenance products."

        elif series_id == "CMRMTSPL":
            return "Real manufacturing sales indicate overall industrial economic health and downstream demand for MRO products across the supply chain."

        elif series_id == "DGORDER":
            if value > 0:
                return "Rising durable goods orders signal increased manufacturing capital investment - expect growing demand for equipment maintenance and industrial supplies."
            else:
                return "Declining durable goods orders suggest manufacturing pullback - monitor for softening MRO demand in equipment-intensive categories."

        # Construction Indicators
        elif series_id == "TLRESCONS":
            return "Residential construction spending drives demand for contractor tools, fasteners, electrical supplies, and building materials."

        elif series_id == "TLNRESCONS":
            return "Nonresidential construction spending is a major driver for heavy equipment, industrial supplies, and commercial building products."

        elif series_id == "HOUST":
            if value > 1400:
                return "Strong housing starts indicate robust residential construction activity - expect sustained demand for building supplies and contractor equipment."
            elif value < 1000:
                return "Weak housing starts signal slowing residential construction - monitor for reduced demand in building materials and tools."
            else:
                return "Housing starts at moderate levels suggest steady but not accelerating construction supply demand."

        elif series_id == "PERMIT":
            return "Building permits are a leading indicator of future construction activity - rising permits signal upcoming demand for construction supplies and equipment."

        # Business Conditions
        elif series_id == "UNRATE":
            if value < 4.0:
                return "Low unemployment indicates strong labor market and robust industrial activity, supporting MRO demand but potentially creating labor cost pressures."
            elif value > 6.0:
                return "Elevated unemployment signals economic weakness - expect reduced manufacturing activity and potential softening of MRO demand."
            else:
                return "Unemployment at moderate levels reflects balanced labor market conditions with stable industrial demand."

        elif series_id == "PCEPILFE":
            if value > 3.0:
                return "Elevated core inflation pressures industrial product costs and margins - review pricing strategies and supplier contracts."
            else:
                return "Moderate inflation environment supports stable pricing for industrial products and MRO supplies."

        elif series_id == "FEDFUNDS" or series_id == "DFF":
            if value > 5.0:
                return "Elevated interest rates increase equipment financing costs, potentially delaying capital equipment purchases and shifting spend toward maintenance and repair."
            else:
                return "Lower interest rates support equipment investment decisions and working capital availability for industrial customers."

        elif series_id == "T10Y2Y":
            if value < 0:
                return "Inverted yield curve signals recession risk - prepare for potential reduction in industrial activity and MRO demand."
            elif value < 0.5:
                return "Flat yield curve suggests economic uncertainty - monitor industrial customer spending patterns closely."
            else:
                return "Normal yield curve indicates stable economic outlook supporting continued industrial investment."

        # Commodities and Costs
        elif series_id == "PPIACO":
            return "Producer Price Index reflects wholesale cost pressures across industrial products - rising PPI signals margin pressure and potential pricing adjustments."

        elif series_id == "WPU101":
            return "Iron and steel prices directly impact manufacturing and construction costs - changes flow through to fasteners, tools, and metal products."

        elif series_id == "DCOILWTICO":
            if value > 90:
                return "High crude oil prices increase transportation and logistics costs, affecting product delivery and petroleum-based supplies."
            elif value < 50:
                return "Low crude oil prices reduce energy and transportation costs, potentially improving margins on logistics-intensive products."
            else:
                return "Moderate crude oil prices support predictable operational and transportation cost structures."

        # Interest Rates
        elif series_id == "DGS10":
            return "Long-term Treasury rates influence equipment financing decisions and construction project economics."

        elif series_id == "MORTGAGE30US":
            if value > 7.0:
                return "High mortgage rates constrain residential construction activity - expect softer demand for building supplies and residential contractor tools."
            else:
                return "Moderate mortgage rates support residential construction activity and related MRO demand."

        # GDP and Growth
        elif series_id == "A191RL1Q225SBEA":
            if value > 2.5:
                return "Strong GDP growth indicates expanding industrial activity across all sectors - position for increased MRO demand."
            elif value < 0:
                return "Economic contraction signals reduced industrial activity - monitor for softening demand across MRO categories."
            else:
                return "Moderate economic growth supports steady industrial demand patterns."

        elif series_id == "GDP":
            return "Overall GDP levels reflect total economic activity and aggregate demand for industrial products and services."

        # Employment
        elif series_id == "PAYEMS":
            return "Total employment levels indicate overall economic health and consumer spending capacity."

        elif series_id == "MANEMP":
            return "Manufacturing employment directly reflects sector health - rising employment signals growing MRO demand from expanding operations."

        elif series_id == "USCONS":
            return "Construction employment indicates sector activity levels - rising construction jobs signal sustained demand for building supplies and tools."

        # Business Confidence
        elif series_id == "BSCICP02USM460S":
            if value > 1:
                return "Strong manufacturing confidence suggests increasing capital investment and maintenance spending - expect rising MRO demand."
            elif value < -1:
                return "Weak manufacturing confidence signals potential pullback in industrial investment - monitor for demand softening."
            else:
                return "Neutral manufacturing confidence indicates stable but cautious industrial spending environment."

        return "Economic indicator warrants monitoring for potential MRO demand implications."

    def _map_to_sectors(self, observation) -> List[ClientSector]:
        """Map FRED data to affected Grainger customer segments"""
        series_id = observation.series_id

        # Industrial Production - Manufacturing customers primary
        if series_id in ["INDPRO", "IPMAN", "DGORDER", "CMRMTSPL"]:
            return [ClientSector.MANUFACTURING, ClientSector.GENERAL]

        # Construction indicators - Contractors segment
        elif series_id in ["TLRESCONS", "TLNRESCONS", "HOUST", "PERMIT", "MORTGAGE30US"]:
            return [ClientSector.CONTRACTORS, ClientSector.GENERAL]

        # Employment - sector-specific
        elif series_id == "MANEMP":
            return [ClientSector.MANUFACTURING, ClientSector.GENERAL]
        elif series_id == "USCONS":
            return [ClientSector.CONTRACTORS, ClientSector.GENERAL]
        elif series_id in ["UNRATE", "PAYEMS"]:
            return [ClientSector.MANUFACTURING, ClientSector.CONTRACTORS, ClientSector.GENERAL]

        # Interest rates - affect contractors and equipment financing
        elif series_id in ["DFF", "DGS10", "FEDFUNDS"]:
            return [ClientSector.CONTRACTORS, ClientSector.MANUFACTURING, ClientSector.GENERAL]

        # Commodities - affect manufacturing and contractors
        elif series_id == "DCOILWTICO":
            return [ClientSector.MANUFACTURING, ClientSector.CONTRACTORS, ClientSector.GENERAL]
        elif series_id in ["PPIACO", "WPU101", "PCU3311133111", "WPU102501", "PALUMUSDM"]:
            return [ClientSector.MANUFACTURING, ClientSector.CONTRACTORS, ClientSector.GENERAL]

        # Government spending - Government segment ($2B+)
        elif series_id in ["FGEXPND", "FDEFX"]:
            return [ClientSector.GOVERNMENT, ClientSector.GENERAL]

        # Inflation affects all
        elif series_id in ["PCEPILFE"]:
            return [ClientSector.GENERAL, ClientSector.MANUFACTURING]

        # Yield curve - economic outlook
        elif series_id == "T10Y2Y":
            return [ClientSector.GENERAL]

        # GDP affects all segments
        elif series_id in ["GDP", "A191RL1Q225SBEA"]:
            return [ClientSector.GENERAL, ClientSector.MANUFACTURING, ClientSector.CONTRACTORS]

        # Business confidence - manufacturing focus
        elif series_id == "BSCICP02USM460S":
            return [ClientSector.MANUFACTURING, ClientSector.GENERAL]

        return [ClientSector.GENERAL]

    def _generate_action_items(self, observation, sectors: List[ClientSector]) -> List[str]:
        """Generate action items based on FRED data for MRO market"""
        series_id = observation.series_id
        actions = []

        # Industrial Activity indicators
        if series_id in ["INDPRO", "IPMAN"]:
            actions.append("Monitor industrial production trends for MRO demand signals")
            actions.append("Update demand forecasts based on manufacturing activity")
            actions.append("Review inventory levels in manufacturing-related categories")

        elif series_id == "DGORDER":
            actions.append("Track durable goods orders as leading indicator of equipment maintenance demand")
            actions.append("Assess capital equipment product positioning based on order trends")

        elif series_id == "CMRMTSPL":
            actions.append("Monitor manufacturing sales for overall industrial demand trends")

        # Construction indicators
        elif series_id in ["TLRESCONS", "TLNRESCONS"]:
            actions.append("Adjust construction supplies inventory based on spending trends")
            actions.append("Review contractor account activity in affected regions")

        elif series_id in ["HOUST", "PERMIT"]:
            actions.append("Use permits and starts data to forecast construction supply demand")
            actions.append("Position inventory for anticipated construction activity")

        # Interest rates
        elif series_id in ["DFF", "DGS10", "FEDFUNDS"]:
            actions.append("Assess impact of financing costs on equipment purchase decisions")
            actions.append("Monitor customer capex plans for rate sensitivity")
            if ClientSector.CONTRACTORS in sectors:
                actions.append("Track construction project financing impacts")

        elif series_id == "MORTGAGE30US":
            actions.append("Monitor residential construction activity based on mortgage trends")
            actions.append("Adjust building supplies forecasts for housing market changes")

        # Commodities and costs
        elif series_id == "DCOILWTICO":
            actions.append("Review transportation and logistics cost assumptions")
            actions.append("Monitor petroleum-based product pricing")

        elif series_id in ["PPIACO", "WPU101"]:
            actions.append("Review pricing strategy based on input cost trends")
            actions.append("Assess supplier cost pass-through impacts")

        elif series_id == "PCEPILFE":
            actions.append("Review pricing strategy for inflation environment")
            actions.append("Assess impact on product margins")

        # Employment
        elif series_id in ["UNRATE", "PAYEMS"]:
            actions.append("Monitor labor market for industrial staffing trends")
            actions.append("Assess impact on customer spending patterns")

        elif series_id == "MANEMP":
            actions.append("Track manufacturing employment as demand indicator")
            actions.append("Adjust manufacturing sector coverage strategy")

        elif series_id == "USCONS":
            actions.append("Monitor construction employment for sector activity")
            actions.append("Review construction account coverage strategy")

        # Yield curve
        elif series_id == "T10Y2Y":
            actions.append("Monitor yield curve for economic outlook signals")
            actions.append("Prepare contingency plans for potential economic shifts")

        # GDP
        elif series_id in ["GDP", "A191RL1Q225SBEA"]:
            actions.append("Adjust demand forecasts based on economic growth trends")
            actions.append("Review capacity planning for projected activity levels")

        # Business confidence
        elif series_id == "BSCICP02USM460S":
            actions.append("Use manufacturing confidence as leading demand indicator")
            actions.append("Adjust sales strategy based on customer sentiment trends")

        if not actions:
            actions.append("Monitor economic indicator for operational impacts")
            actions.append("Brief relevant sectors on trend implications")

        return actions[:3]
