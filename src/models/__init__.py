"""
Models package for the automatic account creation system.

This package provides all database models for the account creation feature,
including SQLAlchemy models and Pydantic schemas for data validation.
"""

from .base import (
    # SQLAlchemy base classes
    BaseSQLModel,

    # Pydantic base classes
    BaseModel,

    # Database manager
    DatabaseManager,

    # Mixins
    TimestampMixin,
    AuditMixin,

    # Account creation enums
    AccountStatus,
    ConsentLevel,
    CreatedVia,
    SessionType,
    SessionStatus,
    Platform,
    ProcessingStatus,
    AccountCreationStatus,

    # Legacy enums
    InscriptionStatut,
    DocumentType,
    StatutOCR,
    ModePaiement,
    StatutPaiement,
    UserRole,
    ActionType
)

from .user_account import UserAccount
from .user_role import UserRole
from .user_role_assignment import UserRoleAssignment
from .user_session import UserSession
from .account_creation_audit import AccountCreationAudit
from .webhook_event import WebhookEvent

# Export all models for easy importing
__all__ = [
    # Base classes
    "BaseSQLModel",
    "BaseModel",
    "DatabaseManager",
    "TimestampMixin",
    "AuditMixin",

    # Account creation models
    "UserAccount",
    "UserRole",
    "UserRoleAssignment",
    "UserSession",
    "AccountCreationAudit",
    "WebhookEvent",

    # Enums
    "AccountStatus",
    "ConsentLevel",
    "CreatedVia",
    "SessionType",
    "SessionStatus",
    "Platform",
    "ProcessingStatus",
    "AccountCreationStatus",

    # Legacy enums
    "InscriptionStatut",
    "DocumentType",
    "StatutOCR",
    "ModePaiement",
    "StatutPaiement",
    "UserRoleEnum",  # Renamed to avoid conflict with UserRole model
    "ActionType"
]

# Set up proper exports for legacy UserRole enum
UserRoleEnum = UserRole