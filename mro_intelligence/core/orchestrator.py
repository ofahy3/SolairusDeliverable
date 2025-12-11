"""
Query Orchestrator for ErgoMind
Generates and manages strategic queries to extract maximum value from Flashpoints Forum data
for MRO market intelligence

Integrates Grainger-specific configuration for:
- Query filtering based on relevance to MRO market
- Geographic focus on US/USMCA region
- Sector prioritization for Grainger customer base
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from mro_intelligence.config.grainger_profile import (
    filter_for_grainger_relevance,
    get_grainger_config,
    get_lookback_months,
    get_minimum_relevance_score,
)
from mro_intelligence.clients.ergomind_client import (
    ErgoMindClient,
    QueryResult,
)
from mro_intelligence.core.processors.base import IntelligenceItem
from mro_intelligence.core.processors.ergomind import ErgoMindProcessor
from mro_intelligence.core.processors.fred import FREDProcessor
from mro_intelligence.core.processors.gta import GTAProcessor
from mro_intelligence.core.query_templates import QueryTemplate, build_query_templates

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """
    Orchestrates intelligent queries to ErgoMind based on Flashpoints Forum focus areas
    Optimized for MRO (Maintenance, Repair & Operations) market intelligence

    Integrates Grainger configuration for:
    - Lookback period from REPORT_SETTINGS
    - Relevance filtering based on RELEVANCE_FILTERS
    - Geographic focus on US/USMCA region
    """

    def __init__(self, client: Optional[ErgoMindClient] = None):
        self.client = client or ErgoMindClient()
        self.ergomind_processor = ErgoMindProcessor()
        self.gta_processor = GTAProcessor()
        self.fred_processor = FREDProcessor()
        self.query_templates = build_query_templates()

        # Load Grainger configuration
        self.grainger_config = get_grainger_config()
        self.lookback_months = get_lookback_months()
        self.min_relevance_score = get_minimum_relevance_score()

        logger.info(
            f"QueryOrchestrator initialized with Grainger config: "
            f"lookback={self.lookback_months}mo, min_relevance={self.min_relevance_score}"
        )

    async def execute_monthly_intelligence_gathering(self) -> Dict[str, List[QueryResult]]:
        """
        Execute the full monthly intelligence gathering process with parallel query execution
        Returns organized results by category
        """
        results: Dict[str, List[QueryResult]] = {}

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
                elif isinstance(result, tuple) and len(result) == 2:
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

        Enhanced to:
        - Extract multiple items from rich ErgoMind responses
        - Apply Grainger relevance filtering (exclude keywords, minimum score)
        - Boost relevance for US/USMCA and MRO-relevant content
        """
        processed_items = []
        grainger_config = get_grainger_config()

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
                            # Check for excluded content before processing
                            if grainger_config.should_exclude(section):
                                logger.debug(f"Excluding content based on Grainger filters")
                                continue

                            item = self.ergomind_processor.process_intelligence(
                                section.strip(), category=category
                            )
                            if item is not None:  # Validation may return None
                                item.sources = result.sources if hasattr(result, 'sources') else []

                                # Apply Grainger relevance boost
                                content_for_boost = section + " " + (item.so_what_statement or "")
                                relevance_boost = grainger_config.calculate_relevance_boost(content_for_boost)
                                item.relevance_score = min(item.relevance_score + relevance_boost, 1.0)

                                # More permissive filtering - use OR instead of AND
                                if item.relevance_score > 0.25 or item.confidence > 0.4:
                                    processed_items.append(item)

        # Remove duplicates based on content similarity
        unique_items: List[IntelligenceItem] = []
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

        # Apply Grainger relevance filter (minimum score threshold)
        filtered_items = filter_for_grainger_relevance(unique_items, self.min_relevance_score)

        # Sort by relevance score
        filtered_items.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(
            f"Processed {len(filtered_items)} Grainger-relevant items "
            f"from {len(unique_items)} unique ({len(processed_items)} total)"
        )
        return filtered_items

    async def execute_gta_intelligence_gathering(self, days_back: int = 60) -> Dict[str, List]:
        """
        Execute GTA queries in parallel to gather trade intervention intelligence

        Args:
            days_back: Number of days to look back for interventions

        Returns:
            Dictionary mapping categories to lists of GTAIntervention objects
        """
        from mro_intelligence.clients.gta_client import GTAClient

        logger.info(f"Starting GTA intelligence gathering ({days_back} days)")

        results: Dict[str, List[Any]] = {}

        async with GTAClient() as gta_client:
            # Test GTA connection
            if not await gta_client.test_connection():
                logger.error("Failed to connect to GTA API")
                return results

            # Execute multiple GTA queries in parallel - focused on MRO-relevant interventions
            query_tasks = {
                "tariffs_trade_policy": gta_client.get_sanctions_and_export_controls(
                    days=days_back, limit=20
                ),
                "capital_controls": gta_client.get_capital_controls(days=days_back, limit=15),
                "industrial_restrictions": gta_client.get_technology_restrictions(
                    days=days_back, limit=15
                ),
                "industrial_sector": gta_client.get_industrial_sector_interventions(days=90, limit=15),
                "harmful_interventions": gta_client.get_recent_harmful_interventions(
                    days=days_back, limit=20
                ),
                "labor_immigration": gta_client.get_immigration_visa_restrictions(
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
                elif isinstance(result, list):
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

        Applies Grainger relevance filtering:
        - Boosts US/USMCA interventions
        - Filters by minimum relevance score
        - Excludes non-MRO-relevant content
        """
        processed_items = []
        grainger_config = get_grainger_config()

        for category, interventions in gta_results.items():
            for intervention in interventions:
                try:
                    # Check for excluded content before processing
                    description = intervention.description if hasattr(intervention, 'description') else ""
                    if grainger_config.should_exclude(description):
                        logger.debug(f"Excluding GTA intervention based on Grainger filters")
                        continue

                    # Use intelligence processor to convert GTA intervention
                    item = self.gta_processor.process_intervention(intervention, category=category)

                    # Apply Grainger relevance boost for US/USMCA
                    content_for_boost = description + " " + (item.so_what_statement or "")
                    relevance_boost = grainger_config.calculate_relevance_boost(content_for_boost)
                    item.relevance_score = min(item.relevance_score + relevance_boost, 1.0)

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

        # Apply Grainger relevance filter
        filtered_items = filter_for_grainger_relevance(unique_items, self.min_relevance_score)

        # Sort by relevance
        filtered_items.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(
            f"Processed {len(filtered_items)} Grainger-relevant GTA items "
            f"from {len(unique_items)} unique ({len(processed_items)} total)"
        )

        return filtered_items

    async def execute_fred_data_gathering(self, days_back: int = 90) -> Dict[str, List]:
        """
        Execute FRED API queries to gather economic indicator data

        Args:
            days_back: Number of days to look back for observations

        Returns:
            Dictionary mapping categories to lists of FREDObservation objects
        """
        from mro_intelligence.clients.fred_client import FREDClient, FREDConfig

        logger.info(f"Starting FRED economic data gathering ({days_back} days)")

        results: Dict[str, List[Any]] = {}

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
                fuel_task = fred_client.get_industrial_fuel_costs(days_back=days_back)
                gdp_task = fred_client.get_gdp_growth_data(days_back=180)  # Quarterly data
                confidence_task = fred_client.get_business_confidence_data(
                    days_back=365
                )  # Monthly OECD data

                gathered_results = await asyncio.gather(
                    inflation_task,
                    rates_task,
                    fuel_task,
                    gdp_task,
                    confidence_task,
                    return_exceptions=True,
                )

                # Unpack with explicit typing
                inflation_result = gathered_results[0]
                rates_result = gathered_results[1]
                fuel_result = gathered_results[2]
                gdp_result = gathered_results[3]
                confidence_result = gathered_results[4]

                # Store results
                if not isinstance(inflation_result, Exception) and isinstance(
                    inflation_result, list
                ):
                    results["inflation"] = inflation_result
                    logger.info(f"FRED inflation: Retrieved {len(inflation_result)} indicators")
                if not isinstance(rates_result, Exception) and isinstance(rates_result, list):
                    results["interest_rates"] = rates_result
                    logger.info(f"FRED interest rates: Retrieved {len(rates_result)} indicators")
                if not isinstance(fuel_result, Exception) and isinstance(fuel_result, list):
                    results["fuel_costs"] = fuel_result
                    logger.info(f"FRED fuel costs: Retrieved {len(fuel_result)} indicators")
                if not isinstance(gdp_result, Exception) and isinstance(gdp_result, list):
                    results["gdp_growth"] = gdp_result
                    logger.info(f"FRED GDP growth: Retrieved {len(gdp_result)} indicators")
                if not isinstance(confidence_result, Exception) and isinstance(
                    confidence_result, list
                ):
                    results["business_confidence"] = confidence_result
                    logger.info(
                        f"FRED business confidence: Retrieved {len(confidence_result)} indicators"
                    )

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
                    item = self.fred_processor.process_observation(observation, category)
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
        from mro_intelligence.utils.cache import get_cache

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
        elif ergomind_results is not None and isinstance(ergomind_results, dict):
            logger.info(f"✓ ErgoMind: {sum(len(v) for v in ergomind_results.values())} responses")
            # Cache successful results (only if freshly fetched)
            if use_cache and "ergomind" in task_names and ergomind_results:
                cache.set("ergomind", cache_params, ergomind_results)

        if isinstance(gta_results, Exception):
            logger.error(f"❌ GTA gathering failed: {gta_results}")
            gta_results = {}
            source_status["gta"] = "failed"
        elif gta_results is not None and isinstance(gta_results, dict):
            logger.info(f"✓ GTA: {sum(len(v) for v in gta_results.values())} interventions")
            # Cache successful results (only if freshly fetched)
            if use_cache and "gta" in task_names and gta_results:
                cache.set("gta", cache_params, gta_results)

        if isinstance(fred_results, Exception):
            logger.error(f"❌ FRED gathering failed: {fred_results}")
            fred_results = {}
            source_status["fred"] = "failed"
        elif fred_results is not None and isinstance(fred_results, dict):
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
