"""
Unit tests for retry module
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import aiohttp

from solairus_intelligence.utils.retry import (
    create_retry_decorator,
    TRANSIENT_EXCEPTIONS,
)


class TestTransientExceptions:
    """Test suite for transient exception definitions"""

    def test_transient_exceptions_defined(self):
        """Test transient exceptions tuple is defined"""
        assert TRANSIENT_EXCEPTIONS is not None
        assert isinstance(TRANSIENT_EXCEPTIONS, tuple)
        assert len(TRANSIENT_EXCEPTIONS) > 0

    def test_includes_common_network_errors(self):
        """Test includes common network error types"""
        assert ConnectionError in TRANSIENT_EXCEPTIONS
        assert TimeoutError in TRANSIENT_EXCEPTIONS


class TestCreateRetryDecorator:
    """Test suite for create_retry_decorator"""

    def test_creates_decorator(self):
        """Test creates a valid decorator"""
        decorator = create_retry_decorator(max_tries=3)

        assert callable(decorator)

    def test_decorator_with_custom_params(self):
        """Test decorator accepts custom parameters"""
        decorator = create_retry_decorator(
            max_tries=5,
            max_time=120,
        )

        assert callable(decorator)

    @pytest.mark.asyncio
    async def test_decorated_function_succeeds(self):
        """Test decorated function succeeds on first attempt"""
        decorator = create_retry_decorator(max_tries=3, max_time=10)

        @decorator
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorated_function_retries_on_transient_error(self):
        """Test decorated function retries on transient errors"""
        call_count = [0]

        decorator = create_retry_decorator(max_tries=3, max_time=10)

        @decorator
        async def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Transient error")
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_decorated_function_exhausts_retries(self):
        """Test decorated function fails after exhausting retries"""
        decorator = create_retry_decorator(max_tries=2, max_time=5)

        @decorator
        async def test_func():
            raise ConnectionError("Permanent failure")

        with pytest.raises(ConnectionError):
            await test_func()

    def test_custom_on_backoff_callback(self):
        """Test custom callback is accepted"""
        callback_called = [False]

        def custom_callback(details):
            callback_called[0] = True

        decorator = create_retry_decorator(
            max_tries=3,
            on_backoff=custom_callback
        )

        assert callable(decorator)
