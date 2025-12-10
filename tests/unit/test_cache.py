"""
Unit tests for cache module
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from solairus_intelligence.utils.cache import ResponseCache


class TestResponseCache:
    """Test suite for ResponseCache"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initializes correctly"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        assert cache is not None
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert cache.enabled is True

    def test_cache_set_and_get(self, temp_cache_dir):
        """Test basic set and get operations"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        cache.set("test_source", {"key": "value"}, {"result": "data"})
        result = cache.get("test_source", {"key": "value"})

        assert result == {"result": "data"}

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss returns None"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        result = cache.get("nonexistent", {"key": "value"})

        assert result is None

    def test_cache_key_generation(self, temp_cache_dir):
        """Test cache generates consistent keys"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        # Same params should generate same key
        cache.set("source", {"a": 1, "b": 2}, "data1")
        result = cache.get("source", {"a": 1, "b": 2})

        assert result == "data1"

    def test_cache_different_params(self, temp_cache_dir):
        """Test different params create different keys"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        cache.set("source", {"a": 1}, "data1")
        cache.set("source", {"a": 2}, "data2")

        assert cache.get("source", {"a": 1}) == "data1"
        assert cache.get("source", {"a": 2}) == "data2"

    def test_cache_disabled_via_env(self, temp_cache_dir):
        """Test cache can be disabled via environment variable"""
        with patch.dict('os.environ', {'CACHE_ENABLED': 'false'}):
            cache = ResponseCache(cache_dir=temp_cache_dir)

            assert cache.enabled is False

            cache.set("source", {"key": "value"}, "data")

            # Should return None when disabled
            assert cache.get("source", {"key": "value"}) is None

    def test_cache_enabled_by_default(self, temp_cache_dir):
        """Test cache is enabled by default"""
        with patch.dict('os.environ', {}, clear=True):
            cache = ResponseCache(cache_dir=temp_cache_dir)
            assert cache.enabled is True

    def test_cache_creates_directory(self, temp_cache_dir):
        """Test cache creates cache directory if it doesn't exist"""
        new_cache_dir = temp_cache_dir / "new_cache"
        cache = ResponseCache(cache_dir=new_cache_dir)

        assert new_cache_dir.exists()

    def test_cache_ttl_configuration(self, temp_cache_dir):
        """Test TTL can be configured"""
        cache = ResponseCache(cache_dir=temp_cache_dir, ttl_hours=48)

        assert cache.ttl_hours == 48
