"""
Configuration settings for WhatsApp AI Concierge Service
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    secret_key: str = Field(default="your-secret-key-here-change-in-production")
    environment: str = Field(default="development")
    tz: str = Field(default="Africa/Dakar")

    # Supabase
    supabase_url: str = Field(default="https://example.supabase.co")
    supabase_anon_key: str = Field(default="default-anon-key")
    supabase_service_role_key: str = Field(default="default-service-key")

    # WAHA
    waha_base_url: str = Field(default="http://localhost:3000")
    waha_api_token: str = Field(default="default-token")
    waha_api_key: str = Field(default="default-token")
    waha_session_id: str = Field(default="default")
    waha_verify_token: str = Field(default="test-token")

    # Webhook Configuration
    webhook_url: str = Field(default="http://localhost:8000/api/v1/webhook")
    webhook_verify_token: str = Field(default="test-token")
    session_name: str = Field(default="default")
    port: int = Field(default=8000)

    # Claude AI
    anthropic_auth_token: str = Field(default="test-key")
    anthropic_base_url: str = Field(default="https://api.anthropic.com")
    claude_model: str = Field(default="claude-3-sonnet-20240229")
    claude_max_tokens: int = Field(default=1000)
    claude_temperature: float = Field(default=0.7)

    # Redis
    redis_url: Optional[str] = Field(default="redis://localhost:6379/0")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)

    # JWT
    jwt_secret_key: str = Field(default="default-jwt-secret")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)

    # Logging
    log_level: str = Field(default="INFO")

    # Service Configuration
    session_timeout_minutes: int = Field(default=30, description="Session timeout in minutes")
    max_retry_attempts: int = Field(default=3, description="Max retry attempts for failed operations")
    rate_limit_per_minute: int = Field(default=10, description="Rate limit per minute per user")

    # Performance
    max_concurrent_requests: int = Field(default=100, description="Max concurrent requests")
    request_timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings