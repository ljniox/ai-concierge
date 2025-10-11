"""
Health check API endpoints for monitoring system health.

This module provides FastAPI endpoints for health monitoring
including individual service checks and overall system health.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Response
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime, timezone

from src.services.health_check_service import (
    get_health_checker,
    check_service_health,
    check_all_services_health,
    log_health_check_event,
    HealthStatus,
    HealthCheckResult,
    SystemHealthReport
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Create router for health endpoints
router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get(
    "/",
    summary="Overall System Health",
    description="Check the health of all system services and return overall status",
    responses={
        200: {
            "description": "System health status",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "total_checks": 6,
                        "healthy_checks": 6,
                        "degraded_checks": 0,
                        "unhealthy_checks": 0,
                        "unknown_checks": 0,
                        "total_response_time_ms": 125,
                        "average_response_time_ms": 20,
                        "checks": [
                            {
                                "service_name": "database",
                                "status": "healthy",
                                "message": "Database is healthy",
                                "response_time_ms": 15
                            }
                        ],
                        "timestamp": "2025-01-01T12:00:00Z",
                        "version": "2.0.0"
                    }
                }
            }
        },
        503: {
            "description": "System is unhealthy or degraded"
        }
    }
)
async def health_check(
    include_details: bool = Query(
        False,
        description="Include detailed health check results for all services"
    ),
    log_check: bool = Query(
        True,
        description="Log the health check event to audit service"
    )
) -> Dict[str, Any]:
    """
    Check the health of all system services.

    This endpoint checks all registered services and returns:
    - Overall system status (healthy/degraded/unhealthy/unknown)
    - Individual service health status
    - Response times and detailed information
    - System version and timestamp

    The endpoint is suitable for load balancers and monitoring systems.
    """
    try:
        # Get comprehensive health report
        report = await check_all_services_health()

        # Optionally log the health check event
        if log_check:
            try:
                await log_health_check_event(report)
            except Exception as log_error:
                logger.warning(f"Failed to log health check event: {log_error}")

        # Prepare response
        response_data = report.to_dict()

        # Set appropriate HTTP status based on overall health
        status_code = 200
        if report.status == HealthStatus.UNHEALTHY:
            status_code = 503
        elif report.status == HealthStatus.DEGRADED:
            status_code = 200  # Still return 200 but indicate degraded status

        # Remove detailed checks if not requested
        if not include_details:
            response_data.pop("checks", None)

        return JSONResponse(
            status_code=status_code,
            content=response_data
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": [],
                "total_checks": 0,
                "healthy_checks": 0,
                "degraded_checks": 0,
                "unhealthy_checks": 0,
                "unknown_checks": 0,
                "total_response_time_ms": 0,
                "version": "2.0.0"
            }
        )


@router.get(
    "/simple",
    summary="Simple Health Check",
    description="Simple health check endpoint for load balancers and monitoring",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "text/plain": {
                    "example": "OK"
                }
            }
        },
        503: {
            "description": "Service is unhealthy"
        }
    }
)
async def simple_health_check() -> str:
    """
    Simple health check endpoint.

    Returns "OK" if the service is running, regardless of component health.
    This endpoint is suitable for basic load balancer health checks.
    """
    return "OK"


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the service is ready to handle requests",
    responses={
        200: {
            "description": "Service is ready"
        },
        503: {
            "description": "Service is not ready"
        }
    }
)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.

    Checks if essential services (database, Redis) are available
    to determine if the service is ready to handle requests.
    """
    try:
        checker = get_health_checker()

        # Check only essential services
        essential_checks = ["database", "redis"]
        results = []

        for service_name in essential_checks:
            result = await checker.check_service_health(service_name)
            results.append(result)

        # Determine if service is ready
        ready = all(result.status == HealthStatus.HEALTHY for result in results)

        status_code = 200 if ready else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "ready": ready,
                "checks": [result.to_dict() for result in results],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get(
    "/live",
    summary="Liveness Check",
    description="Check if the service is alive",
    responses={
        200: {
            "description": "Service is alive"
        }
    }
)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.

    This endpoint always returns 200 if the service process is running.
    It's used by orchestration systems to determine if the container
    needs to be restarted.
    """
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }


@router.get(
    "/service/{service_name}",
    summary="Service Health Check",
    description="Check the health of a specific service",
    responses={
        200: {
            "description": "Service health status"
        },
        404: {
            "description": "Service not found"
        },
        503: {
            "description": "Service is unhealthy"
        }
    }
)
async def service_health_check(
    service_name: str,
    log_check: bool = Query(
        False,
        description="Log the service health check event"
    )
) -> Dict[str, Any]:
    """
    Check the health of a specific service.

    Returns detailed health information for the requested service including:
    - Service status
    - Response time
    - Detailed information and error messages
    - Timestamp of the check
    """
    try:
        result = await check_service_health(service_name)

        # Set appropriate HTTP status
        status_code = 200
        if result.status == HealthStatus.UNHEALTHY:
            status_code = 503
        elif result.status == HealthStatus.UNKNOWN:
            status_code = 404

        response_data = result.to_dict()

        # Optionally log the service health check
        if log_check:
            try:
                from src.services.audit_service import log_audit_event
                await log_audit_event(
                    event_type="service_health_check",
                    user_id="system",
                    event_data={
                        "service_name": service_name,
                        "status": result.status.value,
                        "response_time_ms": result.response_time_ms,
                        "message": result.message
                    },
                    ip_address="127.0.0.1",
                    user_agent="HealthCheckAPI/1.0"
                )
            except Exception as log_error:
                logger.warning(f"Failed to log service health check: {log_error}")

        return JSONResponse(
            status_code=status_code,
            content=response_data
        )

    except Exception as e:
        logger.error(f"Service health check failed for {service_name}: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "service_name": service_name,
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )


@router.get(
    "/services",
    summary="Available Services",
    description="Get list of available health check services"
)
async def get_available_services() -> Dict[str, Any]:
    """
    Get list of services that can be health checked.

    Returns a list of all registered health check services
    that can be individually monitored.
    """
    try:
        checker = get_health_checker()
        services = list(checker.checks.keys())

        return {
            "available_services": services,
            "total_services": len(services),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get available services: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to retrieve available services",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get(
    "/metrics",
    summary="Health Metrics",
    description="Get health check metrics and statistics"
)
async def get_health_metrics() -> Dict[str, Any]:
    """
    Get health check metrics and statistics.

    Returns aggregated metrics about service health over time.
    This endpoint can be used for monitoring dashboards.
    """
    try:
        # Get current health report
        report = await check_all_services_health()

        # Calculate additional metrics
        metrics = {
            "current_status": report.status.value,
            "service_count": {
                "total": report.total_checks,
                "healthy": report.healthy_checks,
                "degraded": report.degraded_checks,
                "unhealthy": report.unhealthy_checks,
                "unknown": report.unknown_checks
            },
            "performance": {
                "total_response_time_ms": report.total_response_time_ms,
                "average_response_time_ms": report.total_response_time_ms // max(report.total_checks, 1)
            },
            "services": {}
        }

        # Add individual service metrics
        for check in report.checks:
            service_name = check.service_name
            metrics["services"][service_name] = {
                "status": check.status.value,
                "response_time_ms": check.response_time_ms,
                "message": check.message
            }

        return {
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get health metrics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to retrieve health metrics",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# Dependency injection for health checker
def get_health_checker_dependency() -> HealthChecker:
    """Dependency function to get health checker."""
    return get_health_checker()