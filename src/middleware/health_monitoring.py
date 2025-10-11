"""
Health monitoring middleware for automatic API health tracking.

This middleware provides automatic health monitoring for API endpoints,
including request timing, error tracking, and service health integration.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
import json

from src.utils.logging import get_logger
from src.services.redis_service import get_redis_service
from src.services.health_check_service import get_health_checker, HealthStatus

logger = get_logger(__name__)


class HealthMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic health monitoring of API endpoints.

    Features:
    - Request timing and performance monitoring
    - Error rate tracking
    - Service health integration
    - Automatic degradation detection
    - Metrics storage in Redis
    """

    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}

        # Configuration options
        self.enabled = self.config.get("enabled", True)
        self.track_request_times = self.config.get("track_request_times", True)
        self.track_error_rates = self.config.get("track_error_rates", True)
        self.track_service_health = self.config.get("track_service_health", True)
        self.health_check_interval = self.config.get("health_check_interval", 300)  # 5 minutes
        self.metrics_retention_hours = self.config.get("metrics_retention_hours", 24)
        self.error_rate_threshold = self.config.get("error_rate_threshold", 0.1)  # 10%
        self.response_time_threshold = self.config.get("response_time_threshold", 5000)  # 5 seconds

        # In-memory metrics cache
        self.request_times = defaultdict(deque)
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
        self.last_health_check = None
        self.current_health_status = HealthStatus.HEALTHY

        # Initialize Redis service for metrics storage
        self.redis_service = None

        logger.info("Health monitoring middleware initialized", config=self.config)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect health metrics."""
        if not self.enabled:
            return await call_next(request)

        start_time = time.time()
        endpoint = self._get_endpoint_name(request)
        method = request.method

        # Initialize request tracking
        self.request_counts[f"{method}:{endpoint}"] += 1

        try:
            # Process the request
            response = await call_next(request)

            # Calculate request time
            request_time = int((time.time() - start_time) * 1000)

            # Track request times
            if self.track_request_times:
                await self._track_request_time(endpoint, method, request_time)

            # Check for slow responses
            if request_time > self.response_time_threshold:
                logger.warning(
                    "Slow response detected",
                    endpoint=endpoint,
                    method=method,
                    request_time_ms=request_time,
                    threshold_ms=self.response_time_threshold
                )

            # Add health headers to response
            response.headers["X-Health-Status"] = self.current_health_status.value
            response.headers["X-Request-Time-Ms"] = str(request_time)

            return response

        except Exception as e:
            # Track errors
            if self.track_error_rates:
                await self._track_error(endpoint, method, str(e))

            # Log the error
            logger.error(
                "Request failed",
                endpoint=endpoint,
                method=method,
                error=str(e),
                request_time_ms=int((time.time() - start_time) * 1000)
            )

            # Re-raise the exception
            raise

    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request."""
        # Try to get route pattern from request
        if hasattr(request, 'scope') and 'route' in request.scope:
            route = request.scope['route']
            if hasattr(route, 'path'):
                return route.path

        # Fallback to URL path
        return request.url.path

    async def _track_request_time(self, endpoint: str, method: str, request_time: int):
        """Track request time for an endpoint."""
        key = f"{method}:{endpoint}"

        # Store in memory (with limited history)
        self.request_times[key].append({
            'time': request_time,
            'timestamp': datetime.now(timezone.utc)
        })

        # Keep only last 1000 requests per endpoint
        if len(self.request_times[key]) > 1000:
            self.request_times[key].popleft()

        # Store in Redis for persistence
        try:
            if not self.redis_service:
                self.redis_service = get_redis_service()

            redis_key = f"health_metrics:request_times:{key}"
            await self.redis_service.set(
                redis_key,
                {
                    'time': request_time,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                ttl=self.metrics_retention_hours * 3600
            )

        except Exception as e:
            logger.warning(f"Failed to store request time metrics: {e}")

    async def _track_error(self, endpoint: str, method: str, error_message: str):
        """Track error for an endpoint."""
        key = f"{method}:{endpoint}"

        # Increment error count
        self.error_counts[key] += 1

        # Store in Redis
        try:
            if not self.redis_service:
                self.redis_service = get_redis_service()

            redis_key = f"health_metrics:errors:{key}"
            error_data = {
                'error_message': error_message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'count': self.error_counts[key]
            }

            await self.redis_service.set(
                redis_key,
                error_data,
                ttl=self.metrics_retention_hours * 3600
            )

            # Check if error rate threshold is exceeded
            await self._check_error_rates()

        except Exception as e:
            logger.warning(f"Failed to store error metrics: {e}")

    async def _check_error_rates(self):
        """Check if error rates exceed thresholds and update health status."""
        try:
            # Calculate recent error rates
            now = datetime.now(timezone.utc)
            recent_window = timedelta(minutes=5)  # Check last 5 minutes

            for endpoint_key in list(self.request_counts.keys()):
                total_requests = self.request_counts[endpoint_key]
                error_count = self.error_counts.get(endpoint_key, 0)

                if total_requests > 0:
                    error_rate = error_count / total_requests

                    if error_rate > self.error_rate_threshold:
                        logger.warning(
                            "High error rate detected",
                            endpoint=endpoint_key,
                            error_rate=error_rate,
                            error_count=error_count,
                            total_requests=total_requests,
                            threshold=self.error_rate_threshold
                        )

                        # Update health status to degraded
                        self.current_health_status = HealthStatus.DEGRADED
                        break

        except Exception as e:
            logger.warning(f"Failed to check error rates: {e}")

    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get current health metrics."""
        try:
            # Calculate metrics from in-memory data
            metrics = {
                "status": self.current_health_status.value,
                "endpoints": {},
                "summary": {
                    "total_requests": sum(self.request_counts.values()),
                    "total_errors": sum(self.error_counts.values()),
                    "active_endpoints": len(self.request_counts)
                }
            }

            # Per-endpoint metrics
            for endpoint_key in self.request_counts.keys():
                method, endpoint = endpoint_key.split(":", 1)
                request_times = list(self.request_times.get(endpoint_key, []))
                error_count = self.error_counts.get(endpoint_key, 0)
                request_count = self.request_counts[endpoint_key]

                # Calculate statistics
                if request_times:
                    avg_time = sum(rt['time'] for rt in request_times) / len(request_times)
                    max_time = max(rt['time'] for rt in request_times)
                    min_time = min(rt['time'] for rt in request_times)
                else:
                    avg_time = max_time = min_time = 0

                error_rate = error_count / max(request_count, 1)

                metrics["endpoints"][endpoint_key] = {
                    "method": method,
                    "endpoint": endpoint,
                    "request_count": request_count,
                    "error_count": error_count,
                    "error_rate": error_rate,
                    "avg_response_time_ms": int(avg_time),
                    "max_response_time_ms": max_time,
                    "min_response_time_ms": min_time,
                    "recent_requests": len(request_times)
                }

            # Add service health information
            if self.track_service_health:
                health_checker = get_health_checker()
                service_health = await health_checker.check_all_services()
                metrics["service_health"] = service_health.to_dict()

            return metrics

        except Exception as e:
            logger.error(f"Failed to get health metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def reset_metrics(self):
        """Reset all health metrics."""
        self.request_times.clear()
        self.error_counts.clear()
        self.request_counts.clear()
        self.current_health_status = HealthStatus.HEALTHY

        # Clear Redis metrics
        try:
            if self.redis_service:
                # Get all health metrics keys
                keys_pattern = "health_metrics:*"
                # Note: This would need a Redis client that supports pattern matching
                # For now, we'll just log the reset
                logger.info("Health metrics reset")
        except Exception as e:
            logger.warning(f"Failed to clear Redis metrics: {e}")

    def set_health_status(self, status: HealthStatus, reason: Optional[str] = None):
        """Manually set health status."""
        old_status = self.current_health_status
        self.current_health_status = status

        if old_status != status:
            logger.info(
                "Health status changed",
                old_status=old_status.value,
                new_status=status.value,
                reason=reason
            )

    async def get_endpoint_health(self, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        """Get health information for a specific endpoint."""
        key = f"{method}:{endpoint}"

        request_times = list(self.request_times.get(key, []))
        error_count = self.error_counts.get(key, 0)
        request_count = self.request_counts.get(key, 0)

        if request_times:
            avg_time = sum(rt['time'] for rt in request_times) / len(request_times)
            recent_times = [rt['time'] for rt in request_times[-10:]]  # Last 10 requests
        else:
            avg_time = 0
            recent_times = []

        error_rate = error_count / max(request_count, 1)

        # Determine endpoint health
        if error_rate > self.error_rate_threshold:
            status = HealthStatus.UNHEALTHY
        elif avg_time > self.response_time_threshold:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return {
            "endpoint": endpoint,
            "method": method,
            "status": status.value,
            "request_count": request_count,
            "error_count": error_count,
            "error_rate": error_rate,
            "avg_response_time_ms": int(avg_time),
            "recent_response_times": recent_times,
            "health_indicators": {
                "error_rate_threshold_met": error_rate > self.error_rate_threshold,
                "response_time_threshold_met": avg_time > self.response_time_threshold,
                "has_recent_requests": len(recent_times) > 0
            }
        }


# Global middleware instance
_health_middleware: Optional[HealthMonitoringMiddleware] = None


def get_health_monitoring_middleware() -> Optional[HealthMonitoringMiddleware]:
    """Get the global health monitoring middleware instance."""
    return _health_middleware


def create_health_monitoring_middleware(
    app: ASGIApp,
    config: Optional[Dict[str, Any]] = None
) -> HealthMonitoringMiddleware:
    """Create and configure health monitoring middleware."""
    global _health_middleware
    _health_middleware = HealthMonitoringMiddleware(app, config)
    return _health_middleware