"""
Role Management Models for Automatic Account Creation System

This module defines the database models for role management, including
user roles, role assignments, and permission management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class RoleType(str, Enum):
    """Role types."""
    SYSTEM = "system"
    CUSTOM = "custom"


class PermissionScope(str, Enum):
    """Permission scopes."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class UserRole(BaseModel):
    """User role model."""

    id: Optional[int] = None
    role_name: str = Field(..., regex=r"^[a-z_]{3,50}$")
    role_display_name: str = Field(..., min_length=1, max_length=100)
    role_description: Optional[str] = Field(None, max_length=500)
    is_system_role: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('role_name')
    def validate_role_name(cls, v):
        """Validate role name format."""
        if not v.islower() or '_' not in v.replace(' ', ''):
            raise ValueError('Role name must be lowercase with underscores')
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class UserRoleCreate(BaseModel):
    """Model for creating new user roles."""

    role_name: str = Field(..., regex=r"^[a-z_]{3,50}$")
    role_display_name: str = Field(..., min_length=1, max_length=100)
    role_description: Optional[str] = Field(None, max_length=500)
    is_system_role: bool = Field(default=False)


class UserRoleUpdate(BaseModel):
    """Model for updating user roles."""

    role_display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role_description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class RoleAssignment(BaseModel):
    """Role assignment model."""

    id: Optional[int] = None
    user_id: int = Field(..., gt=0)
    role_id: int = Field(..., gt=0)
    assigned_by: Optional[int] = Field(None, gt=0)
    assigned_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    assignment_notes: Optional[str] = Field(None, max_length=500)

    @validator('expires_at')
    def validate_expiry_date(cls, v, values):
        """Validate expiry date is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError('Expiry date must be in the future')
        return v

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class RoleAssignmentCreate(BaseModel):
    """Model for creating role assignments."""

    user_id: int = Field(..., gt=0)
    role_name: str = Field(..., regex=r"^[a-z_]{3,50}$")
    assigned_by: Optional[int] = Field(None, gt=0)
    expires_at: Optional[datetime] = None
    assignment_notes: Optional[str] = Field(None, max_length=500)


class RoleAssignmentUpdate(BaseModel):
    """Model for updating role assignments."""

    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    assignment_notes: Optional[str] = Field(None, max_length=500)


class Permission(BaseModel):
    """Permission model."""

    id: Optional[int] = None
    permission_name: str = Field(..., regex=r"^[a-z_]{3,50}$")
    permission_display_name: str = Field(..., min_length=1, max_length=100)
    permission_description: Optional[str] = Field(None, max_length=500)
    resource: str = Field(..., regex=r"^[a-z_]{3,50}$")
    scope: PermissionScope
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None


class RolePermission(BaseModel):
    """Role permission mapping model."""

    id: Optional[int] = None
    role_id: int = Field(..., gt=0)
    permission_id: int = Field(..., gt=0)
    created_at: Optional[datetime] = None


class UserWithRoles(BaseModel):
    """User model with included roles and permissions."""

    user_id: int
    username: Optional[str]
    full_name: Optional[str]
    roles: List[Dict[str, Any]]
    permissions: List[str]
    role_assignments: List[RoleAssignment]


class RoleStats(BaseModel):
    """Role statistics model."""

    total_roles: int
    active_roles: int
    system_roles: int
    custom_roles: int
    total_assignments: int
    active_assignments: int
    assignments_by_role: Dict[str, int]


# Default system roles
DEFAULT_SYSTEM_ROLES = [
    {
        "role_name": "parent",
        "role_display_name": "Parent",
        "role_description": "Parent of catechism student with access to parent-specific functions",
        "is_system_role": True,
        "permissions": [
            "parent:view_children",
            "parent:register_child",
            "parent:view_payments",
            "parent:contact_support"
        ]
    },
    {
        "role_name": "super_admin",
        "role_display_name": "Super Administrateur",
        "role_description": "System administrator with full access to all functions",
        "is_system_role": True,
        "permissions": [
            "admin:manage_users",
            "admin:manage_roles",
            "admin:system_config",
            "admin:view_audit_logs",
            "admin:database_access"
        ]
    },
    {
        "role_name": "catechist",
        "role_display_name": "Catéchiste",
        "role_description": "Catechism teacher with access to class management",
        "is_system_role": True,
        "permissions": [
            "catechist:view_class",
            "catechist:manage_students",
            "catechist:record_attendance",
            "catechist:view_progress"
        ]
    },
    {
        "role_name": "treasurer",
        "role_display_name": "Trésorier",
        "role_description": "Treasury staff with access to payment management",
        "is_system_role": True,
        "permissions": [
            "treasurer:view_payments",
            "treasurer:manage_payments",
            "treasurer:generate_reports",
            "treasurer:manage_fees"
        ]
    },
    {
        "role_name": "secretary",
        "role_display_name": "Secrétaire",
        "role_description": "Administrative staff with access to enrollment management",
        "is_system_role": True,
        "permissions": [
            "secretary:manage_enrollments",
            "secretary:view_student_info",
            "secretary:generate_reports",
            "secretary:manage_classes"
        ]
    }
]


# Database query models
class RoleQuery:
    """Helper class for role database queries."""

    @staticmethod
    def create_roles_table_sql() -> str:
        """SQL for creating user_roles table."""
        return """
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name VARCHAR(50) NOT NULL UNIQUE,
            role_display_name VARCHAR(100) NOT NULL,
            role_description TEXT,
            is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def create_role_assignments_table_sql() -> str:
        """SQL for creating user_role_assignments table."""
        return """
        CREATE TABLE IF NOT EXISTS user_role_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            assigned_by INTEGER NULL,
            assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            assignment_notes TEXT NULL,
            UNIQUE(user_id, role_id),
            FOREIGN KEY (user_id) REFERENCES user_accounts(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES user_roles(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_by) REFERENCES user_accounts(id) ON DELETE SET NULL
        )
        """

    @staticmethod
    def insert_role_sql() -> str:
        """SQL for inserting a new role."""
        return """
        INSERT INTO user_roles (
            role_name, role_display_name, role_description, is_system_role
        ) VALUES (?, ?, ?, ?)
        """

    @staticmethod
    def insert_role_assignment_sql() -> str:
        """SQL for inserting a role assignment."""
        return """
        INSERT INTO user_role_assignments (
            user_id, role_id, assigned_by, expires_at, assignment_notes
        ) VALUES (?, ?, ?, ?, ?)
        """

    @staticmethod
    def select_role_by_name_sql() -> str:
        """SQL for selecting role by name."""
        return """
        SELECT * FROM user_roles WHERE role_name = ? AND is_active = 1
        """

    @staticmethod
    def select_user_roles_sql() -> str:
        """SQL for selecting user roles."""
        return """
        SELECT ur.*, ura.assigned_at, ura.expires_at, ura.is_active as assignment_active
        FROM user_roles ur
        JOIN user_role_assignments ura ON ur.id = ura.role_id
        WHERE ura.user_id = ? AND ur.is_active = 1
        ORDER BY ura.assigned_at DESC
        """

    @staticmethod
    def select_active_user_roles_sql() -> str:
        """SQL for selecting active user roles."""
        return """
        SELECT ur.*
        FROM user_roles ur
        JOIN user_role_assignments ura ON ur.id = ura.role_id
        WHERE ura.user_id = ?
          AND ur.is_active = 1
          AND ura.is_active = 1
          AND (ura.expires_at IS NULL OR ura.expires_at > CURRENT_TIMESTAMP)
        ORDER BY ura.assigned_at DESC
        """

    @staticmethod
    def check_role_assignment_sql() -> str:
        """SQL for checking if user has role."""
        return """
        SELECT COUNT(*) as count
        FROM user_role_assignments ura
        JOIN user_roles ur ON ura.role_id = ur.id
        WHERE ura.user_id = ?
          AND ur.role_name = ?
          AND ura.is_active = 1
          AND (ura.expires_at IS NULL OR ura.expires_at > CURRENT_TIMESTAMP)
        """