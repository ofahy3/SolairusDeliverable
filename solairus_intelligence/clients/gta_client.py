"""
Global Trade Alert (GTA) API Client
Fetches structured trade intervention data to complement ErgoMind intelligence
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import backoff

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GTAConfig:
    """Configuration for GTA API"""

    base_url: str = field(
        default_factory=lambda: os.getenv(
            "GTA_BASE_URL", "https://api.globaltradealert.org/api/v1/data/"
        )
    )
    api_key: str = field(
        default_factory=lambda: os.getenv(
            "GTA_API_KEY", ""  # Must be provided via environment variable
        )
    )
    timeout: int = 30
    max_retries: int = 3
    max_results_per_query: int = 100  # Balance between data richness and performance


@dataclass
class GTAIntervention:
    """Structured GTA intervention data"""

    intervention_id: int
    title: str
    description: str
    gta_evaluation: str  # "Harmful", "Liberalising", "Unclear"
    implementing_jurisdictions: List[Dict[str, Any]]
    affected_jurisdictions: List[Dict[str, Any]]
    intervention_type: str
    intervention_type_id: int
    mast_chapter: Optional[str] = None
    affected_sectors: List[str] = field(default_factory=list)
    date_announced: Optional[str] = None
    date_implemented: Optional[str] = None
    date_removed: Optional[str] = None
    is_in_force: bool = True
    intervention_url: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)

    def get_short_description(self, max_length: int = 200) -> str:
        """Get truncated description for display"""
        if len(self.description) <= max_length:
            return self.description
        return self.description[:max_length] + "..."

    def get_implementing_countries(self) -> List[str]:
        """Extract list of implementing country names"""
        return [j.get("name", "Unknown") for j in self.implementing_jurisdictions]

    def get_affected_countries(self) -> List[str]:
        """Extract list of affected country names"""
        return [j.get("name", "Unknown") for j in self.affected_jurisdictions]


class GTAClient:
    """
    Client for Global Trade Alert API
    Provides structured trade intervention data
    """

    def __init__(self, config: Optional[GTAConfig] = None):
        self.config = config or GTAConfig()
        self.session: Optional[aiohttp.ClientSession] = None

        # Warn if using fallback API key
        if self.config.api_key == "24f03ce8ff0ebf8155033d867de5cec5f7be2b01":
            logger.warning(
                "Using fallback GTA API key - set GTA_API_KEY environment variable for production"
            )

        logger.info(f"GTAClient initialized with API endpoint: {self.config.base_url}")

    async def __aenter__(self):
        """Async context manager entry"""
        # GTA API requires Authorization header with format: APIKey [YOUR_API_KEY]
        self.session = aiohttp.ClientSession(
            headers={
                "Content-Type": "application/json",
                "Authorization": f"APIKey {self.config.api_key}",
            },
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def test_connection(self) -> bool:
        """Test GTA API connectivity and key validity"""
        try:
            logger.info("Testing GTA API connection...")

            # Check if API key is configured
            if not self.config.api_key:
                logger.error("GTA API key not configured - set GTA_API_KEY environment variable")
                return False

            # Test with a simple POST query (GTA API requires POST, not GET)
            request_data = {
                "limit": 1,
                "offset": 0,
            }

            async with self.session.post(self.config.base_url, json=request_data) as response:
                if response.status == 200:
                    data = await response.json()
                    # GTA API returns a list directly
                    if isinstance(data, list):
                        logger.info("✓ GTA API connection successful")
                        return True
                    elif isinstance(data, dict) and "data" in data:
                        logger.info("✓ GTA API connection successful")
                        return True
                    else:
                        logger.error(f"GTA API returned unexpected format: {type(data)}")
                        return False
                elif response.status == 401:
                    logger.error("GTA API authentication failed - check API key")
                    return False
                elif response.status == 403:
                    logger.error("GTA API access forbidden - API key may be invalid or expired")
                    return False
                else:
                    error_text = await response.text()
                    logger.error(f"GTA API connection failed: HTTP {response.status} - {error_text[:200]}")
                    return False
        except Exception as e:
            logger.error(f"GTA API connection test failed: {str(e)}")
            return False

    @backoff.on_exception(backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_tries=3)
    async def _make_request(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make authenticated request to GTA API with retry logic"""
        if not self.session:
            raise RuntimeError(
                "GTAClient session not initialized. Use 'async with' context manager."
            )

        try:
            logger.info(f"GTA API Request: {json.dumps(request_data, indent=2)}")

            async with self.session.post(self.config.base_url, json=request_data) as response:
                response.raise_for_status()
                data = await response.json()

                # GTA API returns a list directly, not wrapped in a dict
                if isinstance(data, list):
                    logger.info(f"GTA API Response: Retrieved {len(data)} interventions")
                    return data
                elif isinstance(data, dict) and "data" in data:
                    # Fallback for alternate response format
                    logger.info(f"GTA API Response: Retrieved {len(data['data'])} interventions")
                    return data["data"]
                else:
                    logger.warning(f"Unexpected GTA API response format: {type(data)}")
                    return []

        except aiohttp.ClientResponseError as e:
            logger.error(f"GTA API HTTP error {e.status}: {e.message}")
            raise
        except Exception as e:
            logger.error(f"GTA API request failed: {str(e)}")
            raise

    def _parse_intervention(self, raw_data: Dict[str, Any]) -> GTAIntervention:
        """Parse raw GTA API response into GTAIntervention object"""
        # Build title from state_act_title (actual API field)
        title = raw_data.get("state_act_title", "Untitled Intervention")

        # Build description from available fields since API doesn't provide one
        impl_countries = ", ".join(
            j.get("name", "") for j in raw_data.get("implementing_jurisdictions", [])
        )
        affected_countries = ", ".join(
            j.get("name", "") for j in raw_data.get("affected_jurisdictions", [])
        )
        intervention_type = raw_data.get("intervention_type", "Unknown")
        mast_chapter = raw_data.get("mast_chapter", "")

        description = f"{intervention_type}"
        if impl_countries:
            description += f" implemented by {impl_countries}"
        if affected_countries:
            description += f" affecting {affected_countries}"
        if mast_chapter:
            description += f". Category: {mast_chapter}"

        # Handle is_in_force as 0/1 integer
        is_in_force_raw = raw_data.get("is_in_force", 1)
        is_in_force = bool(is_in_force_raw) if isinstance(is_in_force_raw, int) else is_in_force_raw

        return GTAIntervention(
            intervention_id=raw_data.get("intervention_id"),
            title=title,
            description=description,
            gta_evaluation=raw_data.get("gta_evaluation", "Unclear"),
            implementing_jurisdictions=raw_data.get("implementing_jurisdictions", []),
            affected_jurisdictions=raw_data.get("affected_jurisdictions", []),
            intervention_type=intervention_type,
            intervention_type_id=raw_data.get("state_act_id", 0),
            mast_chapter=mast_chapter,
            affected_sectors=raw_data.get("affected_sectors", []),
            date_announced=raw_data.get("date_announced"),
            date_implemented=raw_data.get("date_implemented"),
            date_removed=raw_data.get("date_removed"),
            is_in_force=is_in_force,
            intervention_url=raw_data.get("intervention_url"),
            sources=raw_data.get("sources", []),
        )

    async def query_interventions(
        self, request_data: Dict[str, Any], limit: Optional[int] = None
    ) -> List[GTAIntervention]:
        """
        Query GTA interventions with custom filters

        Args:
            request_data: GTA API request parameters
            limit: Maximum number of results to return

        Returns:
            List of GTAIntervention objects
        """
        # Set default limit if not specified
        if limit is None:
            limit = self.config.max_results_per_query

        # Add limit to request
        request_data["limit"] = min(limit, 1000)  # GTA API max is 1000
        request_data["offset"] = 0

        try:
            raw_interventions = await self._make_request(request_data)

            interventions = [self._parse_intervention(raw) for raw in raw_interventions]

            logger.info(f"Parsed {len(interventions)} GTA interventions")
            return interventions[:limit]  # Enforce client-side limit

        except Exception as e:
            logger.error(f"Failed to query GTA interventions: {str(e)}")
            return []

    async def get_recent_harmful_interventions(
        self, days: int = 30, sectors: Optional[List[str]] = None, limit: int = 50
    ) -> List[GTAIntervention]:
        """
        Get recent harmful trade interventions

        Args:
            days: Number of days to look back
            sectors: Optional list of affected sectors to filter
            limit: Maximum number of results

        Returns:
            List of harmful interventions
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request_data = {
            "gta_evaluation": [1, 4],  # Red (1) and Harmful (4)
            "implementation_period": [
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            ],
            "in_force_on_date": end_date.strftime("%Y-%m-%d"),
            "keep_in_force_on_date": True,
        }

        if sectors:
            request_data["affected_sectors"] = sectors

        return await self.query_interventions(request_data, limit=limit)

    async def get_sanctions_and_export_controls(
        self, days: int = 60, limit: int = 50
    ) -> List[GTAIntervention]:
        """
        Get recent sanctions and export controls (critical for aviation)

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of sanction/export control interventions
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request_data = {
            "intervention_types": [
                47,
                18,
                51,
                52,
            ],  # Export tariffs, import tariffs, anti-dumping, sanctions
            "gta_evaluation": [1, 4],  # Harmful
            "implementation_period": [
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            ],
            "in_force_on_date": end_date.strftime("%Y-%m-%d"),
            "keep_in_force_on_date": True,
        }

        return await self.query_interventions(request_data, limit=limit)

    async def get_capital_controls(
        self, days: int = 60, affected_countries: Optional[List[int]] = None, limit: int = 30
    ) -> List[GTAIntervention]:
        """
        Get capital controls and financial restrictions

        Args:
            days: Number of days to look back
            affected_countries: Optional list of country codes to filter
            limit: Maximum number of results

        Returns:
            List of capital control interventions
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request_data = {
            "mast_chapters": [3],  # Capital controls chapter
            "implementation_period": [
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            ],
            "gta_evaluation": [1, 4],  # Harmful
        }

        if affected_countries:
            request_data["affected"] = affected_countries

        return await self.query_interventions(request_data, limit=limit)

    async def get_technology_restrictions(
        self, days: int = 60, limit: int = 40
    ) -> List[GTAIntervention]:
        """
        Get technology sector restrictions (export controls, local content)

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of tech-related interventions
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request_data = {
            "intervention_types": [28, 47, 51],  # Local content requirements, export restrictions
            "affected_sectors": ["software", "semiconductors", "telecommunications", "computers"],
            "implementation_period": [
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            ],
            "gta_evaluation": [1, 4],
        }

        return await self.query_interventions(request_data, limit=limit)

    async def get_aviation_sector_interventions(
        self, days: int = 90, limit: int = 30
    ) -> List[GTAIntervention]:
        """
        Get interventions specifically affecting aviation and aerospace sectors

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of aviation-related interventions
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request_data = {
            "affected_sectors": ["aviation", "aerospace", "aircraft", "air transport"],
            "implementation_period": [
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            ],
            "in_force_on_date": end_date.strftime("%Y-%m-%d"),
            "keep_in_force_on_date": True,
        }

        return await self.query_interventions(request_data, limit=limit)

    async def get_immigration_visa_restrictions(
        self, days: int = 365, limit: int = 30
    ) -> List[GTAIntervention]:
        """
        Get immigration, visa, and labor mobility restrictions.
        Critical for business aviation clients planning international travel.

        Args:
            days: Number of days to look back (default 365 - migration measures are less frequent)
            limit: Maximum number of results

        Returns:
            List of immigration/visa-related interventions
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch broader dataset and filter client-side for migration measures
        # GTA API filter parameters don't consistently work, so we fetch more and filter
        request_data = {
            "implementation_period": [
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            ],
            "in_force_on_date": end_date.strftime("%Y-%m-%d"),
            "keep_in_force_on_date": True,
        }

        # Request more results since we'll filter client-side
        all_interventions = await self.query_interventions(request_data, limit=500)

        # Filter for migration-related interventions by MAST chapter and keywords
        migration_keywords = [
            "migration", "visa", "immigration", "work permit", "labour market",
            "labor market", "travel ban", "entry restriction", "residence",
            "mobility", "foreign worker", "skilled worker"
        ]

        migration_interventions = []
        for intervention in all_interventions:
            # Check MAST chapter
            is_migration = "migration" in (intervention.mast_chapter or "").lower()

            # Check title for keywords
            title_lower = intervention.title.lower()
            has_keyword = any(kw in title_lower for kw in migration_keywords)

            # Check intervention type
            type_lower = intervention.intervention_type.lower()
            type_match = any(kw in type_lower for kw in ["migration", "labour", "labor", "visa"])

            if is_migration or has_keyword or type_match:
                migration_interventions.append(intervention)

        logger.info(f"Filtered {len(migration_interventions)} migration interventions from {len(all_interventions)} total")
        return migration_interventions[:limit]


async def test_gta_client():
    """Test function for GTA client"""
    print("=" * 60)
    print("TESTING GTA CLIENT")
    print("=" * 60)

    async with GTAClient() as client:
        # Test 1: Connection
        print("\n1. Testing API connection...")
        connected = await client.test_connection()
        print(f"   Result: {'✓ PASSED' if connected else '✗ FAILED'}")

        if not connected:
            print("\n⚠️ Connection failed. Check API key and network.")
            return

        # Test 2: Recent harmful interventions
        print("\n2. Fetching recent harmful interventions...")
        harmful = await client.get_recent_harmful_interventions(days=30, limit=5)
        print(f"   Found {len(harmful)} interventions")
        if harmful:
            print(f"   Example: {harmful[0].title[:80]}...")

        # Test 3: Sanctions and export controls
        print("\n3. Fetching sanctions and export controls...")
        sanctions = await client.get_sanctions_and_export_controls(days=60, limit=5)
        print(f"   Found {len(sanctions)} sanctions/controls")
        if sanctions:
            print(f"   Example: {sanctions[0].title[:80]}...")

        # Test 4: Aviation sector
        print("\n4. Fetching aviation sector interventions...")
        aviation = await client.get_aviation_sector_interventions(days=90, limit=5)
        print(f"   Found {len(aviation)} aviation interventions")
        if aviation:
            print(f"   Example: {aviation[0].title[:80]}...")

        # Test 5: Technology restrictions
        print("\n5. Fetching technology restrictions...")
        tech = await client.get_technology_restrictions(days=60, limit=5)
        print(f"   Found {len(tech)} tech restrictions")
        if tech:
            print(f"   Example: {tech[0].title[:80]}...")

    print("\n" + "=" * 60)
    print("GTA CLIENT TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_gta_client())
