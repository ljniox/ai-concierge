"""
Redis-based Rate Limiting Utility

Implements rate limiting for authentication attempts and other operations.
Supports multiple rate limiting strategies (fixed window, sliding window, token bucket).

Research Decision: research.md#5 - Rate limiting for code parent validation
Security: 5 attempts per hour per phone number for code parent authentication

Constitution Principle V: Security (protect against brute force attacks)
"""

import json
import time
import asyncio
from typing import Optional, Dict, Any
import logging
import os

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available, falling back to in-memory rate limiting")

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """
    Redis-based rate limiter with fallback to in-memory storage.

    Supports multiple rate limiting strategies:
    - Fixed Window: Reset count at fixed intervals
    - Sliding Window: Count requests in rolling time window
    - Token Bucket: Refill tokens at a fixed rate
    """

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self._redis_client: Optional['redis.Redis'] = None
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def _get_redis_client(self) -> Optional['redis.Redis']:
        """Get Redis client connection."""
        if not REDIS_AVAILABLE:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connected for rate limiting")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._redis_client = None

        return self._redis_client

    async def is_allowed_fixed_window(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if request is allowed using fixed window rate limiting.

        Args:
            key: Unique identifier (e.g., phone number, IP address)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            bool: True if request is allowed

        Example:
            # 5 attempts per hour
            allowed = await limiter.is_allowed_fixed_window("phone:+221770000001", 5, 3600)
        """
        redis_client = await self._get_redis_client()

        if redis_client:
            # Redis implementation
            current_time = int(time.time())
            window_start = current_time - (current_time % window_seconds)
            redis_key = f"rate_limit:{key}:{window_start}"

            try:
                # Increment counter
                count = await redis_client.incr(redis_key)

                # Set expiration if this is the first request in window
                if count == 1:
                    await redis_client.expire(redis_key, window_seconds)

                return count <= limit

            except Exception as e:
                logger.error(f"Redis rate limit error: {e}")
                # Fall back to in-memory

        # In-memory fallback
        async with self._lock:
            current_time = time.time()
            window_start = current_time - (current_time % window_seconds)

            if key not in self._memory_store:
                self._memory_store[key] = {
                    'count': 0,
                    'window_start': window_start
                }

            # Reset if window has expired
            if self._memory_store[key]['window_start'] != window_start:
                self._memory_store[key]['count'] = 0
                self._memory_store[key]['window_start'] = window_start

            # Check and increment
            if self._memory_store[key]['count'] >= limit:
                return False

            self._memory_store[key]['count'] += 1
            return True

    async def is_allowed_sliding_window(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if request is allowed using sliding window rate limiting.

        Args:
            key: Unique identifier
            limit: Maximum number of requests allowed
            window_seconds: Sliding time window in seconds

        Returns:
            bool: True if request is allowed
        """
        redis_client = await self._get_redis_client()

        if redis_client:
            # Redis implementation with sorted sets
            redis_key = f"rate_limit_sliding:{key}"
            current_time = time.time()
            window_start = current_time - window_seconds

            try:
                # Use Redis pipeline for atomic operations
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(redis_key, 0, window_start)  # Remove old entries
                pipe.zcard(redis_key)  # Count current entries
                pipe.zadd(redis_key, {str(current_time): current_time})  # Add current request
                pipe.expire(redis_key, window_seconds)  # Set expiration
                results = await pipe.execute()

                count = results[1]  # zcard result
                return count <= limit

            except Exception as e:
                logger.error(f"Redis sliding window error: {e}")

        # In-memory fallback (simplified sliding window)
        async with self._lock:
            current_time = time.time()
            window_start = current_time - window_seconds

            if key not in self._memory_store:
                self._memory_store[key] = {
                    'requests': [],
                    'window_start': window_start
                }

            # Remove old requests
            self._memory_store[key]['requests'] = [
                req_time for req_time in self._memory_store[key]['requests']
                if req_time > window_start
            ]

            # Check limit
            if len(self._memory_store[key]['requests']) >= limit:
                return False

            # Add current request
            self._memory_store[key]['requests'].append(current_time)
            return True

    async def get_remaining_requests(self, key: str, limit: int, window_seconds: int) -> int:
        """
        Get number of remaining requests for a key.

        Args:
            key: Unique identifier
            limit: Maximum number of requests
            window_seconds: Time window

        Returns:
            int: Number of remaining requests
        """
        redis_client = await self._get_redis_client()

        if redis_client:
            try:
                current_time = int(time.time())
                window_start = current_time - (current_time % window_seconds)
                redis_key = f"rate_limit:{key}:{window_start}"

                count = await redis_client.get(redis_key)
                if count is None:
                    return limit

                return max(0, limit - int(count))

            except Exception as e:
                logger.error(f"Redis get remaining error: {e}")

        # In-memory fallback
        async with self._lock:
            if key not in self._memory_store:
                return limit

            current_time = time.time()
            window_start = current_time - (current_time % window_seconds)

            if self._memory_store[key].get('window_start') != window_start:
                return limit

            count = self._memory_store[key].get('count', 0)
            return max(0, limit - count)

    async def reset_limit(self, key: str):
        """
        Reset rate limit for a specific key.

        Args:
            key: Unique identifier to reset
        """
        redis_client = await self._get_redis_client()

        if redis_client:
            try:
                # Delete all rate limit keys for this identifier
                pattern = f"rate_limit*:{key}:*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis reset error: {e}")

        # In-memory fallback
        async with self._lock:
            if key in self._memory_store:
                del self._memory_store[key]

    async def get_stats(self, key: str) -> Dict[str, Any]:
        """
        Get rate limiting statistics for a key.

        Args:
            key: Unique identifier

        Returns:
            Dict: Rate limiting statistics
        """
        redis_client = await self._get_redis_client()

        stats = {
            'key': key,
            'redis_available': redis_client is not None,
            'current_count': 0,
            'memory_count': 0
        }

        if redis_client:
            try:
                # Get current count from Redis
                current_time = int(time.time())
                pattern = f"rate_limit:{key}:*"
                keys = await redis_client.keys(pattern)

                if keys:
                    # Get the count from the most recent window
                    recent_key = max(keys)
                    count = await redis_client.get(recent_key)
                    stats['current_count'] = int(count) if count else 0

            except Exception as e:
                logger.error(f"Redis stats error: {e}")

        # Memory store stats
        async with self._lock:
            if key in self._memory_store:
                stats['memory_count'] = self._memory_store[key].get('count', 0)

        return stats


# Global rate limiter instance
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    return _rate_limiter_instance


# Convenience functions for common rate limiting scenarios

async def check_code_parent_limit(telephone: str) -> bool:
    """
    Check code parent authentication rate limit (5 attempts per hour).

    Args:
        telephone: Phone number to check

    Returns:
        bool: True if request is allowed

    Research Decision: research.md#5 - 5 attempts per hour
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_fixed_window(
        key=f"code_parent:{telephone}",
        limit=5,
        window_seconds=3600  # 1 hour
    )


async def check_api_limit(user_id: str, limit: int = 1000, window_seconds: int = 3600) -> bool:
    """
    Check general API rate limit for a user.

    Args:
        user_id: User identifier
        limit: Maximum requests (default: 1000/hour)
        window_seconds: Time window (default: 1 hour)

    Returns:
        bool: True if request is allowed
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_fixed_window(
        key=f"api:{user_id}",
        limit=limit,
        window_seconds=window_seconds
    )


async def check_ocr_limit(user_id: str, limit: int = 50, window_seconds: int = 3600) -> bool:
    """
    Check OCR processing rate limit.

    Args:
        user_id: User identifier
        limit: Maximum OCR requests (default: 50/hour)
        window_seconds: Time window (default: 1 hour)

    Returns:
        bool: True if request is allowed
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_fixed_window(
        key=f"ocr:{user_id}",
        limit=limit,
        window_seconds=window_seconds
    )


async def check_document_upload_limit(user_id: str, limit: int = 20, window_seconds: int = 3600) -> bool:
    """
    Check document upload rate limit.

    Args:
        user_id: User identifier
        limit: Maximum uploads (default: 20/hour)
        window_seconds: Time window (default: 1 hour)

    Returns:
        bool: True if request is allowed
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_fixed_window(
        key=f"upload:{user_id}",
        limit=limit,
        window_seconds=window_seconds
    )


# ==============================================================================
# Account Creation System Rate Limiting
# ==============================================================================

async def check_account_creation_limit(phone_number: str, limit: int = 10, window_seconds: int = 3600) -> bool:
    """
    Check account creation rate limit for phone number.

    Args:
        phone_number: Phone number to check
        limit: Maximum account creation attempts (default: 10/hour)
        window_seconds: Time window (default: 1 hour)

    Returns:
        bool: True if request is allowed

    Usage:
        # Prevent spam account creation from same phone number
        allowed = await check_account_creation_limit("+221770000001")
    """
    limiter = get_rate_limiter()
    # Use phone number for rate limiting to prevent spam
    return await limiter.is_allowed_fixed_window(
        key=f"account_creation:{phone_number}",
        limit=limit,
        window_seconds=window_seconds
    )


async def check_webhook_rate_limit(platform: str, identifier: str, limit: int = 1000, window_seconds: int = 300) -> bool:
    """
    Check webhook request rate limit.

    Args:
        platform: Platform name ('telegram' or 'whatsapp')
        identifier: IP address or other identifier
        limit: Maximum webhook requests (default: 1000/5 minutes)
        window_seconds: Time window (default: 5 minutes)

    Returns:
        bool: True if request is allowed

    Usage:
        # Protect webhook endpoints from abuse
        allowed = await check_webhook_rate_limit("telegram", client_ip)
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_sliding_window(
        key=f"webhook:{platform}:{identifier}",
        limit=limit,
        window_seconds=window_seconds
    )


async def check_phone_validation_rate_limit(ip_address: str, limit: int = 100, window_seconds: int = 60) -> bool:
    """
    Check phone validation rate limit.

    Args:
        ip_address: Client IP address
        limit: Maximum validation requests (default: 100/minute)
        window_seconds: Time window (default: 1 minute)

    Returns:
        bool: True if request is allowed
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_fixed_window(
        key=f"phone_validation:{ip_address}",
        limit=limit,
        window_seconds=window_seconds
    )


async def check_admin_operation_rate_limit(user_id: str, limit: int = 100, window_seconds: int = 300) -> bool:
    """
    Check admin operation rate limit.

    Args:
        user_id: Admin user ID
        limit: Maximum admin operations (default: 100/5 minutes)
        window_seconds: Time window (default: 5 minutes)

    Returns:
        bool: True if request is allowed
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_fixed_window(
        key=f"admin_ops:{user_id}",
        limit=limit,
        window_seconds=window_seconds
    )


async def check_concurrent_session_limit(phone_number: str, limit: int = 5, window_seconds: int = 1800) -> bool:
    """
    Check concurrent session limit for phone number.

    Args:
        phone_number: Phone number
        limit: Maximum concurrent sessions (default: 5/30 minutes)
        window_seconds: Time window (default: 30 minutes)

    Returns:
        bool: True if request is allowed
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_sliding_window(
        key=f"concurrent_session:{phone_number}",
        limit=limit,
        window_seconds=window_seconds
    )


async def check_failed_authentication_rate_limit(identifier: str, limit: int = 5, window_seconds: int = 900) -> bool:
    """
    Check failed authentication rate limit.

    Args:
        identifier: IP address or phone number
        limit: Maximum failed attempts (default: 5/15 minutes)
        window_seconds: Time window (default: 15 minutes)

    Returns:
        bool: True if request is allowed
    """
    limiter = get_rate_limiter()
    return await limiter.is_allowed_fixed_window(
        key=f"failed_auth:{identifier}",
        limit=limit,
        window_seconds=window_seconds
    )


class AccountCreationRateLimiter:
    """
    Specialized rate limiter for account creation system.

    Provides comprehensive rate limiting for all account creation operations
    with different limits for different types of operations.
    """

    def __init__(self):
        """Initialize account creation rate limiter."""
        self.base_limiter = get_rate_limiter()
        self.logger = logging.getLogger(__name__)

    async def check_account_creation_attempt(self, phone_number: str, platform: str) -> bool:
        """
        Check if account creation attempt is allowed.

        Args:
            phone_number: Phone number
            platform: Platform name

        Returns:
            bool: True if allowed
        """
        # Multiple rate limiting checks
        phone_allowed = await check_account_creation_limit(phone_number)
        if not phone_allowed:
            self.logger.warning(f"Account creation rate limit exceeded for phone: {phone_number[:10]}***")
            return False

        # Platform-specific limits
        platform_allowed = await check_webhook_rate_limit(platform, phone_number)
        if not platform_allowed:
            self.logger.warning(f"Platform webhook rate limit exceeded for {platform}")
            return False

        return True

    async def check_phone_validation_request(self, phone_number: str, ip_address: str) -> bool:
        """
        Check if phone validation request is allowed.

        Args:
            phone_number: Phone number being validated
            ip_address: Client IP address

        Returns:
            bool: True if allowed
        """
        # Check IP-based rate limiting
        ip_allowed = await check_phone_validation_rate_limit(ip_address)
        if not ip_allowed:
            self.logger.warning(f"Phone validation rate limit exceeded for IP: {ip_address}")
            return False

        # Additional check for phone number to prevent abuse
        phone_allowed = await self.base_limiter.is_allowed_fixed_window(
            key=f"validate_phone:{phone_number}",
            limit=20,
            window_seconds=300  # 20 validations per 5 minutes per phone number
        )

        if not phone_allowed:
            self.logger.warning(f"Phone validation rate limit exceeded for phone: {phone_number[:10]}***")
            return False

        return True

    async def check_role_assignment_operation(self, user_id: int, admin_user_id: int) -> bool:
        """
        Check if role assignment operation is allowed.

        Args:
            user_id: Target user ID
            admin_user_id: Admin user ID performing operation

        Returns:
            bool: True if allowed
        """
        # Check admin operation limits
        admin_allowed = await check_admin_operation_rate_limit(str(admin_user_id))
        if not admin_allowed:
            self.logger.warning(f"Admin operation rate limit exceeded for user: {admin_user_id}")
            return False

        # Check per-user operation limits
        user_allowed = await self.base_limiter.is_allowed_fixed_window(
            key=f"role_assignment:{user_id}",
            limit=10,
            window_seconds=3600  # 10 role changes per hour per user
        )

        if not user_allowed:
            self.logger.warning(f"Role assignment rate limit exceeded for user: {user_id}")
            return False

        return True

    async def get_rate_limit_status(self, identifier: str, operation_type: str) -> Dict[str, Any]:
        """
        Get current rate limit status for identifier and operation.

        Args:
            identifier: Phone number, IP address, or user ID
            operation_type: Type of operation

        Returns:
            Dict with rate limit status
        """
        # Define limits for different operation types
        operation_limits = {
            "account_creation": (10, 3600),  # 10 per hour
            "phone_validation": (100, 60),   # 100 per minute
            "admin_operations": (100, 300), # 100 per 5 minutes
            "role_assignment": (10, 3600)  # 10 per hour
        }

        limit, window = operation_limits.get(operation_type, (100, 300))

        remaining = await self.base_limiter.get_remaining_requests(
            key=f"{operation_type}:{identifier}",
            limit=limit,
            window_seconds=window
        )

        return {
            "identifier": identifier,
            "operation_type": operation_type,
            "limit": limit,
            "remaining": remaining,
            "window_seconds": window,
            "is_blocked": remaining <= 0
        }

    async def reset_rate_limits(self, identifier: str, operation_type: Optional[str] = None):
        """
        Reset rate limits for identifier.

        Args:
            identifier: Phone number, IP address, or user ID
            operation_type: Specific operation type to reset (None for all)
        """
        if operation_type:
            await self.base_limiter.reset_limit(f"{operation_type}:{identifier}")
        else:
            # Reset all rate limits for this identifier
            for op_type in ["account_creation", "phone_validation", "admin_operations", "role_assignment"]:
                await self.base_limiter.reset_limit(f"{op_type}:{identifier}")


# Global account creation rate limiter instance
_account_rate_limiter: Optional[AccountCreationRateLimiter] = None


def get_account_creation_rate_limiter() -> AccountCreationRateLimiter:
    """Get global account creation rate limiter instance."""
    global _account_rate_limiter
    if _account_rate_limiter is None:
        _account_rate_limiter = AccountCreationRateLimiter()
    return _account_rate_limiter