"""
Session data model for WhatsApp AI Concierge Service

Extended to support account creation system with platform-specific session management
for Telegram and WhatsApp integrations.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator
import json
import uuid


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CLOSED = "closed"


class SessionBase(BaseModel):
    """Base session model with common fields"""
    user_id: str = Field(..., description="Associated user ID")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Session status")
    current_service: Optional[str] = Field(None, description="Current active service")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session context data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional session metadata")


class SessionCreate(SessionBase):
    """Session model for creation"""
    pass


class SessionUpdate(BaseModel):
    """Session model for updates"""
    status: Optional[SessionStatus] = None
    current_service: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Session(SessionBase):
    """Complete session model"""
    id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Session expiration timestamp")
    last_activity_at: datetime = Field(..., description="Last activity timestamp")
    message_count: int = Field(default=0, description="Number of messages in session")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True

    @validator('current_service')
    def validate_service(cls, v):
        """Validate service type"""
        if v is not None:
            valid_services = ['RENSEIGNEMENT', 'CATECHESE', 'CONTACT_HUMAIN', 'SUPER_ADMIN']
            if v not in valid_services:
                raise ValueError(f"Invalid service. Must be one of: {valid_services}")
        return v

    @validator('expires_at')
    def validate_expiration(cls, v, values):
        """Validate expiration timestamp"""
        if v is not None:
            created_at = values.get('created_at')
            if created_at and isinstance(created_at, datetime):
                if v <= created_at:
                    raise ValueError("Expiration time must be after creation time")
        return v

    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.expires_at is None:
            return False
        now = datetime.now(self.expires_at.tzinfo) if self.expires_at.tzinfo else datetime.now()
        return now > self.expires_at

    @property
    def is_active_session(self) -> bool:
        """Check if session is currently active"""
        # Use timezone-aware datetime if session datetime has timezone
        now = datetime.now(self.last_activity_at.tzinfo) if self.last_activity_at.tzinfo else datetime.now()
        return (
            self.status == SessionStatus.ACTIVE and
            not self.is_expired and
            self.last_activity_at > now - timedelta(minutes=30)
        )

    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes"""
        now = datetime.now(self.created_at.tzinfo) if self.created_at.tzinfo else datetime.now()
        end_time = min(now, self.expires_at) if self.expires_at else now
        duration = end_time - self.created_at
        return duration.total_seconds() / 60

    def update_activity(self):
        """Update last activity timestamp"""
        now = datetime.now(self.last_activity_at.tzinfo) if hasattr(self, 'last_activity_at') and self.last_activity_at.tzinfo else datetime.now()
        self.last_activity_at = now
        self.updated_at = now

    def add_message(self):
        """Increment message count and update activity"""
        self.message_count += 1
        self.update_activity()

    def change_service(self, new_service: str):
        """Change current service"""
        self.current_service = new_service
        self.update_activity()

    def update_context(self, key: str, value: Any):
        """Update session context"""
        if self.context is None:
            self.context = {}
        self.context[key] = value
        self.update_activity()

    def close_session(self):
        """Close the session"""
        self.status = SessionStatus.CLOSED
        self.update_activity()


class SessionResponse(Session):
    """Session model for API responses"""
    pass


class SessionInDB(Session):
    """Session model as stored in database"""
    # Add any database-specific fields here
    pass


class SessionWithStats(SessionResponse):
    """Session model with additional statistics"""
    user_name: Optional[str] = Field(None, description="Associated user name")
    service_distribution: Dict[str, int] = Field(default_factory=dict, description="Service usage distribution")
    average_response_time: float = Field(default=0.0, description="Average response time in seconds")


class SessionListResponse(BaseModel):
    """Response model for session list"""
    sessions: list[SessionResponse]
    total: int
    page: int
    per_page: int


def create_session_expiration(duration_minutes: int = 30) -> datetime:
    """
    Create session expiration timestamp

    Args:
        duration_minutes: Session duration in minutes

    Returns:
        Expiration timestamp
    """
    return datetime.now() + timedelta(minutes=duration_minutes)


def validate_session_context(context: Dict[str, Any]) -> bool:
    """
    Validate session context data

    Args:
        context: Session context to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(context, dict):
        return False

    # Check for any sensitive or problematic keys
    sensitive_keys = ['password', 'token', 'secret', 'key', 'auth']
    for key in context.keys():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            return False

    return True


# ==============================================================================
# Account Creation System Session Models
# ==============================================================================

class PlatformType(str, Enum):
    """Supported messaging platforms for account creation."""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"


class SessionType(str, Enum):
    """Session types for account creation system."""
    ACCOUNT_CREATION = "account_creation"
    GENERAL_CONVERSATION = "general_conversation"
    ROLE_MANAGEMENT = "role_management"
    SUPPORT_REQUEST = "support_request"


class AccountCreationSession(BaseModel):
    """Extended session model for account creation system."""

    user_id: Optional[int] = Field(None, gt=0)
    session_id: str = Field(..., regex=r"^[a-f0-9-]{36}$")
    platform: PlatformType = Field(...)
    platform_user_id: str = Field(...)
    account_creation_state: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_type: SessionType = Field(default=SessionType.ACCOUNT_CREATION)
    is_active: bool = Field(default=True)
    expires_at: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None

    @validator('session_id')
    def generate_session_id(cls, v):
        """Generate UUID-based session ID if not provided."""
        if not v:
            return str(uuid.uuid4())
        return v

    @validator('expires_at')
    def validate_expiry(cls, v):
        """Validate expiry date is in the future."""
        if v <= datetime.utcnow():
            raise ValueError('Expiry date must be in the future')
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AccountCreationState(BaseModel):
    """State model for account creation flow."""

    phone_number_provided: bool = Field(default=False)
    phone_number: Optional[str] = None
    phone_validated: bool = Field(default=False)
    parent_found: bool = Field(default=False)
    parent_data: Optional[Dict[str, Any]] = None
    consent_obtained: bool = Field(default=False)
    account_created: bool = Field(default=False)
    user_id: Optional[int] = None
    welcome_sent: bool = Field(default=False)
    current_step: str = Field(default="initial")
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)

    @property
    def is_completed(self) -> bool:
        """Check if account creation flow is completed."""
        return self.account_created and self.welcome_sent

    @property
    def can_retry(self) -> bool:
        """Check if flow can be retried."""
        return self.retry_count < self.max_retries

    def advance_step(self, new_step: str) -> None:
        """Advance to next step."""
        self.previous_step = self.current_step
        self.current_step = new_step

    def set_error(self, error_message: str) -> None:
        """Set error state and increment retry count."""
        self.error_message = error_message
        self.retry_count += 1


class SessionCreate(BaseModel):
    """Model for creating new account creation sessions."""

    platform: PlatformType = Field(...)
    platform_user_id: str = Field(...)
    session_type: SessionType = Field(default=SessionType.ACCOUNT_CREATION)
    session_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    expires_in_minutes: int = Field(default=30, ge=5, le=1440)  # 5 minutes to 24 hours
    user_id: Optional[int] = Field(None, gt=0)


class SessionStats(BaseModel):
    """Session statistics for account creation system."""

    total_sessions: int
    active_sessions: int
    expired_sessions: int
    sessions_by_platform: Dict[str, int]
    sessions_by_type: Dict[str, int]
    average_session_duration_minutes: float
    sessions_created_today: int
    sessions_created_this_hour: int
    successful_account_creations: int
    failed_account_creations: int


# Database query models for account creation sessions
class AccountSessionQuery:
    """Helper class for account creation session database queries."""

    @staticmethod
    def create_account_sessions_view_sql() -> str:
        """SQL for creating view for account creation sessions."""
        return """
        CREATE VIEW IF NOT EXISTS account_creation_sessions AS
        SELECT
            s.*,
            ua.phone_number,
            ua.full_name,
            ua.account_source
        FROM user_sessions s
        LEFT JOIN user_accounts ua ON s.user_id = ua.id
        WHERE s.session_type = 'account_creation'
        """

    @staticmethod
    def select_active_account_sessions_sql() -> str:
        """SQL for selecting active account creation sessions."""
        return """
        SELECT s.*, ua.phone_number, ua.full_name
        FROM user_sessions s
        LEFT JOIN user_accounts ua ON s.user_id = ua.id
        WHERE s.session_type = 'account_creation'
          AND s.is_active = 1
          AND s.expires_at > CURRENT_TIMESTAMP
        ORDER BY s.created_at DESC
        """

    @staticmethod
    def get_account_session_stats_sql() -> str:
        """SQL for getting account creation session statistics."""
        return """
        SELECT
            COUNT(*) as total_sessions,
            COUNT(CASE WHEN is_active = 1 AND expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_sessions,
            COUNT(CASE WHEN is_active = 0 OR expires_at <= CURRENT_TIMESTAMP THEN 1 END) as expired_sessions,
            platform,
            COUNT(CASE WHEN JSON_EXTRACT(session_data, '$.account_created') = true THEN 1 END) as successful_creations,
            COUNT(CASE WHEN JSON_EXTRACT(session_data, '$.account_created') = false THEN 1 END) as failed_creations
        FROM user_sessions
        WHERE session_type = 'account_creation'
        GROUP BY platform
        """