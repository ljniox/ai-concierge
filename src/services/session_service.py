"""
Session service for managing conversation sessions
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from supabase import Client
from src.models.session import Session, SessionCreate, SessionUpdate, SessionStatus, SessionWithStats
from src.models.user import User
from src.services.user_service import UserService
from src.utils.config import get_settings
import structlog
import re

logger = structlog.get_logger()


def parse_datetime_with_varying_precision(datetime_str: str) -> datetime:
    """
    Parse datetime string with varying microsecond precision

    Args:
        datetime_str: Datetime string that may have 5 or 6 digit microseconds

    Returns:
        Parsed datetime object
    """
    try:
        # Try normal parsing first
        return datetime.fromisoformat(datetime_str)
    except ValueError:
        # Handle case where microseconds have 5 digits instead of 6
        # Pattern: YYYY-MM-DDTHH:MM:SS.microseconds+timezone
        pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.)(\d{1,6})([+-]\d{2}:\d{2})$'
        match = re.match(pattern, datetime_str)
        if match:
            date_part, microseconds, timezone = match.groups()
            # Pad microseconds to 6 digits
            microseconds_padded = microseconds.ljust(6, '0')
            fixed_datetime_str = f"{date_part}{microseconds_padded}{timezone}"
            return datetime.fromisoformat(fixed_datetime_str)
        else:
            # Try other common formats
            for fmt in ['%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse datetime: {datetime_str}")


class SessionService:
    """Service for managing session operations"""

    def __init__(self):
        self.settings = get_settings()
        self.supabase: Optional[Client] = None
        self.user_service = UserService()
        self._initialize_supabase()

    def _initialize_supabase(self):
        """Initialize Supabase client"""
        try:
            from supabase import create_client
            # Initialize Supabase with minimal parameters to avoid proxy issues
            self.supabase = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key
            )
            logger.info("supabase_client_initialized")
        except Exception as e:
            logger.error("supabase_initialization_failed", error=str(e))
            # Don't raise - allow application to start without Supabase
            self.supabase = None

    async def create_session(self, session_data: SessionCreate) -> Session:
        """
        Create a new session

        Args:
            session_data: Session creation data

        Returns:
            Created session object
        """
        try:
            logger.info("creating_session", user_id=session_data.user_id)

            # Verify user exists
            user = await self.user_service.get_user_by_id(session_data.user_id)
            if not user:
                raise ValueError(f"User {session_data.user_id} not found")

            # Create session
            session_dict = {
                "user_id": session_data.user_id,
                "status": session_data.status.value if isinstance(session_data.status, SessionStatus) else session_data.status,
                "current_service": session_data.current_service,
                "context": session_data.context or {},
                "metadata": session_data.metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=self.settings.session_timeout_minutes)).isoformat(),
                "last_activity_at": datetime.now().isoformat(),
                "message_count": 0
            }

            response = self.supabase.table("sessions").insert(session_dict).execute()

            if response.data:
                created_session = Session(
                    id=response.data[0]["id"],
                    user_id=session_data.user_id,
                    status=SessionStatus(session_data.status),
                    current_service=session_data.current_service,
                    context=session_data.context or {},
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(minutes=self.settings.session_timeout_minutes),
                    last_activity_at=datetime.now(),
                    message_count=0
                )
                logger.info("session_created_successfully", session_id=created_session.id)
                return created_session
            else:
                raise Exception("Failed to create session")

        except Exception as e:
            logger.error("session_creation_failed", user_id=session_data.user_id, error=str(e))
            raise

    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session object if found, None otherwise
        """
        try:
            logger.info("getting_session_by_id", session_id=session_id)

            response = self.supabase.table("sessions").select("*").eq("id", session_id).execute()

            if response.data:
                session_data = response.data[0]
                return Session(
                    id=session_data["id"],
                    user_id=session_data["user_id"],
                    status=SessionStatus(session_data["status"]),
                    current_service=session_data["current_service"],
                    context=session_data.get("context", {}),
                    metadata=session_data.get("metadata", {}),
                    created_at=parse_datetime_with_varying_precision(session_data["created_at"]),
                    updated_at=parse_datetime_with_varying_precision(session_data["updated_at"]),
                    expires_at=parse_datetime_with_varying_precision(session_data["expires_at"]) if session_data.get("expires_at") else None,
                    last_activity_at=parse_datetime_with_varying_precision(session_data["last_activity_at"]),
                    message_count=session_data.get("message_count", 0)
                )
            return None

        except Exception as e:
            logger.error("get_session_by_id_failed", session_id=session_id, error=str(e))
            raise

    async def get_active_session_by_user(self, user_id: str) -> Optional[Session]:
        """
        Get active session for a user

        Args:
            user_id: User ID

        Returns:
            Active session if found, None otherwise
        """
        try:
            logger.info("getting_active_session_by_user", user_id=user_id)

            response = self.supabase.table("sessions").select("*").eq("user_id", user_id).eq("status", "active").execute()

            if response.data:
                # Return the most recent active session
                session_data = response.data[0]
                session = Session(
                    id=session_data["id"],
                    user_id=session_data["user_id"],
                    status=SessionStatus(session_data["status"]),
                    current_service=session_data["current_service"],
                    context=session_data.get("context", {}),
                    metadata=session_data.get("metadata", {}),
                    created_at=parse_datetime_with_varying_precision(session_data["created_at"]),
                    updated_at=parse_datetime_with_varying_precision(session_data["updated_at"]),
                    expires_at=parse_datetime_with_varying_precision(session_data["expires_at"]) if session_data.get("expires_at") else None,
                    last_activity_at=parse_datetime_with_varying_precision(session_data["last_activity_at"]),
                    message_count=session_data.get("message_count", 0)
                )

                # Check if session is still valid
                if session.is_active_session:
                    return session
                else:
                    # Mark as expired
                    await self.expire_session(session.id)
                    return None

            return None

        except Exception as e:
            logger.error("get_active_session_by_user_failed", user_id=user_id, error=str(e))
            raise

    async def create_or_get_session(self, user_id: str) -> Session:
        """
        Get existing active session or create new one

        Args:
            user_id: User ID

        Returns:
            Session object
        """
        session = await self.get_active_session_by_user(user_id)
        if session:
            logger.info("using_existing_session", session_id=session.id, user_id=user_id)
            return session
        else:
            logger.info("creating_new_session", user_id=user_id)
            session_data = SessionCreate(user_id=user_id)
            return await self.create_session(session_data)

    async def update_session(self, session_id: str, session_data: SessionUpdate) -> Session:
        """
        Update session information

        Args:
            session_id: Session ID to update
            session_data: Update data

        Returns:
            Updated session object
        """
        try:
            logger.info("updating_session", session_id=session_id)

            # Build update dictionary with only provided fields
            update_dict = {}
            for field, value in session_data.dict(exclude_unset=True).items():
                if value is not None:
                    if isinstance(value, SessionStatus):
                        update_dict[field] = value.value
                    else:
                        update_dict[field] = value

            if update_dict:
                update_dict["updated_at"] = datetime.now().isoformat()
                update_dict["last_activity_at"] = datetime.now().isoformat()

                response = self.supabase.table("sessions").update(update_dict).eq("id", session_id).execute()

                if response.data:
                    updated_session = await self.get_session_by_id(session_id)
                    logger.info("session_updated_successfully", session_id=session_id)
                    return updated_session
                else:
                    raise Exception("Failed to update session")
            else:
                # No fields to update, just update activity
                await self.update_session_activity(session_id)
                return await self.get_session_by_id(session_id)

        except Exception as e:
            logger.error("session_update_failed", session_id=session_id, error=str(e))
            raise

    async def update_session_activity(self, session_id: str):
        """
        Update session last activity timestamp

        Args:
            session_id: Session ID to update
        """
        try:
            update_dict = {
                "updated_at": datetime.now().isoformat(),
                "last_activity_at": datetime.now().isoformat()
            }

            self.supabase.table("sessions").update(update_dict).eq("id", session_id).execute()
            logger.info("session_activity_updated", session_id=session_id)

        except Exception as e:
            logger.error("session_activity_update_failed", session_id=session_id, error=str(e))
            raise

    async def increment_message_count(self, session_id: str):
        """
        Increment session message count

        Args:
            session_id: Session ID to update
        """
        try:
            # Get current count
            session = await self.get_session_by_id(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            new_count = session.message_count + 1

            update_dict = {
                "message_count": new_count,
                "updated_at": datetime.now().isoformat(),
                "last_activity_at": datetime.now().isoformat()
            }

            self.supabase.table("sessions").update(update_dict).eq("id", session_id).execute()
            logger.info("session_message_count_incremented", session_id=session_id, new_count=new_count)

        except Exception as e:
            logger.error("session_message_count_increment_failed", session_id=session_id, error=str(e))
            raise

    async def expire_session(self, session_id: str):
        """
        Mark session as expired

        Args:
            session_id: Session ID to expire
        """
        logger.info("expiring_session", session_id=session_id)
        update_data = SessionUpdate(status=SessionStatus.EXPIRED)
        return await self.update_session(session_id, update_data)

    async def close_session(self, session_id: str):
        """
        Close session

        Args:
            session_id: Session ID to close
        """
        logger.info("closing_session", session_id=session_id)
        update_data = SessionUpdate(status=SessionStatus.CLOSED)
        return await self.update_session(session_id, update_data)

    async def cleanup_expired_sessions(self):
        """
        Clean up expired sessions
        """
        try:
            logger.info("cleaning_up_expired_sessions")

            # Find expired sessions
            expired_time = datetime.now().isoformat()
            response = self.supabase.table("sessions").select("id").lt("expires_at", expired_time).eq("status", "active").execute()

            if response.data:
                expired_sessions = [session["id"] for session in response.data]
                logger.info("found_expired_sessions", count=len(expired_sessions))

                # Mark as expired
                for session_id in expired_sessions:
                    await self.expire_session(session_id)

            logger.info("expired_sessions_cleanup_completed")

        except Exception as e:
            logger.error("expired_sessions_cleanup_failed", error=str(e))
            raise

    async def get_session_with_stats(self, session_id: str) -> Optional[SessionWithStats]:
        """
        Get session with additional statistics

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session with statistics if found, None otherwise
        """
        try:
            logger.info("getting_session_with_stats", session_id=session_id)

            # Get basic session info
            session = await self.get_session_by_id(session_id)
            if not session:
                return None

            # Get user info
            user = await self.user_service.get_user_by_id(session.user_id)

            # Get service distribution
            service_distribution = {}
            interactions_response = self.supabase.table("interactions").select("service").eq("session_id", session_id).execute()
            if interactions_response.data:
                for interaction in interactions_response.data:
                    service = interaction["service"]
                    service_distribution[service] = service_distribution.get(service, 0) + 1

            # Calculate average response time
            response_times = []
            if interactions_response.data:
                times_response = self.supabase.table("interactions").select("processing_time_ms").eq("session_id", session_id).not_.is_("processing_time_ms", "null").execute()
                if times_response.data:
                    for interaction in times_response.data:
                        if interaction.get("processing_time_ms"):
                            response_times.append(interaction["processing_time_ms"])

            average_response_time = sum(response_times) / len(response_times) if response_times else 0.0

            return SessionWithStats(
                **session.model_dump() if hasattr(session, 'model_dump') else session.dict(),
                user_name=user.name if user else None,
                service_distribution=service_distribution,
                average_response_time=average_response_time
            )

        except Exception as e:
            logger.error("get_session_with_stats_failed", session_id=session_id, error=str(e))
            raise

    async def list_sessions(self, limit: int = 50, offset: int = 0, status: Optional[SessionStatus] = None) -> List[Session]:
        """
        List sessions with pagination

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            status: Filter by status

        Returns:
            List of session objects
        """
        try:
            logger.info("listing_sessions", limit=limit, offset=offset, status=status)

            query = self.supabase.table("sessions").select("*")

            if status:
                query = query.eq("status", status.value)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

            response = query.execute()

            sessions = []
            if response.data:
                for session_data in response.data:
                    session = Session(
                        id=session_data["id"],
                        user_id=session_data["user_id"],
                        status=SessionStatus(session_data["status"]),
                        current_service=session_data["current_service"],
                        context=session_data.get("context", {}),
                        metadata=session_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(session_data["created_at"]),
                        updated_at=datetime.fromisoformat(session_data["updated_at"]),
                        expires_at=datetime.fromisoformat(session_data["expires_at"]) if session_data.get("expires_at") else None,
                        last_activity_at=datetime.fromisoformat(session_data["last_activity_at"]),
                        message_count=session_data.get("message_count", 0)
                    )
                    sessions.append(session)

            return sessions

        except Exception as e:
            logger.error("list_sessions_failed", error=str(e))
            raise