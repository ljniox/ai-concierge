"""
Health check utilities and helper functions.

This module provides utility functions for health monitoring,
including status calculations, health thresholds, and metric calculations.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum

from src.services.health_check_service import HealthStatus, HealthCheckResult


class HealthThreshold(Enum):
    """Health threshold levels for different metrics."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class HealthThresholds:
    """Health thresholds for various metrics."""
    # Response time thresholds (in milliseconds)
    response_time_excellent: int = 100
    response_time_good: int = 500
    response_time_fair: int = 1000
    response_time_poor: int = 5000

    # Error rate thresholds (as percentage)
    error_rate_excellent: float = 0.01  # 0.01%
    error_rate_good: float = 0.1       # 0.1%
    error_rate_fair: float = 1.0       # 1%
    error_rate_poor: float = 5.0       # 5%

    # Success rate thresholds (as percentage)
    success_rate_excellent: float = 99.9
    success_rate_good: float = 99.0
    success_rate_fair: float = 95.0
    success_rate_poor: float = 90.0

    # Availability thresholds (as percentage)
    availability_excellent: float = 99.9
    availability_good: float = 99.0
    availability_fair: float = 95.0
    availability_poor: float = 90.0


@dataclass
class HealthMetrics:
    """Health metrics for a service or endpoint."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: int = 0
    min_response_time: int = 0
    max_response_time: int = 0
    last_request_time: Optional[datetime] = None
    uptime_start: datetime = None

    def __post_init__(self):
        if self.uptime_start is None:
            self.uptime_start = datetime.now(timezone.utc)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

    @property
    def uptime_seconds(self) -> int:
        """Calculate uptime in seconds."""
        return int((datetime.now(timezone.utc) - self.uptime_start).total_seconds())

    @property
    def availability(self) -> float:
        """Calculate availability as percentage (simplified)."""
        # This is a simplified calculation
        # In production, you'd want to track actual downtime periods
        uptime_percentage = (self.successful_requests / max(self.total_requests, 1)) * 100
        return min(uptime_percentage, 100.0)

    def add_request(self, response_time: int, success: bool):
        """Add a request to the metrics."""
        self.total_requests += 1
        self.total_response_time += response_time
        self.last_request_time = datetime.now(timezone.utc)

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        if self.min_response_time == 0:
            self.min_response_time = response_time
        else:
            self.min_response_time = min(self.min_response_time, response_time)

        self.max_response_time = max(self.max_response_time, response_time)


class HealthCalculator:
    """Calculator for health status and metrics."""

    def __init__(self, thresholds: Optional[HealthThresholds] = None):
        self.thresholds = thresholds or HealthThresholds()

    def calculate_service_health(
        self,
        metrics: HealthMetrics,
        additional_checks: Optional[Dict[str, bool]] = None
    ) -> Tuple[HealthStatus, Dict[str, Any]]:
        """
        Calculate overall health status for a service.

        Returns:
            Tuple of (health_status, detailed_breakdown)
        """
        breakdown = {
            "response_time_health": self._calculate_response_time_health(metrics.average_response_time),
            "success_rate_health": self._calculate_success_rate_health(metrics.success_rate),
            "availability_health": self._calculate_availability_health(metrics.availability),
            "request_volume_health": self._calculate_request_volume_health(metrics.total_requests),
            "additional_checks": additional_checks or {}
        }

        # Determine overall health
        health_scores = [
            breakdown["response_time_health"]["score"],
            breakdown["success_rate_health"]["score"],
            breakdown["availability_health"]["score"],
            breakdown["request_volume_health"]["score"]
        ]

        # Add additional check scores
        for check_name, check_result in breakdown["additional_checks"].items():
            health_scores.append(5 if check_result else 1)

        # Calculate overall score (1-5 scale)
        overall_score = sum(health_scores) / len(health_scores)

        # Map score to health status
        if overall_score >= 4.5:
            health_status = HealthStatus.HEALTHY
        elif overall_score >= 3.0:
            health_status = HealthStatus.DEGRADED
        elif overall_score >= 1.5:
            health_status = HealthStatus.DEGRADED
        else:
            health_status = HealthStatus.UNHEALTHY

        return health_status, breakdown

    def _calculate_response_time_health(self, avg_response_time: float) -> Dict[str, Any]:
        """Calculate response time health score."""
        thresholds = self.thresholds

        if avg_response_time <= thresholds.response_time_excellent:
            level = HealthThreshold.EXCELLENT
            score = 5
        elif avg_response_time <= thresholds.response_time_good:
            level = HealthThreshold.GOOD
            score = 4
        elif avg_response_time <= thresholds.response_time_fair:
            level = HealthThreshold.FAIR
            score = 3
        elif avg_response_time <= thresholds.response_time_poor:
            level = HealthThreshold.POOR
            score = 2
        else:
            level = HealthThreshold.CRITICAL
            score = 1

        return {
            "level": level.value,
            "score": score,
            "value": avg_response_time,
            "thresholds": {
                "excellent": thresholds.response_time_excellent,
                "good": thresholds.response_time_good,
                "fair": thresholds.response_time_fair,
                "poor": thresholds.response_time_poor
            }
        }

    def _calculate_success_rate_health(self, success_rate: float) -> Dict[str, Any]:
        """Calculate success rate health score."""
        thresholds = self.thresholds

        if success_rate >= thresholds.success_rate_excellent:
            level = HealthThreshold.EXCELLENT
            score = 5
        elif success_rate >= thresholds.success_rate_good:
            level = HealthThreshold.GOOD
            score = 4
        elif success_rate >= thresholds.success_rate_fair:
            level = HealthThreshold.FAIR
            score = 3
        elif success_rate >= thresholds.success_rate_poor:
            level = HealthThreshold.POOR
            score = 2
        else:
            level = HealthThreshold.CRITICAL
            score = 1

        return {
            "level": level.value,
            "score": score,
            "value": success_rate,
            "thresholds": {
                "excellent": thresholds.success_rate_excellent,
                "good": thresholds.success_rate_good,
                "fair": thresholds.success_rate_fair,
                "poor": thresholds.success_rate_poor
            }
        }

    def _calculate_availability_health(self, availability: float) -> Dict[str, Any]:
        """Calculate availability health score."""
        thresholds = self.thresholds

        if availability >= thresholds.availability_excellent:
            level = HealthThreshold.EXCELLENT
            score = 5
        elif availability >= thresholds.availability_good:
            level = HealthThreshold.GOOD
            score = 4
        elif availability >= thresholds.availability_fair:
            level = HealthThreshold.FAIR
            score = 3
        elif availability >= thresholds.availability_poor:
            level = HealthThreshold.POOR
            score = 2
        else:
            level = HealthThreshold.CRITICAL
            score = 1

        return {
            "level": level.value,
            "score": score,
            "value": availability,
            "thresholds": {
                "excellent": thresholds.availability_excellent,
                "good": thresholds.availability_good,
                "fair": thresholds.availability_fair,
                "poor": thresholds.availability_poor
            }
        }

    def _calculate_request_volume_health(self, total_requests: int) -> Dict[str, Any]:
        """Calculate request volume health score."""
        # This is a simplified check - in production you'd want more sophisticated logic
        if total_requests > 0:
            level = HealthThreshold.GOOD
            score = 4
        else:
            level = HealthThreshold.CRITICAL
            score = 1

        return {
            "level": level.value,
            "score": score,
            "value": total_requests,
            "has_requests": total_requests > 0
        }

    def aggregate_health_results(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Aggregate multiple health check results into overall status."""
        if not results:
            return HealthStatus.UNKNOWN

        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }

        for result in results:
            status_counts[result.status] += 1

        total = len(results)

        # If any services are unhealthy, overall status is unhealthy
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY

        # If any services are degraded, overall status is degraded
        if status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED

        # If all services are healthy, overall status is healthy
        if status_counts[HealthStatus.HEALTHY] == total:
            return HealthStatus.HEALTHY

        # Default to unknown
        return HealthStatus.UNKNOWN

    def calculate_sla_metrics(
        self,
        metrics: HealthMetrics,
        sla_threshold: float = 99.0
    ) -> Dict[str, Any]:
        """Calculate SLA (Service Level Agreement) metrics."""
        uptime_percentage = metrics.availability
        sla_met = uptime_percentage >= sla_threshold

        # Calculate SLA breach cost (simplified)
        if not sla_met:
            breach_percentage = sla_threshold - uptime_percentage
            # This is a placeholder calculation
            breach_cost = breach_percentage * 100  # Simplified cost calculation
        else:
            breach_cost = 0

        return {
            "sla_threshold": sla_threshold,
            "current_availability": uptime_percentage,
            "sla_met": sla_met,
            "breach_percentage": max(0, sla_threshold - uptime_percentage),
            "estimated_breach_cost": breach_cost,
            "uptime_seconds": metrics.uptime_seconds,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests
        }


class HealthAlertManager:
    """Manager for health alerts and notifications."""

    def __init__(self):
        self.alert_rules = []
        self.active_alerts = {}

    def add_alert_rule(
        self,
        name: str,
        condition: str,
        threshold: float,
        severity: str = "warning"
    ):
        """Add an alert rule."""
        rule = {
            "name": name,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "created_at": datetime.now(timezone.utc)
        }
        self.alert_rules.append(rule)

    def check_alerts(self, metrics: HealthMetrics, breakdown: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check all alert rules against current metrics."""
        alerts = []

        for rule in self.alert_rules:
            alert_triggered = self._evaluate_rule(rule, metrics, breakdown)

            if alert_triggered:
                alert = {
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "condition": rule["condition"],
                    "threshold": rule["threshold"],
                    "current_value": alert_triggered["current_value"],
                    "message": alert_triggered["message"],
                    "timestamp": datetime.now(timezone.utc)
                }

                alerts.append(alert)
                self.active_alerts[rule["name"]] = alert
            else:
                # Clear alert if it was previously active
                if rule["name"] in self.active_alerts:
                    del self.active_alerts[rule["name"]]

        return alerts

    def _evaluate_rule(
        self,
        rule: Dict[str, Any],
        metrics: HealthMetrics,
        breakdown: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a single alert rule."""
        condition = rule["condition"]
        threshold = rule["threshold"]

        if condition == "error_rate_high":
            current_value = metrics.error_rate
            if current_value > threshold:
                return {
                    "current_value": current_value,
                    "message": f"Error rate ({current_value:.2f}%) exceeds threshold ({threshold}%)"
                }

        elif condition == "response_time_high":
            current_value = metrics.average_response_time
            if current_value > threshold:
                return {
                    "current_value": current_value,
                    "message": f"Average response time ({current_value:.0f}ms) exceeds threshold ({threshold}ms)"
                }

        elif condition == "success_rate_low":
            current_value = metrics.success_rate
            if current_value < threshold:
                return {
                    "current_value": current_value,
                    "message": f"Success rate ({current_value:.2f}%) below threshold ({threshold}%)"
                }

        elif condition == "availability_low":
            current_value = metrics.availability
            if current_value < threshold:
                return {
                    "current_value": current_value,
                    "message": f"Availability ({current_value:.2f}%) below threshold ({threshold}%)"
                }

        return None

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently active alerts."""
        return list(self.active_alerts.values())

    def clear_alert(self, rule_name: str):
        """Clear a specific alert."""
        if rule_name in self.active_alerts:
            del self.active_alerts[rule_name]

    def clear_all_alerts(self):
        """Clear all active alerts."""
        self.active_alerts.clear()


# Global instances
_health_calculator: Optional[HealthCalculator] = None
_alert_manager: Optional[HealthAlertManager] = None


def get_health_calculator() -> HealthCalculator:
    """Get the global health calculator instance."""
    global _health_calculator
    if _health_calculator is None:
        _health_calculator = HealthCalculator()
    return _health_calculator


def get_alert_manager() -> HealthAlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = HealthAlertManager()
    return _alert_manager


def create_health_metrics() -> HealthMetrics:
    """Create a new HealthMetrics instance."""
    return HealthMetrics()