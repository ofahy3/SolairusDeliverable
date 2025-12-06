"""
Query Orchestrator for ErgoMind
Generates and manages strategic queries to extract maximum value from Flashpoints Forum data
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from solairus_intelligence.clients.ergomind_client import (
    ErgoMindClient,
    QueryResult,
)
from solairus_intelligence.core.processor import (
    ClientSector,
    IntelligenceItem,
    IntelligenceProcessor,
)

logger = logging.getLogger(__name__)


@dataclass
class QueryTemplate:
    """Template for a strategic query"""

    category: str
    query: str
    follow_ups: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher is more important
    sectors: List[ClientSector] = field(default_factory=list)


class QueryOrchestrator:
    """
    Orchestrates intelligent queries to ErgoMind based on Flashpoints Forum focus areas
    """

    def __init__(self, client: Optional[ErgoMindClient] = None):
        self.client = client or ErgoMindClient()
        self.processor = IntelligenceProcessor()
        self.query_templates = self._initialize_query_templates()

    def _initialize_query_templates(self) -> List[QueryTemplate]:
        """
        Initialize strategic query templates for Flashpoints Forum data
        These are carefully crafted to extract maximum geopolitical/economic intelligence
        """

        # Get current month for temporal queries
        now = datetime.now()
        current_month = now.strftime("%B %Y")
        # Calculate 6 months ago for time constraint
        from dateutil.relativedelta import relativedelta
        six_months_ago = (now - relativedelta(months=6)).strftime("%B %Y")

        # Time constraint to add to queries - ensures ErgoMind only provides recent data
        time_constraint = f" Only include information from {six_months_ago} to present. Do not include any events or data older than 6 months."

        templates = [
            # TIER 1: Critical Aviation & Business Travel Intelligence
            QueryTemplate(
                category="aviation_security",
                query=f"What geopolitical developments in {current_month} have impacted international aviation security, airspace restrictions, or flight routing?{time_constraint}",
                follow_ups=[
                    f"Which regions have new or modified airspace restrictions?{time_constraint}",
                    f"What are the implications for business jet operations?{time_constraint}",
                ],
                priority=10,
                sectors=[ClientSector.GENERAL],
            ),
            QueryTemplate(
                category="sanctions_trade",
                query=f"Summarize all new sanctions, trade restrictions, and export controls implemented in {current_month} that affect international business.{time_constraint}",
                follow_ups=[
                    f"Which countries and sectors are most affected?{time_constraint}",
                    f"What are the compliance requirements for aviation operators?{time_constraint}",
                ],
                priority=9,
                sectors=[ClientSector.GENERAL, ClientSector.TECHNOLOGY, ClientSector.FINANCE],
            ),
            QueryTemplate(
                category="economic_indicators",
                query=f"What key economic indicators and central bank decisions from {current_month} signal changes in business aviation demand?{time_constraint}",
                follow_ups=[
                    f"How are interest rate changes affecting corporate travel budgets?{time_constraint}",
                    f"Which regions show strongest economic growth or contraction?{time_constraint}",
                ],
                priority=9,
                sectors=[ClientSector.FINANCE, ClientSector.REAL_ESTATE],
            ),
            # TIER 2: Regional Geopolitical Assessments
            QueryTemplate(
                category="north_america",
                query=f"Analyze the key political and economic developments in North America during {current_month}, focusing on impacts to corporate aviation and cross-border business.{time_constraint}",
                follow_ups=[
                    f"What regulatory changes affect business aviation?{time_constraint}",
                    f"How are US-Mexico-Canada relations affecting corporate travel?{time_constraint}",
                ],
                priority=8,
                sectors=[ClientSector.GENERAL],
            ),
            QueryTemplate(
                category="europe",
                query=f"What were the significant European political, regulatory, and economic changes in {current_month} that impact business aviation and corporate travel?{time_constraint}",
                follow_ups=[
                    f"How are EU regulations affecting aviation operations?{time_constraint}",
                    f"What is the impact of energy costs on European aviation?{time_constraint}",
                ],
                priority=8,
                sectors=[ClientSector.GENERAL, ClientSector.ENERGY],
            ),
            QueryTemplate(
                category="asia_pacific",
                query=f"Summarize Asia-Pacific geopolitical tensions and economic developments from {current_month}, with focus on China relations and regional stability.{time_constraint}",
                follow_ups=[
                    f"How are US-China tensions affecting technology sector travel?{time_constraint}",
                    f"What are the implications for Pacific route planning?{time_constraint}",
                ],
                priority=8,
                sectors=[ClientSector.TECHNOLOGY, ClientSector.FINANCE],
            ),
            QueryTemplate(
                category="middle_east",
                query=f"Assess Middle East stability, energy markets, and regional conflicts in {current_month} and their impact on aviation operations.{time_constraint}",
                follow_ups=[
                    f"Which airspaces face heightened security risks?{time_constraint}",
                    f"How are energy prices affecting aviation fuel costs?{time_constraint}",
                ],
                priority=7,
                sectors=[ClientSector.ENERGY, ClientSector.GENERAL],
            ),
            # TIER 3: Sector-Specific Intelligence
            QueryTemplate(
                category="technology_sector",
                query=f"What geopolitical factors in {current_month} specifically impacted the global technology sector, including semiconductor supply chains, data sovereignty, and tech regulation?{time_constraint}",
                follow_ups=[
                    f"How are export controls affecting US tech companies?{time_constraint}",
                    f"What are the implications for Silicon Valley business travel?{time_constraint}",
                ],
                priority=7,
                sectors=[ClientSector.TECHNOLOGY],
            ),
            QueryTemplate(
                category="financial_sector",
                query=f"Analyze financial market volatility, banking sector developments, and investment trends from {current_month} that affect private equity and capital markets.{time_constraint}",
                follow_ups=[
                    f"What is the outlook for M&A activity?{time_constraint}",
                    f"How are regulatory changes affecting private equity?{time_constraint}",
                ],
                priority=7,
                sectors=[ClientSector.FINANCE],
            ),
            QueryTemplate(
                category="real_estate_sector",
                query=f"What were the key developments in global real estate markets, construction costs, and infrastructure investment during {current_month}?{time_constraint}",
                follow_ups=[
                    f"How are interest rates affecting real estate development?{time_constraint}",
                    f"What are the supply chain impacts on construction?{time_constraint}",
                ],
                priority=6,
                sectors=[ClientSector.REAL_ESTATE],
            ),
            QueryTemplate(
                category="entertainment_sector",
                query=f"Summarize entertainment industry developments, content regulation changes, and talent mobility issues from {current_month}.{time_constraint}",
                follow_ups=[
                    f"What are the implications for international productions?{time_constraint}",
                    f"How are visa policies affecting talent movement?{time_constraint}",
                ],
                priority=5,
                sectors=[ClientSector.ENTERTAINMENT],
            ),
            # TIER 4: Forward-Looking Intelligence
            QueryTemplate(
                category="risk_forecast",
                query=f"Based on {current_month} developments, what are the top geopolitical and economic risks for international business aviation in the next 3-6 months?{time_constraint}",
                follow_ups=[
                    f"Which regions face highest instability risk?{time_constraint}",
                    f"What contingency planning is recommended?{time_constraint}",
                ],
                priority=8,
                sectors=[ClientSector.GENERAL],
            ),
            QueryTemplate(
                category="opportunity_forecast",
                query=f"What emerging opportunities and positive trends from {current_month} suggest growth potential for business aviation and corporate travel?{time_constraint}",
                follow_ups=[
                    f"Which markets show strongest recovery or growth?{time_constraint}",
                    f"What sectors are increasing travel investment?{time_constraint}",
                ],
                priority=7,
                sectors=[ClientSector.GENERAL],
            ),
            # TIER 5: Specialized Topics
            QueryTemplate(
                category="sustainability_climate",
                query=f"What climate policies, sustainability regulations, and ESG developments from {current_month} affect aviation operations and corporate travel policies?{time_constraint}",
                follow_ups=[
                    f"What are the implications for carbon offsetting?{time_constraint}",
                    f"How are sustainable aviation fuel mandates evolving?{time_constraint}",
                ],
                priority=6,
                sectors=[ClientSector.GENERAL],
            ),
            QueryTemplate(
                category="cybersecurity",
                query=f"Summarize cybersecurity threats, data breaches, and digital infrastructure risks from {current_month} that could impact aviation and corporate operations.{time_constraint}",
                follow_ups=[
                    f"What are the implications for aviation IT systems?{time_constraint}",
                    f"How should operators enhance cyber defenses?{time_constraint}",
                ],
                priority=6,
                sectors=[ClientSector.TECHNOLOGY, ClientSector.GENERAL],
            ),
        ]

        return templates

    async def execute_monthly_intelligence_gathering(self) -> Dict[str, List[QueryResult]]:
        """
        Execute the full monthly intelligence gathering process with parallel query execution
        Returns organized results by category
        """
        results = {}

        # Sort templates by priority (highest first)
        sorted_templates = sorted(self.query_templates, key=lambda x: x.priority, reverse=True)

        logger.info(
            f"Starting parallel intelligence gathering with {len(sorted_templates)} query templates"
        )

        async with self.client:
            # Test connection first
            if not await self.client.test_connection():
                logger.error("Failed to connect to ErgoMind")
                return results

            # Create semaphore to limit concurrent queries (max 3 at once for rate limiting)
            semaphore = asyncio.Semaphore(3)

            # Create tasks for all templates
            async def execute_template_with_semaphore(
                template: QueryTemplate,
            ) -> Tuple[str, List[QueryResult]]:
                """Execute a single template's queries with semaphore control"""
                async with semaphore:
                    logger.info(
                        f"Processing category: {template.category} (Priority: {template.priority})"
                    )

                    category_results = []

                    # Execute main query
                    main_result = await self.client.query_websocket(template.query)
                    if main_result.success:
                        category_results.append(main_result)

                        # If main query successful and has good confidence, ask follow-ups
                        if main_result.confidence_score > 0.6 and template.follow_ups:
                            for follow_up in template.follow_ups[
                                :2
                            ]:  # Limit follow-ups to avoid overload
                                await asyncio.sleep(
                                    1
                                )  # Reduced from 2s since we have semaphore control
                                follow_result = await self.client.query_websocket(follow_up)
                                if follow_result.success:
                                    category_results.append(follow_result)

                    # Small delay between template batches
                    await asyncio.sleep(1)
                    return template.category, category_results

            # Execute all templates in parallel (controlled by semaphore)
            tasks = [execute_template_with_semaphore(template) for template in sorted_templates]

            # Gather all results
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in completed_results:
                if isinstance(result, Exception):
                    logger.error(f"Query failed with exception: {result}")
                else:
                    category, category_results = result
                    if category_results:
                        results[category] = category_results

        logger.info(
            f"Parallel intelligence gathering complete. Collected {sum(len(v) for v in results.values())} responses"
        )
        return results

    async def process_and_filter_results(
        self, raw_results: Dict[str, List[QueryResult]]
    ) -> List[IntelligenceItem]:
        """
        Process raw results and filter for quality and relevance
        Enhanced to extract multiple items from rich ErgoMind responses
        """
        processed_items = []

        for category, results in raw_results.items():
            for result in results:
                # Handle both QueryResult objects and cached dict data
                if isinstance(result, dict):
                    success = result.get("success", True)
                    response = result.get("response", "")
                else:
                    success = result.success
                    response = result.response

                if success and response:
                    response_text = response

                    # Split long responses into multiple items
                    # ErgoMind often returns multiple topics in one response
                    sections = []

                    # Try numbered lists first (1. 2. 3.)
                    if "\n1." in response_text or "\n2." in response_text:
                        # Split on numbered items
                        import re

                        parts = re.split(r"\n\d+\.", response_text)
                        sections = [p.strip() for p in parts if len(p.strip()) > 100]
                    # Try bullet points with dash
                    elif response_text.count("\n- ") >= 2:
                        parts = response_text.split("\n- ")
                        sections = [p.strip() for p in parts if len(p.strip()) > 100]
                    # Try double newlines (paragraph breaks)
                    elif response_text.count("\n\n") >= 2:
                        parts = response_text.split("\n\n")
                        sections = [p.strip() for p in parts if len(p.strip()) > 150]
                    else:
                        # Keep as single item if no clear sections
                        sections = [response_text]

                    # Process each section as a separate intelligence item
                    for section in sections:
                        if len(section.strip()) > 100:  # Minimum content length
                            item = self.processor.process_intelligence(
                                section.strip(), category=category
                            )
                            item.sources = result.sources

                            # More permissive filtering - use OR instead of AND
                            if item.relevance_score > 0.25 or item.confidence > 0.4:
                                processed_items.append(item)

        # Remove duplicates based on content similarity
        unique_items = []
        for item in processed_items:
            is_duplicate = False
            for existing in unique_items:
                # Check if content is substantially similar (first 100 chars match)
                if len(item.processed_content) > 100 and len(existing.processed_content) > 100:
                    if (
                        item.processed_content[:100].lower()
                        == existing.processed_content[:100].lower()
                    ):
                        is_duplicate = True
                        break
            if not is_duplicate:
                unique_items.append(item)

        # Sort by relevance score
        unique_items.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(
            f"Processed {len(unique_items)} unique intelligence items from {len(processed_items)} total items"
        )
        return unique_items

    async def generate_focused_queries(
        self, focus_areas: Optional[List[str]] = None
    ) -> List[QueryTemplate]:
        """
        Generate focused queries based on specific areas of interest
        """
        if not focus_areas:
            return self.query_templates

        focused_templates = []

        for area in focus_areas:
            area_lower = area.lower()

            # Find matching templates
            for template in self.query_templates:
                if area_lower in template.category.lower() or any(
                    area_lower in q.lower() for q in [template.query] + template.follow_ups
                ):
                    focused_templates.append(template)

        return focused_templates if focused_templates else self.query_templates

    def optimize_query_order(self, templates: List[QueryTemplate]) -> List[QueryTemplate]:
        """
        Optimize query order to maximize information gain and minimize redundancy
        """
        # Group by related topics to maintain context
        groups = {"regional": [], "sectoral": [], "thematic": [], "forecast": []}

        for template in templates:
            if any(
                region in template.category for region in ["america", "europe", "asia", "middle"]
            ):
                groups["regional"].append(template)
            elif any(sector.value in template.category for sector in ClientSector):
                groups["sectoral"].append(template)
            elif "forecast" in template.category:
                groups["forecast"].append(template)
            else:
                groups["thematic"].append(template)

        # Combine in logical order: thematic -> regional -> sectoral -> forecast
        optimized = []
        for group in ["thematic", "regional", "sectoral", "forecast"]:
            # Sort within group by priority
            group_templates = sorted(groups[group], key=lambda x: x.priority, reverse=True)
            optimized.extend(group_templates)

        return optimized

    # =====================================================================
    # GTA (Global Trade Alert) Intelligence Gathering Methods
    # =====================================================================

    async def execute_gta_intelligence_gathering(self, days_back: int = 60) -> Dict[str, List]:
        """
        Execute GTA queries in parallel to gather trade intervention intelligence

        Args:
            days_back: Number of days to look back for interventions

        Returns:
            Dictionary mapping categories to lists of GTAIntervention objects
        """
        from solairus_intelligence.clients.gta_client import GTAClient

        logger.info(f"Starting GTA intelligence gathering ({days_back} days)")

        results = {}

        async with GTAClient() as gta_client:
            # Test GTA connection
            if not await gta_client.test_connection():
                logger.error("Failed to connect to GTA API")
                return results

            # Execute multiple GTA queries in parallel
            query_tasks = {
                "sanctions_trade": gta_client.get_sanctions_and_export_controls(
                    days=days_back, limit=20
                ),
                "capital_controls": gta_client.get_capital_controls(days=days_back, limit=15),
                "technology_restrictions": gta_client.get_technology_restrictions(
                    days=days_back, limit=15
                ),
                "aviation_sector": gta_client.get_aviation_sector_interventions(days=90, limit=10),
                "harmful_interventions": gta_client.get_recent_harmful_interventions(
                    days=days_back, limit=20
                ),
                "immigration_visa": gta_client.get_immigration_visa_restrictions(
                    days=days_back, limit=15
                ),
            }

            # Execute all queries in parallel
            query_results = await asyncio.gather(*query_tasks.values(), return_exceptions=True)

            # Map results back to categories
            for (category, _), result in zip(query_tasks.items(), query_results):
                if isinstance(result, Exception):
                    logger.error(f"GTA query failed for {category}: {result}")
                    results[category] = []
                else:
                    results[category] = result
                    logger.info(f"GTA {category}: Retrieved {len(result)} interventions")

        total_interventions = sum(len(v) for v in results.values())
        logger.info(
            f"GTA intelligence gathering complete. Collected {total_interventions} interventions"
        )

        return results

    async def process_gta_results(self, gta_results: Dict[str, List]) -> List[IntelligenceItem]:
        """
        Process GTA interventions into IntelligenceItem objects

        Args:
            gta_results: Dictionary of GTA interventions by category

        Returns:
            List of processed IntelligenceItem objects
        """
        processed_items = []

        for category, interventions in gta_results.items():
            for intervention in interventions:
                try:
                    # Use intelligence processor to convert GTA intervention
                    item = self.processor.process_gta_intervention(intervention, category=category)

                    # Apply relevance filtering (stricter threshold to exclude stale data)
                    if item.relevance_score > 0.4:
                        processed_items.append(item)

                except Exception as e:
                    logger.error(
                        f"Failed to process GTA intervention {intervention.intervention_id}: {e}"
                    )
                    continue

        # Remove duplicates based on intervention ID
        unique_items = []
        seen_ids = set()

        for item in processed_items:
            if item.gta_intervention_id and item.gta_intervention_id not in seen_ids:
                unique_items.append(item)
                seen_ids.add(item.gta_intervention_id)

        # Sort by relevance
        unique_items.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(
            f"Processed {len(unique_items)} unique GTA intelligence items from {len(processed_items)} total"
        )

        return unique_items

    async def execute_fred_data_gathering(self, days_back: int = 90) -> Dict[str, List]:
        """
        Execute FRED API queries to gather economic indicator data

        Args:
            days_back: Number of days to look back for observations

        Returns:
            Dictionary mapping categories to lists of FREDObservation objects
        """
        from solairus_intelligence.clients.fred_client import FREDClient, FREDConfig

        logger.info(f"Starting FRED economic data gathering ({days_back} days)")

        results = {}

        config = FREDConfig()
        if not config.api_key:
            logger.warning("FRED_API_KEY not set - skipping FRED data gathering")
            logger.info("Get free API key from: https://fred.stlouisfed.org/docs/api/api_key.html")
            return results

        async with FREDClient(config) as fred_client:
            # Test FRED connection
            if not await fred_client.test_connection():
                logger.error("Failed to connect to FRED API")
                return results

            # Execute FRED queries for different categories
            try:
                # Gather all categories in parallel
                inflation_task = fred_client.get_inflation_indicators(days_back=days_back)
                rates_task = fred_client.get_interest_rate_data(days_back=days_back)
                fuel_task = fred_client.get_aviation_fuel_costs(days_back=days_back)
                gdp_task = fred_client.get_gdp_growth_data(days_back=180)  # Quarterly data
                confidence_task = fred_client.get_business_confidence_data(days_back=365)  # Monthly OECD data

                inflation, rates, fuel, gdp, confidence = await asyncio.gather(
                    inflation_task, rates_task, fuel_task, gdp_task, confidence_task,
                    return_exceptions=True
                )

                # Store results
                if not isinstance(inflation, Exception):
                    results["inflation"] = inflation
                    logger.info(f"FRED inflation: Retrieved {len(inflation)} indicators")
                if not isinstance(rates, Exception):
                    results["interest_rates"] = rates
                    logger.info(f"FRED interest rates: Retrieved {len(rates)} indicators")
                if not isinstance(fuel, Exception):
                    results["fuel_costs"] = fuel
                    logger.info(f"FRED fuel costs: Retrieved {len(fuel)} indicators")
                if not isinstance(gdp, Exception):
                    results["gdp_growth"] = gdp
                    logger.info(f"FRED GDP growth: Retrieved {len(gdp)} indicators")
                if not isinstance(confidence, Exception):
                    results["business_confidence"] = confidence
                    logger.info(f"FRED business confidence: Retrieved {len(confidence)} indicators")

            except Exception as e:
                logger.error(f"FRED data gathering error: {str(e)}")

        total_observations = sum(len(v) for v in results.values())
        logger.info(
            f"FRED data gathering complete. Collected {total_observations} economic indicators"
        )

        return results

    async def process_fred_results(self, fred_results: Dict[str, List]) -> List[IntelligenceItem]:
        """
        Process FRED observations into IntelligenceItem objects

        Args:
            fred_results: Dictionary of FRED observations by category

        Returns:
            List of processed IntelligenceItem objects
        """
        processed_items = []

        for category, observations in fred_results.items():
            for observation in observations:
                try:
                    # Process each FRED observation into an IntelligenceItem
                    item = self.processor.process_fred_observation(observation, category)
                    processed_items.append(item)
                    logger.debug(
                        f"Processed FRED {category}: {observation.series_name} = {observation.value}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to process FRED observation {observation.series_id}: {str(e)}"
                    )
                    continue

        logger.info(f"Processed {len(processed_items)} FRED intelligence items")

        return processed_items

    async def execute_multi_source_intelligence_gathering(
        self,
        test_mode: bool = False,
        gta_days_back: int = 60,
        fred_days_back: int = 90,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute ErgoMind, GTA, and FRED queries in parallel

        Args:
            test_mode: If True, uses limited queries for testing
            gta_days_back: Number of days to look back for GTA interventions
            fred_days_back: Number of days to look back for FRED data
            use_cache: If True, use cached results when available

        Returns:
            Dictionary with 'ergomind', 'gta', and 'fred' results
        """
        from solairus_intelligence.utils.cache import get_cache

        cache = get_cache()

        logger.info("=" * 60)
        logger.info("MULTI-SOURCE INTELLIGENCE GATHERING (ErgoMind + GTA + FRED)")
        logger.info("=" * 60)

        # Check cache for each source
        cache_params = {
            "gta_days": gta_days_back,
            "fred_days": fred_days_back,
            "test_mode": test_mode,
        }

        ergomind_results = None
        gta_results = None
        fred_results = None

        if use_cache:
            ergomind_results = cache.get("ergomind", cache_params)
            gta_results = cache.get("gta", cache_params)
            fred_results = cache.get("fred", cache_params)

            cache_hits = sum(
                1 for r in [ergomind_results, gta_results, fred_results] if r is not None
            )
            if cache_hits > 0:
                logger.info(f"Cache: {cache_hits}/3 sources loaded from cache")

        # Execute only non-cached sources
        tasks_to_run = []
        task_names = []

        if ergomind_results is None:
            tasks_to_run.append(self.execute_monthly_intelligence_gathering())
            task_names.append("ergomind")
        if gta_results is None:
            tasks_to_run.append(self.execute_gta_intelligence_gathering(days_back=gta_days_back))
            task_names.append("gta")
        if fred_results is None:
            tasks_to_run.append(self.execute_fred_data_gathering(days_back=fred_days_back))
            task_names.append("fred")

        # Execute pending tasks in parallel
        if tasks_to_run:
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

            # Map results back to sources
            result_idx = 0
            if "ergomind" in task_names:
                ergomind_results = results[result_idx]
                result_idx += 1
            if "gta" in task_names:
                gta_results = results[result_idx]
                result_idx += 1
            if "fred" in task_names:
                fred_results = results[result_idx]

        # Handle exceptions gracefully and track source status
        source_status = {"ergomind": "success", "gta": "success", "fred": "success"}

        if isinstance(ergomind_results, Exception):
            logger.error(f"❌ ErgoMind gathering failed: {ergomind_results}")
            ergomind_results = {}
            source_status["ergomind"] = "failed"
        else:
            logger.info(f"✓ ErgoMind: {sum(len(v) for v in ergomind_results.values())} responses")
            # Cache successful results (only if freshly fetched)
            if use_cache and "ergomind" in task_names and ergomind_results:
                cache.set("ergomind", cache_params, ergomind_results)

        if isinstance(gta_results, Exception):
            logger.error(f"❌ GTA gathering failed: {gta_results}")
            gta_results = {}
            source_status["gta"] = "failed"
        else:
            logger.info(f"✓ GTA: {sum(len(v) for v in gta_results.values())} interventions")
            # Cache successful results (only if freshly fetched)
            if use_cache and "gta" in task_names and gta_results:
                cache.set("gta", cache_params, gta_results)

        if isinstance(fred_results, Exception):
            logger.error(f"❌ FRED gathering failed: {fred_results}")
            fred_results = {}
            source_status["fred"] = "failed"
        else:
            logger.info(f"✓ FRED: {sum(len(v) for v in fred_results.values())} economic indicators")
            # Cache successful results (only if freshly fetched)
            if use_cache and "fred" in task_names and fred_results:
                cache.set("fred", cache_params, fred_results)

        # Log overall source status
        logger.info(
            f"\nSource Status: ErgoMind {'✓' if source_status['ergomind'] == 'success' else '✗'}, "
            + f"GTA {'✓' if source_status['gta'] == 'success' else '✗'}, "
            + f"FRED {'✓' if source_status['fred'] == 'success' else '✗'}"
        )

        return {
            "ergomind": ergomind_results,
            "gta": gta_results,
            "fred": fred_results,
            "source_status": source_status,  # Add status tracking
        }

    # Maintain backward compatibility


async def test_query_orchestrator():
    """Test the query orchestrator"""
    orchestrator = QueryOrchestrator()

    # Test with a subset of queries
    print("Testing Query Orchestrator...")
    print(f"Loaded {len(orchestrator.query_templates)} query templates\n")

    # Show some sample queries
    print("Sample High-Priority Queries:")
    high_priority = [t for t in orchestrator.query_templates if t.priority >= 8]
    for template in high_priority[:3]:
        print(f"\nCategory: {template.category}")
        print(f"Priority: {template.priority}")
        print(f"Query: {template.query[:100]}...")
        print(f"Sectors: {[s.value for s in template.sectors]}")


if __name__ == "__main__":
    asyncio.run(test_query_orchestrator())
