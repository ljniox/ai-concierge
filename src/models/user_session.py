"""
User session model for the automatic account creation system.

This module defines the UserSession model which manages user sessions
across different platforms with dual persistence and security features.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column, String, Boolean, Text, Integer, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB, INET
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseSQLModel, SessionType, SessionStatus, Platform


class UserSession(BaseSQLModel):
    """
    User session model for managing platform sessions.

    This model represents user sessions across WhatsApp, Telegram,
    and other platforms with security tracking and dual persistence.
    """

    __tablename__ = "user_sessions"

    # Core relationship fields
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=True,  # Can be None for anonymous sessions
        index=True
    )

    # Session identification
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    platform = Column(String(20), nullable=False, index=True)
    platform_user_id = Column(String(100), nullable=False)
    session_type = Column(
        String(20),
        nullable=False,
        default=SessionType.ACCOUNT_CREATION,
        index=True
    )

    # Session status
    status = Column(
        String(20),
        nullable=False,
        default=SessionStatus.ACTIVE,
        index=True
    )

    # Session data
    context = Column(JSONB, nullable=False, default=dict)
    conversation_state = Column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_activity_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Security fields
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    trust_score = Column(Integer, nullable=False, default=80)  # 0-100 scale

    # Session metrics
    message_count = Column(Integer, nullable=False, default=0)
    metadata_json = Column(JSONB, default=dict, nullable=True)

    # Relationships
    user = relationship("UserAccount", back_populates="sessions")
    audit_records = relationship("AccountCreationAudit", back_populates="session")
    webhook_events = relationship("WebhookEvent", back_populates="session")

    # Table constraints and indexes
    __table_args__ = (
        Index("idx_user_sessions_platform_user", "platform", "platform_user_id"),
        Index("idx_user_sessions_status_activity", "status", "last_activity_at"),
        Index("idx_user_sessions_expires_status", "expires_at", "status"),
        Index("idx_user_sessions_trust_score", "trust_score"),
        {
            "schema": None,  # Uses default schema
        }
    )

    def __repr__(self) -> str:
        """String representation of UserSession."""
        return f"<UserSession(id={self.id}, platform={self.platform}, status={self.status})>"

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return (
            self.status == SessionStatus.ACTIVE and
            not self.is_expired and
            not self.is_deleted
        )

    @property
    def session_age_minutes(self) -> int:
        """Get session age in minutes."""
        delta = datetime.now(timezone.utc) - self.created_at
        return int(delta.total_seconds() / 60)

    @property
    def minutes_since_last_activity(self) -> int:
        """Get minutes since last activity."""
        delta = datetime.now(timezone.utc) - self.last_activity_at
        return int(delta.total_seconds() / 60)

    @property
    def is_trusted(self) -> bool:
        """Check if session is considered trusted."""
        return self.trust_score >= 70

    @property
    def platform_identifier(self) -> str:
        """Get unique platform identifier for the session."""
        return f"{self.platform}:{self.platform_user_id}"

    def update_activity(self, session: Optional[Session] = None) -> None:
        """
        Update last activity timestamp.

        Args:
            session: Database session (optional)
        """
        self.last_activity_at = datetime.now(timezone.utc)
        if session:
            session.add(self)
            session.commit()

    def increment_message_count(self, session: Optional[Session] = None) -> None:
        """
        Increment message counter.

        Args:
            session: Database session (optional)
        """
        self.message_count += 1
        self.update_activity(session)

    def update_trust_score(self, new_score: int, session: Optional[Session] = None) -> None:
        """
        Update trust score.

        Args:
            new_score: New trust score (0-100)
            session: Database session (optional)
        """
        self.trust_score = max(0, min(100, new_score))
        if session:
            session.add(self)
            session.commit()

    def update_conversation_state(self, state: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Update conversation state.

        Args:
            state: New conversation state
            session: Database session (optional)
        """
        if self.conversation_state is None:
            self.conversation_state = {}
        self.conversation_state.update(state)
        self.update_activity(session)

    def update_context(self, context: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Update session context.

        Args:
            context: New context data
            session: Database session (optional)
        """
        if self.context is None:
            self.context = {}
        self.context.update(context)
        self.update_activity(session)

    def set_expiry(self, minutes: int, session: Optional[Session] = None) -> None:
        """
        Set session expiry.

        Args:
            minutes: Minutes until expiry
            session: Database session (optional)
        """
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        if session:
            session.add(self)
            session.commit()

    def extend_expiry(self, minutes: int, session: Optional[Session] = None) -> None:
        """
        Extend session expiry.

        Args:
            minutes: Additional minutes to extend
            session: Database session (optional)
        """
        if self.expires_at is None:
            self.set_expiry(minutes, session)
        else:
            self.expires_at = self.expires_at + timedelta(minutes=minutes)
            if session:
                session.add(self)
                session.commit()

    def activate(self, session: Optional[Session] = None) -> None:
        """
        Activate the session.

        Args:
            session: Database session (optional)
        """
        self.status = SessionStatus.ACTIVE
        self.update_activity(session)

    def deactivate(self, reason: Optional[str] = None, session: Optional[Session] = None) -> None:
        """
        Deactivate the session.

        Args:
            reason: Reason for deactivation
            session: Database session (optional)
        """
        self.status = SessionStatus.INACTIVE
        if reason:
            self.update_context({"deactivation_reason": reason})
        if session:
            session.add(self)
            session.commit()

    def terminate(self, reason: Optional[str] = None, session: Optional[Session] = None) -> None:
        """
        Terminate the session.

        Args:
            reason: Reason for termination
            session: Database session (optional)
        """
        self.status = SessionStatus.TERMINATED
        if reason:
            self.update_context({"termination_reason": reason})
        if session:
            session.add(self)
            session.commit()

    def add_security_event(self, event_type: str, details: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Add security event to session context.

        Args:
            event_type: Type of security event
            details: Event details
            session: Database session (optional)
        """
        if "security_events" not in self.context:
            self.context["security_events"] = []

        security_event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details
        }

        self.context["security_events"].append(security_event)
        self.update_activity(session)

    def get_conversation_flow(self) -> Dict[str, Any]:
        """
        Get conversation flow state.

        Returns:
            Current conversation flow state
        """
        return self.conversation_state.get("flow", {})

    def set_conversation_flow(self, flow_state: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Set conversation flow state.

        Args:
            flow_state: New flow state
            session: Database session (optional)
        """
        self.update_conversation_state({"flow": flow_state}, session)

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert session to dictionary.

        Args:
            include_sensitive: Whether to include sensitive information

        Returns:
            Dictionary representation of session
        """
        data = super().to_dict()

        # Add computed properties
        data.update({
            "is_expired": self.is_expired,
            "is_active": self.is_active,
            "session_age_minutes": self.session_age_minutes,
            "minutes_since_last_activity": self.minutes_since_last_activity,
            "is_trusted": self.is_trusted,
            "platform_identifier": self.platform_identifier
        })

        # Mask sensitive data unless explicitly requested
        if not include_sensitive:
            data["platform_user_id"] = data["platform_user_id"][:10] + "***" if data.get("platform_user_id") else None
            data["ip_address"] = None
            data["user_agent"] = None

        return data

    @classmethod
    def create_session(
        cls,
        session: Session,
        session_id: str,
        platform: str,
        platform_user_id: str,
        user_id: Optional[UUID] = None,
        session_type: str = SessionType.ACCOUNT_CREATION,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_minutes: Optional[int] = None
    ) -> "UserSession":
        """
        Create a new user session.

        Args:
            session: Database session
            session_id: Unique session identifier
            platform: Platform (whatsapp, telegram)
            platform_user_id: Platform-specific user ID
            user_id: User ID (optional for anonymous sessions)
            session_type: Type of session
            ip_address: Client IP address
            user_agent: Client user agent
            expires_in_minutes: Session expiry in minutes

        Returns:
            Created UserSession instance
        """
        user_session = cls(
            session_id=session_id,
            platform=platform,
            platform_user_id=platform_user_id,
            user_id=user_id,
            session_type=session_type,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if expires_in_minutes:
            user_session.set_expiry(expires_in_minutes)

        session.add(user_session)
        session.commit()
        session.refresh(user_session)

        return user_session

    @classmethod
    def find_by_session_id(cls, session: Session, session_id: str) -> Optional["UserSession"]:
        """
        Find session by session ID.

        Args:
            session: Database session
            session_id: Session ID

        Returns:
            UserSession instance or None
        """
        return session.query(cls).filter(
            cls.session_id == session_id,
            cls.is_deleted == False
        ).first()

    @classmethod
    def find_by_platform_user(
        cls,
        session: Session,
        platform: str,
        platform_user_id: str,
        active_only: bool = True
    ) -> Optional["UserSession"]:
        """
        Find session by platform and user ID.

        Args:
            session: Database session
            platform: Platform
            platform_user_id: Platform-specific user ID
            active_only: Whether to return only active sessions

        Returns:
            UserSession instance or None
        """
        query = session.query(cls).filter(
            cls.platform == platform,
            cls.platform_user_id == platform_user_id,
            cls.is_deleted == False
        )

        if active_only:
            query = query.filter(
                cls.status == SessionStatus.ACTIVE,
                cls.expires_at > datetime.now(timezone.utc)
            )

        return query.first()

    @classmethod
    def get_user_sessions(
        cls,
        session: Session,
        user_id: UUID,
        active_only: bool = True
    ) -> list["UserSession"]:
        """
        Get all sessions for a user.

        Args:
            session: Database session
            user_id: User ID
            active_only: Whether to return only active sessions

        Returns:
            List of UserSession instances
        """
        query = session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_deleted == False
        )

        if active_only:
            query = query.filter(cls.status == SessionStatus.ACTIVE)

        return query.all()

    @classmethod
    def get_active_sessions(cls, session: Session, platform: Optional[str] = None) -> list["UserSession"]:
        """
        Get all active sessions.

        Args:
            session: Database session
            platform: Optional platform filter

        Returns:
            List of active UserSession instances
        """
        query = session.query(cls).filter(
            cls.status == SessionStatus.ACTIVE,
            cls.is_deleted == False
        )

        if platform:
            query = query.filter(cls.platform == platform)

        return query.all()

    @classmethod
    def get_expired_sessions(cls, session: Session) -> list["UserSession"]:
        """
        Get sessions that have expired but are still active.

        Args:
            session: Database session

        Returns:
            List of expired UserSession instances
        """
        return session.query(cls).filter(
            cls.expires_at <= datetime.now(timezone.utc),
            cls.status == SessionStatus.ACTIVE,
            cls.is_deleted == False
        ).all()

    @classmethod
    def cleanup_expired_sessions(cls, session: Session) -> int:
        """
        Deactivate all expired sessions.

        Args:
            session: Database session

        Returns:
            Number of sessions deactivated
        """
        expired_sessions = cls.get_expired_sessions(session)
        count = 0

        for user_session in expired_sessions:
            user_session.status = SessionStatus.EXPIRED
            count += 1

        session.commit()
        return count

    @classmethod
    def get_session_statistics(cls, session: Session) -> Dict[str, Any]:
        """
        Get session statistics.

        Args:
            session: Database session

        Returns:
            Dictionary with session statistics
        """
        from sqlalchemy import func

        # Total sessions
        total_sessions = session.query(cls).filter(cls.is_deleted == False).count()

        # Active sessions
        active_sessions = session.query(cls).filter(
            cls.status == SessionStatus.ACTIVE,
            cls.is_deleted == False
        ).count()

        # Sessions by platform
        platform_stats = session.query(
            cls.platform,
            func.count(cls.id).label("count")
        ).filter(
            cls.is_deleted == False
        ).group_by(cls.platform).all()

        # Sessions by type
        type_stats = session.query(
            cls.session_type,
            func.count(cls.id).label("count")
        ).filter(
            cls.is_deleted == False
        ).group_by(cls.session_type).all()

        # Average session duration and message count
        avg_stats = session.query(
            func.avg(cls.message_count).label("avg_messages"),
            func.avg(func.extract('epoch', datetime.now(timezone.utc) - cls.created_at) / 60).label("avg_duration_minutes")
        ).filter(
            cls.is_deleted == False
        ).first()

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "by_platform": {stat.platform: stat.count for stat in platform_stats},
            "by_type": {stat.session_type: stat.count for stat in type_stats},
            "average_messages_per_session": float(avg_stats.avg_messages) if avg_stats.avg_messages else 0,
            "average_session_duration_minutes": float(avg_stats.avg_duration_minutes) if avg_stats.avg_duration_minutes else 0
        }


# Import for timedelta
from datetime import timedelta