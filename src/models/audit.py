"""
Audit Models for Automatic Account Creation System

This module defines the database models for audit logging, including
account creation events, role assignments, and compliance tracking.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class AuditEventType(str, Enum):
    """Audit event types."""
    ACCOUNT_CREATION_STARTED = "account_creation_started"
    ACCOUNT_CREATION_SUCCESS = "account_creation_success"
    ACCOUNT_CREATION_FAILED = "account_creation_failed"
    PHONE_VALIDATION = "phone_validation"
    PARENT_DATABASE_LOOKUP = "parent_database_lookup"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PLATFORM_ACCOUNT_LINKED = "platform_account_linked"
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_ACCESSED = "data_accessed"
    DUPLICATE_ACCOUNT_PREVENTED = "duplicate_account_prevented"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"


class CreationStatus(str, Enum):
    """Account creation status."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class PhoneValidationResult(str, Enum):
    """Phone number validation results."""
    VALID = "valid"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    DUPLICATE = "duplicate"
    RATE_LIMITED = "rate_limited"


class AuditEvent(BaseModel):
    """Base audit event model."""

    id: Optional[int] = None
    event_type: AuditEventType
    user_id: Optional[int] = None
    phone_number: Optional[str] = None
    platform: Optional[str] = None
    platform_user_id: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = Field(default=True)
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None

    @validator('phone_number')
    def mask_phone_number(cls, v):
        """Mask phone number for privacy."""
        if v and len(v) > 6:
            return v[:3] + "***" + v[-3:]
        return v

    @validator('platform_user_id')
    def mask_platform_user_id(cls, v):
        """Mask platform user ID for privacy."""
        if v and len(v) > 6:
            return v[:3] + "***" + v[-3:]
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AccountCreationAudit(AuditEvent):
    """Specific audit event for account creation."""

    user_id: Optional[int] = None  # NULL if creation failed
    phone_number: str
    phone_validation_result: PhoneValidationResult
    parent_match_found: bool
    parent_id: Optional[int] = None
    creation_status: CreationStatus
    creation_source: str  # 'telegram', 'whatsapp'
    webhook_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None

    @validator('creation_source')
    def validate_creation_source(cls, v):
        """Validate creation source."""
        if v not in ['telegram', 'whatsapp', 'admin']:
            raise ValueError('Creation source must be telegram, whatsapp, or admin')
        return v


class PhoneValidationAudit(AuditEvent):
    """Audit event for phone number validation."""

    phone_number: str
    country_code: str
    validation_result: PhoneValidationResult
    normalized_number: Optional[str] = None
    is_mobile: Optional[bool] = None
    carrier: Optional[str] = None
    validation_details: Optional[Dict[str, Any]] = None


class RoleAssignmentAudit(AuditEvent):
    """Audit event for role assignments."""

    target_user_id: int
    role_name: str
    assigned_by: Optional[int] = None
    assignment_type: str = Field(default="assigned")  # 'assigned', 'removed'
    expires_at: Optional[datetime] = None
    assignment_reason: Optional[str] = None


class ConsentAudit(AuditEvent):
    """Audit event for consent management."""

    consent_type: str  # 'account_creation', 'data_processing', 'marketing'
    consent_given: bool
    consent_method: str  # 'automatic', 'explicit', 'implied'
    consent_version: str = Field(default="1.0")
    withdrawal_reason: Optional[str] = None


class DataAccessAudit(AuditEvent):
    """Audit event for data access."""

    accessed_resource: str
    access_type: str  # 'read', 'write', 'delete'
    access_reason: Optional[str] = None
    record_count: Optional[int] = None
    query_parameters: Optional[Dict[str, Any]] = None


class PlatformAccountAudit(AuditEvent):
    """Audit event for platform account linking."""

    platform: str
    platform_user_id: str
    link_type: str  # 'linked', 'unlinked', 'updated'
    previous_platform_user_id: Optional[str] = None
    verification_method: Optional[str] = None


class AuditSearchFilters(BaseModel):
    """Filters for audit log search."""

    event_type: Optional[AuditEventType] = None
    user_id: Optional[int] = None
    phone_number: Optional[str] = None
    platform: Optional[str] = None
    success: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditSearchResponse(BaseModel):
    """Response model for audit log search."""

    events: List[AuditEvent]
    total: int
    limit: int
    offset: int
    has_more: bool


class AuditStats(BaseModel):
    """Audit statistics model."""

    total_events: int
    events_by_type: Dict[str, int]
    events_by_platform: Dict[str, int]
    success_rate: float
    average_processing_time_ms: float
    events_today: int
    events_this_hour: int
    unique_users: int
    unique_phone_numbers: int


class ComplianceReport(BaseModel):
    """GDPR compliance report model."""

    report_period_start: datetime
    report_period_end: datetime
    total_data_subjects: int
    new_accounts_created: int
    consent_records: int
    data_access_requests: int
    data_deletion_requests: int
    consent_withdrawals: int
    audit_log_entries: int
    data_retention_compliance: bool
    consent_management_compliance: bool
    audit_logging_compliance: bool
    recommendations: List[str]


# Database query models
class AuditQuery:
    """Helper class for audit database queries."""

    @staticmethod
    def create_audit_table_sql() -> str:
        """SQL for creating account_creation_audit table."""
        return """
        CREATE TABLE IF NOT EXISTS account_creation_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            phone_number VARCHAR(20) NOT NULL,
            phone_validation_result VARCHAR(20) NOT NULL,
            parent_match_found BOOLEAN NOT NULL,
            parent_id INTEGER NULL,
            creation_status VARCHAR(20) NOT NULL,
            creation_source VARCHAR(10) NOT NULL,
            webhook_data TEXT NULL,
            error_message TEXT NULL,
            processing_time_ms INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            event_type VARCHAR(50) DEFAULT 'account_creation',
            platform VARCHAR(10) NULL,
            platform_user_id VARCHAR(50) NULL,
            success BOOLEAN DEFAULT TRUE,
            ip_address VARCHAR(45) NULL,
            user_agent TEXT NULL,
            FOREIGN KEY (user_id) REFERENCES user_accounts(id) ON DELETE SET NULL,
            FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE SET NULL
        )
        """

    @staticmethod
    def insert_audit_event_sql() -> str:
        """SQL for inserting audit event."""
        return """
        INSERT INTO account_creation_audit (
            user_id, phone_number, phone_validation_result, parent_match_found,
            parent_id, creation_status, creation_source, webhook_data,
            error_message, processing_time_ms, event_type, platform,
            platform_user_id, success, ip_address, user_agent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

    @staticmethod
    def select_audit_events_sql() -> str:
        """SQL for selecting audit events with filters."""
        return """
        SELECT * FROM account_creation_audit
        WHERE 1=1
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """

    @staticmethod
    def select_audit_events_by_type_sql() -> str:
        """SQL for selecting audit events by type."""
        return """
        SELECT * FROM account_creation_audit
        WHERE event_type = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """

    @staticmethod
    def select_audit_events_by_phone_sql() -> str:
        """SQL for selecting audit events by phone number."""
        return """
        SELECT * FROM account_creation_audit
        WHERE phone_number = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """

    @staticmethod
    def select_audit_events_by_user_sql() -> str:
        """SQL for selecting audit events by user ID."""
        return """
        SELECT * FROM account_creation_audit
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """

    @staticmethod
    def count_audit_events_sql() -> str:
        """SQL for counting audit events."""
        return """
        SELECT COUNT(*) as total FROM account_creation_audit
        """

    @staticmethod
    def get_audit_stats_sql() -> str:
        """SQL for getting audit statistics."""
        return """
        SELECT
            COUNT(*) as total_events,
            event_type,
            COUNT(CASE WHEN success = 1 THEN 1 END) as successful_events,
            COUNT(CASE WHEN success = 0 THEN 1 END) as failed_events,
            AVG(processing_time_ms) as avg_processing_time,
            platform,
            COUNT(DISTINCT phone_number) as unique_phone_numbers,
            COUNT(DISTINCT user_id) as unique_users
        FROM account_creation_audit
        WHERE created_at >= datetime('now', '-24 hours')
        GROUP BY event_type, platform
        """

    @staticmethod
    def create_audit_indexes_sql() -> str:
        """SQL for creating audit table indexes."""
        return """
        CREATE INDEX IF NOT EXISTS idx_audit_phone_number ON account_creation_audit(phone_number);
        CREATE INDEX IF NOT EXISTS idx_audit_user_id ON account_creation_audit(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_event_type ON account_creation_audit(event_type);
        CREATE INDEX IF NOT EXISTS idx_audit_platform ON account_creation_audit(platform);
        CREATE INDEX IF NOT EXISTS idx_audit_created_at ON account_creation_audit(created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_success ON account_creation_audit(success);
        CREATE INDEX IF NOT EXISTS idx_audit_lookup ON account_creation_audit(phone_number, platform, created_at);
        """

    @staticmethod
    def cleanup_old_audit_records_sql() -> str:
        """SQL for cleaning up old audit records."""
        return """
        DELETE FROM account_creation_audit
        WHERE created_at < datetime('now', '-1 year')
        """


# GDPR compliance utilities
class GDPRCompliance:
    """GDPR compliance utilities for audit system."""

    @staticmethod
    def anonymize_phone_number(phone_number: str) -> str:
        """Anonymize phone number for GDPR compliance."""
        if len(phone_number) <= 6:
            return "*" * len(phone_number)
        return phone_number[:3] + "*" * (len(phone_number) - 6) + phone_number[-3:]

    @staticmethod
    def anonymize_platform_user_id(platform_user_id: str) -> str:
        """Anonymize platform user ID for GDPR compliance."""
        if len(platform_user_id) <= 6:
            return "*" * len(platform_user_id)
        return platform_user_id[:3] + "*" * (len(platform_user_id) - 6) + platform_user_id[-3:]

    @staticmethod
    def should_retain_record(record_date: datetime, retention_days: int = 365) -> bool:
        """Check if audit record should be retained."""
        expiry_date = record_date + timedelta(days=retention_days)
        return datetime.utcnow() < expiry_date

    @staticmethod
    def create_data_subject_export(user_id: int, audit_events: List[AuditEvent]) -> Dict[str, Any]:
        """Create data subject export for GDPR compliance."""
        return {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "audit_events": [
                {
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "platform": event.platform,
                    "success": event.success,
                    "processing_time_ms": event.processing_time_ms
                }
                for event in audit_events
            ],
            "total_events": len(audit_events)
        }