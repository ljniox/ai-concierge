"""
Session Management Service

This service handles user session management with dual persistence
in both Supabase (long-term storage) and Redis (fast access).
Enhanced for Phase 3 with comprehensive session lifecycle management.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from src.models.user_session import UserSession, SessionStatus, SessionType
from src.services.database_service import get_database_service
from src.services.redis_service import get_redis_service
from src.utils.logging import get_logger
from src.utils.exceptions import (
    DatabaseConnectionError,
    SessionNotFoundError,
    ValidationError,
    SecurityError
)


class SessionManagementService:
    """
    Service for managing user sessions with dual persistence.

    This service provides session management with both long-term storage
    in Supabase and fast access through Redis caching.
    """

    def __init__(
        self,
        database_service=None,
        redis_service=None,
        session_timeout_minutes: int = 60,
        redis_ttl_seconds: int = 3600
    ):
        """
        Initialize session management service.

        Args:
            database_service: Database service instance
            redis_service: Redis service instance
            session_timeout_minutes: Default session timeout in minutes
            redis_ttl_seconds: Redis TTL for session cache
        """
        self.database_service = database_service or get_database_service()
        self.redis_service = redis_service or get_redis_service()
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.redis_ttl = redis_ttl_seconds
        self.logger = get_logger(__name__)

    async def create_session(
        self,
        user_id: UUID,
        platform: str,
        platform_user_id: str,
        session_type: SessionType = SessionType.INTERACTIVE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            user_id: User ID
            platform: Platform name (telegram, whatsapp, api)
            platform_user_id: Platform-specific user ID
            session_type: Type of session
            metadata: Additional session metadata

        Returns:
            Created session
        """
        try:
            # Generate session ID
            session_id = uuid4()
            now = datetime.now(timezone.utc)
            expires_at = now + self.session_timeout

            # Create session object
            session = UserSession(
                id=session_id,
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                session_type=session_type,
                status=SessionStatus.ACTIVE,
                started_at=now,
                last_activity_at=now,
                expires_at=expires_at,
                metadata=metadata or {}
            )

            # Save to database (long-term storage)
            session_dict = session.to_dict()
            await self.database_service.insert(
                "user_sessions",
                session_dict,
                database_name="supabase"
            )

            # Cache in Redis for fast access
            await self._cache_session(session)

            self.logger.info(
                f"Session created: {session_id} for user {user_id} on {platform}"
            )
            return session

        except Exception as e:
            self.logger.error(f"Failed to create session: {str(e)}")
            raise DatabaseConnectionError(f"Session creation failed: {str(e)}")

    async def get_session(self, session_id: UUID) -> Optional[UserSession]:
        """
        Get session by ID (with cache lookup).

        Args:
            session_id: Session ID

        Returns:
            Session if found, None otherwise
        """
        try:
            # Try Redis cache first
            cached_session = await self._get_cached_session(session_id)
            if cached_session:
                # Check if session is still valid
                if cached_session.expires_at > datetime.now(timezone.utc):
                    await self._update_last_activity(session_id)
                    return cached_session
                else:
                    # Session expired, remove from cache
                    await self._remove_cached_session(session_id)

            # Fallback to database
            session = await self._get_session_from_db(session_id)
            if session:
                # Check if session is still valid
                if session.expires_at > datetime.now(timezone.utc):
                    # Cache the session for future access
                    await self._cache_session(session)
                    await self._update_last_activity(session_id)
                    return session
                else:
                    # Mark session as expired
                    await self._mark_session_expired(session_id)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None

    async def get_active_session(
        self,
        user_id: UUID,
        platform: str,
        platform_user_id: str
    ) -> Optional[UserSession]:
        """
        Get active session for a user on a specific platform.

        Args:
            user_id: User ID
            platform: Platform name
            platform_user_id: Platform-specific user ID

        Returns:
            Active session if found, None otherwise
        """
        try:
            # Check Redis cache first for active session key
            cache_key = f"active_session:{platform}:{platform_user_id}"
            cached_session_id = await self.redis_service.get(cache_key)

            if cached_session_id:
                session_id = UUID(cached_session_id)
                session = await self.get_session(session_id)
                if session and session.status == SessionStatus.ACTIVE:
                    return session

            # Fallback to database query
            query = """
            SELECT * FROM user_sessions
            WHERE user_id = ? AND platform = ? AND platform_user_id = ?
              AND status = 'ACTIVE' AND expires_at > ?
            ORDER BY last_activity_at DESC
            LIMIT 1
            """

            result = await self.database_service.fetch_one(
                query,
                (str(user_id), platform, platform_user_id, datetime.now(timezone.utc)),
                database_name="supabase"
            )

            if result:
                session_dict = dict(result)
                session = UserSession(**session_dict)

                # Cache the active session reference
                await self.redis_service.set(
                    cache_key,
                    str(session.id),
                    ttl=self.redis_ttl
                )

                # Cache the full session
                await self._cache_session(session)

                return session

            return None

        except Exception as e:
            self.logger.error(f"Failed to get active session: {str(e)}")
            return None

    async def update_session(
        self,
        session_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
        extend_session: bool = True
    ) -> bool:
        """
        Update session metadata and optionally extend expiration.

        Args:
            session_id: Session ID
            metadata: New metadata to merge
            extend_session: Whether to extend session expiration

        Returns:
            True if update successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False

            # Update metadata
            if metadata:
                session.metadata.update(metadata)

            # Update last activity
            session.last_activity_at = datetime.now(timezone.utc)

            # Extend expiration if requested
            if extend_session:
                session.expires_at = datetime.now(timezone.utc) + self.session_timeout

            # Update database
            update_data = {
                "metadata": json.dumps(session.metadata),
                "last_activity_at": session.last_activity_at,
                "expires_at": session.expires_at,
                "updated_at": datetime.now(timezone.utc)
            }

            await self.database_service.update(
                "user_sessions",
                update_data,
                {"id": str(session_id)},
                database_name="supabase"
            )

            # Update cache
            await self._cache_session(session)

            self.logger.info(f"Session updated: {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update session {session_id}: {str(e)}")
            return False

    async def end_session(self, session_id: UUID, reason: str = "user_logout") -> bool:
        """
        End a session.

        Args:
            session_id: Session ID
            reason: Reason for ending session

        Returns:
            True if session ended successfully, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False

            # Update session status
            session.status = SessionStatus.ENDED
            session.ended_at = datetime.now(timezone.utc)
            session.last_activity_at = session.ended_at

            # Update database
            update_data = {
                "status": session.status.value,
                "ended_at": session.ended_at,
                "last_activity_at": session.last_activity_at,
                "end_reason": reason,
                "updated_at": datetime.now(timezone.utc)
            }

            await self.database_service.update(
                "user_sessions",
                update_data,
                {"id": str(session_id)},
                database_name="supabase"
            )

            # Remove from cache
            await self._remove_cached_session(session_id)
            await self._remove_active_session_reference(session)

            self.logger.info(f"Session ended: {session_id} (reason: {reason})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to end session {session_id}: {str(e)}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        try:
            # Find expired sessions in database
            query = """
            SELECT id, platform, platform_user_id FROM user_sessions
            WHERE status = 'ACTIVE' AND expires_at < ?
            """

            expired_sessions = await self.database_service.fetch_all(
                query,
                (datetime.now(timezone.utc),),
                database_name="supabase"
            )

            cleanup_count = 0
            for session in expired_sessions:
                session_id = UUID(session['id'])

                # Mark as expired in database
                await self._mark_session_expired(session_id)

                # Remove from cache
                cache_key = f"active_session:{session['platform']}:{session['platform_user_id']}"
                await self.redis_service.delete(cache_key)

                cleanup_count += 1

            self.logger.info(f"Cleaned up {cleanup_count} expired sessions")
            return cleanup_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0

    async def get_user_sessions(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50
    ) -> List[UserSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of sessions to return

        Returns:
            List of sessions
        """
        try:
            where_clause = "WHERE user_id = ?"
            params = [str(user_id)]

            if status:
                where_clause += " AND status = ?"
                params.append(status.value)

            query = f"""
            SELECT * FROM user_sessions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
            """

            results = await self.database_service.fetch_all(
                query,
                params + [limit],
                database_name="supabase"
            )

            sessions = []
            for result in results:
                session_dict = dict(result)
                session = UserSession(**session_dict)
                sessions.append(session)

            return sessions

        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {str(e)}")
            return []

    async def _cache_session(self, session: UserSession) -> None:
        """Cache session in Redis."""
        try:
            cache_key = f"session:{session.id}"
            session_json = json.dumps(session.to_dict(), default=str)
            await self.redis_service.set(cache_key, session_json, ttl=self.redis_ttl)

            # Also cache active session reference
            if session.status == SessionStatus.ACTIVE:
                active_cache_key = f"active_session:{session.platform}:{session.platform_user_id}"
                await self.redis_service.set(
                    active_cache_key,
                    str(session.id),
                    ttl=self.redis_ttl
                )

        except Exception as e:
            self.logger.error(f"Failed to cache session: {str(e)}")

    async def _get_cached_session(self, session_id: UUID) -> Optional[UserSession]:
        """Get session from Redis cache."""
        try:
            cache_key = f"session:{session_id}"
            session_json = await self.redis_service.get(cache_key)

            if session_json:
                session_dict = json.loads(session_json)
                return UserSession(**session_dict)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get cached session: {str(e)}")
            return None

    async def _remove_cached_session(self, session_id: UUID) -> None:
        """Remove session from Redis cache."""
        try:
            cache_key = f"session:{session_id}"
            await self.redis_service.delete(cache_key)

        except Exception as e:
            self.logger.error(f"Failed to remove cached session: {str(e)}")

    async def _remove_active_session_reference(self, session: UserSession) -> None:
        """Remove active session reference from Redis."""
        try:
            cache_key = f"active_session:{session.platform}:{session.platform_user_id}"
            await self.redis_service.delete(cache_key)

        except Exception as e:
            self.logger.error(f"Failed to remove active session reference: {str(e)}")

    async def _update_last_activity(self, session_id: UUID) -> None:
        """Update last activity timestamp in cache."""
        try:
            cache_key = f"session:{session_id}"
            session_json = await self.redis_service.get(cache_key)

            if session_json:
                session_dict = json.loads(session_json)
                session_dict['last_activity_at'] = datetime.now(timezone.utc).isoformat()

                await self.redis_service.set(
                    cache_key,
                    json.dumps(session_dict, default=str),
                    ttl=self.redis_ttl
                )

        except Exception as e:
            self.logger.error(f"Failed to update last activity: {str(e)}")

    async def _get_session_from_db(self, session_id: UUID) -> Optional[UserSession]:
        """Get session from database."""
        try:
            query = "SELECT * FROM user_sessions WHERE id = ?"
            result = await self.database_service.fetch_one(
                query,
                (str(session_id),),
                database_name="supabase"
            )

            if result:
                session_dict = dict(result)
                return UserSession(**session_dict)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get session from DB: {str(e)}")
            return None

    async def _mark_session_expired(self, session_id: UUID) -> None:
        """Mark session as expired in database."""
        try:
            update_data = {
                "status": SessionStatus.EXPIRED.value,
                "ended_at": datetime.now(timezone.utc),
                "end_reason": "expired",
                "updated_at": datetime.now(timezone.utc)
            }

            await self.database_service.update(
                "user_sessions",
                update_data,
                {"id": str(session_id)},
                database_name="supabase"
            )

        except Exception as e:
            self.logger.error(f"Failed to mark session as expired: {str(e)}")


# Factory function for getting session management service
def get_session_management_service() -> SessionManagementService:
    """Get session management service instance."""
    return SessionManagementService()