"""
Federal Reserve Economic Data (FRED) API Client
Provides MRO-relevant economic indicators to support intelligence with concrete data points
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import backoff

logger = logging.getLogger(__name__)


@dataclass
class FREDConfig:
    """Configuration for FRED API client"""

    api_key: str = field(default_factory=lambda: os.getenv("FRED_API_KEY", ""))
    base_url: str = "https://api.stlouisfed.org/fred"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class FREDObservation:
    """Represents a single FRED data observation"""

    series_id: str
    series_name: str
    value: float
    date: str
    units: str
    category: str  # Category grouping for the indicator


class FREDClient:
    """
    Client for Federal Reserve Economic Data (FRED) API
    Provides MRO market-relevant economic indicators to quantify intelligence
    """

    # Key economic series for MRO market intelligence
    # Grainger-specific commodities explicitly mentioned by Jenna Anderson (VP Strategy)
    SERIES = {
        # Industrial Activity - Key manufacturing and production indicators
        "industrial_activity": {
            "INDPRO": "Industrial Production Index",
            "IPMAN": "Industrial Production: Manufacturing",
            "CMRMTSPL": "Real Manufacturing and Trade Industries Sales",
            "DGORDER": "Manufacturers' New Orders: Durable Goods",
        },
        # Construction Sector - Building activity indicators (key for Contractors segment)
        "construction": {
            "TLRESCONS": "Total Construction Spending: Residential",
            "TLNRESCONS": "Total Construction Spending: Nonresidential",
            "HOUST": "Housing Starts",
            "PERMIT": "Building Permits",
        },
        # Business Conditions - General economic health
        "business_conditions": {
            "UNRATE": "Unemployment Rate",
            "PCEPILFE": "Core PCE Inflation (excluding food and energy)",
            "FEDFUNDS": "Federal Funds Effective Rate",
            "T10Y2Y": "10-Year Treasury Minus 2-Year (Yield Curve)",
        },
        # Grainger-Critical Commodities - Explicitly mentioned by Jenna as important to business
        # "Steel is really important" and "aluminum is really important to our business"
        "grainger_commodities": {
            # Steel - explicitly mentioned by Jenna
            "WPU101": "PPI: Iron and Steel",
            "PCU3311133111": "PPI: Steel Mill Products",
            # Aluminum - "really important to our business"
            "WPU102501": "PPI: Aluminum Mill Shapes",
            "PALUMUSDM": "Global Price of Aluminum",
            # Plastics - part of their product mix
            "WPU0721": "PPI: Plastic Products",
        },
        # General Commodities and Costs - Input cost indicators
        "commodities": {
            "PPIACO": "Producer Price Index: All Commodities",
            "DCOILWTICO": "Crude Oil Prices: West Texas Intermediate (WTI)",
        },
        # Interest Rates - Financing cost indicators (key for Contractors/construction)
        "interest_rates": {
            "DFF": "Federal Funds Effective Rate",
            "DGS10": "10-Year Treasury Constant Maturity Rate",
            "MORTGAGE30US": "30-Year Fixed Rate Mortgage Average",
        },
        # GDP and Growth
        "gdp_growth": {
            "A191RL1Q225SBEA": "Real GDP Growth Rate (Quarterly)",
            "GDP": "Gross Domestic Product",
        },
        # Employment
        "employment": {
            "PAYEMS": "Total Nonfarm Payrolls",
            "MANEMP": "Manufacturing Employment",
            "USCONS": "Construction Employment",
        },
        # Business Confidence
        "business_confidence": {
            "BSCICP02USM460S": "Business Confidence Index: Manufacturing for United States",
        },
        # Government Spending - Key for Government segment ($2B+ Grainger revenue)
        "government": {
            "FGEXPND": "Federal Government: Current Expenditures",
            "FDEFX": "Federal Government: National Defense Consumption Expenditures",
        },
    }

    # Human-readable descriptions for "So What" analysis
    SERIES_DESCRIPTIONS = {
        # Industrial Activity
        "INDPRO": {
            "name": "Industrial Production Index",
            "description": "Measures real output from manufacturing, mining, and utilities",
            "mro_impact": "Direct indicator of manufacturing activity and MRO consumables demand",
            "units": "Index 2017=100",
        },
        "IPMAN": {
            "name": "Manufacturing Production",
            "description": "Industrial production specifically from manufacturing sector",
            "mro_impact": "Key driver of demand for industrial supplies, safety equipment, and maintenance products",
            "units": "Index 2017=100",
        },
        "CMRMTSPL": {
            "name": "Real Manufacturing Sales",
            "description": "Inflation-adjusted sales from manufacturing and trade industries",
            "mro_impact": "Reflects overall industrial economic activity and downstream MRO demand",
            "units": "Millions of Chained 2017 Dollars",
        },
        "DGORDER": {
            "name": "Durable Goods Orders",
            "description": "New orders for long-lasting manufactured goods",
            "mro_impact": "Leading indicator of manufacturing capex and equipment maintenance needs",
            "units": "Millions of Dollars",
        },
        # Construction
        "TLRESCONS": {
            "name": "Residential Construction Spending",
            "description": "Total value of residential construction put in place",
            "mro_impact": "Drives demand for construction tools, fasteners, and building supplies",
            "units": "Millions of Dollars",
        },
        "TLNRESCONS": {
            "name": "Nonresidential Construction Spending",
            "description": "Commercial, industrial, and infrastructure construction spending",
            "mro_impact": "Major driver for heavy equipment, industrial supplies, and contractor tools",
            "units": "Millions of Dollars",
        },
        "HOUST": {
            "name": "Housing Starts",
            "description": "Number of new residential construction projects started",
            "mro_impact": "Leading indicator for residential construction supply demand",
            "units": "Thousands of Units",
        },
        "PERMIT": {
            "name": "Building Permits",
            "description": "Authorized building permits for new construction",
            "mro_impact": "Forward-looking indicator of construction activity and material needs",
            "units": "Thousands of Units",
        },
        # Business Conditions
        "UNRATE": {
            "name": "Unemployment Rate",
            "description": "Percentage of labor force that is unemployed",
            "mro_impact": "Affects labor availability for manufacturing and construction, influences overall economic demand",
            "units": "Percent",
        },
        "PCEPILFE": {
            "name": "Core PCE Inflation",
            "description": "Personal consumption expenditures price index excluding food and energy",
            "mro_impact": "Key inflation measure affecting industrial product pricing and margins",
            "units": "Percent Change from Year Ago",
        },
        "FEDFUNDS": {
            "name": "Federal Funds Rate",
            "description": "Interest rate at which banks lend reserves overnight",
            "mro_impact": "Impacts equipment financing costs and industrial capital investment decisions",
            "units": "Percent",
        },
        "T10Y2Y": {
            "name": "Yield Curve Spread",
            "description": "Difference between 10-year and 2-year Treasury yields",
            "mro_impact": "Economic outlook indicator - inversion often precedes recession and reduced industrial activity",
            "units": "Percent",
        },
        # Commodities
        "PPIACO": {
            "name": "Producer Price Index",
            "description": "Measures average change in prices received by domestic producers",
            "mro_impact": "Direct indicator of wholesale cost pressures for industrial products",
            "units": "Index 1982=100",
        },
        "WPU101": {
            "name": "Iron and Steel PPI",
            "description": "Producer price index for iron and steel products",
            "mro_impact": "Key input cost for manufacturing and construction - affects pricing across product categories",
            "units": "Index 1982=100",
        },
        "DCOILWTICO": {
            "name": "Crude Oil (WTI)",
            "description": "West Texas Intermediate crude oil spot price",
            "mro_impact": "Affects energy costs, transportation logistics, and petroleum-based product pricing",
            "units": "Dollars per Barrel",
        },
        # Interest Rates
        "DFF": {
            "name": "Fed Funds Rate",
            "description": "Federal Reserve's target interest rate",
            "mro_impact": "Benchmark for equipment financing and working capital costs",
            "units": "Percent",
        },
        "DGS10": {
            "name": "10-Year Treasury Rate",
            "description": "Yield on 10-year US government bonds",
            "mro_impact": "Long-term financing benchmark affecting major equipment purchases",
            "units": "Percent",
        },
        "MORTGAGE30US": {
            "name": "30-Year Mortgage Rate",
            "description": "Average rate on 30-year fixed mortgages",
            "mro_impact": "Key driver of residential construction activity and related MRO demand",
            "units": "Percent",
        },
        # GDP
        "A191RL1Q225SBEA": {
            "name": "Real GDP Growth",
            "description": "Quarterly percentage change in real GDP",
            "mro_impact": "Overall economic growth indicator affecting all industrial sectors",
            "units": "Percent",
        },
        "GDP": {
            "name": "Gross Domestic Product",
            "description": "Total value of goods and services produced",
            "mro_impact": "Broad measure of economic activity and industrial demand",
            "units": "Billions of Dollars",
        },
        # Employment
        "PAYEMS": {
            "name": "Total Nonfarm Payrolls",
            "description": "Total number of employed workers excluding farm workers",
            "mro_impact": "Overall employment health affecting consumer and business spending",
            "units": "Thousands of Persons",
        },
        "MANEMP": {
            "name": "Manufacturing Employment",
            "description": "Number of employees in manufacturing sector",
            "mro_impact": "Direct indicator of manufacturing sector health and MRO demand",
            "units": "Thousands of Persons",
        },
        "USCONS": {
            "name": "Construction Employment",
            "description": "Number of employees in construction sector",
            "mro_impact": "Indicator of construction activity and demand for building supplies",
            "units": "Thousands of Persons",
        },
        # Business Confidence
        "BSCICP02USM460S": {
            "name": "Manufacturing Business Confidence",
            "description": "OECD Business Confidence Index for US Manufacturing",
            "mro_impact": "Leading indicator of manufacturing investment and maintenance spending",
            "units": "Index centered at 0",
        },
        # Grainger-Critical Commodities (Jenna's specific requests)
        "PCU3311133111": {
            "name": "Steel Mill Products PPI",
            "description": "Producer Price Index for Steel Mill Products",
            "mro_impact": "Key input cost for manufacturing and construction - Jenna specifically tracks steel pricing",
            "units": "Index Dec 2003=100",
        },
        "WPU102501": {
            "name": "Aluminum Mill Shapes PPI",
            "description": "Producer Price Index for Aluminum Mill Shapes",
            "mro_impact": "Critical commodity for Grainger - aluminum pricing affects product costs and margins",
            "units": "Index 1982=100",
        },
        "PALUMUSDM": {
            "name": "Global Aluminum Price",
            "description": "Global price of aluminum, monthly",
            "mro_impact": "Global aluminum pricing affects Grainger's sourcing costs and product pricing",
            "units": "Dollars per Metric Ton",
        },
        "WPU0721": {
            "name": "Plastic Products PPI",
            "description": "Producer Price Index for Plastic Products",
            "mro_impact": "Affects cost of plastic-based MRO products in Grainger's catalog",
            "units": "Index 1982=100",
        },
        # Government Spending
        "FGEXPND": {
            "name": "Federal Government Expenditures",
            "description": "Federal Government Current Expenditures",
            "mro_impact": "Indicates federal spending capacity - key for Grainger's $2B+ government business",
            "units": "Billions of Dollars",
        },
        "FDEFX": {
            "name": "Defense Spending",
            "description": "Federal Government National Defense Consumption Expenditures",
            "mro_impact": "Military spending drives Grainger's $400M defense business segment",
            "units": "Billions of Dollars",
        },
    }

    def __init__(self, config: Optional[FREDConfig] = None):
        """Initialize FRED API client"""
        self.config = config or FREDConfig()
        self.session: Optional[aiohttp.ClientSession] = None

        if not self.config.api_key:
            logger.warning(
                "FRED_API_KEY not set. Get free key from https://fred.stlouisfed.org/docs/api/api_key.html"
            )

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @backoff.on_exception(
        backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_tries=3, max_time=30
    )
    async def test_connection(self) -> bool:
        """Test FRED API connectivity with retry logic"""
        try:
            logger.info("Testing FRED API connection...")

            # Check if API key is configured
            if not self.config.api_key:
                logger.error("FRED API key not configured - set FRED_API_KEY environment variable")
                return False

            # Test with a simple series request
            url = f"{self.config.base_url}/series"
            params = {"series_id": "INDPRO", "api_key": self.config.api_key, "file_type": "json"}

            if self.session is None:
                raise RuntimeError(
                    "Session not initialized. Use async context manager or call initialize()"
                )
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    logger.info("✓ FRED API connection successful")
                    return True
                elif response.status == 400:
                    error_text = await response.text()
                    logger.error(f"FRED API bad request (check API key): {error_text[:200]}")
                    return False
                else:
                    logger.error(f"FRED API connection failed: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"FRED API connection test failed: {str(e)}")
            return False

    def get_series_info(self, series_id: str) -> Dict:
        """Get metadata about a series for 'So What' generation"""
        return self.SERIES_DESCRIPTIONS.get(series_id, {
            "name": series_id,
            "description": "Economic indicator",
            "mro_impact": "Monitor for potential MRO demand implications",
            "units": "Unknown",
        })

    async def get_industrial_activity(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get industrial production and manufacturing indicators

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of industrial activity observations
        """
        return await self._get_series_category("industrial_activity", days_back)

    async def get_construction_data(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get construction sector indicators

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of construction observations
        """
        return await self._get_series_category("construction", days_back)

    async def get_business_conditions(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get general business condition indicators

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of business condition observations
        """
        return await self._get_series_category("business_conditions", days_back)

    async def get_commodity_prices(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get commodity and input cost indicators

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of commodity price observations
        """
        return await self._get_series_category("commodities", days_back)

    async def get_inflation_indicators(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get inflation data (PCEPILFE and PPIACO)

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of inflation observations
        """
        # Combine relevant inflation indicators from different categories
        observations = []

        # Get business conditions which includes PCEPILFE
        bc_obs = await self._get_series_category("business_conditions", days_back)
        for obs in bc_obs:
            if obs.series_id == "PCEPILFE":
                obs.category = "inflation"
                observations.append(obs)

        # Get commodities which includes PPIACO
        comm_obs = await self._get_series_category("commodities", days_back)
        for obs in comm_obs:
            if obs.series_id == "PPIACO":
                obs.category = "inflation"
                observations.append(obs)

        return observations

    async def get_interest_rate_data(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get interest rate data

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of interest rate observations
        """
        return await self._get_series_category("interest_rates", days_back)

    async def get_industrial_fuel_costs(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get energy and commodity cost data relevant to industrial operations

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of fuel/energy cost observations
        """
        return await self._get_series_category("commodities", days_back)

    async def get_gdp_growth_data(self, days_back: int = 180) -> List[FREDObservation]:
        """
        Get GDP and growth data (typically quarterly)

        Args:
            days_back: Number of days to look back (default 180 for quarterly data)

        Returns:
            List of GDP observations
        """
        return await self._get_series_category("gdp_growth", days_back)

    async def get_employment_data(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get employment indicators including manufacturing and construction employment

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of employment observations
        """
        return await self._get_series_category("employment", days_back)

    async def get_business_confidence_data(self, days_back: int = 365) -> List[FREDObservation]:
        """
        Get business confidence indicators (OECD Manufacturing Confidence Index).
        This series is centered around 0:
        - Positive values indicate optimism (confidence above neutral)
        - Negative values indicate pessimism (confidence below neutral)
        - The magnitude shows strength of sentiment

        This is a leading indicator for manufacturing investment and MRO demand.

        Args:
            days_back: Number of days to look back (default 365 for monthly OECD data)

        Returns:
            List of business confidence observations
        """
        return await self._get_series_category("business_confidence", days_back)

    async def get_grainger_commodity_data(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get Grainger-critical commodity data (steel, aluminum, plastics).

        These commodities were explicitly mentioned by Jenna Anderson as important:
        - Steel: "really important" to business
        - Aluminum: "really important to our business"
        - Plastics: part of product mix

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of commodity observations
        """
        return await self._get_series_category("grainger_commodities", days_back)

    async def get_government_spending_data(self, days_back: int = 180) -> List[FREDObservation]:
        """
        Get government spending indicators.

        Key for Grainger's government segment:
        - $2B+ in government business
        - $400M military segment

        Args:
            days_back: Number of days to look back (default 180 for quarterly data)

        Returns:
            List of government spending observations
        """
        return await self._get_series_category("government", days_back)

    async def get_all_mro_indicators(self, days_back: int = 90) -> Dict[str, List[FREDObservation]]:
        """
        Get all MRO-relevant indicators organized by category.

        Includes Grainger-specific categories:
        - grainger_commodities: Steel, aluminum, plastics (Jenna's specific requests)
        - government: Federal and defense spending (Grainger's $2B+ gov business)

        Args:
            days_back: Number of days to look back

        Returns:
            Dictionary mapping categories to lists of observations
        """
        results = {}

        # Gather all categories in parallel, including Grainger-specific ones
        tasks = {
            "industrial_activity": self.get_industrial_activity(days_back),
            "construction": self.get_construction_data(days_back),
            "business_conditions": self.get_business_conditions(days_back),
            "commodities": self.get_commodity_prices(days_back),
            "grainger_commodities": self.get_grainger_commodity_data(days_back),
            "interest_rates": self.get_interest_rate_data(days_back),
            "employment": self.get_employment_data(days_back),
            "government": self.get_government_spending_data(180),  # Quarterly data
        }

        gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for (category, _), result in zip(tasks.items(), gathered):
            if isinstance(result, Exception):
                logger.error(f"Failed to get {category}: {result}")
                results[category] = []
            else:
                results[category] = result

        return results

    async def _get_series_category(self, category: str, days_back: int) -> List[FREDObservation]:
        """
        Get all series for a category

        Args:
            category: Category name from SERIES dict
            days_back: Number of days to look back

        Returns:
            List of observations for all series in category
        """
        if category not in self.SERIES:
            logger.error(f"Unknown category: {category}")
            return []

        observations = []
        for series_id, series_name in self.SERIES[category].items():
            try:
                obs = await self._get_series_observations(series_id, days_back)
                if obs:
                    # Get the most recent observation
                    latest = obs[-1]  # FRED returns chronologically sorted

                    # Get units from series info
                    series_info = self.get_series_info(series_id)
                    units = series_info.get("units", "Unknown")

                    observations.append(
                        FREDObservation(
                            series_id=series_id,
                            series_name=series_name,
                            value=float(latest["value"]),
                            date=latest["date"],
                            units=units,
                            category=category,
                        )
                    )
                    logger.info(f"✓ Retrieved {series_name}: {latest['value']} ({latest['date']})")
            except Exception as e:
                logger.error(f"Failed to retrieve {series_name}: {str(e)}")
                continue

        return observations

    @backoff.on_exception(
        backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_tries=3, max_time=60
    )
    async def _get_series_observations(self, series_id: str, days_back: int) -> List[Dict]:
        """
        Low-level API call to get series observations

        Args:
            series_id: FRED series identifier
            days_back: Number of days to look back

        Returns:
            List of observation dicts from FRED API
        """
        observation_start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        url = f"{self.config.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.config.api_key,
            "file_type": "json",
            "observation_start": observation_start,
            "sort_order": "asc",
        }

        if self.session is None:
            raise RuntimeError(
                "Session not initialized. Use async context manager or call initialize()"
            )
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                observations = data.get("observations", [])
                # Filter out non-numeric values (FRED uses '.' for missing data)
                valid_obs = [obs for obs in observations if obs["value"] != "."]
                return valid_obs
            elif response.status == 400:
                error_text = await response.text()
                logger.error(f"FRED API error for {series_id}: {error_text}")
                return []
            else:
                logger.error(f"FRED API returned status {response.status} for {series_id}")
                return []
