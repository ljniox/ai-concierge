"""
User data model for WhatsApp AI Concierge Service
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re
import phonenumbers


class UserBase(BaseModel):
    """Base user model with common fields"""
    phone_number: str = Field(..., description="User's phone number in E.164 format")
    name: Optional[str] = Field(None, description="User's name")
    preferred_language: str = Field(default="fr", description="Preferred language code")
    timezone: str = Field(default="Africa/Dakar", description="User's timezone")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional user metadata")


class UserCreate(UserBase):
    """User model for creation"""
    pass


class UserUpdate(BaseModel):
    """User model for updates"""
    name: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class User(UserBase):
    """Complete user model"""
    id: str = Field(..., description="Unique user identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the user is active")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        try:
            # Handle WhatsApp special numbers (groups, broadcasts, etc.)
            if v.endswith('@g.us') or v.endswith('@s.whatsapp.net') or v == 'status@broadcast':
                return v  # Accept WhatsApp special numbers as-is

            # Handle WAHA format (numbers without + prefix)
            if v.isdigit() and len(v) >= 8:  # Basic phone number without +
                # Try to parse with common country codes
                if v.startswith('221'):  # Senegal
                    parsed_number = phonenumbers.parse(f"+{v}", None)
                elif v.startswith('1'):  # US/Canada
                    parsed_number = phonenumbers.parse(f"+{v}", None)
                elif v.startswith('44'):  # UK
                    parsed_number = phonenumbers.parse(f"+{v}", None)
                elif v.startswith('33'):  # France
                    parsed_number = phonenumbers.parse(f"+{v}", None)
                else:
                    # Try parsing as-is first, then with + if that fails
                    try:
                        parsed_number = phonenumbers.parse(v, None)
                    except phonenumbers.NumberParseException:
                        parsed_number = phonenumbers.parse(f"+{v}", None)
            else:
                # Parse phone number with + prefix
                parsed_number = phonenumbers.parse(v, None)

            # Check if it's a valid number
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")

            # Return in E.164 format
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")
        except Exception:
            raise ValueError("Phone number validation failed")

    @validator('preferred_language')
    def validate_language(cls, v):
        """Validate language code"""
        valid_languages = ['fr', 'en', 'wo']  # French, English, Wolof
        if v not in valid_languages:
            raise ValueError(f"Invalid language code. Must be one of: {valid_languages}")
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone"""
        # Simple validation for common timezones
        valid_timezones = [
            'Africa/Dakar', 'Africa/Abidjan', 'Africa/Accra', 'Africa/Lagos',
            'Africa/Nairobi', 'Africa/Johannesburg', 'UTC', 'Europe/Paris'
        ]
        if v not in valid_timezones:
            raise ValueError(f"Invalid timezone. Must be one of: {valid_timezones}")
        return v


class UserResponse(User):
    """User model for API responses"""
    pass


class UserInDB(User):
    """User model as stored in database"""
    # Add any database-specific fields here
    pass


class UserWithStats(UserResponse):
    """User model with additional statistics"""
    total_sessions: int = Field(default=0, description="Total number of sessions")
    total_interactions: int = Field(default=0, description="Total number of interactions")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction timestamp")
    preferred_service: Optional[str] = Field(None, description="Most frequently used service")


def validate_phone_number_format(phone_number: str) -> bool:
    """
    Validate phone number format (standalone function)

    Args:
        phone_number: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        # Handle WhatsApp special numbers (groups, broadcasts, etc.)
        if phone_number.endswith('@g.us') or phone_number.endswith('@s.whatsapp.net') or phone_number == 'status@broadcast':
            return True  # Accept WhatsApp special numbers

        # Handle WAHA format (numbers without + prefix)
        if phone_number.isdigit() and len(phone_number) >= 8:
            # Try to parse with common country codes
            if phone_number.startswith('221'):  # Senegal
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            elif phone_number.startswith('1'):  # US/Canada
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            elif phone_number.startswith('44'):  # UK
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            elif phone_number.startswith('33'):  # France
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            else:
                # Try parsing as-is first, then with + if that fails
                try:
                    parsed_number = phonenumbers.parse(phone_number, None)
                except phonenumbers.NumberParseException:
                    parsed_number = phonenumbers.parse(f"+{phone_number}", None)
        else:
            # Parse phone number with + prefix
            parsed_number = phonenumbers.parse(phone_number, None)

        return phonenumbers.is_valid_number(parsed_number)
    except Exception:
        return False


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number to E.164 format

    Args:
        phone_number: Phone number to normalize

    Returns:
        Normalized phone number in E.164 format
    """
    try:
        # Handle WhatsApp special numbers (groups, broadcasts, etc.)
        if phone_number.endswith('@g.us') or phone_number.endswith('@s.whatsapp.net') or phone_number == 'status@broadcast':
            return phone_number  # Return WhatsApp special numbers as-is

        # Handle WAHA format (numbers without + prefix)
        if phone_number.isdigit() and len(phone_number) >= 8:
            # Try to parse with common country codes
            if phone_number.startswith('221'):  # Senegal
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            elif phone_number.startswith('1'):  # US/Canada
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            elif phone_number.startswith('44'):  # UK
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            elif phone_number.startswith('33'):  # France
                parsed_number = phonenumbers.parse(f"+{phone_number}", None)
            else:
                # Try parsing as-is first, then with + if that fails
                try:
                    parsed_number = phonenumbers.parse(phone_number, None)
                except phonenumbers.NumberParseException:
                    parsed_number = phonenumbers.parse(f"+{phone_number}", None)
        else:
            # Parse phone number with + prefix
            parsed_number = phonenumbers.parse(phone_number, None)

        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        raise ValueError(f"Cannot normalize phone number: {phone_number}")