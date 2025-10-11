"""
User account model for the automatic account creation system.

This module defines the UserAccount model which stores user information,
authentication details, and account status for parents and catechism participants.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import Column, String, Boolean, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseSQLModel, AccountStatus, ConsentLevel, CreatedVia


class UserAccount(BaseSQLModel):
    """
    User account model for storing parent and participant information.

    This model represents user accounts created through WhatsApp, Telegram,
    or manual processes, with GDPR compliance and platform integration.
    """

    __tablename__ = "user_accounts"

    # Core identity fields
    phone_number = Column(String(20), nullable=False, unique=True, index=True)
    normalized_phone = Column(String(20), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)

    # Account status and verification
    status = Column(
        String(20),
        nullable=False,
        default=AccountStatus.ACTIVE,
        index=True
    )
    is_verified = Column(Boolean, nullable=False, default=False)
    parent_database_id = Column(String(100), nullable=True)  # Reference to catechism database

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # GDPR compliance fields
    consent_given = Column(Boolean, nullable=False, default=False)
    consent_level = Column(
        String(20),
        nullable=False,
        default=ConsentLevel.MINIMAL
    )
    data_retention_until = Column(DateTime(timezone=True), nullable=True)

    # Platform integration fields
    created_via = Column(
        String(20),
        nullable=False,
        index=True
    )
    platform_user_id = Column(String(100), nullable=True)
    metadata_json = Column(JSONB, default=dict, nullable=True)

    # Relationships
    role_assignments = relationship(
        "UserRoleAssignment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_records = relationship(
        "AccountCreationAudit",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("idx_user_accounts_phone_status", "phone_number", "status"),
        Index("idx_user_accounts_platform_user", "created_via", "platform_user_id"),
        Index("idx_user_accounts_created_via", "created_via", "created_at"),
        {
            "schema": None,  # Uses default schema
        }
    )

    def __repr__(self) -> str:
        """String representation of UserAccount."""
        return f"<UserAccount(id={self.id}, phone={self.phone_number[:4]}****, status={self.status})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return self.username
        else:
            return f"User {self.phone_number[:4]}****"

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == AccountStatus.ACTIVE and not self.is_deleted

    @property
    def has_gdpr_consent(self) -> bool:
        """Check if user has given GDPR consent."""
        return self.consent_given and self.consent_level in ConsentLevel.all_values()

    @property
    def display_phone(self) -> str:
        """Get masked phone number for display."""
        if len(self.phone_number) > 7:
            return self.phone_number[:4] + '*' * (len(self.phone_number) - 7) + self.phone_number[-3:]
        else:
            return '*' * len(self.phone_number)

    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform integration information."""
        return {
            "created_via": self.created_via,
            "platform_user_id": self.platform_user_id,
            "is_verified": self.is_verified,
            "has_consent": self.consent_given,
            "consent_level": self.consent_level
        }

    def update_last_login(self, session: Session) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.now(timezone.utc)
        session.add(self)
        session.commit()

    def grant_consent(self, consent_level: str = ConsentLevel.STANDARD, session: Optional[Session] = None) -> None:
        """
        Grant GDPR consent to user.

        Args:
            consent_level: Level of consent granted
            session: Database session (optional)
        """
        self.consent_given = True
        self.consent_level = consent_level

        # Set data retention period (2 years for standard consent)
        if consent_level == ConsentLevel.STANDARD:
            self.data_retention_until = datetime.now(timezone.utc).replace(
                year=datetime.now(timezone.utc).year + 2
            )
        elif consent_level == ConsentLevel.FULL:
            self.data_retention_until = datetime.now(timezone.utc).replace(
                year=datetime.now(timezone.utc).year + 5
            )

        if session:
            session.add(self)
            session.commit()

    def revoke_consent(self, session: Optional[Session] = None) -> None:
        """
        Revoke GDPR consent from user.

        Args:
            session: Database session (optional)
        """
        self.consent_given = False
        self.consent_level = ConsentLevel.MINIMAL
        self.data_retention_until = datetime.now(timezone.utc).replace(
            year=datetime.now(timezone.utc).year + 1
        )  # Keep minimal data for 1 year

        if session:
            session.add(self)
            session.commit()

    def change_status(self, new_status: str, session: Optional[Session] = None) -> None:
        """
        Change account status.

        Args:
            new_status: New account status
            session: Database session (optional)
        """
        if new_status not in AccountStatus.all_values():
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        if session:
            session.add(self)
            session.commit()

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert user account to dictionary.

        Args:
            include_sensitive: Whether to include sensitive information

        Returns:
            Dictionary representation of user account
        """
        data = super().to_dict()

        # Add computed properties
        data.update({
            "full_name": self.full_name,
            "is_active": self.is_active,
            "has_gdpr_consent": self.has_gdpr_consent,
            "display_phone": self.display_phone,
            "platform_info": self.get_platform_info()
        })

        # Mask sensitive data unless explicitly requested
        if not include_sensitive:
            data["phone_number"] = self.display_phone
            data["normalized_phone"] = self.display_phone
            data["email"] = None

        return data

    @classmethod
    def find_by_phone(cls, session: Session, phone_number: str, include_deleted: bool = False) -> Optional["UserAccount"]:
        """
        Find user account by phone number.

        Args:
            session: Database session
            phone_number: Phone number to search for
            include_deleted: Whether to include deleted accounts

        Returns:
            UserAccount instance or None
        """
        query = session.query(cls).filter(cls.phone_number == phone_number)

        if not include_deleted:
            query = query.filter(cls.is_deleted == False)

        return query.first()

    @classmethod
    def find_by_platform_user(cls, session: Session, platform: str, platform_user_id: str) -> Optional["UserAccount"]:
        """
        Find user account by platform user ID.

        Args:
            session: Database session
            platform: Platform (whatsapp, telegram)
            platform_user_id: Platform-specific user ID

        Returns:
            UserAccount instance or None
        """
        return session.query(cls).filter(
            cls.created_via == platform,
            cls.platform_user_id == platform_user_id,
            cls.is_deleted == False
        ).first()

    @classmethod
    def get_active_users(cls, session: Session, limit: Optional[int] = None) -> List["UserAccount"]:
        """
        Get list of active users.

        Args:
            session: Database session
            limit: Maximum number of users to return

        Returns:
            List of active UserAccount instances
        """
        query = session.query(cls).filter(
            cls.status == AccountStatus.ACTIVE,
            cls.is_deleted == False
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    @classmethod
    def get_users_by_consent_level(cls, session: Session, consent_level: str) -> List["UserAccount"]:
        """
        Get users by consent level.

        Args:
            session: Database session
            consent_level: Consent level to filter by

        Returns:
            List of UserAccount instances with specified consent level
        """
        return session.query(cls).filter(
            cls.consent_given == True,
            cls.consent_level == consent_level,
            cls.is_deleted == False
        ).all()

    @classmethod
    def search_users(cls, session: Session, search_term: str, limit: int = 20) -> List["UserAccount"]:
        """
        Search users by name, username, or phone.

        Args:
            session: Database session
            search_term: Search term
            limit: Maximum number of results

        Returns:
            List of matching UserAccount instances
        """
        search_pattern = f"%{search_term}%"

        return session.query(cls).filter(
            cls.is_deleted == False,
            (
                cls.first_name.ilike(search_pattern) |
                cls.last_name.ilike(search_pattern) |
                cls.username.ilike(search_pattern) |
                cls.phone_number.ilike(search_pattern)
            )
        ).limit(limit).all()

    @classmethod
    def get_registration_stats(cls, session: Session, days: int = 30) -> Dict[str, Any]:
        """
        Get registration statistics for the specified period.

        Args:
            session: Database session
            days: Number of days to look back

        Returns:
            Dictionary with registration statistics
        """
        from sqlalchemy import extract

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Total registrations in period
        total_registrations = session.query(cls).filter(
            cls.created_at >= cutoff_date,
            cls.is_deleted == False
        ).count()

        # Registrations by platform
        platform_stats = session.query(
            cls.created_via,
            func.count(cls.id).label("count")
        ).filter(
            cls.created_at >= cutoff_date,
            cls.is_deleted == False
        ).group_by(cls.created_via).all()

        # Registrations by status
        status_stats = session.query(
            cls.status,
            func.count(cls.id).label("count")
        ).filter(
            cls.created_at >= cutoff_date,
            cls.is_deleted == False
        ).group_by(cls.status).all()

        # Consent statistics
        consent_stats = session.query(
            cls.consent_given,
            func.count(cls.id).label("count")
        ).filter(
            cls.created_at >= cutoff_date,
            cls.is_deleted == False
        ).group_by(cls.consent_given).all()

        return {
            "period_days": days,
            "total_registrations": total_registrations,
            "by_platform": {stat.created_via: stat.count for stat in platform_stats},
            "by_status": {stat.status: stat.count for stat in status_stats},
            "consent_given": {bool(stat.consent_given): stat.count for stat in consent_stats}
        }


# Import for timedelta
from datetime import timedelta