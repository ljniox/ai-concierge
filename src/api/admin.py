"""
Admin endpoints for WhatsApp AI Concierge Service
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from src.utils.config import get_settings
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()
admin_router = APIRouter()
security = HTTPBearer()


class AdminStatsResponse(BaseModel):
    """Response model for admin statistics"""
    total_users: int
    active_sessions: int
    total_interactions: int
    service_distribution: Dict[str, int]
    response_times: Dict[str, float]
    uptime_hours: float


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    phone_number: str
    status: str
    current_service: Optional[str]
    created_at: str
    updated_at: str
    message_count: int


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: dict = Depends(get_settings)
) -> bool:
    """
    Verify admin authentication token
    """
    # TODO: Implement proper JWT validation
    # For now, just check if token exists
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


@admin_router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    authenticated: bool = Depends(verify_admin_token),
    settings: dict = Depends(get_settings)
):
    """
    Get administrative statistics
    """
    try:
        logger.info("admin_stats_request")

        # TODO: Implement actual statistics calculation
        mock_stats = {
            "total_users": 150,
            "active_sessions": 45,
            "total_interactions": 1250,
            "service_distribution": {
                "RENSEIGNEMENT": 650,
                "CATECHESE": 400,
                "CONTACT_HUMAIN": 200
            },
            "response_times": {
                "average": 2.3,
                "p95": 5.1,
                "p99": 8.7
            },
            "uptime_hours": 168.5
        }

        logger.info("admin_stats_retrieved")
        return AdminStatsResponse(**mock_stats)

    except Exception as e:
        logger.error("admin_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@admin_router.get("/admin/sessions", response_model=List[SessionInfo])
async def get_admin_sessions(
    limit: int = 50,
    offset: int = 0,
    authenticated: bool = Depends(verify_admin_token),
    settings: dict = Depends(get_settings)
):
    """
    Get list of recent sessions for admin monitoring
    """
    try:
        logger.info("admin_sessions_request", limit=limit, offset=offset)

        # TODO: Implement actual session retrieval from database
        mock_sessions = [
            {
                "session_id": f"session-{i}",
                "phone_number": f"+221771234{i:03d}",
                "status": "active" if i % 3 == 0 else "inactive",
                "current_service": "RENSEIGNEMENT" if i % 2 == 0 else "CATECHESE",
                "created_at": (datetime.now() - timedelta(hours=i)).isoformat(),
                "updated_at": (datetime.now() - timedelta(minutes=i*10)).isoformat(),
                "message_count": i * 3
            }
            for i in range(1, min(limit + 1, 11))
        ]

        logger.info("admin_sessions_retrieved", count=len(mock_sessions))
        return [SessionInfo(**session) for session in mock_sessions]

    except Exception as e:
        logger.error("admin_sessions_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@admin_router.get("/admin/health/detailed")
async def get_detailed_health(
    authenticated: bool = Depends(verify_admin_token),
    settings: dict = Depends(get_settings)
):
    """
    Get detailed health information for monitoring
    """
    try:
        logger.info("detailed_health_request")

        # TODO: Implement actual health checks for all services
        detailed_health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "database": {
                    "status": "healthy",
                    "response_time": 0.023,
                    "last_check": datetime.now().isoformat()
                },
                "redis": {
                    "status": "healthy",
                    "response_time": 0.001,
                    "last_check": datetime.now().isoformat()
                },
                "waha": {
                    "status": "healthy",
                    "response_time": 0.150,
                    "last_check": datetime.now().isoformat()
                },
                "claude": {
                    "status": "healthy",
                    "response_time": 1.250,
                    "last_check": datetime.now().isoformat()
                }
            },
            "metrics": {
                "memory_usage_mb": 256,
                "cpu_usage_percent": 15.2,
                "active_connections": 45,
                "queue_size": 12
            }
        }

        logger.info("detailed_health_retrieved")
        return detailed_health

    except Exception as e:
        logger.error("detailed_health_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve health information")