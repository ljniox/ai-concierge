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
    secret_key: str = Field(..., env="SECRET_KEY")
    environment: str = Field(default="development", env="ENVIRONMENT")
    tz: str = Field(default="Africa/Dakar", env="TZ")

    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")

    # WAHA
    waha_base_url: str = Field(..., env="WAHA_BASE_URL")
    waha_api_token: str = Field(..., env="WAHA_API_TOKEN")

    # Claude AI
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")

    # Redis
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # JWT
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Service Configuration
    session_timeout_minutes: int = Field(default=30, description="Session timeout in minutes")
    max_retry_attempts: int = Field(default=3, description="Max retry attempts for failed operations")

    # Performance
    max_concurrent_requests: int = Field(default=100, description="Max concurrent requests")
    request_timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings