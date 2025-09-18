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
    secret_key: str = Field(default="your-secret-key-here-change-in-production", env="SECRET_KEY")
    environment: str = Field(default="development", env="ENVIRONMENT")
    tz: str = Field(default="Africa/Dakar", env="TZ")

    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")

    # WAHA
    waha_base_url: str = Field(default="http://localhost:3000", env="WAHA_BASE_URL")
    waha_api_token: str = Field(default="default-token", env="WAHA_API_TOKEN")
    waha_api_key: str = Field(default="default-token", env="WAHA_API_KEY")
    waha_session_id: str = Field(default="default", env="WAHA_SESSION_ID")
    waha_verify_token: str = Field(default="test-token", env="WAHA_VERIFY_TOKEN", alias="WEBHOOK_VERIFY_TOKEN")

    # Webhook Configuration
    webhook_url: str = Field(default="http://localhost:8000/api/v1/webhook", env="WEBHOOK_URL")
    webhook_verify_token: str = Field(default="test-token", env="WEBHOOK_VERIFY_TOKEN")
    session_name: str = Field(default="default", env="SESSION_NAME")
    port: int = Field(default=8000, env="PORT")

    # Claude AI
    anthropic_api_key: str = Field(default="test-key", env="ANTHROPIC_AUTH_TOKEN")
    anthropic_base_url: str = Field(default="https://api.anthropic.com", env="ANTHROPIC_BASE_URL")
    claude_model: str = Field(default="glm-4.5", env="ANTHROPIC_MODEL")
    claude_max_tokens: int = Field(default=1000, env="CLAUDE_MAX_TOKENS")
    claude_temperature: float = Field(default=0.7, env="CLAUDE_TEMPERATURE")

    # Redis
    redis_url: Optional[str] = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # JWT
    jwt_secret_key: str = Field(default="default-jwt-secret", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

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
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings