"""
User role model for the automatic account creation system.

This module defines the UserRole model which represents system roles
that can be assigned to users with specific permissions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import Column, String, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseSQLModel


class UserRole(BaseSQLModel):
    """
    User role model for defining system roles and permissions.

    This model represents roles that can be assigned to users,
    with associated permissions and role metadata.
    """

    __tablename__ = "user_roles"

    # Role identity fields
    name = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Permission configuration
    permissions = Column(JSONB, nullable=False, default=list)
    is_system_role = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Role hierarchy (optional - for future enhancement)
    parent_role_id = Column(PostgreSQLUUID(as_uuid=True), nullable=True)
    priority_level = Column(Integer, nullable=False, default=0)

    # Relationships
    role_assignments = relationship(
        "UserRoleAssignment",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of UserRole."""
        return f"<UserRole(id={self.id}, name={self.name}, active={self.is_active})>"

    @property
    def permission_list(self) -> List[str]:
        """Get permissions as a clean list."""
        if isinstance(self.permissions, list):
            return self.permissions
        elif isinstance(self.permissions, dict):
            return list(self.permissions.keys())
        else:
            return []

    @property
    def has_admin_permissions(self) -> bool:
        """Check if role has administrative permissions."""
        admin_permissions = ["admin", "manage_users", "manage_roles", "system_config"]
        return any(perm in self.permission_list for perm in admin_permissions)

    @property
    def has_full_access(self) -> bool:
        """Check if role has full system access."""
        return "*" in self.permission_list

    def has_permission(self, permission: str) -> bool:
        """
        Check if role has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if role has permission
        """
        if self.has_full_access:
            return True

        # Direct permission check
        if permission in self.permission_list:
            return True

        # Wildcard permission check (e.g., "users.*" matches "users.view")
        for perm in self.permission_list:
            if perm.endswith(".*"):
                base_perm = perm[:-2]
                if permission.startswith(f"{base_perm}."):
                    return True

        return False

    def add_permission(self, permission: str, session: Optional[Session] = None) -> None:
        """
        Add a permission to the role.

        Args:
            permission: Permission to add
            session: Database session (optional)
        """
        if permission not in self.permission_list:
            current_perms = self.permission_list
            current_perms.append(permission)
            self.permissions = current_perms

            if session:
                session.add(self)
                session.commit()

    def remove_permission(self, permission: str, session: Optional[Session] = None) -> None:
        """
        Remove a permission from the role.

        Args:
            permission: Permission to remove
            session: Database session (optional)
        """
        if permission in self.permission_list:
            current_perms = self.permission_list
            current_perms.remove(permission)
            self.permissions = current_perms

            if session:
                session.add(self)
                session.commit()

    def activate(self, session: Optional[Session] = None) -> None:
        """
        Activate the role.

        Args:
            session: Database session (optional)
        """
        self.is_active = True
        if session:
            session.add(self)
            session.commit()

    def deactivate(self, session: Optional[Session] = None) -> None:
        """
        Deactivate the role.

        Args:
            session: Database session (optional)
        """
        self.is_active = False
        if session:
            session.add(self)
            session.commit()

    def to_dict(self, include_permissions: bool = True) -> Dict[str, Any]:
        """
        Convert role to dictionary.

        Args:
            include_permissions: Whether to include permission details

        Returns:
            Dictionary representation of role
        """
        data = super().to_dict()

        # Add computed properties
        data.update({
            "permission_count": len(self.permission_list),
            "has_admin_permissions": self.has_admin_permissions,
            "has_full_access": self.has_full_access
        })

        if include_permissions:
            data["permissions"] = self.permission_list

        return data

    @classmethod
    def find_by_name(cls, session: Session, name: str) -> Optional["UserRole"]:
        """
        Find role by name.

        Args:
            session: Database session
            name: Role name

        Returns:
            UserRole instance or None
        """
        return session.query(cls).filter(
            cls.name == name,
            cls.is_deleted == False
        ).first()

    @classmethod
    def get_active_roles(cls, session: Session) -> List["UserRole"]:
        """
        Get all active roles.

        Args:
            session: Database session

        Returns:
            List of active UserRole instances
        """
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_deleted == False
        ).all()

    @classmethod
    def get_system_roles(cls, session: Session) -> List["UserRole"]:
        """
        Get all system roles.

        Args:
            session: Database session

        Returns:
            List of system UserRole instances
        """
        return session.query(cls).filter(
            cls.is_system_role == True,
            cls.is_deleted == False
        ).all()

    @classmethod
    def get_custom_roles(cls, session: Session) -> List["UserRole"]:
        """
        Get all custom (non-system) roles.

        Args:
            session: Database session

        Returns:
            List of custom UserRole instances
        """
        return session.query(cls).filter(
            cls.is_system_role == False,
            cls.is_deleted == False
        ).all()

    @classmethod
    def search_roles(cls, session: Session, search_term: str, limit: int = 20) -> List["UserRole"]:
        """
        Search roles by name or description.

        Args:
            session: Database session
            search_term: Search term
            limit: Maximum number of results

        Returns:
            List of matching UserRole instances
        """
        search_pattern = f"%{search_term}%"

        return session.query(cls).filter(
            cls.is_deleted == False,
            (
                cls.name.ilike(search_pattern) |
                cls.display_name.ilike(search_pattern) |
                cls.description.ilike(search_pattern)
            )
        ).limit(limit).all()

    @classmethod
    def get_roles_with_permission(cls, session: Session, permission: str) -> List["UserRole"]:
        """
        Get roles that have a specific permission.

        Args:
            session: Database session
            permission: Permission to check

        Returns:
            List of UserRole instances with the permission
        """
        # This is a simplified implementation - in production, you might want
        # to use JSONB query operators for better performance
        roles = cls.get_active_roles(session)
        return [role for role in roles if role.has_permission(permission)]

    @classmethod
    def create_system_role(
        cls,
        session: Session,
        name: str,
        display_name: str,
        description: str,
        permissions: List[str]
    ) -> "UserRole":
        """
        Create a new system role.

        Args:
            session: Database session
            name: Role name (unique)
            display_name: Display name
            description: Role description
            permissions: List of permissions

        Returns:
            Created UserRole instance
        """
        role = cls(
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions,
            is_system_role=True,
            is_active=True
        )

        session.add(role)
        session.commit()
        session.refresh(role)

        return role

    @classmethod
    def create_custom_role(
        cls,
        session: Session,
        name: str,
        display_name: str,
        description: str,
        permissions: List[str],
        parent_role_id: Optional[UUID] = None
    ) -> "UserRole":
        """
        Create a new custom role.

        Args:
            session: Database session
            name: Role name (unique)
            display_name: Display name
            description: Role description
            permissions: List of permissions
            parent_role_id: Parent role ID (optional)

        Returns:
            Created UserRole instance
        """
        role = cls(
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions,
            is_system_role=False,
            is_active=True,
            parent_role_id=parent_role_id
        )

        session.add(role)
        session.commit()
        session.refresh(role)

        return role

    def get_role_statistics(self, session: Session) -> Dict[str, Any]:
        """
        Get usage statistics for this role.

        Args:
            session: Database session

        Returns:
            Dictionary with role statistics
        """
        from .user_role_assignment import UserRoleAssignment

        # Count active assignments
        active_assignments = session.query(UserRoleAssignment).filter(
            UserRoleAssignment.role_id == self.id,
            UserRoleAssignment.is_active == True
        ).count()

        # Count expired assignments
        expired_assignments = session.query(UserRoleAssignment).filter(
            UserRoleAssignment.role_id == self.id,
            UserRoleAssignment.expires_at <= datetime.now(timezone.utc)
        ).count()

        return {
            "role_id": str(self.id),
            "role_name": self.name,
            "active_assignments": active_assignments,
            "expired_assignments": expired_assignments,
            "total_assignments": active_assignments + expired_assignments,
            "permission_count": len(self.permission_list),
            "is_system_role": self.is_system_role,
            "is_active": self.is_active
        }