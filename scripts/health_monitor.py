#!/usr/bin/env python3
"""
Health monitoring CLI script for managing and monitoring system health.

This script provides command-line tools for:
- Checking system health
- Monitoring specific services
- Viewing health metrics
- Managing health alerts
- Exporting health reports
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import aiohttp

from src.services.health_check_service import (
    get_health_checker,
    check_all_services_health,
    check_service_health,
    HealthStatus
)
from src.utils.health_utils import (
    get_health_calculator,
    get_alert_manager,
    create_health_metrics
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HealthMonitorCLI:
    """Command-line interface for health monitoring."""

    def __init__(self):
        self.health_checker = get_health_checker()
        self.health_calculator = get_health_calculator()
        self.alert_manager = get_alert_manager()

    async def check_all_health(self, output_format: str = "table") -> bool:
        """Check health of all services."""
        print("🔍 Checking health of all services...")
        print("-" * 60)

        try:
            report = await check_all_services_health()

            if output_format == "json":
                print(json.dumps(report.to_dict(), indent=2))
                return report.status == HealthStatus.HEALTHY

            # Display in table format
            print(f"Overall Status: {self._format_status(report.status)}")
            print(f"Total Checks: {report.total_checks}")
            print(f"Response Time: {report.total_response_time_ms}ms")
            print(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print()

            # Service details
            print("Service Details:")
            for check in report.checks:
                status_icon = self._get_status_icon(check.status)
                response_time = f"{check.response_time_ms}ms" if check.response_time_ms else "N/A"
                print(f"  {status_icon} {check.service_name:<20} {check.status:<12} {response_time:<8} {check.message}")

            print()
            return report.status == HealthStatus.HEALTHY

        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

    async def check_service_health(self, service_name: str, output_format: str = "table") -> bool:
        """Check health of a specific service."""
        print(f"🔍 Checking health of service: {service_name}")
        print("-" * 50)

        try:
            result = await check_service_health(service_name)

            if output_format == "json":
                print(json.dumps(result.to_dict(), indent=2))
                return result.status == HealthStatus.HEALTHY

            # Display in table format
            status_icon = self._get_status_icon(result.status)
            response_time = f"{result.response_time_ms}ms" if result.response_time_ms else "N/A"

            print(f"Service: {result.service_name}")
            print(f"Status: {status_icon} {result.status}")
            print(f"Response Time: {response_time}")
            print(f"Message: {result.message}")
            print(f"Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            if result.details:
                print("Details:")
                for key, value in result.details.items():
                    print(f"  {key}: {value}")

            if result.error:
                print(f"Error: {result.error}")

            print()
            return result.status == HealthStatus.HEALTHY

        except Exception as e:
            print(f"❌ Service health check failed: {e}")
            return False

    async def list_services(self):
        """List all available health check services."""
        print("📋 Available Health Check Services")
        print("-" * 40)

        services = list(self.health_checker.checks.keys())
        services.sort()

        for i, service in enumerate(services, 1):
            print(f"  {i}. {service}")

        print(f"\nTotal: {len(services)} services")
        print()

    async def monitor_continuous(
        self,
        interval: int = 30,
        service: Optional[str] = None,
        alerts_only: bool = False
    ):
        """Continuously monitor health at specified intervals."""
        print(f"🔄 Starting continuous health monitoring")
        print(f"   Interval: {interval} seconds")
        if service:
            print(f"   Service: {service}")
        if alerts_only:
            print(f"   Mode: Alerts only")
        print(f"   Press Ctrl+C to stop")
        print("-" * 60)

        last_status = None

        try:
            while True:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if service:
                    result = await check_service_health(service)
                    status = result.status
                    message = f"{service}: {result.message}"
                else:
                    report = await check_all_services_health()
                    status = report.status
                    message = f"Overall: {report.healthy_checks}/{report.total_checks} healthy"

                # Only output if status changed or if not in alerts-only mode
                if not alerts_only or status != last_status:
                    status_icon = self._get_status_icon(status)
                    print(f"[{timestamp}] {status_icon} {message}")

                    if status != last_status and last_status is not None:
                        old_icon = self._get_status_icon(last_status)
                        print(f"    Status changed: {old_icon} {last_status} → {status_icon} {status}")

                    last_status = status

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")

    async def show_metrics(self, service: Optional[str] = None):
        """Show detailed health metrics."""
        print("📊 Health Metrics")
        print("-" * 30)

        try:
            if service:
                # Show metrics for specific service
                result = await check_service_health(service)
                print(f"Service: {service}")
                print(f"Status: {self._format_status(result.status)}")
                print(f"Response Time: {result.response_time_ms}ms")
                print(f"Message: {result.message}")

                if result.details:
                    print("\nDetails:")
                    for key, value in result.details.items():
                        print(f"  {key}: {value}")
            else:
                # Show overall metrics
                report = await check_all_services_health()

                print(f"Overall Status: {self._format_status(report.status)}")
                print(f"Total Services: {report.total_checks}")
                print(f"Healthy: {report.healthy_checks}")
                print(f"Degraded: {report.degraded_checks}")
                print(f"Unhealthy: {report.unhealthy_checks}")
                print(f"Unknown: {report.unknown_checks}")
                print(f"Total Response Time: {report.total_response_time_ms}ms")
                print(f"Average Response Time: {report.total_response_time_ms // max(report.total_checks, 1)}ms")

                print("\nService Breakdown:")
                for check in report.checks:
                    status_icon = self._get_status_icon(check.status)
                    response_time = f"{check.response_time_ms}ms" if check.response_time_ms else "N/A"
                    print(f"  {status_icon} {check.service_name:<20} {check.status:<12} {response_time}")

        except Exception as e:
            print(f"❌ Failed to get metrics: {e}")

        print()

    async def setup_alerts(self):
        """Setup default health alerts."""
        print("🚨 Setting up default health alerts...")
        print("-" * 40)

        # Add default alert rules
        self.alert_manager.add_alert_rule(
            name="high_error_rate",
            condition="error_rate_high",
            threshold=5.0,
            severity="critical"
        )

        self.alert_manager.add_alert_rule(
            name="slow_response",
            condition="response_time_high",
            threshold=5000,
            severity="warning"
        )

        self.alert_manager.add_alert_rule(
            name="low_success_rate",
            condition="success_rate_low",
            threshold=95.0,
            severity="warning"
        )

        print("✅ Default alerts configured:")
        print("  • High error rate (>5%) - Critical")
        print("  • Slow response time (>5000ms) - Warning")
        print("  • Low success rate (<95%) - Warning")
        print()

    async def show_alerts(self):
        """Show active health alerts."""
        print("🚨 Active Health Alerts")
        print("-" * 30)

        alerts = self.alert_manager.get_active_alerts()

        if not alerts:
            print("✅ No active alerts")
            print()
            return

        for alert in alerts:
            severity_icon = "🔴" if alert["severity"] == "critical" else "🟡"
            print(f"{severity_icon} {alert['rule_name']}")
            print(f"   Severity: {alert['severity']}")
            print(f"   Message: {alert['message']}")
            print(f"   Time: {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print()

    async def export_report(self, filename: Optional[str] = None, format: str = "json"):
        """Export health report to file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"health_report_{timestamp}.{format}"

        print(f"📄 Exporting health report to {filename}...")
        print("-" * 50)

        try:
            report = await check_all_services_health()

            if format == "json":
                with open(filename, 'w') as f:
                    json.dump(report.to_dict(), f, indent=2, default=str)
            elif format == "markdown":
                self._export_markdown_report(report, filename)
            else:
                print(f"❌ Unsupported format: {format}")
                return

            print(f"✅ Report exported to {filename}")
            print()

        except Exception as e:
            print(f"❌ Failed to export report: {e}")

    def _export_markdown_report(self, report, filename: str):
        """Export report as Markdown."""
        with open(filename, 'w') as f:
            f.write("# System Health Report\n\n")
            f.write(f"**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"**Status:** {self._format_status(report.status)}\n")
            f.write(f"**Version:** {report.version}\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total Services:** {report.total_checks}\n")
            f.write(f"- **Healthy:** {report.healthy_checks}\n")
            f.write(f"- **Degraded:** {report.degraded_checks}\n")
            f.write(f"- **Unhealthy:** {report.unhealthy_checks}\n")
            f.write(f"- **Unknown:** {report.unknown_checks}\n")
            f.write(f"- **Total Response Time:** {report.total_response_time_ms}ms\n\n")

            f.write("## Service Details\n\n")
            f.write("| Service | Status | Response Time | Message |\n")
            f.write("|---------|--------|---------------|---------|\n")

            for check in report.checks:
                status_icon = self._get_status_icon(check.status)
                response_time = f"{check.response_time_ms}ms" if check.response_time_ms else "N/A"
                f.write(f"| {check.service_name} | {status_icon} {check.status} | {response_time} | {check.message} |\n")

    def _format_status(self, status: HealthStatus) -> str:
        """Format health status with emoji."""
        status_map = {
            HealthStatus.HEALTHY: "✅ Healthy",
            HealthStatus.DEGRADED: "⚠️  Degraded",
            HealthStatus.UNHEALTHY: "❌ Unhealthy",
            HealthStatus.UNKNOWN: "❓ Unknown"
        }
        return status_map.get(status, str(status))

    def _get_status_icon(self, status: HealthStatus) -> str:
        """Get status icon."""
        icon_map = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓"
        }
        return icon_map.get(status, "❓")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Health Monitoring CLI for Automatic Account Creation System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Check all health
    subparsers.add_parser("check", help="Check health of all services")

    # Check specific service
    service_parser = subparsers.add_parser("service", help="Check health of specific service")
    service_parser.add_argument("name", help="Service name to check")

    # List services
    subparsers.add_parser("list", help="List all available services")

    # Monitor continuously
    monitor_parser = subparsers.add_parser("monitor", help="Continuously monitor health")
    monitor_parser.add_argument("--interval", "-i", type=int, default=30, help="Monitoring interval in seconds")
    monitor_parser.add_argument("--service", "-s", help="Specific service to monitor")
    monitor_parser.add_argument("--alerts-only", action="store_true", help="Only show alerts and status changes")

    # Show metrics
    metrics_parser = subparsers.add_parser("metrics", help="Show detailed health metrics")
    metrics_parser.add_argument("--service", "-s", help="Specific service metrics")

    # Setup alerts
    subparsers.add_parser("setup-alerts", help="Setup default health alerts")

    # Show alerts
    subparsers.add_parser("alerts", help="Show active health alerts")

    # Export report
    export_parser = subparsers.add_parser("export", help="Export health report")
    export_parser.add_argument("--filename", "-f", help="Output filename")
    export_parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Export format")

    # Format options
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = HealthMonitorCLI()

    try:
        if args.command == "check":
            success = await cli.check_all_health(args.format)
            sys.exit(0 if success else 1)

        elif args.command == "service":
            success = await cli.check_service_health(args.name, args.format)
            sys.exit(0 if success else 1)

        elif args.command == "list":
            await cli.list_services()

        elif args.command == "monitor":
            await cli.monitor_continuous(
                interval=args.interval,
                service=args.service,
                alerts_only=args.alerts_only
            )

        elif args.command == "metrics":
            await cli.show_metrics(args.service)

        elif args.command == "setup-alerts":
            await cli.setup_alerts()

        elif args.command == "alerts":
            await cli.show_alerts()

        elif args.command == "export":
            await cli.export_report(args.filename, args.format)

    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())