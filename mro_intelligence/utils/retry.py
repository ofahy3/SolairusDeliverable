"""
Shared retry utilities for API clients
Provides consistent retry behavior across all external API integrations
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

import aiohttp
import backoff

logger = logging.getLogger(__name__)

# Common transient exceptions that should trigger retries
TRANSIENT_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    aiohttp.ClientError,
    aiohttp.ServerTimeoutError,
    asyncio.TimeoutError,
    ConnectionError,
    TimeoutError,
)


def create_retry_decorator(
    max_tries: int = 3,
    max_time: int = 60,
    exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    on_backoff: Optional[Callable] = None,
) -> Callable:
    """
    Create a retry decorator with consistent behavior.

    Args:
        max_tries: Maximum number of retry attempts
        max_time: Maximum total time for all retries (seconds)
        exceptions: Tuple of exception types to retry on
        on_backoff: Optional callback function called on each retry

    Returns:
        Decorator function
    """

    def default_on_backoff(details):
        logger.warning(
            f"Retry attempt {details['tries']} for {details['target'].__name__} "
            f"after {details['wait']:.1f}s (exception: {details['exception']})"
        )

    callback = on_backoff or default_on_backoff

    return backoff.on_exception(
        backoff.expo,
        exceptions,
        max_tries=max_tries,
        max_time=max_time,
        on_backoff=callback,
        logger=None,  # We handle logging in callback
    )


# Pre-configured decorators for common use cases
retry_api_call = create_retry_decorator(max_tries=3, max_time=30)
retry_api_call_aggressive = create_retry_decorator(max_tries=5, max_time=60)
retry_api_call_light = create_retry_decorator(max_tries=2, max_time=15)


class RetryableError(Exception):
    """
    Exception that indicates an operation should be retried.
    Use this to signal retryable failures in application logic.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


async def with_timeout(
    coro: Any, timeout: float, error_message: str = "Operation timed out"
) -> Any:
    """
    Execute a coroutine with a timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        error_message: Error message if timeout occurs

    Returns:
        Result of the coroutine

    Raises:
        asyncio.TimeoutError: If the operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"{error_message} (timeout: {timeout}s)")
        raise


def log_retry(func_name: str, attempt: int, max_attempts: int, error: Exception) -> None:
    """
    Log a retry attempt with consistent formatting.

    Args:
        func_name: Name of the function being retried
        attempt: Current attempt number
        max_attempts: Maximum number of attempts
        error: The exception that triggered the retry
    """
    logger.warning(
        f"Retry {attempt}/{max_attempts} for {func_name}: {type(error).__name__}: {error}"
    )


class CircuitBreaker:
    """
    Simple circuit breaker implementation for API calls.
    Prevents cascading failures by temporarily disabling failing services.
    """

    def __init__(
        self, failure_threshold: int = 5, recovery_timeout: float = 30.0, name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        if self._state == "open":
            # Check if recovery timeout has passed
            if self._last_failure_time:
                import time

                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = "half-open"
                    return False
            return True
        return False

    def record_success(self) -> None:
        """Record a successful call"""
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        """Record a failed call"""
        import time

        self._failures += 1
        self._last_failure_time = time.time()

        if self._failures >= self.failure_threshold:
            self._state = "open"
            logger.warning(f"Circuit breaker '{self.name}' opened after {self._failures} failures")

    def __call__(self, func: Callable) -> Callable:
        """Decorator usage"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.is_open:
                raise RetryableError(
                    f"Circuit breaker '{self.name}' is open - service temporarily unavailable"
                )

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception:
                self.record_failure()
                raise

        return wrapper
