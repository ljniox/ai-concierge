"""
Interaction data model for WhatsApp AI Concierge Service
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class InteractionType(str, Enum):
    """Interaction type enumeration"""
    MESSAGE = "message"
    SYSTEM = "system"
    HANDOFF = "handoff"
    ERROR = "error"


class MessageType(str, Enum):
    """Message type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"


class InteractionBase(BaseModel):
    """Base interaction model with common fields"""
    session_id: str = Field(..., description="Associated session ID")
    user_message: Optional[str] = Field(None, description="User's message")
    assistant_response: Optional[str] = Field(None, description="Assistant's response")
    service: str = Field(..., description="Service that handled the interaction")
    interaction_type: InteractionType = Field(default=InteractionType.MESSAGE, description="Type of interaction")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for AI response")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional interaction metadata")


class InteractionCreate(InteractionBase):
    """Interaction model for creation"""
    pass


class InteractionUpdate(BaseModel):
    """Interaction model for updates"""
    user_message: Optional[str] = None
    assistant_response: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class Interaction(InteractionBase):
    """Complete interaction model"""
    id: str = Field(..., description="Unique interaction identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    language_detected: Optional[str] = Field(None, description="Detected language")
    intent_detected: Optional[str] = Field(None, description="Detected intent")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Sentiment score")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True

    @validator('service')
    def validate_service(cls, v):
        """Validate service type"""
        valid_services = ['RENSEIGNEMENT', 'CATECHESE', 'CONTACT_HUMAIN']
        if v not in valid_services:
            raise ValueError(f"Invalid service. Must be one of: {valid_services}")
        return v

    @validator('confidence_score')
    def validate_confidence(cls, v):
        """Validate confidence score"""
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

    @validator('sentiment_score')
    def validate_sentiment(cls, v):
        """Validate sentiment score"""
        if v is not None and (v < -1.0 or v > 1.0):
            raise ValueError("Sentiment score must be between -1.0 and 1.0")
        return v

    @validator('language_detected')
    def validate_language(cls, v):
        """Validate language code"""
        if v is not None:
            valid_languages = ['fr', 'en', 'wo']  # French, English, Wolof
            if v not in valid_languages:
                raise ValueError(f"Invalid language code. Must be one of: {valid_languages}")
        return v

    @property
    def is_high_confidence(self) -> bool:
        """Check if interaction has high confidence"""
        return self.confidence_score >= 0.8

    @property
    def is_low_confidence(self) -> bool:
        """Check if interaction has low confidence"""
        return self.confidence_score < 0.5

    @property
    def requires_human_review(self) -> bool:
        """Check if interaction requires human review"""
        return (
            self.is_low_confidence or
            self.sentiment_score is not None and self.sentiment_score < -0.5 or
            self.interaction_type == InteractionType.ERROR
        )

    @property
    def processing_time_seconds(self) -> float:
        """Get processing time in seconds"""
        if self.processing_time_ms is not None:
            return self.processing_time_ms / 1000.0
        return 0.0

    def update_processing_time(self, start_time: datetime):
        """Update processing time based on start time"""
        end_time = datetime.now()
        self.processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        self.updated_at = end_time

    def add_metadata(self, key: str, value: Any):
        """Add metadata to interaction"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
        self.updated_at = datetime.now()


class InteractionResponse(Interaction):
    """Interaction model for API responses"""
    pass


class InteractionInDB(Interaction):
    """Interaction model as stored in database"""
    # Add any database-specific fields here
    pass


class InteractionWithDetails(InteractionResponse):
    """Interaction model with additional details"""
    user_name: Optional[str] = Field(None, description="Associated user name")
    session_status: Optional[str] = Field(None, description="Session status")
    follow_up_required: bool = Field(default=False, description="Whether follow-up is required")


class InteractionListResponse(BaseModel):
    """Response model for interaction list"""
    interactions: list[InteractionResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class InteractionAnalytics(BaseModel):
    """Analytics data for interactions"""
    total_interactions: int
    service_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]  # low, medium, high
    sentiment_distribution: Dict[str, int]  # positive, neutral, negative
    average_processing_time: float
    peak_hours: list[int]  # Hours with most interactions
    language_distribution: Dict[str, int]


def calculate_confidence_category(confidence_score: float) -> str:
    """
    Calculate confidence category from score

    Args:
        confidence_score: Confidence score between 0.0 and 1.0

    Returns:
        Confidence category: 'low', 'medium', or 'high'
    """
    if confidence_score < 0.5:
        return 'low'
    elif confidence_score < 0.8:
        return 'medium'
    else:
        return 'high'


def calculate_sentiment_category(sentiment_score: float) -> str:
    """
    Calculate sentiment category from score

    Args:
        sentiment_score: Sentiment score between -1.0 and 1.0

    Returns:
        Sentiment category: 'negative', 'neutral', or 'positive'
    """
    if sentiment_score < -0.2:
        return 'negative'
    elif sentiment_score > 0.2:
        return 'positive'
    else:
        return 'neutral'


def validate_interaction_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate interaction metadata

    Args:
        metadata: Metadata to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(metadata, dict):
        return False

    # Check for any sensitive or problematic keys
    sensitive_keys = ['password', 'token', 'secret', 'key', 'auth', 'credit_card']
    for key in metadata.keys():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            return False

    return True