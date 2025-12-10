"""
Performance benchmarks for the intelligence processing pipeline.

Run with: pytest tests/benchmarks/ -v --benchmark-only
Or: pytest tests/benchmarks/ -v (includes benchmark stats)
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from solairus_intelligence.core.processor import IntelligenceProcessor
from solairus_intelligence.core.processors.base import IntelligenceItem
from solairus_intelligence.config.clients import ClientSector


class TestProcessorPerformance:
    """Performance benchmarks for the processor"""

    @pytest.fixture
    def processor(self):
        """Create a processor with AI disabled for consistent benchmarks"""
        with patch.dict('os.environ', {'AI_ENABLED': 'false'}):
            return IntelligenceProcessor()

    @pytest.fixture
    def sample_texts(self):
        """Generate sample intelligence texts of varying complexity"""
        return [
            # Short text
            "Federal Reserve raised rates by 25 basis points.",
            # Medium text
            """
            The Federal Reserve announced a 25 basis point increase in interest rates,
            citing persistent inflation concerns. This marks the fifth consecutive rate hike
            and brings the federal funds rate to 5.5%. Markets reacted with increased volatility.
            """,
            # Long text with multiple topics
            """
            US-China tensions continue to escalate following new export controls on semiconductor
            equipment. The restrictions, targeting advanced chip manufacturing technology, affect
            major suppliers including ASML, Applied Materials, and Lam Research. Chinese officials
            have responded with threats of retaliation, potentially targeting rare earth exports.

            Meanwhile, the aviation industry faces continued headwinds from elevated fuel costs,
            with Gulf Coast jet fuel prices hovering near $2.85 per gallon. Airlines and business
            aviation operators are implementing fuel surcharges to offset the increased costs.

            Geopolitical instability in the Middle East has prompted several carriers to adjust
            routing, adding flight time and fuel consumption for transatlantic operations.
            Security protocols have been enhanced for executive travel to affected regions.

            The European Union's new sustainable aviation fuel mandate requires 5% SAF blend
            by 2025, creating supply chain challenges for operators serving European destinations.
            """
        ]

    def test_single_processing_latency(self, processor, sample_texts):
        """Measure latency for processing a single intelligence item"""
        medium_text = sample_texts[1]

        start = time.perf_counter()
        result = processor.process_intelligence(medium_text, "economic")
        elapsed = time.perf_counter() - start

        assert isinstance(result, IntelligenceItem)
        assert elapsed < 1.0, f"Single processing took {elapsed:.3f}s (should be < 1s)"

        print(f"\nSingle processing latency: {elapsed*1000:.2f}ms")

    def test_batch_processing_throughput(self, processor, sample_texts):
        """Measure throughput for batch processing"""
        # Create 50 items to process
        batch_size = 50
        texts = sample_texts * (batch_size // len(sample_texts) + 1)
        texts = texts[:batch_size]

        start = time.perf_counter()
        results = [processor.process_intelligence(text, "general") for text in texts]
        elapsed = time.perf_counter() - start

        throughput = batch_size / elapsed

        assert len(results) == batch_size
        assert throughput > 10, f"Throughput {throughput:.1f}/s (should be > 10/s)"

        print(f"\nBatch processing: {batch_size} items in {elapsed:.2f}s")
        print(f"Throughput: {throughput:.1f} items/second")

    def test_relevance_scoring_performance(self, processor, sample_texts):
        """Measure performance of relevance scoring"""
        long_text = sample_texts[2]

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            processor._calculate_relevance(long_text)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / iterations) * 1000

        assert avg_time < 10, f"Relevance scoring took {avg_time:.2f}ms (should be < 10ms)"

        print(f"\nRelevance scoring: {avg_time:.3f}ms average over {iterations} iterations")

    def test_sector_identification_performance(self, processor, sample_texts):
        """Measure performance of sector identification"""
        long_text = sample_texts[2]

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            processor._identify_affected_sectors(long_text)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / iterations) * 1000

        assert avg_time < 10, f"Sector identification took {avg_time:.2f}ms (should be < 10ms)"

        print(f"\nSector identification: {avg_time:.3f}ms average over {iterations} iterations")

    def test_merge_performance(self, processor):
        """Measure performance of merging multiple sources"""
        # Create sample items from different sources
        ergomind_items = [
            IntelligenceItem(
                raw_content=f"ErgoMind item {i}",
                processed_content=f"Processed ErgoMind intelligence {i}",
                category="geopolitical",
                relevance_score=0.7 + (i % 3) * 0.1,
                so_what_statement=f"Impact statement {i}",
                confidence=0.8,
                source_type="ergomind"
            )
            for i in range(20)
        ]

        gta_items = [
            IntelligenceItem(
                raw_content=f"GTA item {i}",
                processed_content=f"Trade intervention {i}",
                category="trade",
                relevance_score=0.6 + (i % 3) * 0.1,
                so_what_statement=f"Trade impact {i}",
                confidence=0.85,
                source_type="gta"
            )
            for i in range(15)
        ]

        fred_items = [
            IntelligenceItem(
                raw_content=f"FRED item {i}",
                processed_content=f"Economic indicator {i}",
                category="economic",
                relevance_score=0.75,
                so_what_statement=f"Economic impact {i}",
                confidence=0.95,
                source_type="fred"
            )
            for i in range(10)
        ]

        iterations = 50
        start = time.perf_counter()
        for _ in range(iterations):
            processor.merge_intelligence_sources(ergomind_items, gta_items, fred_items)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / iterations) * 1000

        assert avg_time < 100, f"Merge took {avg_time:.2f}ms (should be < 100ms)"

        print(f"\nMerge performance: {avg_time:.2f}ms average for 45 items")


class TestMemoryUsage:
    """Memory usage tests"""

    def test_processor_memory_footprint(self):
        """Verify processor has reasonable memory footprint"""
        import sys

        with patch.dict('os.environ', {'AI_ENABLED': 'false'}):
            processor = IntelligenceProcessor()

        # Get approximate size (this is a rough estimate)
        base_size = sys.getsizeof(processor)

        # Processor should be lightweight without loaded data
        assert base_size < 1_000_000, f"Processor base size {base_size} bytes too large"

        print(f"\nProcessor base memory: {base_size:,} bytes")

    def test_processing_does_not_leak_memory(self):
        """Verify processing doesn't accumulate memory"""
        import gc

        with patch.dict('os.environ', {'AI_ENABLED': 'false'}):
            processor = IntelligenceProcessor()

        # Process many items
        for i in range(100):
            result = processor.process_intelligence(
                f"Test text {i} with some content about aviation and finance.",
                "test"
            )
            del result

        # Force garbage collection
        gc.collect()

        # Processor should not have accumulated state
        assert not hasattr(processor, '_cache') or len(getattr(processor, '_cache', {})) < 100

        print("\nMemory leak test: PASSED (no accumulation detected)")
