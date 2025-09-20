"""
Health check endpoints for WhatsApp AI Concierge Service
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from src.utils.config import Settings, get_settings
import structlog

logger = structlog.get_logger()
health_router = APIRouter()


@health_router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint for monitoring service status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
        "services": {
            "database": "unknown",  # Will be updated with actual health check
            "redis": "unknown",
            "waha": "unknown",
            "claude": "unknown"
        }
    }


@health_router.get("/version")
async def version_check():
    """
    Version information endpoint
    """
    return {
        "version": "1.0.0",
        "name": "WhatsApp AI Concierge Service",
        "build_date": datetime.now().isoformat(),
        "commit": "development"  # Will be updated with actual commit hash
    }


@health_router.get("/config")
async def config_check(settings: Settings = Depends(get_settings)):
    """
    Configuration diagnostic endpoint (without exposing sensitive data)
    """
    # Check which sensitive values are set (without revealing them)
    sensitive_keys = [
        'anthropic_api_key', 'supabase_service_role_key', 'supabase_anon_key',
        'waha_api_token', 'waha_api_key', 'redis_password'
    ]
    
    config_status = {}
    for key in sensitive_keys:
        value = getattr(settings, key, None)
        if value and value != "" and value != "test-key" and value != "default-token":
            config_status[key] = "SET"
        else:
            config_status[key] = "NOT_SET"
    
    # Check non-sensitive config
    non_sensitive = {
        'environment': settings.environment,
        'waha_base_url': settings.waha_base_url,
        'supabase_url': settings.supabase_url,
        'anthropic_base_url': settings.anthropic_base_url,
        'claude_model': settings.claude_model,
        'redis_url': settings.redis_url,
        'redis_host': settings.redis_host,
        'redis_port': settings.redis_port,
        'session_timeout_minutes': settings.session_timeout_minutes
    }
    
    return {
        "status": "configuration_check",
        "timestamp": datetime.now().isoformat(),
        "sensitive_config": config_status,
        "non_sensitive_config": non_sensitive,
        "note": "This endpoint helps diagnose configuration issues without exposing secrets"
    }