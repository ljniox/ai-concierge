"""
User Role Assignment Service

This service handles role assignment and management for user accounts,
with automatic assignment of default 'parent' role for newly created accounts.
Enhanced for Phase 3 with comprehensive role-based access control.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Set
from uuid import UUID
from enum import Enum

from src.services.database_service import get_database_service
from src.utils.logging import get_logger
from src.utils.exceptions import (
    DatabaseConnectionError,
    RoleNotFoundError,
    ValidationError,
    SecurityError
)


class UserRole(Enum):
    """Available user roles in the system."""
    PARENT = "parent"
    ADMIN = "admin"
    MODERATOR = "moderator"
    TEACHER = "teacher"
    VOLUNTEER = "volunteer"
    GUEST = "guest"


class Permission(Enum):
    """System permissions."""
    # Parent permissions
    VIEW_OWN_CHILDREN = "view_own_children"
    MANAGE_OWN_PROFILE = "manage_own_profile"
    VIEW_SCHEDULE = "view_schedule"
    COMMUNICATE_WITH_TEACHERS = "communicate_with_teachers"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_ALL_CHILDREN = "view_all_children"
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"

    # Teacher permissions
    MANAGE_CLASSES = "manage_classes"
    VIEW_ASSIGNED_CHILDREN = "view_assigned_children"
    COMMUNICATE_WITH_PARENTS = "communicate_with_parents"
    MANAGE_GRADES = "manage_grades"

    # General permissions
    SEND_MESSAGES = "send_messages"
    RECEIVE_NOTIFICATIONS = "receive_notifications"
    ACCESS_REPORTS = "access_reports"


class RolePermissionMapping:
    """Maps roles to their default permissions."""

    ROLE_PERMISSIONS = {
        UserRole.PARENT: {
            Permission.VIEW_OWN_CHILDREN,
            Permission.MANAGE_OWN_PROFILE,
            Permission.VIEW_SCHEDULE,
            Permission.COMMUNICATE_WITH_TEACHERS,
            Permission.SEND_MESSAGES,
            Permission.RECEIVE_NOTIFICATIONS,
            Permission.ACCESS_REPORTS
        },
        UserRole.ADMIN: {
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_ALL_CHILDREN,
            Permission.MANAGE_SYSTEM_SETTINGS,
            Permission.SEND_MESSAGES,
            Permission.RECEIVE_NOTIFICATIONS,
            Permission.ACCESS_REPORTS
        },
        UserRole.MODERATOR: {
            Permission.VIEW_ALL_CHILDREN,
            Permission.COMMUNICATE_WITH_PARENTS,
            Permission.COMMUNICATE_WITH_TEACHERS,
            Permission.SEND_MESSAGES,
            Permission.RECEIVE_NOTIFICATIONS,
            Permission.ACCESS_REPORTS
        },
        UserRole.TEACHER: {
            Permission.MANAGE_CLASSES,
            Permission.VIEW_ASSIGNED_CHILDREN,
            Permission.COMMUNICATE_WITH_PARENTS,
            Permission.MANAGE_GRADES,
            Permission.SEND_MESSAGES,
            Permission.RECEIVE_NOTIFICATIONS,
            Permission.ACCESS_REPORTS
        },
        UserRole.VOLUNTEER: {
            Permission.VIEW_ASSIGNED_CHILDREN,
            Permission.COMMUNICATE_WITH_PARENTS,
            Permission.SEND_MESSAGES,
            Permission.RECEIVE_NOTIFICATIONS
        },
        UserRole.GUEST: {
            Permission.VIEW_SCHEDULE,
            Permission.RECEIVE_NOTIFICATIONS
        }
    }


class RoleAssignmentResult:
    """Result of role assignment operation."""

    def __init__(
        self,
        success: bool,
        user_id: Optional[UUID] = None,
        roles_assigned: Optional[List[str]] = None,
        permissions_granted: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.user_id = user_id
        self.roles_assigned = roles_assigned or []
        self.permissions_granted = permissions_granted or []
        self.error_code = error_code
        self.error_message = error_message
        self.timestamp = datetime.now(timezone.utc)


class UserRoleAssignmentService:
    """
    Service for managing user roles and permissions.

    This service handles role assignment, permission management,
    and access control for user accounts.
    """

    def __init__(self, database_service=None):
        """
        Initialize user role assignment service.

        Args:
            database_service: Database service instance
        """
        self.database_service = database_service or get_database_service()
        self.logger = get_logger(__name__)

    async def assign_default_role(self, user_id: UUID, platform: str = "unknown") -> RoleAssignmentResult:
        """
        Assign default 'parent' role to newly created user.

        Args:
            user_id: User ID
            platform: Platform where user was created

        Returns:
            Role assignment result
        """
        try:
            return await self.assign_role(user_id, UserRole.PARENT, assigned_by="system", source=f"auto_assignment_{platform}")

        except Exception as e:
            self.logger.error(f"Failed to assign default role to user {user_id}: {str(e)}")
            return RoleAssignmentResult(
                success=False,
                user_id=user_id,
                error_code="DEFAULT_ROLE_ASSIGNMENT_FAILED",
                error_message=str(e)
            )

    async def assign_role(
        self,
        user_id: UUID,
        role: UserRole,
        assigned_by: str = "system",
        source: str = "manual_assignment",
        metadata: Optional[Dict[str, Any]] = None
    ) -> RoleAssignmentResult:
        """
        Assign a specific role to a user.

        Args:
            user_id: User ID
            role: Role to assign
            assigned_by: Who is assigning the role
            source: Source of assignment
            metadata: Additional metadata

        Returns:
            Role assignment result
        """
        try:
            # Check if role exists
            role_id = await self._get_role_id(role.value)
            if not role_id:
                return RoleAssignmentResult(
                    success=False,
                    user_id=user_id,
                    error_code="ROLE_NOT_FOUND",
                    error_message=f"Role '{role.value}' not found"
                )

            # Check if user already has this role
            if await self._user_has_role(user_id, role_id):
                self.logger.info(f"User {user_id} already has role '{role.value}'")
                permissions = await self._get_user_permissions(user_id)
                return RoleAssignmentResult(
                    success=True,
                    user_id=user_id,
                    roles_assigned=[role.value],
                    permissions_granted=list(permissions)
                )

            # Assign the role
            assignment_data = {
                "user_id": str(user_id),
                "role_id": role_id,
                "assigned_by": assigned_by,
                "assigned_at": datetime.now(timezone.utc),
                "source": source,
                "is_active": True,
                "metadata": metadata or {}
            }

            await self.database_service.insert(
                "user_role_assignments",
                assignment_data,
                database_name="supabase"
            )

            # Get user's updated permissions
            permissions = await self._get_user_permissions(user_id)

            self.logger.info(f"Role '{role.value}' assigned to user {user_id}")

            return RoleAssignmentResult(
                success=True,
                user_id=user_id,
                roles_assigned=[role.value],
                permissions_granted=list(permissions)
            )

        except Exception as e:
            self.logger.error(f"Failed to assign role {role.value} to user {user_id}: {str(e)}")
            return RoleAssignmentResult(
                success=False,
                user_id=user_id,
                error_code="ROLE_ASSIGNMENT_FAILED",
                error_message=str(e)
            )

    async def remove_role(
        self,
        user_id: UUID,
        role: UserRole,
        removed_by: str = "system"
    ) -> RoleAssignmentResult:
        """
        Remove a role from a user.

        Args:
            user_id: User ID
            role: Role to remove
            removed_by: Who is removing the role

        Returns:
            Role assignment result
        """
        try:
            role_id = await self._get_role_id(role.value)
            if not role_id:
                return RoleAssignmentResult(
                    success=False,
                    user_id=user_id,
                    error_code="ROLE_NOT_FOUND",
                    error_message=f"Role '{role.value}' not found"
                )

            # Update role assignment to inactive
            update_data = {
                "is_active": False,
                "removed_by": removed_by,
                "removed_at": datetime.now(timezone.utc)
            }

            condition = {
                "user_id": str(user_id),
                "role_id": role_id,
                "is_active": True
            }

            await self.database_service.update(
                "user_role_assignments",
                update_data,
                condition,
                database_name="supabase"
            )

            # Get updated permissions
            permissions = await self._get_user_permissions(user_id)

            self.logger.info(f"Role '{role.value}' removed from user {user_id}")

            return RoleAssignmentResult(
                success=True,
                user_id=user_id,
                roles_assigned=[],  # Role removed
                permissions_granted=list(permissions)
            )

        except Exception as e:
            self.logger.error(f"Failed to remove role {role.value} from user {user_id}: {str(e)}")
            return RoleAssignmentResult(
                success=False,
                user_id=user_id,
                error_code="ROLE_REMOVAL_FAILED",
                error_message=str(e)
            )

    async def get_user_roles(self, user_id: UUID) -> List[UserRole]:
        """
        Get all active roles for a user.

        Args:
            user_id: User ID

        Returns:
            List of user roles
        """
        try:
            query = """
            SELECT r.role_name FROM user_roles r
            INNER JOIN user_role_assignments ura ON r.id = ura.role_id
            WHERE ura.user_id = ? AND ura.is_active = TRUE AND r.is_active = TRUE
            """

            results = await self.database_service.fetch_all(
                query,
                (str(user_id),),
                database_name="supabase"
            )

            roles = []
            for result in results:
                try:
                    role = UserRole(result['role_name'])
                    roles.append(role)
                except ValueError:
                    self.logger.warning(f"Unknown role: {result['role_name']}")

            return roles

        except Exception as e:
            self.logger.error(f"Failed to get user roles for {user_id}: {str(e)}")
            return []

    async def get_user_permissions(self, user_id: UUID) -> Set[Permission]:
        """
        Get all permissions for a user based on their roles.

        Args:
            user_id: User ID

        Returns:
            Set of user permissions
        """
        try:
            roles = await self.get_user_roles(user_id)
            permissions = set()

            for role in roles:
                role_permissions = RolePermissionMapping.ROLE_PERMISSIONS.get(role, set())
                permissions.update(role_permissions)

            return permissions

        except Exception as e:
            self.logger.error(f"Failed to get user permissions for {user_id}: {str(e)}")
            return set()

    async def has_permission(self, user_id: UUID, permission: Permission) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User ID
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        try:
            user_permissions = await self.get_user_permissions(user_id)
            return permission in user_permissions

        except Exception as e:
            self.logger.error(f"Failed to check permission for user {user_id}: {str(e)}")
            return False

    async def has_role(self, user_id: UUID, role: UserRole) -> bool:
        """
        Check if user has a specific role.

        Args:
            user_id: User ID
            role: Role to check

        Returns:
            True if user has role, False otherwise
        """
        try:
            user_roles = await self.get_user_roles(user_id)
            return role in user_roles

        except Exception as e:
            self.logger.error(f"Failed to check role for user {user_id}: {str(e)}")
            return False

    async def create_role(
        self,
        role_name: str,
        description: str,
        permissions: List[Permission],
        created_by: str = "system"
    ) -> bool:
        """
        Create a new role with specified permissions.

        Args:
            role_name: Name of the role
            description: Role description
            permissions: List of permissions for the role
            created_by: Who is creating the role

        Returns:
            True if role created successfully, False otherwise
        """
        try:
            # Create role
            role_data = {
                "role_name": role_name,
                "description": description,
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc),
                "is_active": True
            }

            await self.database_service.insert(
                "user_roles",
                role_data,
                database_name="supabase"
            )

            # Get role ID
            role_id = await self._get_role_id(role_name)
            if not role_id:
                return False

            # Assign permissions to role
            for permission in permissions:
                permission_data = {
                    "role_id": role_id,
                    "permission_name": permission.value,
                    "granted_by": created_by,
                    "granted_at": datetime.now(timezone.utc),
                    "is_active": True
                }

                await self.database_service.insert(
                    "role_permissions",
                    permission_data,
                    database_name="supabase"
                )

            self.logger.info(f"Role '{role_name}' created with {len(permissions)} permissions")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create role {role_name}: {str(e)}")
            return False

    async def get_role_assignment_history(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get role assignment history for a user.

        Args:
            user_id: User ID

        Returns:
            List of role assignment history
        """
        try:
            query = """
            SELECT ura.*, r.role_name, r.description
            FROM user_role_assignments ura
            INNER JOIN user_roles r ON ura.role_id = r.id
            WHERE ura.user_id = ?
            ORDER BY ura.assigned_at DESC, ura.removed_at DESC
            """

            results = await self.database_service.fetch_all(
                query,
                (str(user_id),),
                database_name="supabase"
            )

            history = []
            for result in results:
                history.append(dict(result))

            return history

        except Exception as e:
            self.logger.error(f"Failed to get role assignment history for {user_id}: {str(e)}")
            return []

    async def cleanup_inactive_assignments(self, days_threshold: int = 90) -> int:
        """
        Cleanup inactive role assignments older than threshold.

        Args:
            days_threshold: Number of days to keep inactive assignments

        Returns:
            Number of assignments cleaned up
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)

            query = """
            DELETE FROM user_role_assignments
            WHERE is_active = FALSE AND removed_at < ?
            """

            result = await self.database_service.execute(
                query,
                (cutoff_date,),
                database_name="supabase"
            )

            cleaned_count = result.rowcount if result else 0
            self.logger.info(f"Cleaned up {cleaned_count} inactive role assignments")
            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup inactive assignments: {str(e)}")
            return 0

    async def _get_role_id(self, role_name: str) -> Optional[str]:
        """Get role ID by name."""
        try:
            query = "SELECT id FROM user_roles WHERE role_name = ? AND is_active = TRUE"
            result = await self.database_service.fetch_one(
                query,
                (role_name,),
                database_name="supabase"
            )
            return str(result['id']) if result else None

        except Exception as e:
            self.logger.error(f"Failed to get role ID for {role_name}: {str(e)}")
            return None

    async def _user_has_role(self, user_id: UUID, role_id: str) -> bool:
        """Check if user already has an active role assignment."""
        try:
            query = """
            SELECT COUNT(*) as count FROM user_role_assignments
            WHERE user_id = ? AND role_id = ? AND is_active = TRUE
            """

            result = await self.database_service.fetch_one(
                query,
                (str(user_id), role_id),
                database_name="supabase"
            )

            return result['count'] > 0 if result else False

        except Exception as e:
            self.logger.error(f"Failed to check if user has role: {str(e)}")
            return False

    async def _get_user_permissions(self, user_id: UUID) -> Set[Permission]:
        """Get user permissions from database."""
        try:
            # Get user roles
            roles = await self.get_user_roles(user_id)
            permissions = set()

            # Get permissions for each role
            for role in roles:
                role_permissions = RolePermissionMapping.ROLE_PERMISSIONS.get(role, set())
                permissions.update(role_permissions)

            return permissions

        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {str(e)}")
            return set()


# Factory function for getting user role assignment service
def get_user_role_assignment_service() -> UserRoleAssignmentService:
    """Get user role assignment service instance."""
    return UserRoleAssignmentService()