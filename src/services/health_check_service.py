"""
Health check system for monitoring all foundational services.

This module provides comprehensive health monitoring for database, Redis,
authentication, rate limiting, and other system components.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum

from src.utils.logging import get_logger
from src.services.database_service import get_database_service, DatabaseConfig
from src.services.redis_service import get_redis_service
from src.services.auth_service import get_auth_service
from src.services.phone_validation_service import get_phone_validation_service
from src.services.webhook_signature_service import get_webhook_signature_service
from src.services.audit_service import log_audit_event
from src.middleware.rate_limiting import get_rate_limiter

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    service_name: str
    status: HealthStatus
    message: str
    response_time_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        result['status'] = self.status.value
        return result


@dataclass
class SystemHealthReport:
    """Overall system health report."""
    status: HealthStatus
    total_checks: int
    healthy_checks: int
    degraded_checks: int
    unhealthy_checks: int
    unknown_checks: int
    total_response_time_ms: int
    checks: List[HealthCheckResult]
    timestamp: datetime
    version: str = "2.0.0"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'status': self.status.value,
            'total_checks': self.total_checks,
            'healthy_checks': self.healthy_checks,
            'degraded_checks': self.degraded_checks,
            'unhealthy_checks': self.unhealthy_checks,
            'unknown_checks': self.unknown_checks,
            'total_response_time_ms': self.total_response_time_ms,
            'average_response_time_ms': self.total_response_time_ms // max(self.total_checks, 1),
            'checks': [check.to_dict() for check in self.checks],
            'timestamp': self.timestamp.isoformat(),
            'version': self.version
        }


class HealthChecker:
    """Health check service for monitoring system components."""

    def __init__(self):
        self.checks = {}
        self._setup_default_checks()

    def _setup_default_checks(self):
        """Setup default health checks."""
        self.register_check("database", self._check_database_health)
        self.register_check("redis", self._check_redis_health)
        self.register_check("auth_service", self._check_auth_service_health)
        self.register_check("phone_validation", self._check_phone_validation_health)
        self.register_check("webhook_signature", self._check_webhook_signature_health)
        self.register_check("rate_limiting", self._check_rate_limiting_health)

    def register_check(self, name: str, check_func):
        """Register a health check function."""
        self.checks[name] = check_func

    async def check_service_health(self, service_name: str) -> HealthCheckResult:
        """Check health of a specific service."""
        if service_name not in self.checks:
            return HealthCheckResult(
                service_name=service_name,
                status=HealthStatus.UNKNOWN,
                message=f"Unknown service: {service_name}"
            )

        start_time = time.time()
        try:
            result = await self.checks[service_name]()
            response_time = int((time.time() - start_time) * 1000)
            result.response_time_ms = response_time
            return result
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            logger.error(f"Health check failed for {service_name}: {str(e)}")
            return HealthCheckResult(
                service_name=service_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )

    async def check_all_services(self) -> SystemHealthReport:
        """Check health of all registered services."""
        checks = []
        total_response_time = 0

        # Run all checks concurrently for better performance
        tasks = [self.check_service_health(service_name) for service_name in self.checks.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self.checks.keys())[i]
                checks.append(HealthCheckResult(
                    service_name=service_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check execution failed: {str(result)}",
                    error=str(result)
                ))
            else:
                checks.append(result)
                if result.response_time_ms:
                    total_response_time += result.response_time_ms

        # Calculate overall status
        healthy_count = sum(1 for check in checks if check.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for check in checks if check.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for check in checks if check.status == HealthStatus.UNHEALTHY)
        unknown_count = sum(1 for check in checks if check.status == HealthStatus.UNKNOWN)
        total_count = len(checks)

        # Determine overall system status
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        elif unknown_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return SystemHealthReport(
            status=overall_status,
            total_checks=total_count,
            healthy_checks=healthy_count,
            degraded_checks=degraded_count,
            unhealthy_checks=unhealthy_count,
            unknown_checks=unknown_count,
            total_response_time_ms=total_response_time,
            checks=checks,
            timestamp=datetime.now(timezone.utc)
        )

    async def _check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and basic operations."""
        start_time = time.time()
        try:
            db_service = get_database_service()

            # Test basic connectivity
            is_connected = db_service.is_connected()
            if not is_connected:
                return HealthCheckResult(
                    service_name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database not connected"
                )

            # Test basic query
            result = db_service.execute_query("SELECT 1 as health_check")
            if not result or len(result) == 0:
                return HealthCheckResult(
                    service_name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database query failed"
                )

            # Test connection pool
            pool_stats = db_service.get_connection_pool_stats()

            return HealthCheckResult(
                service_name="database",
                status=HealthStatus.HEALTHY,
                message="Database is healthy",
                details={
                    "connection_type": "connection_pool",
                    "pool_stats": pool_stats,
                    "test_query_result": result[0] if result else None
                }
            )

        except Exception as e:
            return HealthCheckResult(
                service_name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
                error=str(e)
            )

    async def _check_redis_health(self) -> HealthCheckResult:
        """Check Redis connectivity and basic operations."""
        try:
            redis_service = get_redis_service()

            # Test basic operations
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": time.time()}

            # Test set operation
            set_result = redis_service.set_sync(test_key, test_value, ttl=60)
            if not set_result:
                return HealthCheckResult(
                    service_name="redis",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis SET operation failed"
                )

            # Test get operation
            get_result = redis_service.get_sync(test_key)
            if get_result is None:
                return HealthCheckResult(
                    service_name="redis",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis GET operation failed"
                )

            # Clean up
            redis_service.delete_sync(test_key)

            # Get Redis info
            redis_info = redis_service.get_info()

            return HealthCheckResult(
                service_name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis is healthy",
                details={
                    "redis_info": {
                        "version": redis_info.get("redis_version"),
                        "used_memory": redis_info.get("used_memory_human"),
                        "connected_clients": redis_info.get("connected_clients"),
                        "uptime_in_seconds": redis_info.get("uptime_in_seconds")
                    },
                    "test_operations": {
                        "set": True,
                        "get": True,
                        "delete": True
                    }
                }
            )

        except Exception as e:
            return HealthCheckResult(
                service_name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis health check failed: {str(e)}",
                error=str(e)
            )

    async def _check_auth_service_health(self) -> HealthCheckResult:
        """Check authentication service health."""
        try:
            auth_service = get_auth_service()

            # Test JWT token generation and validation
            test_user_id = "00000000-0000-0000-0000-000000000000"
            test_claims = {"health_check": True}

            # Generate test token
            token_info = auth_service.generate_access_token(test_user_id, test_claims)
            if not token_info or not token_info.token:
                return HealthCheckResult(
                    service_name="auth_service",
                    status=HealthStatus.UNHEALTHY,
                    message="JWT token generation failed"
                )

            # Validate test token
            payload = auth_service.verify_access_token(token_info.token)
            if not payload:
                return HealthCheckResult(
                    service_name="auth_service",
                    status=HealthStatus.UNHEALTHY,
                    message="JWT token validation failed"
                )

            # Test token blacklisting
            blacklist_result = auth_service.blacklist_token(token_info.jti)

            return HealthCheckResult(
                service_name="auth_service",
                status=HealthStatus.HEALTHY,
                message="Authentication service is healthy",
                details={
                    "jwt_operations": {
                        "token_generation": True,
                        "token_validation": True,
                        "token_blacklisting": blacklist_result
                    },
                    "token_info": {
                        "expires_at": token_info.expires_at.isoformat() if token_info.expires_at else None,
                        "jti": token_info.jti
                    }
                }
            )

        except Exception as e:
            return HealthCheckResult(
                service_name="auth_service",
                status=HealthStatus.UNHEALTHY,
                message=f"Auth service health check failed: {str(e)}",
                error=str(e)
            )

    async def _check_phone_validation_health(self) -> HealthCheckResult:
        """Check phone validation service health."""
        try:
            phone_service = get_phone_validation_service()

            # Test with known valid Senegal numbers
            test_numbers = [
                "+221771234567",  # Orange
                "+221781234567",  # Free
                "+221751234567",  # Expresso
            ]

            validation_results = []
            for number in test_numbers:
                try:
                    result = phone_service.validate_phone_number(number)
                    validation_results.append({
                        "number": number,
                        "valid": result.is_valid,
                        "carrier": result.carrier,
                        "type": result.phone_type
                    })
                except Exception:
                    validation_results.append({
                        "number": number,
                        "valid": False,
                        "error": "Validation failed"
                    })

            # Check if validations are working
            successful_validations = sum(1 for r in validation_results if r.get("valid", False))
            total_validations = len(validation_results)

            if successful_validations == 0:
                return HealthCheckResult(
                    service_name="phone_validation",
                    status=HealthStatus.UNHEALTHY,
                    message="Phone validation not working for any test numbers"
                )
            elif successful_validations < total_validations:
                return HealthCheckResult(
                    service_name="phone_validation",
                    status=HealthStatus.DEGRADED,
                    message=f"Phone validation working for {successful_validations}/{total_validations} test numbers",
                    details={"validation_results": validation_results}
                )

            return HealthCheckResult(
                service_name="phone_validation",
                status=HealthStatus.HEALTHY,
                message="Phone validation service is healthy",
                details={
                    "test_validations": validation_results,
                    "success_rate": f"{successful_validations}/{total_validations}"
                }
            )

        except Exception as e:
            return HealthCheckResult(
                service_name="phone_validation",
                status=HealthStatus.UNHEALTHY,
                message=f"Phone validation health check failed: {str(e)}",
                error=str(e)
            )

    async def _check_webhook_signature_health(self) -> HealthCheckResult:
        """Check webhook signature service health."""
        try:
            webhook_service = get_webhook_signature_service()

            # Test signature generation and verification
            test_payload = '{"test": "health_check", "timestamp": ' + str(int(time.time())) + '}'
            test_platform = "telegram"

            # Check if configuration exists
            config = webhook_service.get_configuration(test_platform)
            if not config:
                return HealthCheckResult(
                    service_name="webhook_signature",
                    status=HealthStatus.DEGRADED,
                    message=f"No webhook configuration for platform: {test_platform}",
                    details={"available_platforms": list(webhook_service.configurations.keys())}
                )

            # Generate test signature
            try:
                signature = webhook_service.generate_signature(test_platform, test_payload)
                if not signature:
                    return HealthCheckResult(
                        service_name="webhook_signature",
                        status=HealthStatus.UNHEALTHY,
                        message="Signature generation failed"
                    )
            except Exception as e:
                return HealthCheckResult(
                    service_name="webhook_signature",
                    status=HealthStatus.DEGRADED,
                    message=f"Signature generation failed (missing secret?): {str(e)}"
                )

            # Test signature verification
            test_headers = {config.platform_settings['header_name']: signature}
            verification_result = webhook_service.verify_signature(test_platform, test_payload, test_headers)

            if not verification_result.is_valid:
                return HealthCheckResult(
                    service_name="webhook_signature",
                    status=HealthStatus.UNHEALTHY,
                    message="Signature verification failed",
                    details={
                        "provided_signature": verification_result.provided_signature,
                        "computed_signature": verification_result.computed_signature,
                        "errors": verification_result.errors
                    }
                )

            # Get service statistics
            stats = webhook_service.get_verification_statistics()

            return HealthCheckResult(
                service_name="webhook_signature",
                status=HealthStatus.HEALTHY,
                message="Webhook signature service is healthy",
                details={
                    "signature_operations": {
                        "generation": True,
                        "verification": verification_result.is_valid
                    },
                    "service_stats": stats
                }
            )

        except Exception as e:
            return HealthCheckResult(
                service_name="webhook_signature",
                status=HealthStatus.UNHEALTHY,
                message=f"Webhook signature health check failed: {str(e)}",
                error=str(e)
            )

    async def _check_rate_limiting_health(self) -> HealthCheckResult:
        """Check rate limiting service health."""
        try:
            rate_limiter = get_rate_limiter()

            # Test rate limiting operations
            test_identifier = "health_check_test"
            test_config = {
                "requests_per_window": 5,
                "window_seconds": 60
            }

            # First request should be allowed
            result1 = rate_limiter.check_rate_limit(test_identifier, test_config)
            if not result1.allowed:
                return HealthCheckResult(
                    service_name="rate_limiting",
                    status=HealthStatus.UNHEALTHY,
                    message="Rate limiting blocked first request"
                )

            # Test multiple requests to check rate limiting logic
            results = []
            for i in range(3):
                result = rate_limiter.check_rate_limit(f"{test_identifier}_{i}", test_config)
                results.append(result.allowed)

            # All requests should be allowed (under limit)
            if not all(results):
                return HealthCheckResult(
                    service_name="rate_limiting",
                    status=HealthStatus.DEGRADED,
                    message="Rate limiting blocking requests unexpectedly",
                    details={"request_results": results}
                )

            # Check Redis connectivity for rate limiting
            redis_info = rate_limiter.get_redis_info()

            return HealthCheckResult(
                service_name="rate_limiting",
                status=HealthStatus.HEALTHY,
                message="Rate limiting service is healthy",
                details={
                    "test_results": {
                        "first_request_allowed": result1.allowed,
                        "multiple_requests_allowed": all(results)
                    },
                    "redis_info": redis_info
                }
            )

        except Exception as e:
            return HealthCheckResult(
                service_name="rate_limiting",
                status=HealthStatus.UNHEALTHY,
                message=f"Rate limiting health check failed: {str(e)}",
                error=str(e)
            )


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


async def check_service_health(service_name: str) -> HealthCheckResult:
    """Check health of a specific service using global checker."""
    checker = get_health_checker()
    return await checker.check_service_health(service_name)


async def check_all_services_health() -> SystemHealthReport:
    """Check health of all services using global checker."""
    checker = get_health_checker()
    return await checker.check_all_services()


async def log_health_check_event(report: SystemHealthReport):
    """Log health check event to audit service."""
    event_data = {
        "health_report": report.to_dict(),
        "summary": {
            "total_checks": report.total_checks,
            "healthy_checks": report.healthy_checks,
            "degraded_checks": report.degraded_checks,
            "unhealthy_checks": report.unhealthy_checks,
            "overall_status": report.status.value
        }
    }

    await log_audit_event(
        event_type="system_health_check",
        user_id="system",
        event_data=event_data,
        ip_address="127.0.0.1",
        user_agent="HealthCheckService/1.0"
    )