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