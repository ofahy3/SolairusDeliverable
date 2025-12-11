"""
Core intelligence processing modules.

Provides:
- QueryOrchestrator: Manages query execution across data sources
- IntelligenceItem: Standard intelligence data structure
- SectorIntelligence: Sector-grouped intelligence
- DocumentGenerator: Report generation
"""

from mro_intelligence.core.orchestrator import QueryOrchestrator
from mro_intelligence.core.query_templates import QueryTemplate, build_query_templates
from mro_intelligence.core.processor import (
    ClientSector,
    IntelligenceItem,
    SectorIntelligence,
)
from mro_intelligence.core.document.generator import DocumentGenerator

__all__ = [
    "QueryOrchestrator",
    "QueryTemplate",
    "ClientSector",
    "IntelligenceItem",
    "SectorIntelligence",
    "DocumentGenerator",
]
