"""
Shared pytest fixtures for Solairus Intelligence tests
"""

import pytest
from datetime import datetime
from solairus_intelligence.core.processor import IntelligenceItem, ClientSector


@pytest.fixture
def sample_intelligence_item():
    """Create a sample intelligence item for testing"""
    return IntelligenceItem(
        raw_content="US inflation rises to 3.5% in Q4",
        processed_content="US inflation rose to 3.5% in Q4 2025, driven by energy costs",
        category="economic",
        relevance_score=0.85,
        confidence=0.9,
        so_what_statement="Higher operating costs expected for aviation sector",
        affected_sectors=[ClientSector.GENERAL],
        source_type="fred",
        sources=[],
        action_items=[],
        fred_series_id="CPIAUCSL",
        fred_observation_date="2025-10-01"
    )


@pytest.fixture
def sample_intelligence_items():
    """Create multiple sample intelligence items"""
    return [
        IntelligenceItem(
            raw_content="China export controls on semiconductors",
            processed_content="China imposed new export controls on semiconductor equipment",
            category="geopolitical",
            relevance_score=0.88,
            confidence=0.85,
            so_what_statement="Supply chain risks for tech clients",
            affected_sectors=[ClientSector.TECHNOLOGY],
            source_type="ergomind",
            sources=["Source A", "Source B"],
            action_items=["Monitor tech sector impacts"]
        ),
        IntelligenceItem(
            raw_content="US tariffs on EU goods",
            processed_content="US announces new tariffs on European manufactured goods",
            category="trade",
            relevance_score=0.75,
            confidence=0.8,
            so_what_statement="Trade policy impacts manufacturing clients",
            affected_sectors=[ClientSector.GENERAL],
            source_type="gta",
            sources=[],
            action_items=["Review client exposure"],
            gta_intervention_id="12345",
            gta_implementing_countries=["United States"],
            gta_affected_countries=["Germany", "France"]
        )
    ]


@pytest.fixture
def mock_env_config(monkeypatch):
    """Mock environment configuration for testing"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    monkeypatch.setenv("AI_ENABLED", "false")  # Disable AI for most tests
    monkeypatch.setenv("ERGOMIND_API_KEY", "test_key")
    monkeypatch.setenv("GTA_API_KEY", "test_key")
    monkeypatch.setenv("FRED_API_KEY", "test_key")
