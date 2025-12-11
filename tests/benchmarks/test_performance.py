"""
Performance benchmarks for the intelligence processing pipeline.

Run with: pytest tests/benchmarks/ -v
"""

import time
from unittest.mock import patch

import pytest

from solairus_intelligence.config.clients import ClientSector
from solairus_intelligence.core.processors.base import IntelligenceItem
from solairus_intelligence.core.processors.ergomind import ErgoMindProcessor
from solairus_intelligence.core.processors.merger import IntelligenceMerger


class TestProcessorPerformance:
    """Performance benchmarks for the processor"""

    @pytest.fixture
    def ergomind_processor(self):
        """Create an ErgoMind processor for detailed tests"""
        with patch.dict("os.environ", {"AI_ENABLED": "false"}):
            return ErgoMindProcessor()

    @pytest.fixture
    def merger(self):
        """Create a merger instance"""
        return IntelligenceMerger()

    @pytest.fixture
    def sample_texts(self):
        """Generate sample intelligence texts of varying complexity"""
        return [
            "Federal Reserve raised rates by 25 basis points.",
            """
            The Federal Reserve announced a 25 basis point increase in interest rates,
            citing persistent inflation concerns. This marks the fifth consecutive rate hike
            and brings the federal funds rate to 5.5%. Markets reacted with increased volatility.
            """,
            """
            US-China tensions continue to escalate following new export controls on semiconductor
            equipment. The restrictions, targeting advanced chip manufacturing technology, affect
            major suppliers including ASML, Applied Materials, and Lam Research.

            Meanwhile, the aviation industry faces continued headwinds from elevated fuel costs,
            with Gulf Coast jet fuel prices hovering near $2.85 per gallon.

            The European Union's new sustainable aviation fuel mandate requires 5% SAF blend
            by 2025, creating supply chain challenges for operators serving European destinations.
            """,
        ]

    def test_single_processing_latency(self, ergomind_processor, sample_texts):
        """Measure latency for processing a single intelligence item"""
        medium_text = sample_texts[1]

        start = time.perf_counter()
        result = ergomind_processor.process_intelligence(medium_text, "economic")
        elapsed = time.perf_counter() - start

        assert isinstance(result, IntelligenceItem)
        assert elapsed < 1.0, f"Single processing took {elapsed:.3f}s (should be < 1s)"

    def test_batch_processing_throughput(self, ergomind_processor, sample_texts):
        """Measure throughput for batch processing"""
        batch_size = 50
        texts = sample_texts * (batch_size // len(sample_texts) + 1)
        texts = texts[:batch_size]

        start = time.perf_counter()
        results = [ergomind_processor.process_intelligence(text, "general") for text in texts]
        elapsed = time.perf_counter() - start

        throughput = batch_size / elapsed

        assert len(results) == batch_size
        assert throughput > 10, f"Throughput {throughput:.1f}/s (should be > 10/s)"

    def test_relevance_scoring_performance(self, ergomind_processor, sample_texts):
        """Measure performance of relevance scoring"""
        long_text = sample_texts[2]

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            ergomind_processor.calculate_base_relevance(long_text)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / iterations) * 1000
        assert avg_time < 10, f"Relevance scoring took {avg_time:.2f}ms (should be < 10ms)"

    def test_sector_identification_performance(self, ergomind_processor, sample_texts):
        """Measure performance of sector identification"""
        long_text = sample_texts[2]

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            ergomind_processor._identify_affected_sectors(long_text)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / iterations) * 1000
        assert avg_time < 10, f"Sector identification took {avg_time:.2f}ms (should be < 10ms)"

    def test_merge_performance(self, merger):
        """Measure performance of merging multiple sources"""
        ergomind_items = [
            IntelligenceItem(
                raw_content=f"ErgoMind item {i}",
                processed_content=f"Processed ErgoMind intelligence {i}",
                category="geopolitical",
                relevance_score=0.7 + (i % 3) * 0.1,
                so_what_statement=f"Impact statement {i}",
                confidence=0.8,
                source_type="ergomind",
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
                source_type="gta",
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
                source_type="fred",
            )
            for i in range(10)
        ]

        iterations = 50
        start = time.perf_counter()
        for _ in range(iterations):
            merger.merge_sources(ergomind_items, gta_items, fred_items)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / iterations) * 1000
        assert avg_time < 100, f"Merge took {avg_time:.2f}ms (should be < 100ms)"


class TestMemoryUsage:
    """Memory usage tests"""

    def test_processor_memory_footprint(self):
        """Verify processor has reasonable memory footprint"""
        import sys

        with patch.dict("os.environ", {"AI_ENABLED": "false"}):
            processor = ErgoMindProcessor()

        base_size = sys.getsizeof(processor)
        assert base_size < 1_000_000, f"Processor base size {base_size} bytes too large"

    def test_processing_does_not_leak_memory(self):
        """Verify processing doesn't accumulate memory"""
        import gc

        with patch.dict("os.environ", {"AI_ENABLED": "false"}):
            processor = ErgoMindProcessor()

        for i in range(100):
            result = processor.process_intelligence(
                f"Test text {i} with some content about aviation and finance.", "test"
            )
            del result

        gc.collect()
        assert not hasattr(processor, "_cache") or len(getattr(processor, "_cache", {})) < 100
