"""
MRO Intelligence Report Generator for Grainger
Main application that orchestrates the entire intelligence gathering and report generation process
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from mro_intelligence.clients.ergomind_client import ErgoMindClient, ErgoMindConfig
from mro_intelligence.core.document.generator import DocumentGenerator
from mro_intelligence.core.orchestrator import QueryOrchestrator
from mro_intelligence.core.processors.merger import IntelligenceMerger
from mro_intelligence.utils.config import ENV_CONFIG, get_status_file_path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MROIntelligenceGenerator:
    """
    Main application class for generating MRO intelligence reports for Grainger
    """

    def __init__(self, config: Optional[ErgoMindConfig] = None):
        self.config = config or ErgoMindConfig()
        self.client = ErgoMindClient(self.config)
        self.orchestrator = QueryOrchestrator(self.client)
        self.merger = IntelligenceMerger()
        self.generator = DocumentGenerator()
        self.last_run_status: Optional[Dict[str, Any]] = None

        # Log environment configuration
        logger.info(f"Initialized with: {ENV_CONFIG}")

    async def generate_monthly_report(self, test_mode: bool = False) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a complete monthly intelligence report.

        Args:
            test_mode: If True, uses limited queries for testing.

        Returns:
            Tuple of (filepath, status_dict)
        """
        start_time = datetime.now()
        status: Dict[str, Any] = {
            "start_time": start_time.isoformat(),
            "success": False,
            "queries_executed": 0,
            "items_processed": 0,
            "sectors_covered": [],
            "report_path": None,
            "errors": [],
            "quality_score": 0.0,
        }

        try:
            logger.info("=" * 50)
            logger.info("Starting MRO Intelligence Report Generation")
            logger.info(f"Mode: {'TEST' if test_mode else 'PRODUCTION'}")
            logger.info("=" * 50)

            # Step 1: Gather intelligence from ErgoMind AND GTA (Combined!)
            logger.info("\n📡 Phase 1: Combined Intelligence Gathering (ErgoMind + GTA)")

            if test_mode:
                # Use limited queries in test mode - still use ErgoMind only for speed
                raw_results = await self._test_intelligence_gathering()
                ergomind_items = await self.orchestrator.process_and_filter_results(raw_results)

                # Add GTA in test mode too, but fewer items
                logger.info("  Gathering GTA data (test mode)...")
                gta_results = await self.orchestrator.execute_gta_intelligence_gathering(
                    days_back=30
                )
                gta_items = await self.orchestrator.process_gta_results(gta_results)

                # Add FRED in test mode
                logger.info("  Gathering FRED economic data (test mode)...")
                fred_results = await self.orchestrator.execute_fred_data_gathering(days_back=90)
                fred_items = await self.orchestrator.process_fred_results(fred_results)

                # Merge all intelligence sources
                processed_items = self.merger.merge_sources(ergomind_items, gta_items, fred_items)

                status["queries_executed"] = (
                    sum(len(v) for v in raw_results.values())
                    + sum(len(v) for v in gta_results.values())
                    + sum(len(v) for v in fred_results.values())
                )
            else:
                # Full production mode with all three sources in parallel
                multi_source_results = (
                    await self.orchestrator.execute_multi_source_intelligence_gathering()
                )

                # Capture source status for reporting
                source_status = multi_source_results.get(
                    "source_status", {"ergomind": "unknown", "gta": "unknown", "fred": "unknown"}
                )
                status["source_status"] = source_status

                # Process ErgoMind results
                ergomind_items = await self.orchestrator.process_and_filter_results(
                    multi_source_results["ergomind"]
                )

                # Process GTA results
                gta_items = await self.orchestrator.process_gta_results(multi_source_results["gta"])

                # Process FRED results
                fred_items = await self.orchestrator.process_fred_results(
                    multi_source_results["fred"]
                )

                # Merge all intelligence sources
                processed_items = self.merger.merge_sources(ergomind_items, gta_items, fred_items)

                status["queries_executed"] = (
                    sum(len(v) for v in multi_source_results["ergomind"].values())
                    + sum(len(v) for v in multi_source_results["gta"].values())
                    + sum(len(v) for v in multi_source_results["fred"].values())
                )

            logger.info(
                f"✓ Collected {status['queries_executed']} total responses (ErgoMind + GTA + FRED)"
            )
            logger.info(f"  ├─ ErgoMind: {len(ergomind_items)} items")
            logger.info(f"  ├─ GTA: {len(gta_items)} items")
            logger.info(f"  ├─ FRED: {len(fred_items)} items")
            logger.info(f"  └─ Merged: {len(processed_items)} unique items")

            # Check for empty results and warn user
            if len(processed_items) == 0:
                warning_msg = "WARNING: No intelligence items collected from any source!"
                logger.warning(warning_msg)
                status["errors"].append(warning_msg)

                # Provide specific source failure info
                if len(ergomind_items) == 0:
                    status["errors"].append(
                        "ErgoMind returned no usable data - check API connection"
                    )
                if len(gta_items) == 0:
                    status["errors"].append("GTA returned no usable data - check API key")
                if len(fred_items) == 0:
                    status["errors"].append("FRED returned no usable data - check API key")
            elif len(processed_items) < 5:
                warning_msg = f"WARNING: Only {len(processed_items)} intelligence items collected - report may be sparse"
                logger.warning(warning_msg)
                status["errors"].append(warning_msg)

            # Step 2: Intelligence quality validation
            logger.info("\n🔍 Phase 2: Intelligence Quality Validation")
            status["items_processed"] = len(processed_items)
            status["ergomind_count"] = len(
                [i for i in processed_items if i.source_type == "ergomind"]
            )
            status["gta_count"] = len([i for i in processed_items if i.source_type == "gta"])
            status["fred_count"] = len([i for i in processed_items if i.source_type == "fred"])
            logger.info(f"✓ Validated {len(processed_items)} high-quality intelligence items")
            logger.info(
                f"  Source breakdown: {status['ergomind_count']} ErgoMind + {status['gta_count']} GTA + {status['fred_count']} FRED"
            )

            # Step 3: Organize by sector
            logger.info("\n📊 Phase 3: Sector Organization")
            sector_intelligence = self.merger.organize_by_sector(processed_items)
            status["sectors_covered"] = [s.value for s in sector_intelligence.keys()]
            logger.info(f"✓ Organized intelligence for {len(sector_intelligence)} sectors")

            # Step 4: Generate document
            logger.info("\n📝 Phase 4: Document Generation")
            doc = self.generator.create_report(
                processed_items, sector_intelligence, datetime.now().strftime("%B %Y")
            )

            # Capture AI usage stats if available
            if self.generator.ai_generator:
                ai_usage = self.generator.ai_generator.get_usage_summary()
                status["ai_usage"] = ai_usage
                if ai_usage.get("total_requests", 0) > 0:
                    logger.info(
                        f"✓ AI-enhanced generation used {ai_usage['total_requests']} API calls (${ai_usage['total_cost_usd']:.4f})"
                    )

            # Step 5: Save document
            filepath = self.generator.save_report(doc)
            status["report_path"] = filepath
            logger.info(f"✓ Report saved to: {filepath}")

            # Step 6: Quality assessment
            quality_score = self._assess_quality(processed_items, sector_intelligence)
            status["quality_score"] = quality_score
            logger.info(f"\n✨ Quality Score: {quality_score:.1%}")

            status["success"] = True

            # Generate summary
            self._print_summary(status, start_time)

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            status["errors"].append(str(e))
            status["success"] = False

        finally:
            # Save status for monitoring
            self.last_run_status = status
            self._save_status(status)

        return status.get("report_path", ""), status

    async def _test_intelligence_gathering(self) -> Dict:
        """Limited intelligence gathering for testing"""
        logger.info("Running in TEST mode - executing more queries for content variety")

        # Use MORE queries in test mode to get variety - lower threshold
        test_templates = [
            t
            for t in self.orchestrator.query_templates
            if t.priority >= 7  # Lower threshold from 8 to 7
        ][
            :6
        ]  # Use 6 queries instead of 3 for more content

        results = {}

        async with self.client:
            if not await self.client.test_connection():
                raise Exception("Failed to connect to ErgoMind")

            for template in test_templates:
                logger.info(f"Testing query: {template.category}")
                result = await self.client.query_websocket(template.query)
                if result.success:
                    results[template.category] = [result]
                await asyncio.sleep(2)  # Rate limiting

        return results

    def _assess_quality(self, items: List, sector_intel: Dict) -> float:
        """
        Assess the quality of the generated report
        Returns a score between 0 and 1
        """
        # Handle empty items list gracefully
        if not items:
            return 0.0

        score = 0.0
        max_score = 0.0

        # Check for minimum content
        if len(items) >= 5:
            score += 0.2
        max_score += 0.2

        # Check for sector coverage
        sectors_with_content = sum(1 for s in sector_intel.values() if s.items)
        if sectors_with_content >= 3:
            score += 0.2
        max_score += 0.2

        # Check relevance scores
        high_relevance_items = [i for i in items if i.relevance_score > 0.7]
        if len(high_relevance_items) >= 3:
            score += 0.2
        max_score += 0.2

        # Check for "So What" statements
        items_with_sowhat = [i for i in items if i.so_what_statement]
        if len(items_with_sowhat) / len(items) > 0.8:
            score += 0.2
        max_score += 0.2

        # Check for action items
        items_with_actions = [i for i in items if i.action_items]
        if len(items_with_actions) / len(items) > 0.6:
            score += 0.2
        max_score += 0.2

        return score / max_score if max_score > 0 else 0

    def _print_summary(self, status: Dict, start_time: datetime):
        """Print a summary of the generation process"""
        duration = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 60)
        print("REPORT GENERATION SUMMARY")
        print("=" * 60)
        print(f"✓ Status: {'SUCCESS' if status['success'] else 'FAILED'}")
        print(f"✓ Duration: {duration:.1f} seconds")
        print(f"✓ Queries Executed: {status['queries_executed']}")
        print(f"✓ Intelligence Items: {status['items_processed']}")
        print(f"✓ Sectors Covered: {', '.join(status['sectors_covered'])}")
        print(f"✓ Quality Score: {status['quality_score']:.1%}")

        # Display source status if available
        if "source_status" in status:
            source_status = status["source_status"]
            print("\n📡 Data Sources:")
            print(
                f"   ErgoMind: {'✓ Success' if source_status.get('ergomind') == 'success' else '✗ Failed'}"
            )
            print(
                f"   GTA:      {'✓ Success' if source_status.get('gta') == 'success' else '✗ Failed'}"
            )
            print(
                f"   FRED:     {'✓ Success' if source_status.get('fred') == 'success' else '✗ Failed'}"
            )

        # Display AI usage if available
        if "ai_usage" in status and status["ai_usage"].get("total_requests", 0) > 0:
            ai_usage = status["ai_usage"]
            print("\n🤖 AI Enhancement:")
            print(
                f"   API Calls: {ai_usage['total_requests']} ({ai_usage['successful_requests']} successful)"
            )
            print(
                f"   Tokens: {ai_usage['total_input_tokens']:,} in / {ai_usage['total_output_tokens']:,} out"
            )
            print(f"   Cost: ${ai_usage['total_cost_usd']:.4f}")

        if status["report_path"]:
            print("\n📄 Report Location:")
            print(f"   {status['report_path']}")

        if status["errors"]:
            print("\n⚠️ Errors:")
            for error in status["errors"]:
                print(f"   - {error}")

        print("=" * 60 + "\n")

    def _save_status(self, status: Dict):
        """Save status to a JSON file for monitoring"""
        status_file = get_status_file_path()

        with open(status_file, "w") as f:
            json.dump(status, f, indent=2, default=str)


async def main():
    """Main entry point for the application"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate MRO Intelligence Report for Grainger")
    parser.add_argument("--test", action="store_true", help="Run in test mode with limited queries")

    args = parser.parse_args()

    generator = MROIntelligenceGenerator()
    filepath, status = await generator.generate_monthly_report(test_mode=args.test)

    if status["success"]:
        print("\n✅ Report successfully generated!")
        print(f"📄 Open the report: {filepath}")
        return 0
    else:
        print("\n❌ Report generation failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
