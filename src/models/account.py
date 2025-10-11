"""
User Account Models for Automatic Account Creation System

This module defines the core database models for user account management,
including user accounts, role assignments, and related entities.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class AccountSource(str, Enum):
    """Account creation sources."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    ADMIN = "admin"


class PlatformType(str, Enum):
    """Supported messaging platforms."""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"


class CreationStatus(str, Enum):
    """Account creation status."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class PhoneValidationResult(str, Enum):
    """Phone number validation results."""
    VALID = "valid"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class UserAccount(BaseModel):
    """Core user account model."""

    id: Optional[int] = None
    parent_id: Optional[int] = None
    phone_number: str = Field(..., regex=r"^\+[1-9]\d{1,14}$")
    phone_country_code: str = Field(default="+221")
    phone_national_number: str = Field(...)
    phone_is_valid: bool = Field(default=True)
    username: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9_]{3,50}$")
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    account_source: AccountSource = Field(default=AccountSource.AUTOMATIC)
    created_via: PlatformType = Field(...)
    telegram_user_id: Optional[int] = None
    whatsapp_user_id: Optional[str] = None
    consent_given: bool = Field(default=False)
    consent_date: Optional[datetime] = None
    data_retention_days: int = Field(default=365)
    notes: Optional[str] = None

    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        import phonenumbers
        try:
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError('Invalid phone number format')
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number format')
        return v

    @validator('whatsapp_user_id')
    def validate_whatsapp_user_id(cls, v):
        """Validate WhatsApp user ID format."""
        if v and not v.endswith('@c.us'):
            raise ValueError('WhatsApp user ID must end with @c.us')
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class UserAccountCreate(BaseModel):
    """Model for creating new user accounts."""

    phone_number: str
    phone_country_code: str = "+221"
    phone_national_number: str
    created_via: PlatformType
    platform_user_id: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    parent_id: Optional[int] = None
    consent_given: bool = True
    consent_date: Optional[datetime] = Field(default_factory=datetime.utcnow)


class UserAccountUpdate(BaseModel):
    """Model for updating user accounts."""

    username: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9_]{3,50}$")
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    is_active: Optional[bool] = None
    last_login_at: Optional[datetime] = None
    notes: Optional[str] = None
    data_retention_days: Optional[int] = Field(None, ge=1, le=3650)


class PlatformAccountLink(BaseModel):
    """Model for linking platform accounts to user accounts."""

    platform: PlatformType
    platform_user_id: str
    verification_code: Optional[str] = None


class UserAccountWithRoles(UserAccount):
    """User account model with included roles."""

    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    parent_info: Optional[Dict[str, Any]] = None


class AccountCreationRequest(BaseModel):
    """Request model for account creation."""

    phone_number: str
    country_code: str = "+221"
    source: PlatformType
    platform_user_id: str
    contact_name: Optional[str] = None
    consent_given: bool = True
    parent_match: Optional[Dict[str, Any]] = None


class AccountCreationResponse(BaseModel):
    """Response model for account creation."""

    success: bool
    user_id: Optional[int] = None
    account_id: Optional[int] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = False
    created_at: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list)
    platform_links: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error_code: Optional[str] = None


class AccountLookupRequest(BaseModel):
    """Request model for account lookup."""

    phone_number: Optional[str] = None
    platform: Optional[PlatformType] = None
    platform_user_id: Optional[str] = None
    username: Optional[str] = None
    user_id: Optional[int] = None


class AccountLookupResponse(BaseModel):
    """Response model for account lookup."""

    found: bool
    account: Optional[UserAccountWithRoles] = None
    message: Optional[str] = None


class AccountStats(BaseModel):
    """Account statistics model."""

    total_accounts: int
    active_accounts: int
    accounts_by_platform: Dict[str, int]
    accounts_by_source: Dict[str, int]
    accounts_created_today: int
    accounts_created_this_week: int
    accounts_created_this_month: int


class AccountSearchFilters(BaseModel):
    """Filters for account search."""

    phone_number: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    account_source: Optional[AccountSource] = None
    created_via: Optional[PlatformType] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_role: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class AccountSearchResponse(BaseModel):
    """Response model for account search."""

    accounts: List[UserAccountWithRoles]
    total: int
    limit: int
    offset: int
    has_more: bool


# Database query models
class AccountQuery:
    """Helper class for database queries."""

    @staticmethod
    def create_account_table_sql() -> str:
        """SQL for creating user_accounts table."""
        return """
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER NULL,
            phone_number VARCHAR(20) NOT NULL UNIQUE,
            phone_country_code VARCHAR(5) NOT NULL DEFAULT '+221',
            phone_national_number VARCHAR(15) NOT NULL,
            phone_is_valid BOOLEAN NOT NULL DEFAULT TRUE,
            username VARCHAR(50) UNIQUE,
            full_name VARCHAR(100),
            email VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP NULL,
            account_source VARCHAR(20) NOT NULL DEFAULT 'automatic',
            created_via VARCHAR(10) NOT NULL,
            telegram_user_id BIGINT NULL,
            whatsapp_user_id VARCHAR(50) NULL,
            consent_given BOOLEAN NOT NULL DEFAULT FALSE,
            consent_date TIMESTAMP NULL,
            data_retention_days INTEGER NOT NULL DEFAULT 365,
            notes TEXT NULL,
            FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE SET NULL
        )
        """

    @staticmethod
    def insert_account_sql() -> str:
        """SQL for inserting a new account."""
        return """
        INSERT INTO user_accounts (
            parent_id, phone_number, phone_country_code, phone_national_number,
            username, full_name, email, created_via, telegram_user_id,
            whatsapp_user_id, consent_given, consent_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

    @staticmethod
    def select_by_phone_sql() -> str:
        """SQL for selecting account by phone number."""
        return """
        SELECT ua.*, GROUP_CONCAT(ur.role_name) as roles
        FROM user_accounts ua
        LEFT JOIN user_role_assignments ura ON ua.id = ura.user_id
        LEFT JOIN user_roles ur ON ura.role_id = ur.id
        WHERE ua.phone_number = ? AND ua.is_active = 1
        GROUP BY ua.id
        """

    @staticmethod
    def select_by_platform_sql() -> str:
        """SQL for selecting account by platform user ID."""
        return """
        SELECT ua.*, GROUP_CONCAT(ur.role_name) as roles
        FROM user_accounts ua
        LEFT JOIN user_role_assignments ura ON ua.id = ura.user_id
        LEFT JOIN user_roles ur ON ura.role_id = ur.id
        WHERE ua.telegram_user_id = ? AND ua.is_active = 1
        GROUP BY ua.id
        """

    @staticmethod
    def select_by_whatsapp_platform_sql() -> str:
        """SQL for selecting account by WhatsApp platform user ID."""
        return """
        SELECT ua.*, GROUP_CONCAT(ur.role_name) as roles
        FROM user_accounts ua
        LEFT JOIN user_role_assignments ura ON ua.id = ura.user_id
        LEFT JOIN user_roles ur ON ura.role_id = ur.id
        WHERE ua.whatsapp_user_id = ? AND ua.is_active = 1
        GROUP BY ua.id
        """