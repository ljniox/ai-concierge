"""
Session data model for WhatsApp AI Concierge Service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


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
            valid_services = ['RENSEIGNEMENT', 'CATECHESE', 'CONTACT_HUMAIN']
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
        return datetime.now() > self.expires_at

    @property
    def is_active_session(self) -> bool:
        """Check if session is currently active"""
        return (
            self.status == SessionStatus.ACTIVE and
            not self.is_expired and
            self.last_activity_at > datetime.now() - timedelta(minutes=30)
        )

    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes"""
        now = datetime.now()
        end_time = min(now, self.expires_at) if self.expires_at else now
        duration = end_time - self.created_at
        return duration.total_seconds() / 60

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.now()
        self.updated_at = datetime.now()

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