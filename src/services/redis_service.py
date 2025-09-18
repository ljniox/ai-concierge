"""
Redis caching service for session management and performance optimization
"""

import json
import pickle
from typing import Optional, Any, List, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis
from src.utils.config import get_settings
import structlog

logger = structlog.get_logger()


class RedisService:
    """Service for Redis caching operations"""

    def __init__(self):
        self.settings = get_settings()
        self.redis: Optional[redis.Redis] = None
        # Don't initialize Redis connection during __init__ to avoid startup issues

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                decode_responses=False,  # Use pickle/JSON for complex objects
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            logger.info(
                "redis_client_initialized",
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db
            )
        except Exception as e:
            logger.error("redis_initialization_failed", error=str(e))
            # Don't raise - allow application to start without Redis

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
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("redis_connection_closed")