"""
Configuration settings for WhatsApp AI Concierge Service
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List
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

    # AI Provider Selection
    ai_provider: str = Field(default="anthropic", env="AI_PROVIDER")
    enable_anthropic: bool = Field(default=True, env="ENABLE_ANTHROPIC")
    enable_gemini: bool = Field(default=False, env="ENABLE_GEMINI")
    enable_openrouter: bool = Field(default=False, env="ENABLE_OPENROUTER")

    # Anthropic/Claude AI Configuration
    anthropic_auth_token: str = Field(default="test-key")
    anthropic_base_url: str = Field(default="https://api.anthropic.com")
    claude_model: str = Field(default="glm-4.5-air", env="ANTHROPIC_DEFAULT_HAIKU_MODEL")
    claude_sonnet_model: str = Field(default="glm-4.6", env="ANTHROPIC_DEFAULT_SONNET_MODEL")
    claude_opus_model: str = Field(default="glm-4.6", env="ANTHROPIC_DEFAULT_OPUS_MODEL")
    claude_max_tokens: int = Field(default=1000)
    claude_temperature: float = Field(default=0.7)

    # Gemini AI Configuration
    gemini_api_keys: list = Field(default=[], env="GEMINI_API_KEYS")
    gemini_base_url: str = Field(default="https://generativelanguage.googleapis.com", env="GEMINI_BASE_URL")
    gemini_model: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    gemini_max_tokens: int = Field(default=1000)
    gemini_temperature: float = Field(default=0.7)

    # OpenRouter AI Configuration
    openrouter_api_keys: list = Field(default=[], env="OPENROUTER_API_KEYS")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    openrouter_model: str = Field(default="anthropic/claude-3.5-sonnet", env="OPENROUTER_MODEL")
    openrouter_max_tokens: int = Field(default=1000)
    openrouter_temperature: float = Field(default=0.7)

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

    # External URLs
    external_base_url: str = Field(default="http://localhost:8000", description="External base URL for shareable links")

    # Telegram Bot
    telegram_bot_token: str = Field(default="your-telegram-bot-token", description="Telegram bot API token")
    telegram_webhook_url: Optional[str] = Field(default=None, description="Telegram webhook URL")

    @validator('gemini_api_keys', pre=True)
    def parse_gemini_api_keys(cls, v):
        """Parse Gemini API keys from individual environment variables"""
        keys = []
        for i in range(1, 5):  # Support up to 4 keys
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key and key != f'your-gemini-api-key-{i}':
                keys.append(key)
        return keys

    @validator('openrouter_api_keys', pre=True)
    def parse_openrouter_api_keys(cls, v):
        """Parse OpenRouter API keys from individual environment variables"""
        keys = []
        for i in range(1, 5):  # Support up to 4 keys
            key = os.getenv(f'OPENROUTER_API_KEY_{i}')
            if key and key != f'your-openrouter-api-key-{i}':
                keys.append(key)
        return keys

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