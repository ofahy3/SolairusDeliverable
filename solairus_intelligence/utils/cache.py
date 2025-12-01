"""
Simple File-Based Cache for API Responses
Caches responses for same-day runs to speed up development and testing
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
import os

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    Simple file-based cache for API responses

    - Caches API responses by source type and query hash
    - Automatically expires after configurable time (default: same day)
    - Can be disabled via environment variable CACHE_ENABLED=false
    """

    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """
        Initialize cache

        Args:
            cache_dir: Directory to store cache files (default: outputs/.cache)
            ttl_hours: Time-to-live in hours for cached items (default: 24)
        """
        self.enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.ttl_hours = ttl_hours

        if cache_dir:
            self.cache_dir = cache_dir
        else:
            # Use outputs/.cache directory
            from solairus_intelligence.utils.config import get_output_dir
            self.cache_dir = get_output_dir() / ".cache"

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache enabled: {self.cache_dir}")
        else:
            logger.info("Cache disabled via environment variable")

    def _get_cache_key(self, source: str, query_params: dict) -> str:
        """Generate unique cache key from source and query parameters"""
        # Include today's date in key for daily expiry
        today = datetime.now().strftime("%Y-%m-%d")

        # Create hash of query params
        params_str = json.dumps(query_params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]

        return f"{source}_{today}_{params_hash}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, source: str, query_params: dict) -> Optional[Any]:
        """
        Retrieve cached response if available and not expired

        Args:
            source: Source identifier (e.g., 'ergomind', 'gta', 'fred')
            query_params: Query parameters to hash for cache key

        Returns:
            Cached data or None if not found/expired
        """
        if not self.enabled:
            return None

        cache_key = self._get_cache_key(source, query_params)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)

            # Check expiry
            cached_at = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            if datetime.now() - cached_at > timedelta(hours=self.ttl_hours):
                logger.debug(f"Cache expired for {source}")
                cache_path.unlink()  # Delete expired cache
                return None

            logger.info(f"Cache HIT for {source} ({cache_key})")
            return cached.get('data')

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Cache read error for {source}: {e}")
            return None

    def set(self, source: str, query_params: dict, data: Any) -> bool:
        """
        Store response in cache

        Args:
            source: Source identifier
            query_params: Query parameters used
            data: Data to cache (must be JSON-serializable)

        Returns:
            True if cached successfully
        """
        if not self.enabled:
            return False

        cache_key = self._get_cache_key(source, query_params)
        cache_path = self._get_cache_path(cache_key)

        try:
            cache_entry = {
                'source': source,
                'query_params': query_params,
                'cached_at': datetime.now().isoformat(),
                'data': data
            }

            with open(cache_path, 'w') as f:
                json.dump(cache_entry, f, indent=2, default=str)

            logger.debug(f"Cached {source} response ({cache_key})")
            return True

        except (TypeError, OSError) as e:
            logger.warning(f"Cache write error for {source}: {e}")
            return False

    def clear(self, source: Optional[str] = None) -> int:
        """
        Clear cache entries

        Args:
            source: Optional source to clear (None = clear all)

        Returns:
            Number of entries cleared
        """
        if not self.cache_dir.exists():
            return 0

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            if source is None or cache_file.name.startswith(source):
                cache_file.unlink()
                count += 1

        logger.info(f"Cleared {count} cache entries")
        return count

    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.cache_dir.exists():
            return {'enabled': self.enabled, 'entries': 0, 'size_bytes': 0}

        entries = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in entries)

        return {
            'enabled': self.enabled,
            'entries': len(entries),
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }


# Global cache instance
_cache_instance: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache()
    return _cache_instance
