"""
Web interface for MRO Intelligence.

Provides:
- FastAPI-based web UI for report generation
- Run with: python -m mro_intelligence.web.app
"""

from mro_intelligence.web.app import app

__all__ = ["app"]
