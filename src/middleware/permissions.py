"""
Permission Checking Middleware with Role-Based Access Control

Implements fine-grained permissions based on user roles (FR-022).
Supports the 13 defined roles with appropriate permission sets.

Role Categories:
1. Executive: super_admin, cure
2. Clerical: sacristain, secretaire_cure, secretaire_bureau, secretaire_adjoint_bureau
3. Financial: tresorier_bureau, tresorier_adjoint_bureau
4. Management: president_bureau, responsable_organisation_bureau
5. External Relations: charge_relations_exterieures_bureau, charge_relations_exterieures_adjoint_bureau
6. Educational: catechiste
7. Access: parent

Constitution Principle V: Security (principle of least privilege)
"""

import json
from typing import Dict, List, Optional, Any, Callable
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from ..models.base import UserRole
from ..services.auth_service import get_auth_service

logger = logging.getLogger(__name__)

security = HTTPBearer()


class PermissionChecker:
    """
    Permission checking system with role-based access control.

    Implements hierarchical permissions where higher-level roles
    inherit permissions from lower-level roles.
    """

    # Role permission definitions (FR-022-029)
    ROLE_PERMISSIONS = {
        # Executive roles - full system access
        UserRole.SUPER_ADMIN: {
            "system_config": True,
            "user_management": True,
            "enrollment_management": True,
            "payment_validation": True,
            "class_management": True,
            "document_management": True,
            "audit_access": True,
            "reports_access": True,
            "sacristy_access": True,
            "clerical_access": True
        },
        UserRole.CURE: {
            "system_config": True,
            "user_management": True,
            "enrollment_management": True,
            "payment_validation": True,
            "class_management": True,
            "document_management": True,
            "audit_access": True,
            "reports_access": True,
            "sacristy_access": True,
            "clerical_access": True
        },

        # Clerical roles - administrative functions
        UserRole.SACRISTAIN: {
            "enrollment_management": True,
            "class_management": True,
            "document_management": True,
            "reports_access": True,
            "sacristy_access": True
        },
        UserRole.SECRETAIRE_CURE: {
            "enrollment_management": True,
            "class_management": True,
            "document_management": True,
            "clerical_access": True,
            "reports_access": True
        },
        UserRole.SECRETAIRE_BUREAU: {
            "enrollment_management": True,
            "document_management": True,
            "clerical_access": True,
            "reports_access": True
        },
        UserRole.SECRETAIRE_ADJOINT_BUREAU: {
            "enrollment_management": True,
            "document_management": True,
            "clerical_access": True,
            "reports_access": True
        },

        # Financial roles - payment processing
        UserRole.TRESORIER_BUREAU: {
            "payment_validation": True,
            "payment_reports": True,
            "enrollment_view": True,
            "document_management": True
        },
        UserRole.TRESORIER_ADJOINT_BUREAU: {
            "payment_validation": True,
            "payment_reports": True,
            "enrollment_view": True,
            "document_management": True
        },

        # Management roles
        UserRole.PRESIDENT_BUREAU: {
            "enrollment_management": True,
            "payment_validation": True,
            "class_management": True,
            "reports_access": True,
            "document_management": True
        },
        UserRole.RESPONSABLE_ORGANISATION_BUREAU: {
            "class_management": True,
            "enrollment_view": True,
            "reports_access": True
        },

        # External relations
        UserRole.CHARGE_RELATIONS_EXTERIEURES_BUREAU: {
            "enrollment_view": True,
            "reports_access": True,
            "document_management": True
        },
        UserRole.CHARGE_RELATIONS_EXTERIEURES_ADJOINT_BUREAU: {
            "enrollment_view": True,
            "reports_access": True,
            "document_management": True
        },

        # Educational roles
        UserRole.CATECHISTE: {
            "class_view": True,
            "student_records_view": True,
            "document_management": True
        },

        # Access roles - limited access
        UserRole.PARENT: {
            "create_inscription": True,
            "view_own_inscriptions": True,
            "upload_documents": True,
            "submit_payments": True,
            "validate_ocr": True
        }
    }

    # Resource ownership permissions
    OWNERSHIP_PERMISSIONS = {
        "enrollment": {
            "parent": ["view", "edit", "delete"],
            "catechiste": ["view"],
            "admin": ["view", "edit", "delete"]
        },
        "payment": {
            "parent": ["view", "create"],
            "treasurer": ["view", "validate", "reject"],
            "admin": ["view", "edit", "delete"]
        },
        "document": {
            "parent": ["view", "upload"],
            "admin": ["view", "delete"]
        }
    }

    @classmethod
    def has_permission(cls, user_role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.

        Args:
            user_role: User's role
            permission: Permission to check

        Returns:
            bool: True if role has permission
        """
        role_permissions = cls.ROLE_PERMISSIONS.get(user_role, {})
        return role_permissions.get(permission, False)

    @classmethod
    def has_any_permission(cls, user_role: str, permissions: List[str]) -> bool:
        """
        Check if a role has any of the specified permissions.

        Args:
            user_role: User's role
            permissions: List of permissions to check

        Returns:
            bool: True if role has any of the permissions
        """
        return any(cls.has_permission(user_role, perm) for perm in permissions)

    @classmethod
    def can_access_resource(cls, user_role: str, resource_type: str,
                           user_id: str, resource_owner_id: Optional[str] = None) -> bool:
        """
        Check if user can access a specific resource based on ownership.

        Args:
            user_role: User's role
            resource_type: Type of resource (enrollment, payment, document)
            user_id: Current user's ID
            resource_owner_id: Owner of the resource (if applicable)

        Returns:
            bool: True if user can access resource
        """
        # Admin roles can access everything
        if user_role in UserRole.admin_roles():
            return True

        # Check ownership permissions
        if resource_owner_id and resource_owner_id == user_id:
            ownership_perms = cls.OWNERSHIP_PERMISSIONS.get(resource_type, {}).get(user_role, [])
            return len(ownership_perms) > 0

        # Check role-based permissions
        resource_permission = f"{resource_type}_management"
        return cls.has_permission(user_role, resource_permission)

    @classmethod
    def get_user_permissions(cls, user_role: str) -> Dict[str, bool]:
        """
        Get all permissions for a given role.

        Args:
            user_role: User's role

        Returns:
            Dict: Permission name -> boolean
        """
        return cls.ROLE_PERMISSIONS.get(user_role, {})


def require_permission(permission: str):
    """
    FastAPI dependency to require specific permission.

    Args:
        permission: Required permission

    Returns:
        Dependency function that checks permission

    Example:
        @router.post("/inscriptions")
        async def create_inscription(
            current_user: Dict = Depends(require_permission("enrollment_management"))
        ):
            ...
    """
    async def permission_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
        # Verify token
        auth_service = get_auth_service()
        payload = await auth_service.verify_token(credentials.credentials)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check permission
        user_role = payload.get('role')
        if not PermissionChecker.has_permission(user_role, permission):
            logger.warning(f"Access denied: user {payload['user_id']} with role {user_role} "
                          f"attempted to access permission '{permission}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}"
            )

        return payload

    return permission_dependency


def require_any_permission(permissions: List[str]):
    """
    FastAPI dependency to require any of the specified permissions.

    Args:
        permissions: List of acceptable permissions

    Returns:
        Dependency function that checks permissions
    """
    async def permission_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
        # Verify token
        auth_service = get_auth_service()
        payload = await auth_service.verify_token(credentials.credentials)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check if user has any of the required permissions
        user_role = payload.get('role')
        if not PermissionChecker.has_any_permission(user_role, permissions):
            logger.warning(f"Access denied: user {payload['user_id']} with role {user_role} "
                          f"attempted to access permissions {permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required one of: {permissions}"
            )

        return payload

    return permission_dependency


def require_role(roles: List[str]):
    """
    FastAPI dependency to require specific role(s).

    Args:
        roles: List of allowed roles

    Returns:
        Dependency function that checks role

    Example:
        @router.post("/payments/validate")
        async def validate_payment(
            current_user: Dict = Depends(require_role(["tresorier_bureau", "cure"]))
        ):
            ...
    """
    async def role_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
        # Verify token
        auth_service = get_auth_service()
        payload = await auth_service.verify_token(credentials.credentials)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check role
        user_role = payload.get('role')
        if user_role not in roles:
            logger.warning(f"Access denied: user {payload['user_id']} with role {user_role} "
                          f"attempted to access role-protected endpoint requiring {roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {roles}"
            )

        return payload

    return role_dependency


def require_resource_access(resource_type: str, action: str = "view"):
    """
    FastAPI dependency to require resource access based on ownership.

    Args:
        resource_type: Type of resource (enrollment, payment, document)
        action: Action being performed (view, edit, delete, etc.)

    Returns:
        Dependency function that checks resource access
    """
    async def resource_dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        # Verify token
        auth_service = get_auth_service()
        payload = await auth_service.verify_token(credentials.credentials)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Extract resource ID from request path
        path_params = request.path_params
        resource_id = path_params.get('id') or path_params.get(f'{resource_type}_id')

        if not resource_id:
            # If no resource ID, check general permission
            user_role = payload.get('role')
            required_permission = f"{resource_type}_management"
            if not PermissionChecker.has_permission(user_role, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {required_permission}"
                )
            return payload

        # TODO: Implement resource ownership checking
        # This would require querying the database to get resource owner
        # For now, just check role-based permissions

        user_role = payload.get('role')
        if user_role in UserRole.admin_roles():
            return payload

        # Check role-based access
        required_permission = f"{resource_type}_{action}"
        if not PermissionChecker.has_permission(user_role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {required_permission}"
            )

        return payload

    return resource_dependency


# Common permission dependencies
require_admin = require_role(UserRole.admin_roles())
require_treasurer = require_role(UserRole.treasurer_roles())
require_parent = require_role([UserRole.PARENT])
require_enrollment_management = require_permission("enrollment_management")
require_payment_validation = require_permission("payment_validation")
require_document_management = require_permission("document_management")
require_class_management = require_permission("class_management")


class PermissionMiddleware:
    """
    Middleware for automatic permission checking on API routes.

    Can be used to enforce permissions globally or on specific route patterns.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add permission checking logic here if needed
            pass

        await self.app(scope, receive, send)