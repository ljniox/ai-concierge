"""
User role assignment model for the automatic account creation system.

This module defines the UserRoleAssignment model which represents the
many-to-many relationship between users and roles.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB
from sqlalchemy.orm import relationship, Session

from .base import BaseSQLModel


class UserRoleAssignment(BaseSQLModel):
    """
    User role assignment model linking users to roles.

    This model represents the assignment of a role to a user,
    with assignment metadata and expiration handling.
    """

    __tablename__ = "user_role_assignments"

    # Core relationship fields
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Assignment metadata
    assigned_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    assigned_by = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("user_accounts.id"),
        nullable=True
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Assignment details
    assignment_reason = Column(String(255), nullable=True)
    assignment_context = Column(JSONB, default=dict, nullable=True)

    # Relationships
    user = relationship("UserAccount", foreign_keys=[user_id], back_populates="role_assignments")
    role = relationship("UserRole", foreign_keys=[role_id], back_populates="role_assignments")
    assigned_by_user = relationship("UserAccount", foreign_keys=[assigned_by])

    # Table constraints and indexes
    __table_args__ = (
        Index("idx_user_role_assignments_unique", "user_id", "role_id", unique=True),
        Index("idx_user_role_assignments_active", "is_active", "expires_at"),
        Index("idx_user_role_assignments_expires", "expires_at"),
        {
            "schema": None,  # Uses default schema
        }
    )

    def __repr__(self) -> str:
        """String representation of UserRoleAssignment."""
        return f"<UserRoleAssignment(user_id={self.user_id}, role_id={self.role_id}, active={self.is_active})>"

    @property
    def is_expired(self) -> bool:
        """Check if assignment has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if assignment is currently valid."""
        return self.is_active and not self.is_expired and not self.is_deleted

    @property
    def days_until_expiry(self) -> Optional[int]:
        """
        Get days until assignment expires.

        Returns:
            Number of days until expiry, None if no expiry
        """
        if self.expires_at is None:
            return None

        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.days if delta.days > 0 else 0

    def activate(self, session: Optional[Session] = None) -> None:
        """
        Activate the role assignment.

        Args:
            session: Database session (optional)
        """
        self.is_active = True
        if session:
            session.add(self)
            session.commit()

    def deactivate(self, session: Optional[Session] = None) -> None:
        """
        Deactivate the role assignment.

        Args:
            session: Database session (optional)
        """
        self.is_active = False
        if session:
            session.add(self)
            session.commit()

    def extend_expiry(self, days: int, session: Optional[Session] = None) -> None:
        """
        Extend assignment expiry by specified number of days.

        Args:
            days: Number of days to extend
            session: Database session (optional)
        """
        if self.expires_at is None:
            self.expires_at = datetime.now(timezone.utc)
        self.expires_at = self.expires_at.replace(
            day=self.expires_at.day + days
        )  # Simplified - in production, use proper date arithmetic

        if session:
            session.add(self)
            session.commit()

    def set_expiry(self, expiry_date: datetime, session: Optional[Session] = None) -> None:
        """
        Set specific expiry date for the assignment.

        Args:
            expiry_date: New expiry date
            session: Database session (optional)
        """
        self.expires_at = expiry_date
        if session:
            session.add(self)
            session.commit()

    def remove_expiry(self, session: Optional[Session] = None) -> None:
        """
        Remove expiry date (make assignment permanent).

        Args:
            session: Database session (optional)
        """
        self.expires_at = None
        if session:
            session.add(self)
            session.commit()

    def update_assignment_context(self, context: Dict[str, Any], session: Optional[Session] = None) -> None:
        """
        Update assignment context metadata.

        Args:
            context: New context data
            session: Database session (optional)
        """
        if self.assignment_context is None:
            self.assignment_context = {}
        self.assignment_context.update(context)

        if session:
            session.add(self)
            session.commit()

    def to_dict(self, include_role_details: bool = True) -> Dict[str, Any]:
        """
        Convert assignment to dictionary.

        Args:
            include_role_details: Whether to include role information

        Returns:
            Dictionary representation of assignment
        """
        data = super().to_dict()

        # Add computed properties
        data.update({
            "is_expired": self.is_expired,
            "is_valid": self.is_valid,
            "days_until_expiry": self.days_until_expiry
        })

        if include_role_details and self.role:
            data["role"] = {
                "id": str(self.role.id),
                "name": self.role.name,
                "display_name": self.role.display_name,
                "permissions": self.role.permission_list
            }

        return data

    @classmethod
    def assign_role(
        cls,
        session: Session,
        user_id: UUID,
        role_id: UUID,
        assigned_by: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
        assignment_reason: Optional[str] = None,
        assignment_context: Optional[Dict[str, Any]] = None
    ) -> "UserRoleAssignment":
        """
        Assign a role to a user.

        Args:
            session: Database session
            user_id: User ID
            role_id: Role ID
            assigned_by: User ID who made the assignment
            expires_at: Expiry date (optional)
            assignment_reason: Reason for assignment (optional)
            assignment_context: Assignment context metadata (optional)

        Returns:
            Created UserRoleAssignment instance
        """
        # Check if assignment already exists
        existing = session.query(cls).filter(
            cls.user_id == user_id,
            cls.role_id == role_id,
            cls.is_deleted == False
        ).first()

        if existing:
            # Reactivate existing assignment
            existing.is_active = True
            existing.assigned_by = assigned_by
            existing.expires_at = expires_at
            existing.assignment_reason = assignment_reason
            if assignment_context:
                existing.update_assignment_context(assignment_context)
            session.commit()
            session.refresh(existing)
            return existing

        # Create new assignment
        assignment = cls(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
            assignment_reason=assignment_reason,
            assignment_context=assignment_context or {}
        )

        session.add(assignment)
        session.commit()
        session.refresh(assignment)

        return assignment

    @classmethod
    def revoke_assignment(
        cls,
        session: Session,
        user_id: UUID,
        role_id: UUID,
        revoked_by: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Revoke a role assignment.

        Args:
            session: Database session
            user_id: User ID
            role_id: Role ID
            revoked_by: User ID who revoked the assignment
            reason: Reason for revocation

        Returns:
            True if assignment was revoked, False if not found
        """
        assignment = session.query(cls).filter(
            cls.user_id == user_id,
            cls.role_id == role_id,
            cls.is_deleted == False
        ).first()

        if assignment:
            assignment.is_active = False
            if reason:
                assignment.update_assignment_context({"revoked_reason": reason})
            if revoked_by:
                assignment.update_assignment_context({"revoked_by": str(revoked_by)})
            session.commit()
            return True

        return False

    @classmethod
    def get_user_assignments(
        cls,
        session: Session,
        user_id: UUID,
        active_only: bool = True
    ) -> list["UserRoleAssignment"]:
        """
        Get all role assignments for a user.

        Args:
            session: Database session
            user_id: User ID
            active_only: Whether to return only active assignments

        Returns:
            List of UserRoleAssignment instances
        """
        query = session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_deleted == False
        )

        if active_only:
            query = query.filter(cls.is_active == True)

        return query.all()

    @classmethod
    def get_role_assignments(
        cls,
        session: Session,
        role_id: UUID,
        active_only: bool = True
    ) -> list["UserRoleAssignment"]:
        """
        Get all assignments for a role.

        Args:
            session: Database session
            role_id: Role ID
            active_only: Whether to return only active assignments

        Returns:
            List of UserRoleAssignment instances
        """
        query = session.query(cls).filter(
            cls.role_id == role_id,
            cls.is_deleted == False
        )

        if active_only:
            query = query.filter(cls.is_active == True)

        return query.all()

    @classmethod
    def get_expiring_assignments(
        cls,
        session: Session,
        days: int = 7
    ) -> list["UserRoleAssignment"]:
        """
        Get assignments that will expire within the specified number of days.

        Args:
            session: Database session
            days: Number of days to look ahead

        Returns:
            List of UserRoleAssignment instances
        """
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days)

        return session.query(cls).filter(
            cls.expires_at <= cutoff_date,
            cls.expires_at > datetime.now(timezone.utc),
            cls.is_active == True,
            cls.is_deleted == False
        ).all()

    @classmethod
    def get_expired_assignments(cls, session: Session) -> list["UserRoleAssignment"]:
        """
        Get assignments that have expired but are still marked as active.

        Args:
            session: Database session

        Returns:
            List of UserRoleAssignment instances
        """
        return session.query(cls).filter(
            cls.expires_at <= datetime.now(timezone.utc),
            cls.is_active == True,
            cls.is_deleted == False
        ).all()

    @classmethod
    def cleanup_expired_assignments(cls, session: Session) -> int:
        """
        Deactivate all expired assignments.

        Args:
            session: Database session

        Returns:
            Number of assignments deactivated
        """
        expired_assignments = cls.get_expired_assignments(session)
        count = 0

        for assignment in expired_assignments:
            assignment.deactivate()
            count += 1

        return count

    @classmethod
    def user_has_role(
        cls,
        session: Session,
        user_id: UUID,
        role_name: str
    ) -> bool:
        """
        Check if user has a specific role (by name).

        Args:
            session: Database session
            user_id: User ID
            role_name: Role name

        Returns:
            True if user has the role
        """
        from .user_role import UserRole

        role = UserRole.find_by_name(session, role_name)
        if not role:
            return False

        assignment = session.query(cls).filter(
            cls.user_id == user_id,
            cls.role_id == role.id,
            cls.is_active == True,
            cls.is_deleted == False
        ).first()

        return assignment is not None and not assignment.is_expired

    @classmethod
    def get_assignment_statistics(cls, session: Session) -> Dict[str, Any]:
        """
        Get overall assignment statistics.

        Args:
            session: Database session

        Returns:
            Dictionary with assignment statistics
        """
        from sqlalchemy import func

        # Total assignments
        total_assignments = session.query(cls).filter(
            cls.is_deleted == False
        ).count()

        # Active assignments
        active_assignments = session.query(cls).filter(
            cls.is_active == True,
            cls.is_deleted == False
        ).count()

        # Expired but still active
        expired_active = session.query(cls).filter(
            cls.expires_at <= datetime.now(timezone.utc),
            cls.is_active == True,
            cls.is_deleted == False
        ).count()

        # Expiring in next 30 days
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=30)
        expiring_soon = session.query(cls).filter(
            cls.expires_at <= cutoff_date,
            cls.expires_at > datetime.now(timezone.utc),
            cls.is_active == True,
            cls.is_deleted == False
        ).count()

        # Assignments by role
        role_stats = session.query(
            cls.role_id,
            func.count(cls.id).label("count")
        ).filter(
            cls.is_active == True,
            cls.is_deleted == False
        ).group_by(cls.role_id).all()

        return {
            "total_assignments": total_assignments,
            "active_assignments": active_assignments,
            "expired_but_active": expired_active,
            "expiring_next_30_days": expiring_soon,
            "assignments_by_role": {str(stat.role_id): stat.count for stat in role_stats}
        }


# Import for timedelta
from datetime import timedelta