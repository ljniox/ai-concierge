"""
Rate limiting middleware for the automatic account creation system.

This module provides Redis-based rate limiting with multiple strategies,
configurable limits, and comprehensive tracking and analytics.
"""

import time
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from functools import wraps
import asyncio

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from src.utils.logging import get_logger
from src.utils.exceptions import RateLimitError

logger = get_logger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_time: int
    retry_after: int
    identifier: str
    window_seconds: int
    strategy: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'allowed': self.allowed,
            'limit': self.limit,
            'remaining': self.remaining,
            'reset_time': self.reset_time,
            'retry_after': self.retry_after,
            'identifier': self.identifier,
            'window_seconds': self.window_seconds,
            'strategy': self.strategy,
            'metadata': self.metadata
        }


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    def __init__(
        self,
        requests_per_window: int,
        window_seconds: int,
        strategy: str = "sliding_window",
        key_func: Optional[Callable[[Request], str]] = None,
        headers_enabled: bool = True,
        error_message: Optional[str] = None,
        skip_successful_requests: bool = False
    ):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.strategy = strategy
        self.key_func = key_func or self._default_key_func
        self.headers_enabled = headers_enabled
        self.error_message = error_message or f"Rate limit exceeded: {requests_per_window} requests per {window_seconds} seconds"
        self.skip_successful_requests = skip_successful_requests

    @staticmethod
    def _default_key_func(request: Request) -> str:
        """Default key function for rate limiting."""
        # Use IP address as default identifier
        return request.client.host if request.client else "unknown"


class RateLimiter:
    """
    Rate limiting implementation with multiple strategies.

    Supports various rate limiting strategies including sliding window,
    fixed window, token bucket, and leaky bucket algorithms.
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.supported_strategies = {
            'sliding_window': self._sliding_window_check,
            'fixed_window': self._fixed_window_check,
            'token_bucket': self._token_bucket_check,
            'leaky_bucket': self._leaky_bucket_check
        }

    def check_rate_limit(
        self,
        identifier: str,
        config: RateLimitConfig
    ) -> RateLimitResult:
        """
        Check rate limit for an identifier.

        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            config: Rate limit configuration

        Returns:
            RateLimitResult with check results
        """
        if config.strategy not in self.supported_strategies:
            raise RateLimitError(f"Unsupported rate limiting strategy: {config.strategy}")

        try:
            return self.supported_strategies[config.strategy](identifier, config)
        except Exception as e:
            logger.error("Rate limit check failed",
                        identifier=identifier,
                        strategy=config.strategy,
                        error=str(e))
            # Allow request if rate limiting fails
            return RateLimitResult(
                allowed=True,
                limit=config.requests_per_window,
                remaining=config.requests_per_window,
                reset_time=int(time.time()) + config.window_seconds,
                retry_after=0,
                identifier=identifier,
                window_seconds=config.window_seconds,
                strategy=config.strategy,
                metadata={'error': str(e)}
            )

    def _sliding_window_check(self, identifier: str, config: RateLimitConfig) -> RateLimitResult:
        """
        Sliding window rate limiting.

        Uses Redis sorted set to maintain a sliding window of requests.
        """
        if not self.redis_client:
            return self._fallback_check(identifier, config)

        current_time = time.time()
        window_start = current_time - config.window_seconds
        key = f"rate_limit:sliding:{identifier}"

        try:
            # Remove old entries outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            current_count = self.redis_client.zcard(key)

            # Check if limit exceeded
            if current_count >= config.requests_per_window:
                # Get oldest request time for retry after calculation
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                retry_after = 0
                if oldest_request:
                    _, oldest_time = oldest_request[0]
                    retry_after = int(oldest_time + config.window_seconds - current_time)

                return RateLimitResult(
                    allowed=False,
                    limit=config.requests_per_window,
                    remaining=0,
                    reset_time=int(current_time + config.window_seconds),
                    retry_after=max(0, retry_after),
                    identifier=identifier,
                    window_seconds=config.window_seconds,
                    strategy=config.strategy
                )

            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, config.window_seconds)

            return RateLimitResult(
                allowed=True,
                limit=config.requests_per_window,
                remaining=config.requests_per_window - current_count - 1,
                reset_time=int(current_time + config.window_seconds),
                retry_after=0,
                identifier=identifier,
                window_seconds=config.window_seconds,
                strategy=config.strategy
            )

        except Exception as e:
            logger.error("Sliding window check failed", error=str(e))
            return self._fallback_check(identifier, config)

    def _fixed_window_check(self, identifier: str, config: RateLimitConfig) -> RateLimitResult:
        """
        Fixed window rate limiting.

        Uses Redis counter with expiration for fixed time windows.
        """
        if not self.redis_client:
            return self._fallback_check(identifier, config)

        current_time = time.time()
        window_start = int(current_time // config.window_seconds) * config.window_seconds
        key = f"rate_limit:fixed:{identifier}:{int(window_start)}"

        try:
            # Increment counter
            current_count = self.redis_client.incr(key)

            # Set expiration on first request in window
            if current_count == 1:
                self.redis_client.expire(key, config.window_seconds)

            # Check if limit exceeded
            if current_count > config.requests_per_window:
                retry_after = int(window_start + config.window_seconds - current_time)

                return RateLimitResult(
                    allowed=False,
                    limit=config.requests_per_window,
                    remaining=0,
                    reset_time=int(window_start + config.window_seconds),
                    retry_after=max(0, retry_after),
                    identifier=identifier,
                    window_seconds=config.window_seconds,
                    strategy=config.strategy
                )

            return RateLimitResult(
                allowed=True,
                limit=config.requests_per_window,
                remaining=config.requests_per_window - current_count,
                reset_time=int(window_start + config.window_seconds),
                retry_after=0,
                identifier=identifier,
                window_seconds=config.window_seconds,
                strategy=config.strategy
            )

        except Exception as e:
            logger.error("Fixed window check failed", error=str(e))
            return self._fallback_check(identifier, config)

    def _token_bucket_check(self, identifier: str, config: RateLimitConfig) -> RateLimitResult:
        """
        Token bucket rate limiting.

        Uses Redis hash to implement token bucket algorithm.
        """
        if not self.redis_client:
            return self._fallback_check(identifier, config)

        current_time = time.time()
        key = f"rate_limit:token_bucket:{identifier}"

        try:
            # Get current bucket state
            bucket_data = self.redis_client.hgetall(key)

            if not bucket_data:
                # Initialize new bucket
                tokens = config.requests_per_window
                last_refill = current_time
            else:
                tokens = float(bucket_data.get('tokens', 0))
                last_refill = float(bucket_data.get('last_refill', current_time))

            # Calculate tokens to add based on elapsed time
            time_elapsed = current_time - last_refill
            tokens_to_add = (time_elapsed / config.window_seconds) * config.requests_per_window

            # Add tokens but don't exceed capacity
            tokens = min(config.requests_per_window, tokens + tokens_to_add)

            # Check if a token is available
            if tokens >= 1:
                # Consume one token
                tokens -= 1

                # Update bucket state
                self.redis_client.hset(key, {
                    'tokens': tokens,
                    'last_refill': current_time
                })
                self.redis_client.expire(key, config.window_seconds * 2)

                return RateLimitResult(
                    allowed=True,
                    limit=config.requests_per_window,
                    remaining=int(tokens),
                    reset_time=int(current_time + config.window_seconds),
                    retry_after=0,
                    identifier=identifier,
                    window_seconds=config.window_seconds,
                    strategy=config.strategy,
                    metadata={'tokens_available': tokens}
                )
            else:
                # Calculate when next token will be available
                retry_after = int((1 - tokens) * config.window_seconds / config.requests_per_window)

                return RateLimitResult(
                    allowed=False,
                    limit=config.requests_per_window,
                    remaining=0,
                    reset_time=int(current_time + retry_after),
                    retry_after=max(0, retry_after),
                    identifier=identifier,
                    window_seconds=config.window_seconds,
                    strategy=config.strategy,
                    metadata={'tokens_available': tokens}
                )

        except Exception as e:
            logger.error("Token bucket check failed", error=str(e))
            return self._fallback_check(identifier, config)

    def _leaky_bucket_check(self, identifier: str, config: RateLimitConfig) -> RateLimitResult:
        """
        Leaky bucket rate limiting.

        Uses Redis list to implement leaky bucket algorithm.
        """
        if not self.redis_client:
            return self._fallback_check(identifier, config)

        current_time = time.time()
        key = f"rate_limit:leaky_bucket:{identifier}"

        try:
            # Calculate leak rate
            leak_rate = config.requests_per_window / config.window_seconds

            # Remove old entries based on leak rate
            pipe = self.redis_client.pipeline()
            while True:
                oldest_request = self.redis_client.lindex(key, 0)
                if not oldest_request:
                    break

                oldest_time = float(oldest_request)
                if current_time - oldest_time > config.window_seconds:
                    pipe.lpop(key)
                else:
                    break

            pipe.execute()

            # Check bucket size
            bucket_size = self.redis_client.llen(key)

            if bucket_size >= config.requests_per_window:
                # Calculate when next request can be processed
                oldest_request = self.redis_client.lindex(key, 0)
                if oldest_request:
                    oldest_time = float(oldest_request)
                    retry_after = int(oldest_time + config.window_seconds - current_time)
                else:
                    retry_after = config.window_seconds

                return RateLimitResult(
                    allowed=False,
                    limit=config.requests_per_window,
                    remaining=0,
                    reset_time=int(current_time + retry_after),
                    retry_after=max(0, retry_after),
                    identifier=identifier,
                    window_seconds=config.window_seconds,
                    strategy=config.strategy
                )

            # Add current request to bucket
            self.redis_client.rpush(key, str(current_time))
            self.redis_client.expire(key, config.window_seconds * 2)

            return RateLimitResult(
                allowed=True,
                limit=config.requests_per_window,
                remaining=config.requests_per_window - bucket_size - 1,
                reset_time=int(current_time + config.window_seconds),
                retry_after=0,
                identifier=identifier,
                window_seconds=config.window_seconds,
                strategy=config.strategy
            )

        except Exception as e:
            logger.error("Leaky bucket check failed", error=str(e))
            return self._fallback_check(identifier, config)

    def _fallback_check(self, identifier: str, config: RateLimitConfig) -> RateLimitResult:
        """
        Fallback rate limiting using in-memory storage.

        Used when Redis is not available.
        """
        logger.warning("Using fallback rate limiting (in-memory)", identifier=identifier)

        # Simple in-memory fallback (not recommended for production)
        if not hasattr(self, '_fallback_storage'):
            self._fallback_storage = {}

        key = f"{identifier}:{config.strategy}"
        current_time = time.time()

        if key not in self._fallback_storage:
            self._fallback_storage[key] = {
                'count': 0,
                'window_start': current_time,
                'last_reset': current_time
            }

        storage = self._fallback_storage[key]

        # Reset window if expired
        if current_time - storage['window_start'] > config.window_seconds:
            storage['count'] = 0
            storage['window_start'] = current_time

        # Check limit
        if storage['count'] >= config.requests_per_window:
            retry_after = int(storage['window_start'] + config.window_seconds - current_time)
            return RateLimitResult(
                allowed=False,
                limit=config.requests_per_window,
                remaining=0,
                reset_time=int(storage['window_start'] + config.window_seconds),
                retry_after=max(0, retry_after),
                identifier=identifier,
                window_seconds=config.window_seconds,
                strategy=config.strategy,
                metadata={'fallback': True}
            )

        # Increment count
        storage['count'] += 1

        return RateLimitResult(
            allowed=True,
            limit=config.requests_per_window,
            remaining=config.requests_per_window - storage['count'],
            reset_time=int(storage['window_start'] + config.window_seconds),
            retry_after=0,
            identifier=identifier,
            window_seconds=config.window_seconds,
            strategy=config.strategy,
            metadata={'fallback': True}
        )

    def get_statistics(self, identifier: str = None) -> Dict[str, Any]:
        """
        Get rate limiting statistics.

        Args:
            identifier: Specific identifier to get stats for (optional)

        Returns:
            Rate limiting statistics
        """
        stats = {
            'strategies_supported': list(self.supported_strategies.keys()),
            'redis_available': self.redis_client is not None,
            'fallback_in_use': hasattr(self, '_fallback_storage'),
        }

        if identifier:
            # Get specific identifier stats
            identifier_stats = {}
            for strategy in self.supported_strategies.keys():
                try:
                    if self.redis_client:
                        key = f"rate_limit:{strategy}:{identifier}"
                        if strategy == 'sliding_window':
                            count = self.redis_client.zcard(key)
                        elif strategy == 'fixed_window':
                            # This is simplified - would need to find current window key
                            count = 0
                        else:
                            count = len(self.redis_client.hgetall(key))

                        identifier_stats[strategy] = {
                            'current_usage': count,
                            'key_exists': count > 0
                        }
                except Exception:
                    identifier_stats[strategy] = {'error': 'Failed to get stats'}

            stats['identifier_stats'] = identifier_stats

        return stats


class RateLimitMiddleware:
    """
    FastAPI middleware for rate limiting.

    Provides configurable rate limiting for API endpoints with
    automatic response headers and error handling.
    """

    def __init__(self, redis_client=None):
        self.rate_limiter = RateLimiter(redis_client)
        self.default_configs = {}
        self.path_configs = {}

        # Load default configurations from environment
        self._load_default_configurations()

    def _load_default_configurations(self) -> None:
        """Load default rate limit configurations from environment variables."""

        # General API rate limiting
        api_limit = int(os.getenv("RATE_LIMIT_API_REQUESTS", "100"))
        api_window = int(os.getenv("RATE_LIMIT_API_WINDOW", "60"))
        self.default_configs['api'] = RateLimitConfig(api_limit, api_window)

        # Account creation rate limiting
        account_creation_limit = int(os.getenv("RATE_LIMIT_ACCOUNT_CREATION", "5"))
        account_creation_window = int(os.getenv("RATE_LIMIT_ACCOUNT_CREATION_WINDOW", "300"))
        self.default_configs['account_creation'] = RateLimitConfig(
            account_creation_limit,
            account_creation_window,
            strategy="sliding_window"
        )

        # Webhook rate limiting
        webhook_limit = int(os.getenv("RATE_LIMIT_WEBHOOK", "1000"))
        webhook_window = int(os.getenv("RATE_LIMIT_WEBHOOK_WINDOW", "60"))
        self.default_configs['webhook'] = RateLimitConfig(webhook_limit, webhook_window)

    def add_config(self, name: str, config: RateLimitConfig) -> None:
        """Add a rate limit configuration."""
        self.default_configs[name] = config

    def add_path_config(self, path_pattern: str, config_name: str) -> None:
        """Add rate limit configuration for a specific path pattern."""
        self.path_configs[path_pattern] = config_name

    def get_config_for_path(self, path: str) -> Optional[str]:
        """Get rate limit configuration name for a path."""
        for pattern, config_name in self.path_configs.items():
            if pattern in path or path.startswith(pattern):
                return config_name
        return None

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Rate limiting middleware entry point."""
        # Determine which configuration to use
        config_name = self.get_config_for_path(request.url.path) or 'api'
        config = self.default_configs.get(config_name)

        if not config:
            # No rate limiting configured
            return await call_next(request)

        # Get identifier for rate limiting
        identifier = config.key_func(request)

        # Check rate limit
        result = self.rate_limiter.check_rate_limit(identifier, config)

        # Add rate limit headers to response
        response = await self._process_request(request, call_next, result, config)

        # Add rate limit headers if enabled
        if config.headers_enabled:
            self._add_rate_limit_headers(response, result)

        return response

    async def _process_request(
        self,
        request: Request,
        call_next: Callable,
        result: RateLimitResult,
        config: RateLimitConfig
    ) -> Response:
        """Process the request based on rate limit result."""
        if result.allowed:
            return await call_next(request)
        else:
            # Rate limit exceeded
            logger.warning(
                "Rate limit exceeded",
                identifier=result.identifier,
                strategy=result.strategy,
                limit=result.limit,
                retry_after=result.retry_after
            )

            # Return rate limit error response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    'error': 'Rate limit exceeded',
                    'message': config.error_message,
                    'retry_after': result.retry_after,
                    'limit': result.limit,
                    'window_seconds': result.window_seconds
                },
                headers={
                    'Retry-After': str(result.retry_after),
                    'X-RateLimit-Limit': str(result.limit),
                    'X-RateLimit-Remaining': str(result.remaining),
                    'X-RateLimit-Reset': str(result.reset_time)
                }
            )

    def _add_rate_limit_headers(self, response: Response, result: RateLimitResult) -> None:
        """Add rate limit headers to response."""
        response.headers['X-RateLimit-Limit'] = str(result.limit)
        response.headers['X-RateLimit-Remaining'] = str(result.remaining)
        response.headers['X-RateLimit-Reset'] = str(result.reset_time)
        response.headers['X-RateLimit-Strategy'] = result.strategy

        if not result.allowed:
            response.headers['Retry-After'] = str(result.retry_after)


def rate_limit(
    requests_per_window: int,
    window_seconds: int,
    strategy: str = "sliding_window",
    key_func: Optional[Callable[[Request], str]] = None
):
    """
    Decorator for rate limiting specific endpoints.

    Args:
        requests_per_window: Maximum requests per window
        window_seconds: Time window in seconds
        strategy: Rate limiting strategy
        key_func: Function to extract identifier from request
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break

            if not request:
                # If no request found, proceed normally
                return await func(*args, **kwargs)

            # Create rate limit configuration
            config = RateLimitConfig(
                requests_per_window=requests_per_window,
                window_seconds=window_seconds,
                strategy=strategy,
                key_func=key_func
            )

            # Check rate limit
            rate_limiter = RateLimiter()
            identifier = config.key_func(request)
            result = rate_limiter.check_rate_limit(identifier, config)

            if not result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        'Retry-After': str(result.retry_after),
                        'X-RateLimit-Limit': str(result.limit),
                        'X-RateLimit-Remaining': str(result.remaining),
                        'X-RateLimit-Reset': str(result.reset_time)
                    }
                )

            # Proceed with the function
            response = await func(*args, **kwargs)

            # Add rate limit headers if response supports it
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(result.limit)
                response.headers['X-RateLimit-Remaining'] = str(result.remaining)
                response.headers['X-RateLimit-Reset'] = str(result.reset_time)
                response.headers['X-RateLimit-Strategy'] = result.strategy

            return response

        return wrapper
    return decorator


# Global rate limiting middleware instance
_rate_limit_middleware: Optional[RateLimitMiddleware] = None


def get_rate_limit_middleware(redis_client=None) -> RateLimitMiddleware:
    """Get the global rate limiting middleware instance."""
    global _rate_limit_middleware
    if _rate_limit_middleware is None:
        _rate_limit_middleware = RateLimitMiddleware(redis_client)
    return _rate_limit_middleware


def check_rate_limit(
    identifier: str,
    requests_per_window: int,
    window_seconds: int,
    strategy: str = "sliding_window"
) -> RateLimitResult:
    """Check rate limit using global service."""
    middleware = get_rate_limit_middleware()
    config = RateLimitConfig(requests_per_window, window_seconds, strategy)
    return middleware.rate_limiter.check_rate_limit(identifier, config)


def get_rate_limiter(redis_client=None) -> RateLimiter:
    """Get a rate limiter instance."""
    return RateLimiter(redis_client)