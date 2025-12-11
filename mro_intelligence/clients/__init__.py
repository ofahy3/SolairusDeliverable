"""
API clients for external data sources.

Provides clients for:
- ErgoMind: Flashpoints Forum geopolitical intelligence
- FRED: Federal Reserve Economic Data
- GTA: Global Trade Alert
"""

from mro_intelligence.clients.ergomind_client import (
    ErgoMindClient,
    ErgoMindConfig,
    QueryResult,
)
from mro_intelligence.clients.fred_client import (
    FREDClient,
    FREDConfig,
    FREDObservation,
)
from mro_intelligence.clients.gta_client import (
    GTAClient,
    GTAConfig,
    GTAIntervention,
)

__all__ = [
    # ErgoMind
    "ErgoMindClient",
    "ErgoMindConfig",
    "QueryResult",
    # FRED
    "FREDClient",
    "FREDConfig",
    "FREDObservation",
    # GTA
    "GTAClient",
    "GTAConfig",
    "GTAIntervention",
]
