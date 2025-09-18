"""
Message data model for WhatsApp AI Concierge Service
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Message type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    REACTION = "reaction"


class MessageStatus(str, Enum):
    """Message status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class MessageBase(BaseModel):
    """Base message model with common fields"""
    session_id: str = Field(..., description="Associated session ID")
    phone_number: str = Field(..., description="Recipient phone number")
    message_type: MessageType = Field(..., description="Type of message")
    content: Optional[str] = Field(None, description="Message content")
    media_url: Optional[str] = Field(None, description="URL for media files")
    status: MessageStatus = Field(default=MessageStatus.PENDING, description="Message status")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional message metadata")


class MessageCreate(MessageBase):
    """Message model for creation"""
    pass


class MessageUpdate(BaseModel):
    """Message model for updates"""
    status: Optional[MessageStatus] = None
    content: Optional[str] = None
    media_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Message(MessageBase):
    """Complete message model"""
    id: str = Field(..., description="Message ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class Sentiment(str, Enum):
    """Sentiment enumeration for message analysis"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class Confidence(BaseModel):
    """Confidence scores for AI predictions"""
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    intent: float = Field(..., ge=0.0, le=1.0, description="Intent classification confidence")
    sentiment: float = Field(..., ge=0.0, le=1.0, description="Sentiment analysis confidence")
    entities: float = Field(..., ge=0.0, le=1.0, description="Entity recognition confidence")


class MessageWithAnalysis(Message):
    """Message model with AI analysis"""
    sentiment: Optional[Sentiment] = Field(None, description="Message sentiment")
    confidence: Optional[Confidence] = Field(None, description="AI confidence scores")
    intent: Optional[str] = Field(None, description="Detected user intent")
    entities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted entities")


class MessageAnalytics(BaseModel):
    """Analytics for message metrics"""
    total_messages: int = Field(..., description="Total number of messages")
    messages_by_type: Dict[str, int] = Field(default_factory=dict, description="Messages broken down by type")
    messages_by_status: Dict[str, int] = Field(default_factory=dict, description="Messages broken down by status")
    average_response_time: Optional[float] = Field(None, description="Average response time in seconds")
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of message sentiments")
    top_intents: List[Dict[str, Any]] = Field(default_factory=list, description="Top detected intents")
    period_start: Optional[datetime] = Field(None, description="Start of analysis period")
    period_end: Optional[datetime] = Field(None, description="End of analysis period")