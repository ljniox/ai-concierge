"""
Redis caching service for session management and performance optimization

Enhanced with synchronous support for the automatic account creation system.
"""

import json
import pickle
import os
from typing import Optional, Any, List, Dict, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse
import redis.asyncio as redis
import redis
from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.exceptions import CacheError, CacheConnectionError

logger = get_logger(__name__)


class RedisConfig:
    """Redis configuration management for account creation system."""

    def __init__(self):
        self.settings = get_settings()

        # Extract connection details from REDIS_URL if available
        redis_url = os.getenv("REDIS_URL", self.settings.redis_url if hasattr(self.settings, 'redis_url') else None)

        if redis_url:
            parsed = urlparse(redis_url)
            self.redis_host = parsed.hostname or "localhost"
            self.redis_port = parsed.port or 6379
            self.redis_password = parsed.password or os.getenv("REDIS_PASSWORD")
            self.redis_db = int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0
        else:
            self.redis_host = getattr(self.settings, 'redis_host', 'localhost')
            self.redis_port = getattr(self.settings, 'redis_port', 6379)
            self.redis_password = getattr(self.settings, 'redis_password', None) or os.getenv("REDIS_PASSWORD")
            self.redis_db = getattr(self.settings, 'redis_db', 0)

        # Cache TTL settings (seconds)
        self.session_ttl = int(os.getenv("REDIS_SESSION_TTL", "3600"))  # 1 hour
        self.rate_limit_ttl = int(os.getenv("REDIS_RATE_LIMIT_TTL", "300"))  # 5 minutes
        self.verification_code_ttl = int(os.getenv("REDIS_VERIFICATION_CODE_TTL", "600"))  # 10 minutes
        self.default_ttl = int(os.getenv("REDIS_DEFAULT_TTL", "1800"))  # 30 minutes
        self.redis_timeout = int(os.getenv("REDIS_TIMEOUT", "5"))
        self.redis_max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))


class RedisService:
    """Service for Redis caching operations with both async and sync support"""

    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or RedisConfig()
        self.settings = get_settings()
        self.redis: Optional[redis.Redis] = None
        self.sync_redis: Optional[redis.Redis] = None
        self._initialized = False
        # Don't initialize Redis connection during __init__ to avoid startup issues

    async def initialize(self):
        """Initialize Redis connections (both async and sync)"""
        if self._initialized:
            return

        try:
            # Initialize async Redis client
            redis_url = os.getenv("REDIS_URL", getattr(self.settings, 'redis_url', None))
            if redis_url:
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_connect_timeout=self.config.redis_timeout,
                    socket_timeout=self.config.redis_timeout,
                    retry_on_timeout=True
                )
            else:
                self.redis = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    password=self.config.redis_password,
                    db=self.config.redis_db,
                    decode_responses=False,
                    socket_connect_timeout=self.config.redis_timeout,
                    socket_timeout=self.config.redis_timeout,
                    retry_on_timeout=True
                )

            # Initialize sync Redis client for account creation system
            self.sync_redis = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password,
                db=self.config.redis_db,
                decode_responses=True,
                socket_connect_timeout=self.config.redis_timeout,
                socket_timeout=self.config.redis_timeout,
                retry_on_timeout=True
            )

            # Test async connection
            await self.redis.ping()

            # Test sync connection
            self.sync_redis.ping()

            self._initialized = True
            logger.info(
                "redis_clients_initialized",
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db
            )
        except Exception as e:
            logger.error("redis_initialization_failed", error=str(e))
            logger.warning("redis_will_be_disabled_gracefully")
            self.redis = None
            self.sync_redis = None
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure sync Redis client is initialized."""
        if not self._initialized:
            raise CacheConnectionError("Redis service not initialized. Call initialize() first.")

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        try:
            if isinstance(value, (dict, list, tuple)):
                return json.dumps(value, default=str)
            elif isinstance(value, (datetime,)):
                return value.isoformat()
            else:
                return str(value)
        except Exception as e:
            logger.error("Failed to serialize value for Redis", value=value, error=str(e))
            raise CacheError(f"Value serialization failed: {e}")

    def _deserialize_value(self, value: str, target_type: Optional[type] = None) -> Any:
        """Deserialize value from Redis storage."""
        if value is None:
            return None

        try:
            # Try JSON deserialization first
            try:
                result = json.loads(value)
                if target_type and target_type != str:
                    return target_type(result)
                return result
            except json.JSONDecodeError:
                # If not JSON, return as string or convert to target type
                if target_type == int:
                    return int(value)
                elif target_type == float:
                    return float(value)
                elif target_type == bool:
                    return value.lower() in ('true', '1', 'yes', 'on')
                else:
                    return value
        except Exception as e:
            logger.error("Failed to deserialize value from Redis", value=value, error=str(e))
            raise CacheError(f"Value deserialization failed: {e}")

    # Synchronous methods for account creation system
    def set_sync(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Set a value in Redis (synchronous)."""
        self._ensure_initialized()

        if not self.sync_redis:
            raise CacheConnectionError("Sync Redis client not initialized")

        try:
            # Add namespace prefix if provided
            full_key = f"{namespace}:{key}" if namespace else key

            # Serialize value
            serialized_value = self._serialize_value(value)

            # Set with TTL
            if ttl:
                result = self.sync_redis.setex(full_key, ttl, serialized_value)
            else:
                result = self.sync_redis.set(full_key, serialized_value)

            if result:
                logger.debug("Cache set successful", key=full_key, ttl=ttl)
            else:
                logger.warning("Cache set failed", key=full_key)

            return bool(result)

        except Exception as e:
            logger.error("Cache set failed", key=key, error=str(e))
            raise CacheError(f"Cache set failed: {e}")

    def get_sync(
        self,
        key: str,
        default: Any = None,
        target_type: Optional[type] = None,
        namespace: Optional[str] = None
    ) -> Any:
        """Get a value from Redis (synchronous)."""
        self._ensure_initialized()

        if not self.sync_redis:
            raise CacheConnectionError("Sync Redis client not initialized")

        try:
            # Add namespace prefix if provided
            full_key = f"{namespace}:{key}" if namespace else key

            # Get value from Redis
            value = self.sync_redis.get(full_key)

            if value is None:
                logger.debug("Cache miss", key=full_key)
                return default

            # Deserialize value
            result = self._deserialize_value(value, target_type)
            logger.debug("Cache hit", key=full_key)
            return result

        except Exception as e:
            logger.error("Cache get failed", key=key, error=str(e))
            return default

    def delete_sync(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete a key from Redis (synchronous)."""
        self._ensure_initialized()

        if not self.sync_redis:
            raise CacheConnectionError("Sync Redis client not initialized")

        try:
            # Add namespace prefix if provided
            full_key = f"{namespace}:{key}" if namespace else key

            # Delete key
            result = self.sync_redis.delete(full_key)
            return bool(result)

        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False

    def exists_sync(self, key: str, namespace: Optional[str] = None) -> bool:
        """Check if a key exists in Redis (synchronous)."""
        self._ensure_initialized()

        if not self.sync_redis:
            raise CacheConnectionError("Sync Redis client not initialized")

        try:
            # Add namespace prefix if provided
            full_key = f"{namespace}:{key}" if namespace else key

            # Check existence
            result = self.sync_redis.exists(full_key)
            return bool(result)

        except Exception as e:
            logger.error("Cache exists check failed", key=key, error=str(e))
            return False

    def increment_sync(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> int:
        """Increment a numeric value in Redis (synchronous)."""
        self._ensure_initialized()

        if not self.sync_redis:
            raise CacheConnectionError("Sync Redis client not initialized")

        try:
            # Add namespace prefix if provided
            full_key = f"{namespace}:{key}" if namespace else key

            # Increment value
            result = self.sync_redis.incrby(full_key, amount)

            # Set TTL if this is a new key and TTL is specified
            if ttl and result == amount:
                self.sync_redis.expire(full_key, ttl)

            logger.debug("Cache increment successful", key=full_key, result=result)
            return result

        except Exception as e:
            logger.error("Cache increment failed", key=key, error=str(e))
            raise CacheError(f"Cache increment failed: {e}")

    # Account creation system specific methods
    def set_session_data_sync(self, session_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store session data in Redis (synchronous)."""
        return self.set_sync(
            key=session_id,
            value=data,
            ttl=ttl or self.config.session_ttl,
            namespace="session"
        )

    def get_session_data_sync(self, session_id: str) -> Dict[str, Any]:
        """Get session data from Redis (synchronous)."""
        return self.get_sync(
            key=session_id,
            default={},
            target_type=dict,
            namespace="session"
        )

    def delete_session_sync(self, session_id: str) -> bool:
        """Delete session data from Redis (synchronous)."""
        return self.delete_sync(key=session_id, namespace="session")

    def set_verification_code_sync(
        self,
        identifier: str,
        code: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Store verification code in Redis (synchronous)."""
        return self.set_sync(
            key=identifier,
            value=code,
            ttl=ttl or self.config.verification_code_ttl,
            namespace="verification"
        )

    def get_verification_code_sync(self, identifier: str) -> Optional[str]:
        """Get verification code from Redis (synchronous)."""
        return self.get_sync(
            key=identifier,
            namespace="verification"
        )

    def delete_verification_code_sync(self, identifier: str) -> bool:
        """Delete verification code from Redis (synchronous)."""
        return self.delete_sync(key=identifier, namespace="verification")

    def check_rate_limit_sync(
        self,
        identifier: str,
        limit: int,
        window: int,
        namespace: str = "rate_limit"
    ) -> Dict[str, Any]:
        """Check rate limit for an identifier (synchronous)."""
        try:
            current_count = self.increment_sync(
                key=identifier,
                amount=1,
                ttl=window,
                namespace=namespace
            )

            ttl = self.sync_redis.ttl(f"{namespace}:{identifier}")
            is_allowed = current_count <= limit
            reset_time = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None

            return {
                "allowed": is_allowed,
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "current": current_count,
                "reset_time": reset_time.isoformat() if reset_time else None,
                "retry_after": ttl if not is_allowed and ttl > 0 else 0
            }

        except Exception as e:
            logger.error("Rate limit check failed", identifier=identifier, error=str(e))
            # Allow request if rate limiting fails
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit,
                "current": 0,
                "reset_time": None,
                "retry_after": 0,
                "error": str(e)
            }

    def health_check_sync(self) -> Dict[str, Any]:
        """Perform Redis health check (synchronous)."""
        try:
            if not self._initialized:
                return {
                    "status": "unhealthy",
                    "error": "Redis not initialized",
                    "timestamp": None
                }

            # Test basic operations with sync client
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": datetime.now().isoformat()}

            # Test set and get
            self.set_sync(test_key, test_value, ttl=10)
            retrieved_value = self.get_sync(test_key)
            self.delete_sync(test_key)

            # Get Redis info
            info = self.sync_redis.info() if self.sync_redis else {}

            return {
                "status": "healthy",
                "test_passed": retrieved_value == test_value,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return await self.redis.ping()
        except Exception as e:
            logger.error("redis_ping_failed", error=str(e))
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value:
                try:
                    # Try to decode as JSON first
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Fall back to pickle for complex objects
                    return pickle.loads(value)
            return None
        except Exception as e:
            logger.error("redis_get_failed", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        use_pickle: bool = False
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
            use_pickle: Use pickle serialization for complex objects

        Returns:
            True if successful, False otherwise
        """
        try:
            if use_pickle:
                serialized_value = pickle.dumps(value)
            else:
                # Use JSON for simple objects
                serialized_value = json.dumps(value, default=str).encode('utf-8')

            if expire:
                await self.redis.setex(key, expire, serialized_value)
            else:
                await self.redis.set(key, serialized_value)

            logger.debug("redis_set_success", key=key, expire=expire)
            return True
        except Exception as e:
            logger.error("redis_set_failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error("redis_delete_failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error("redis_exists_failed", key=key, error=str(e))
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error("redis_expire_failed", key=key, error=str(e))
            return False

    async def ttl(self, key: str) -> int:
        """
        Get time-to-live for a key

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error("redis_ttl_failed", key=key, error=str(e))
            return -2

    # Session-specific caching methods
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data from cache

        Args:
            session_id: Session ID

        Returns:
            Session data or None
        """
        key = f"session:{session_id}"
        return await self.get(key)

    async def set_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        expire: Optional[int] = None
    ) -> bool:
        """
        Set session data in cache

        Args:
            session_id: Session ID
            session_data: Session data to cache
            expire: Expiration time in seconds (default: session_timeout_minutes)

        Returns:
            True if successful, False otherwise
        """
        key = f"session:{session_id}"
        if expire is None:
            expire = self.settings.session_timeout_minutes * 60
        return await self.set(key, session_data, expire)

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session from cache

        Args:
            session_id: Session ID

        Returns:
            True if successful, False otherwise
        """
        key = f"session:{session_id}"
        return await self.delete(key)

    async def get_user_active_session(self, user_id: str) -> Optional[str]:
        """
        Get active session ID for a user

        Args:
            user_id: User ID

        Returns:
            Session ID or None
        """
        key = f"user_active_session:{user_id}"
        return await self.get(key)

    async def set_user_active_session(
        self,
        user_id: str,
        session_id: str,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set active session ID for a user

        Args:
            user_id: User ID
            session_id: Session ID
            expire: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"user_active_session:{user_id}"
        if expire is None:
            expire = self.settings.session_timeout_minutes * 60
        return await self.set(key, session_id, expire)

    async def delete_user_active_session(self, user_id: str) -> bool:
        """
        Delete active session ID for a user

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        key = f"user_active_session:{user_id}"
        return await self.delete(key)

    # Rate limiting methods
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Dict[str, Any]:
        """
        Check and update rate limit using sliding window algorithm

        Args:
            key: Rate limit key (e.g., user_id or phone number)
            limit: Maximum number of requests
            window: Time window in seconds

        Returns:
            Dict with rate limit status
        """
        try:
            current_time = datetime.now().timestamp()
            window_start = current_time - window

            # Check if Redis is available
            if self.redis is None:
                logger.warning("redis_not_available", key=key)
                return {
                    "allowed": True,
                    "remaining": limit,
                    "reset_time": current_time + window,
                    "note": "Redis not available - rate limiting disabled"
                }

            # Remove old entries
            await self.redis.zremrangebyscore(key, 0, window_start)

            # Count current requests
            current_count = await self.redis.zcard(key)

            # Check if limit exceeded
            if current_count >= limit:
                reset_time = await self.redis.zrange(key, 0, 0, withscores=True)
                reset_timestamp = reset_time[0][1] if reset_time else current_time + window

                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": int(reset_timestamp + window),
                    "current_count": current_count
                }

            # Add current request
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, window)

            return {
                "allowed": True,
                "remaining": limit - current_count - 1,
                "reset_time": int(current_time + window),
                "current_count": current_count + 1
            }

        except Exception as e:
            logger.error("rate_limit_check_failed", key=key, error=str(e))
            return {"allowed": True, "remaining": limit, "reset_time": 0, "current_count": 0}

    # Message queue methods
    async def enqueue_message(
        self,
        queue_name: str,
        message_data: Dict[str, Any],
        priority: int = 0
    ) -> bool:
        """
        Enqueue a message for processing

        Args:
            queue_name: Queue name
            message_data: Message data
            priority: Message priority (higher = higher priority)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use sorted set for priority queue
            score = priority * 1000000 + datetime.now().timestamp()
            key = f"queue:{queue_name}"

            await self.redis.zadd(key, {json.dumps(message_data): score})
            logger.debug("message_enqueued", queue=queue_name, priority=priority)
            return True
        except Exception as e:
            logger.error("message_enqueue_failed", queue=queue_name, error=str(e))
            return False

    async def dequeue_message(
        self,
        queue_name: str,
        timeout: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Dequeue a message with highest priority

        Args:
            queue_name: Queue name
            timeout: Timeout in seconds

        Returns:
            Message data or None if no message
        """
        try:
            key = f"queue:{queue_name}"

            # Get message with highest score (lowest timestamp for same priority)
            result = await self.redis.zrevrange(key, 0, 0, withscores=True)

            if not result:
                return None

            message_json, score = result[0]

            # Remove from queue
            await self.redis.zrem(key, message_json)

            message_data = json.loads(message_json)
            logger.debug("message_dequeued", queue=queue_name)
            return message_data

        except Exception as e:
            logger.error("message_dequeue_failed", queue=queue_name, error=str(e))
            return None

    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get queue length

        Args:
            queue_name: Queue name

        Returns:
            Number of messages in queue
        """
        try:
            key = f"queue:{queue_name}"
            return await self.redis.zcard(key)
        except Exception as e:
            logger.error("queue_length_failed", queue=queue_name, error=str(e))
            return 0

    # Cache statistics
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics

        Returns:
            Cache statistics
        """
        try:
            info = await self.redis.info("memory")
            stats = {
                "connected": await self.ping(),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }

            # Calculate hit rate
            hits = stats.get("keyspace_hits", 0)
            misses = stats.get("keyspace_misses", 0)
            total = hits + misses
            stats["hit_rate"] = round(hits / total * 100, 2) if total > 0 else 0.0

            return stats
        except Exception as e:
            logger.error("cache_stats_failed", error=str(e))
            return {"connected": False, "error": str(e)}

    # Cleanup methods
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired session keys

        Returns:
            Number of keys removed
        """
        try:
            pattern = "session:*"
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                ttl = await self.redis.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    continue
                elif ttl == -1:  # No expiration, check if should be expired
                    # For session keys without TTL, we'll clean them up
                    # based on session timeout configuration
                    session_data = await self.get(key)
                    if session_data:
                        expires_at = session_data.get("expires_at")
                        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                            keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info("expired_sessions_cleaned", count=deleted)
                return deleted

            return 0
        except Exception as e:
            logger.error("session_cleanup_failed", error=str(e))
            return 0

    async def clear_all_cache(self) -> bool:
        """
        Clear all cache data (use with caution)

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.redis.flushdb()
            logger.info("cache_cleared")
            return True
        except Exception as e:
            logger.error("cache_clear_failed", error=str(e))
            return False

    async def close(self):
        """Close Redis connections"""
        if self.redis:
            await self.redis.close()
        if self.sync_redis:
            self.sync_redis.close()
        self._initialized = False
        logger.info("redis_connections_closed")

    def close_sync(self):
        """Close synchronous Redis connection"""
        if self.sync_redis:
            self.sync_redis.close()
        self._initialized = False
        logger.info("sync_redis_connection_closed")


# Global Redis service instance and convenience functions
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Get the global Redis service instance."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service


def initialize_redis() -> RedisService:
    """Initialize the global Redis service."""
    service = get_redis_service()
    return service


# Synchronous convenience functions for account creation system
def cache_set_sync(
    key: str,
    value: Any,
    ttl: Optional[int] = None,
    namespace: Optional[str] = None
) -> bool:
    """Set a value in Redis using the global service."""
    service = get_redis_service()
    return service.set_sync(key, value, ttl, namespace)


def cache_get_sync(
    key: str,
    default: Any = None,
    target_type: Optional[type] = None,
    namespace: Optional[str] = None
) -> Any:
    """Get a value from Redis using the global service."""
    service = get_redis_service()
    return service.get_sync(key, default, target_type, namespace)


def cache_delete_sync(key: str, namespace: Optional[str] = None) -> bool:
    """Delete a key from Redis using the global service."""
    service = get_redis_service()
    return service.delete_sync(key, namespace)


def cache_exists_sync(key: str, namespace: Optional[str] = None) -> bool:
    """Check if a key exists in Redis using the global service."""
    service = get_redis_service()
    return service.exists_sync(key, namespace)


def set_session_data_sync(session_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
    """Store session data using the global service."""
    service = get_redis_service()
    return service.set_session_data_sync(session_id, data, ttl)


def get_session_data_sync(session_id: str) -> Dict[str, Any]:
    """Get session data using the global service."""
    service = get_redis_service()
    return service.get_session_data_sync(session_id)


def delete_session_sync(session_id: str) -> bool:
    """Delete session data using the global service."""
    service = get_redis_service()
    return service.delete_session_sync(session_id)


def set_verification_code_sync(identifier: str, code: str, ttl: Optional[int] = None) -> bool:
    """Store verification code using the global service."""
    service = get_redis_service()
    return service.set_verification_code_sync(identifier, code, ttl)


def get_verification_code_sync(identifier: str) -> Optional[str]:
    """Get verification code using the global service."""
    service = get_redis_service()
    return service.get_verification_code_sync(identifier)


def delete_verification_code_sync(identifier: str) -> bool:
    """Delete verification code using the global service."""
    service = get_redis_service()
    return service.delete_verification_code_sync(identifier)


def check_rate_limit_sync(
    identifier: str,
    limit: int,
    window: int,
    namespace: str = "rate_limit"
) -> Dict[str, Any]:
    """Check rate limit using the global service."""
    service = get_redis_service()
    return service.check_rate_limit_sync(identifier, limit, window, namespace)


def check_redis_health_sync() -> Dict[str, Any]:
    """Check Redis health using the global service."""
    service = get_redis_service()
    return service.health_check_sync()