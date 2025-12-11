"""
Federal Reserve Economic Data (FRED) API Client
Provides economic indicators to support ErgoMind intelligence with concrete data points
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
    category: str  # 'inflation', 'interest_rate', 'fuel_cost', 'gdp_growth'


class FREDClient:
    """
    Client for Federal Reserve Economic Data (FRED) API
    Provides economic indicators to quantify ErgoMind's narrative intelligence
    """

    # Key economic series for business aviation - focused indicators
    SERIES = {
        "fuel_costs": {
            "WJFUELUSGULF": "US Gulf Coast Kerosene-Type Jet Fuel Price",
            "DCOILWTICO": "Crude Oil Prices: West Texas Intermediate (WTI)",
        },
        "interest_rates": {
            "DFF": "Federal Funds Effective Rate",
            "DGS10": "10-Year Treasury Constant Maturity Rate",
            "MORTGAGE30US": "30-Year Fixed Rate Mortgage Average",
        },
        "business_confidence": {
            "BSCICP02USM460S": "Business Confidence Index: Manufacturing for United States",
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
            params = {"series_id": "CPIAUCSL", "api_key": self.config.api_key, "file_type": "json"}

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

    async def get_inflation_indicators(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get latest inflation data

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of inflation observations
        """
        return await self._get_series_category("inflation", days_back)

    async def get_interest_rate_data(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get latest interest rate data

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of interest rate observations
        """
        return await self._get_series_category("interest_rates", days_back)

    async def get_aviation_fuel_costs(self, days_back: int = 90) -> List[FREDObservation]:
        """
        Get jet fuel and crude oil price data

        Args:
            days_back: Number of days to look back for observations

        Returns:
            List of fuel cost observations
        """
        return await self._get_series_category("fuel_costs", days_back)

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
        Get employment indicators

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

        This is a leading indicator for corporate travel and charter demand.
        When business confidence is high, corporate travel typically increases.

        Args:
            days_back: Number of days to look back (default 365 for monthly OECD data)

        Returns:
            List of business confidence observations
        """
        return await self._get_series_category("business_confidence", days_back)

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
                    observations.append(
                        FREDObservation(
                            series_id=series_id,
                            series_name=series_name,
                            value=float(latest["value"]),
                            date=latest["date"],
                            units=obs[0].get("units", "Unknown"),
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
