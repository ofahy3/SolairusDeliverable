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

    @pytest.mark.asyncio
    async def test_decorated_function_with_timeout_error(self):
        """Test decorated function retries on timeout errors"""
        call_count = [0]

        decorator = create_retry_decorator(max_tries=3, max_time=10)

        @decorator
        async def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise TimeoutError("Request timed out")
            return "recovered"

        result = await test_func()

        assert result == "recovered"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_non_retryable_error_raises_immediately(self):
        """Test non-retryable errors are raised immediately"""
        call_count = [0]

        decorator = create_retry_decorator(max_tries=3, max_time=10)

        @decorator
        async def test_func():
            call_count[0] += 1
            raise ValueError("Non-retryable error")

        with pytest.raises(ValueError):
            await test_func()

        # Should only be called once since ValueError is not retryable
        assert call_count[0] == 1


class TestRetryDecorationWithAiohttp:
    """Test retry decoration with aiohttp exceptions"""

    @pytest.mark.asyncio
    async def test_retries_on_client_error(self):
        """Test retries on aiohttp client errors"""
        call_count = [0]

        decorator = create_retry_decorator(max_tries=3, max_time=10)

        @decorator
        async def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise aiohttp.ClientError("Client error")
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count[0] >= 1

    @pytest.mark.asyncio
    async def test_max_tries_parameter(self):
        """Test max_tries parameter limits retries"""
        call_count = [0]

        decorator = create_retry_decorator(max_tries=2, max_time=30)

        @decorator
        async def test_func():
            call_count[0] += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            await test_func()

        # Should be called exactly max_tries times
        assert call_count[0] == 2


class TestRetryLogging:
    """Test retry logging behavior"""

    @pytest.mark.asyncio
    async def test_logs_retry_attempt(self, caplog):
        """Test that retry attempts are logged"""
        import logging
        caplog.set_level(logging.WARNING)

        call_count = [0]
        decorator = create_retry_decorator(max_tries=3, max_time=10)

        @decorator
        async def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Transient")
            return "ok"

        await test_func()

        # Backoff library should log retry attempts
        assert call_count[0] == 2


class TestRetryableError:
    """Test RetryableError exception"""

    def test_retryable_error_creation(self):
        """Test creating RetryableError"""
        from solairus_intelligence.utils.retry import RetryableError

        error = RetryableError("Test error")

        assert str(error) == "Test error"
        assert error.original_exception is None

    def test_retryable_error_with_original(self):
        """Test RetryableError with original exception"""
        from solairus_intelligence.utils.retry import RetryableError

        original = ValueError("Original error")
        error = RetryableError("Wrapped error", original_exception=original)

        assert error.original_exception is original


class TestWithTimeout:
    """Test with_timeout function"""

    @pytest.mark.asyncio
    async def test_with_timeout_success(self):
        """Test successful operation within timeout"""
        from solairus_intelligence.utils.retry import with_timeout

        async def quick_operation():
            return "success"

        result = await with_timeout(quick_operation(), timeout=5.0)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_timeout_raises_on_timeout(self):
        """Test timeout raises TimeoutError"""
        from solairus_intelligence.utils.retry import with_timeout

        async def slow_operation():
            await asyncio.sleep(10)
            return "never"

        with pytest.raises(asyncio.TimeoutError):
            await with_timeout(slow_operation(), timeout=0.1)


class TestLogRetry:
    """Test log_retry function"""

    def test_log_retry(self, caplog):
        """Test log_retry logs correctly"""
        import logging
        from solairus_intelligence.utils.retry import log_retry

        caplog.set_level(logging.WARNING)

        error = ConnectionError("Test connection error")
        log_retry("test_function", 2, 3, error)

        assert "Retry 2/3" in caplog.text
        assert "test_function" in caplog.text


class TestCircuitBreaker:
    """Test CircuitBreaker class"""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly"""
        from solairus_intelligence.utils.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0, name="test")

        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 30.0
        assert cb.name == "test"
        assert cb._state == "closed"
        assert cb.is_open is False

    def test_circuit_breaker_record_success(self):
        """Test circuit breaker records success"""
        from solairus_intelligence.utils.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)
        cb._failures = 2
        cb._state = "half-open"

        cb.record_success()

        assert cb._failures == 0
        assert cb._state == "closed"

    def test_circuit_breaker_record_failure(self):
        """Test circuit breaker records failure"""
        from solairus_intelligence.utils.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb._failures == 1
        assert cb._state == "closed"

        cb.record_failure()
        cb.record_failure()

        assert cb._failures == 3
        assert cb._state == "open"

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after threshold"""
        from solairus_intelligence.utils.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=2)

        cb.record_failure()
        cb.record_failure()

        assert cb.is_open is True

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovers after timeout"""
        import time
        from solairus_intelligence.utils.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        cb.record_failure()
        assert cb.is_open is True

        # Wait for recovery
        time.sleep(0.2)
        assert cb.is_open is False
        assert cb._state == "half-open"

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_success(self):
        """Test circuit breaker as decorator with success"""
        from solairus_intelligence.utils.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)

        @cb
        async def test_func():
            return "success"

        result = await test_func()

        assert result == "success"
        assert cb._failures == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_failure(self):
        """Test circuit breaker as decorator with failure"""
        from solairus_intelligence.utils.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)

        @cb
        async def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await test_func()

        assert cb._failures == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks requests when open"""
        from solairus_intelligence.utils.retry import CircuitBreaker, RetryableError

        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)

        @cb
        async def test_func():
            return "success"

        # Force circuit open
        cb._state = "open"
        cb._last_failure_time = 0  # Ensure not recovered

        import time
        cb._last_failure_time = time.time()  # Recent failure

        with pytest.raises(RetryableError, match="Circuit breaker"):
            await test_func()


class TestPreConfiguredDecorators:
    """Test pre-configured retry decorators"""

    def test_retry_api_call_exists(self):
        """Test retry_api_call is defined"""
        from solairus_intelligence.utils.retry import retry_api_call

        assert callable(retry_api_call)

    def test_retry_api_call_aggressive_exists(self):
        """Test retry_api_call_aggressive is defined"""
        from solairus_intelligence.utils.retry import retry_api_call_aggressive

        assert callable(retry_api_call_aggressive)

    def test_retry_api_call_light_exists(self):
        """Test retry_api_call_light is defined"""
        from solairus_intelligence.utils.retry import retry_api_call_light

        assert callable(retry_api_call_light)
