"""
Unit tests for cache module
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

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
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
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
        with patch.dict("os.environ", {"CACHE_ENABLED": "false"}):
            cache = ResponseCache(cache_dir=temp_cache_dir)

            assert cache.enabled is False

            cache.set("source", {"key": "value"}, "data")

            # Should return None when disabled
            assert cache.get("source", {"key": "value"}) is None

    def test_cache_enabled_by_default(self, temp_cache_dir):
        """Test cache is enabled by default"""
        with patch.dict("os.environ", {}, clear=True):
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


class TestCacheKeyGeneration:
    """Test cache key generation"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_same_params_same_key(self, temp_cache_dir):
        """Test same parameters produce same cache key"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        params = {"days_back": 30, "query": "test"}

        cache.set("source1", params, "data1")
        result = cache.get("source1", params)

        assert result == "data1"

    def test_param_order_independent(self, temp_cache_dir):
        """Test parameter order doesn't affect cache key"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        params1 = {"a": 1, "b": 2}
        params2 = {"b": 2, "a": 1}

        cache.set("source", params1, "data")

        # Should get same result regardless of param order
        result = cache.get("source", params2)
        assert result == "data"


class TestCacheExpiration:
    """Test cache expiration behavior"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cache_has_ttl_attribute(self, temp_cache_dir):
        """Test cache has TTL configuration"""
        cache = ResponseCache(cache_dir=temp_cache_dir, ttl_hours=24)

        assert hasattr(cache, "ttl_hours")
        assert cache.ttl_hours == 24

    def test_default_ttl(self, temp_cache_dir):
        """Test default TTL is reasonable"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        # Default should be 24 hours
        assert cache.ttl_hours >= 1


class TestCacheDataTypes:
    """Test caching different data types"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cache_dict(self, temp_cache_dir):
        """Test caching dictionary data"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        data = {"key": "value", "nested": {"a": 1}}
        cache.set("source", {"param": 1}, data)

        result = cache.get("source", {"param": 1})
        assert result == data

    def test_cache_list(self, temp_cache_dir):
        """Test caching list data"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        data = [1, 2, 3, {"nested": "dict"}]
        cache.set("source", {"param": 1}, data)

        result = cache.get("source", {"param": 1})
        assert result == data

    def test_cache_string(self, temp_cache_dir):
        """Test caching string data"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        data = "simple string data"
        cache.set("source", {"param": 1}, data)

        result = cache.get("source", {"param": 1})
        assert result == data

    def test_cache_complex_nested(self, temp_cache_dir):
        """Test caching complex nested structures"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        data = {
            "items": [
                {"id": 1, "values": [1, 2, 3]},
                {"id": 2, "values": [4, 5, 6]},
            ],
            "metadata": {
                "count": 2,
                "source": "test",
            },
        }
        cache.set("source", {"param": 1}, data)

        result = cache.get("source", {"param": 1})
        assert result == data


class TestCacheClear:
    """Test cache clearing functionality"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cache_has_clear_method(self, temp_cache_dir):
        """Test cache has clear method"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        assert hasattr(cache, "clear") or hasattr(cache, "invalidate")

    def test_overwrite_existing_cache(self, temp_cache_dir):
        """Test overwriting existing cached data"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        cache.set("source", {"param": 1}, "old_data")
        cache.set("source", {"param": 1}, "new_data")

        result = cache.get("source", {"param": 1})
        assert result == "new_data"


class TestCacheMultipleSources:
    """Test caching from multiple sources"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_different_sources_isolated(self, temp_cache_dir):
        """Test different sources are isolated"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        cache.set("ergomind", {"param": 1}, "ergomind_data")
        cache.set("gta", {"param": 1}, "gta_data")
        cache.set("fred", {"param": 1}, "fred_data")

        assert cache.get("ergomind", {"param": 1}) == "ergomind_data"
        assert cache.get("gta", {"param": 1}) == "gta_data"
        assert cache.get("fred", {"param": 1}) == "fred_data"

    def test_same_source_different_params(self, temp_cache_dir):
        """Test same source with different params"""
        cache = ResponseCache(cache_dir=temp_cache_dir)

        cache.set("ergomind", {"days": 30}, "30_day_data")
        cache.set("ergomind", {"days": 60}, "60_day_data")

        assert cache.get("ergomind", {"days": 30}) == "30_day_data"
        assert cache.get("ergomind", {"days": 60}) == "60_day_data"
