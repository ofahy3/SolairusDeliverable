"""
Query Templates for MRO Intelligence Gathering

Grainger-specific query templates organized by priority tier:
- Tier 1: Jenna's explicit questions (tariffs, MRO outlook, steel, pricing)
- Tier 1.5: China tariff exposure (20% COGS from China)
- Tier 2: Customer segment intelligence (manufacturing, government, contractors)
- Tier 3: Commodity pricing (aluminum, energy)
- Tier 4: Competitive intelligence (Amazon Business threat)
- Tier 5: Risk/opportunity forecasting
- Tier 6: Regulatory and safety
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from mro_intelligence.config.clients import ClientSector
from mro_intelligence.config.grainger_profile import REPORT_SETTINGS


@dataclass
class QueryTemplate:
    """Template for a strategic query"""

    category: str
    query: str
    follow_ups: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher is more important
    sectors: List[ClientSector] = field(default_factory=list)


def build_query_templates() -> List[QueryTemplate]:
    """
    Build strategic query templates for Flashpoints Forum data.

    These are carefully crafted to extract MRO market-relevant geopolitical/economic intelligence.
    Uses Grainger configuration for lookback period and geographic focus.
    """
    from dateutil.relativedelta import relativedelta

    # Get current month for temporal queries
    now = datetime.now()
    current_month = now.strftime("%B %Y")

    # Use configurable lookback period from Grainger profile
    lookback_months = REPORT_SETTINGS.get("lookback_months", 3)
    lookback_start = (now - relativedelta(months=lookback_months)).strftime("%B %Y")

    # Time constraint to add to queries - uses Grainger's 3-month lookback
    time_constraint = (
        f" Only include information from {lookback_start} to present. "
        f"Do not include any events or data older than {lookback_months} months. "
        f"Focus on US domestic and USMCA region developments."
    )

    return [
        # =================================================================
        # TIER 1: JENNA'S EXPLICIT QUESTIONS (Priority 10)
        # These are the questions Jenna Anderson explicitly asked for
        # =================================================================
        QueryTemplate(
            category="tariffs_mro_impact",
            query=f"What's happening with tariffs that would impact the US MRO market? Include any new Section 301, Section 232, or other tariff changes affecting industrial goods, equipment, and materials.{time_constraint}",
            follow_ups=[
                f"How are current tariff changes affecting industrial supply pricing?{time_constraint}",
                f"What pricing strategies should MRO distributors consider?{time_constraint}",
            ],
            priority=10,
            sectors=[ClientSector.MANUFACTURING, ClientSector.CONTRACTORS, ClientSector.GENERAL],
        ),
        QueryTemplate(
            category="us_mro_outlook",
            query=f"What are the outlooks for the US MRO market? Include manufacturing activity, construction spending, and industrial demand trends.{time_constraint}",
            follow_ups=[
                f"Which MRO product categories are seeing strongest demand?{time_constraint}",
                f"What are the leading indicators for MRO demand in the next 90 days?{time_constraint}",
            ],
            priority=10,
            sectors=[ClientSector.MANUFACTURING, ClientSector.CONTRACTORS, ClientSector.GENERAL],
        ),
        QueryTemplate(
            category="steel_mro_demand",
            query=f"What will happen to the price of steel, and how does that affect MRO market demand? Include steel tariffs, supply dynamics, and impact on manufacturing/construction activity.{time_constraint}",
            follow_ups=[
                f"What manufacturing sectors are most sensitive to steel costs?{time_constraint}",
                f"How do steel tariffs impact construction project economics and timing?{time_constraint}",
            ],
            priority=10,
            sectors=[ClientSector.MANUFACTURING, ClientSector.CONTRACTORS],
        ),
        QueryTemplate(
            category="pricing_strategy",
            query=f"How should industrial MRO distributors approach pricing pass-through given current tariff and commodity cost changes? What pricing strategies are competitors using?{time_constraint}",
            follow_ups=[
                f"What are the pricing elasticity dynamics in MRO distribution?{time_constraint}",
                f"How are suppliers adjusting their pricing to distributors?{time_constraint}",
            ],
            priority=10,
            sectors=[ClientSector.MANUFACTURING, ClientSector.CONTRACTORS],
        ),
        # =================================================================
        # TIER 1.5: CHINA TARIFF EXPOSURE (Priority 9)
        # Grainger sources 20% of COGS from China - critical to track
        # =================================================================
        QueryTemplate(
            category="china_tariff_exposure",
            query=f"What tariff changes on Chinese industrial goods will impact US MRO distributors? Focus on Section 301 tariffs, industrial supplies, and manufacturing equipment sourced from China.{time_constraint}",
            follow_ups=[
                f"How are tariffs affecting the price of industrial supplies sourced from China?{time_constraint}",
                f"What supply chain shifts are occurring as companies reduce China sourcing exposure?{time_constraint}",
            ],
            priority=9,
            sectors=[ClientSector.MANUFACTURING, ClientSector.GENERAL],
        ),
        QueryTemplate(
            category="china_sourcing_shifts",
            query=f"What supply chain shifts are occurring as US companies diversify away from China sourcing? Track nearshoring to Mexico, Vietnam alternatives, and domestic reshoring.{time_constraint}",
            follow_ups=[
                f"Which product categories are most affected by China-US trade tensions?{time_constraint}",
                f"What is the timeline for supply chain restructuring?{time_constraint}",
            ],
            priority=9,
            sectors=[ClientSector.MANUFACTURING, ClientSector.GENERAL],
        ),
        # =================================================================
        # TIER 2: GRAINGER CUSTOMER SEGMENT INTELLIGENCE
        # Tailored to Grainger's actual customer base
        # =================================================================
        QueryTemplate(
            category="manufacturing_demand",
            query=f"Analyze manufacturing sector trends in {current_month}, including reshoring initiatives, automation investments, factory construction, and production volumes that drive MRO consumables demand.{time_constraint}",
            follow_ups=[
                f"What regions are seeing new manufacturing facility investments?{time_constraint}",
                f"How are production levels affecting maintenance and spare parts demand?{time_constraint}",
            ],
            priority=9,
            sectors=[ClientSector.MANUFACTURING],
        ),
        QueryTemplate(
            category="government_spending",
            query=f"What federal, state, and military spending developments in {current_month} affect MRO procurement? Include defense budget, infrastructure spending, and government facility maintenance.{time_constraint}",
            follow_ups=[
                f"What defense procurement opportunities are emerging?{time_constraint}",
                f"How are federal budget dynamics affecting government MRO contracts?{time_constraint}",
            ],
            priority=9,
            sectors=[ClientSector.GOVERNMENT],
        ),
        QueryTemplate(
            category="contractor_activity",
            query=f"What were the construction and contractor activity trends in {current_month}? Include housing starts, building permits, commercial construction, and infrastructure project pipeline.{time_constraint}",
            follow_ups=[
                f"How are interest rates and materials costs affecting project economics?{time_constraint}",
                f"What is the outlook for skilled trades labor availability?{time_constraint}",
            ],
            priority=9,
            sectors=[ClientSector.CONTRACTORS],
        ),
        QueryTemplate(
            category="commercial_facilities",
            query=f"What commercial real estate and facilities management trends from {current_month} affect MRO demand? Include office occupancy, retail activity, healthcare expansion, and building maintenance.{time_constraint}",
            follow_ups=[
                f"How are return-to-office trends affecting commercial facility maintenance?{time_constraint}",
                f"What building code or efficiency mandates are driving equipment upgrades?{time_constraint}",
            ],
            priority=8,
            sectors=[ClientSector.COMMERCIAL_FACILITIES],
        ),
        QueryTemplate(
            category="capex_activity",
            query=f"What is the outlook for discretionary capital projects and new construction that drive MRO demand? Include capex trends, project delays/cancellations, and investment sentiment.{time_constraint}",
            follow_ups=[
                f"Which sectors are delaying or accelerating capital expenditures?{time_constraint}",
                f"What is the outlook for industrial construction starts?{time_constraint}",
            ],
            priority=9,
            sectors=[ClientSector.COMMERCIAL_FACILITIES, ClientSector.CONTRACTORS],
        ),
        # =================================================================
        # TIER 3: COMMODITY PRICING INTELLIGENCE
        # Steel and aluminum explicitly important per Jenna
        # =================================================================
        QueryTemplate(
            category="aluminum_pricing",
            query=f"What are the aluminum price trends and outlook? How do aluminum costs affect industrial product pricing and MRO demand?{time_constraint}",
            follow_ups=[
                f"How are aluminum tariffs affecting manufacturing costs?{time_constraint}",
                f"What is the supply outlook for aluminum products?{time_constraint}",
            ],
            priority=8,
            sectors=[ClientSector.MANUFACTURING, ClientSector.CONTRACTORS],
        ),
        QueryTemplate(
            category="energy_logistics_costs",
            query=f"Summarize oil, diesel, and logistics cost trends from {current_month} and their implications for industrial distribution operations.{time_constraint}",
            follow_ups=[
                f"How are energy costs affecting manufacturing and logistics operations?{time_constraint}",
                f"What is the outlook for shipping and freight costs?{time_constraint}",
            ],
            priority=8,
            sectors=[ClientSector.MANUFACTURING, ClientSector.CONTRACTORS, ClientSector.GENERAL],
        ),
        # =================================================================
        # TIER 4: COMPETITIVE INTELLIGENCE
        # Amazon Business is Grainger's biggest disruptor ($25B sales)
        # =================================================================
        QueryTemplate(
            category="competitive_landscape",
            query=f"How are digital-first competitors changing pricing and service expectations in industrial distribution? Include Amazon Business, online marketplaces, and B2B ecommerce trends.{time_constraint}",
            follow_ups=[
                f"What are the implications of Amazon Business expansion in MRO?{time_constraint}",
                f"How are traditional distributors responding to digital competition?{time_constraint}",
            ],
            priority=7,
            sectors=[ClientSector.MANUFACTURING, ClientSector.GENERAL],
        ),
        # =================================================================
        # TIER 5: RISK AND OPPORTUNITY FORECAST
        # =================================================================
        QueryTemplate(
            category="supply_chain_risks",
            query=f"What geopolitical developments in {current_month} have disrupted or threaten to disrupt industrial supply chains, manufacturing inputs, or raw materials affecting the US market?{time_constraint}",
            follow_ups=[
                f"Which supply chain vulnerabilities require immediate attention?{time_constraint}",
                f"What contingency planning is recommended for procurement?{time_constraint}",
            ],
            priority=8,
            sectors=[ClientSector.MANUFACTURING, ClientSector.GENERAL],
        ),
        QueryTemplate(
            category="risk_forecast",
            query=f"Based on {current_month} developments, what are the top risks for US industrial supply chains and MRO demand in the next 90 days?{time_constraint}",
            follow_ups=[
                f"What contingency planning should MRO distributors consider?{time_constraint}",
                f"Which product categories face the highest supply risk?{time_constraint}",
            ],
            priority=8,
            sectors=[ClientSector.GENERAL],
        ),
        QueryTemplate(
            category="opportunity_forecast",
            query=f"What emerging opportunities from {current_month} suggest growth potential for US industrial MRO products and services?{time_constraint}",
            follow_ups=[
                f"Which industrial sectors are increasing capital investment?{time_constraint}",
                f"What regions show strongest industrial growth?{time_constraint}",
            ],
            priority=7,
            sectors=[ClientSector.GENERAL],
        ),
        # =================================================================
        # TIER 6: REGULATORY AND SAFETY
        # =================================================================
        QueryTemplate(
            category="safety_regulations",
            query=f"What OSHA, EPA, and other regulatory changes from {current_month} affect industrial safety equipment and compliance requirements?{time_constraint}",
            follow_ups=[
                f"What new PPE or safety equipment requirements are being implemented?{time_constraint}",
                f"How are environmental regulations affecting industrial operations?{time_constraint}",
            ],
            priority=7,
            sectors=[ClientSector.MANUFACTURING, ClientSector.CONTRACTORS, ClientSector.GENERAL],
        ),
    ]
