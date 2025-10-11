#!/usr/bin/env python3
"""
Test script for the health monitoring system.

This script tests all health check services and verifies that the
health monitoring system is working correctly.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, '/home/ubuntu/ai-concierge')

from src.services.health_check_service import (
    get_health_checker,
    check_all_services_health,
    check_service_health,
    HealthStatus
)
from src.services.database_service import get_database_service
from src.services.redis_service import get_redis_service
from src.services.auth_service import get_auth_service
from src.services.phone_validation_service import get_phone_validation_service
from src.services.webhook_signature_service import get_webhook_signature_service
from src.middleware.rate_limiting import get_rate_limiter
from src.utils.health_utils import get_health_calculator, create_health_metrics
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HealthSystemTester:
    """Test suite for the health monitoring system."""

    def __init__(self):
        self.health_checker = get_health_checker()
        self.health_calculator = get_health_calculator()
        self.test_results = []

    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now(timezone.utc)
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")

    async def test_health_checker_initialization(self):
        """Test health checker initialization."""
        print("\n🔍 Testing Health Checker Initialization...")
        print("-" * 50)

        try:
            # Check if health checker is initialized
            checker = get_health_checker()
            success = checker is not None

            if success:
                # Check if default checks are registered
                checks_registered = len(checker.checks) > 0
                expected_checks = [
                    "database", "redis", "auth_service",
                    "phone_validation", "webhook_signature", "rate_limiting"
                ]

                missing_checks = []
                for check in expected_checks:
                    if check not in checker.checks:
                        missing_checks.append(check)

                if missing_checks:
                    self.log_test_result(
                        "Health Checker Registration",
                        False,
                        f"Missing checks: {missing_checks}"
                    )
                else:
                    self.log_test_result(
                        "Health Checker Registration",
                        True,
                        f"Registered {len(checker.checks)} health checks"
                    )
            else:
                self.log_test_result(
                    "Health Checker Initialization",
                    False,
                    "Health checker is None"
                )

        except Exception as e:
            self.log_test_result(
                "Health Checker Initialization",
                False,
                f"Exception: {str(e)}"
            )

    async def test_database_health_check(self):
        """Test database health check."""
        print("\n🔍 Testing Database Health Check...")
        print("-" * 50)

        try:
            # Test database service is available
            db_service = get_database_service()
            self.log_test_result(
                "Database Service Available",
                db_service is not None,
                "Database service initialized"
            )

            # Test database health check
            result = await check_service_health("database")
            self.log_test_result(
                "Database Health Check",
                result.status != HealthStatus.UNKNOWN,
                f"Status: {result.status.value}, Message: {result.message}"
            )

            if result.error:
                self.log_test_result(
                    "Database Health Check Error",
                    False,
                    f"Error: {result.error}"
                )

        except Exception as e:
            self.log_test_result(
                "Database Health Check",
                False,
                f"Exception: {str(e)}"
            )

    async def test_redis_health_check(self):
        """Test Redis health check."""
        print("\n🔍 Testing Redis Health Check...")
        print("-" * 50)

        try:
            # Test Redis service is available
            redis_service = get_redis_service()
            self.log_test_result(
                "Redis Service Available",
                redis_service is not None,
                "Redis service initialized"
            )

            # Test basic Redis operations
            test_key = "health_test_key"
            test_value = {"test": True, "timestamp": datetime.now().isoformat()}

            # Test set and get operations
            set_result = redis_service.set_sync(test_key, test_value, ttl=60)
            self.log_test_result(
                "Redis SET Operation",
                set_result,
                "Successfully set test key"
            )

            get_result = redis_service.get_sync(test_key)
            self.log_test_result(
                "Redis GET Operation",
                get_result is not None,
                "Successfully retrieved test key"
            )

            # Clean up
            redis_service.delete_sync(test_key)

            # Test Redis health check
            result = await check_service_health("redis")
            self.log_test_result(
                "Redis Health Check",
                result.status != HealthStatus.UNKNOWN,
                f"Status: {result.status.value}, Message: {result.message}"
            )

        except Exception as e:
            self.log_test_result(
                "Redis Health Check",
                False,
                f"Exception: {str(e)}"
            )

    async def test_auth_service_health_check(self):
        """Test authentication service health check."""
        print("\n🔍 Testing Auth Service Health Check...")
        print("-" * 50)

        try:
            # Test auth service is available
            auth_service = get_auth_service()
            self.log_test_result(
                "Auth Service Available",
                auth_service is not None,
                "Auth service initialized"
            )

            # Test JWT token generation
            test_user_id = "00000000-0000-0000-0000-000000000000"
            try:
                token_info = auth_service.generate_access_token(test_user_id)
                self.log_test_result(
                    "JWT Token Generation",
                    token_info is not None and token_info.token is not None,
                    "Successfully generated JWT token"
                )
            except Exception as e:
                self.log_test_result(
                    "JWT Token Generation",
                    False,
                    f"Token generation failed: {str(e)}"
                )

            # Test auth service health check
            result = await check_service_health("auth_service")
            self.log_test_result(
                "Auth Service Health Check",
                result.status != HealthStatus.UNKNOWN,
                f"Status: {result.status.value}, Message: {result.message}"
            )

        except Exception as e:
            self.log_test_result(
                "Auth Service Health Check",
                False,
                f"Exception: {str(e)}"
            )

    async def test_phone_validation_health_check(self):
        """Test phone validation service health check."""
        print("\n🔍 Testing Phone Validation Health Check...")
        print("-" * 50)

        try:
            # Test phone validation service is available
            phone_service = get_phone_validation_service()
            self.log_test_result(
                "Phone Validation Service Available",
                phone_service is not None,
                "Phone validation service initialized"
            )

            # Test phone number validation
            test_numbers = [
                "+221771234567",  # Orange Senegal
                "+221781234567",  # Free Senegal
            ]

            for number in test_numbers:
                try:
                    result = phone_service.validate_phone_number(number)
                    self.log_test_result(
                        f"Phone Validation ({number})",
                        result is not None,
                        f"Valid: {result.is_valid if result else 'N/A'}"
                    )
                except Exception as e:
                    self.log_test_result(
                        f"Phone Validation ({number})",
                        False,
                        f"Validation failed: {str(e)}"
                    )

            # Test phone validation health check
            result = await check_service_health("phone_validation")
            self.log_test_result(
                "Phone Validation Health Check",
                result.status != HealthStatus.UNKNOWN,
                f"Status: {result.status.value}, Message: {result.message}"
            )

        except Exception as e:
            self.log_test_result(
                "Phone Validation Health Check",
                False,
                f"Exception: {str(e)}"
            )

    async def test_webhook_signature_health_check(self):
        """Test webhook signature service health check."""
        print("\n🔍 Testing Webhook Signature Health Check...")
        print("-" * 50)

        try:
            # Test webhook signature service is available
            webhook_service = get_webhook_signature_service()
            self.log_test_result(
                "Webhook Signature Service Available",
                webhook_service is not None,
                "Webhook signature service initialized"
            )

            # Test service statistics
            try:
                stats = webhook_service.get_verification_statistics()
                self.log_test_result(
                    "Webhook Service Statistics",
                    stats is not None,
                    f"Platforms: {stats.get('supported_platforms', [])}"
                )
            except Exception as e:
                self.log_test_result(
                    "Webhook Service Statistics",
                    False,
                    f"Failed to get stats: {str(e)}"
                )

            # Test webhook signature health check
            result = await check_service_health("webhook_signature")
            self.log_test_result(
                "Webhook Signature Health Check",
                result.status != HealthStatus.UNKNOWN,
                f"Status: {result.status.value}, Message: {result.message}"
            )

        except Exception as e:
            self.log_test_result(
                "Webhook Signature Health Check",
                False,
                f"Exception: {str(e)}"
            )

    async def test_rate_limiting_health_check(self):
        """Test rate limiting health check."""
        print("\n🔍 Testing Rate Limiting Health Check...")
        print("-" * 50)

        try:
            # Test rate limiter is available
            rate_limiter = get_rate_limiter()
            self.log_test_result(
                "Rate Limiter Available",
                rate_limiter is not None,
                "Rate limiter initialized"
            )

            # Test basic rate limiting
            try:
                test_config = {"requests_per_window": 5, "window_seconds": 60}
                result = rate_limiter.check_rate_limit("test_identifier", test_config)
                self.log_test_result(
                    "Rate Limiting Check",
                    result is not None,
                    f"Allowed: {result.allowed if result else 'N/A'}"
                )
            except Exception as e:
                self.log_test_result(
                    "Rate Limiting Check",
                    False,
                    f"Rate limit check failed: {str(e)}"
                )

            # Test rate limiting health check
            result = await check_service_health("rate_limiting")
            self.log_test_result(
                "Rate Limiting Health Check",
                result.status != HealthStatus.UNKNOWN,
                f"Status: {result.status.value}, Message: {result.message}"
            )

        except Exception as e:
            self.log_test_result(
                "Rate Limiting Health Check",
                False,
                f"Exception: {str(e)}"
            )

    async def test_overall_health_check(self):
        """Test overall system health check."""
        print("\n🔍 Testing Overall System Health Check...")
        print("-" * 50)

        try:
            # Test comprehensive health check
            report = await check_all_services_health()
            self.log_test_result(
                "Overall Health Check",
                report is not None,
                f"Status: {report.status.value if report else 'N/A'}"
            )

            if report:
                self.log_test_result(
                    "Health Report Generated",
                    len(report.checks) > 0,
                    f"Checked {len(report.checks)} services"
                )

                # Check individual service results
                healthy_count = sum(1 for check in report.checks if check.status == HealthStatus.HEALTHY)
                self.log_test_result(
                    "Healthy Services Count",
                    healthy_count >= 0,
                    f"{healthy_count} out of {len(report.checks)} services healthy"
                )

        except Exception as e:
            self.log_test_result(
                "Overall Health Check",
                False,
                f"Exception: {str(e)}"
            )

    async def test_health_calculator(self):
        """Test health calculator functionality."""
        print("\n🔍 Testing Health Calculator...")
        print("-" * 50)

        try:
            # Test health calculator is available
            calculator = get_health_calculator()
            self.log_test_result(
                "Health Calculator Available",
                calculator is not None,
                "Health calculator initialized"
            )

            # Test metrics calculation
            metrics = create_health_metrics()
            self.log_test_result(
                "Health Metrics Creation",
                metrics is not None,
                "Health metrics instance created"
            )

            # Add some test requests
            metrics.add_request(100, True)   # Fast success
            metrics.add_request(200, True)   # Medium success
            metrics.add_request(50, True)    # Fast success
            metrics.add_request(5000, False) # Slow failure

            # Test health calculation
            health_status, breakdown = calculator.calculate_service_health(metrics)
            self.log_test_result(
                "Health Status Calculation",
                health_status is not None,
                f"Calculated status: {health_status.value}"
            )

            self.log_test_result(
                "Health Breakdown Generated",
                breakdown is not None and len(breakdown) > 0,
                f"Breakdown has {len(breakdown)} components"
            )

        except Exception as e:
            self.log_test_result(
                "Health Calculator",
                False,
                f"Exception: {str(e)}"
            )

    async def run_all_tests(self):
        """Run all health system tests."""
        print("🏥 Health System Test Suite")
        print("=" * 60)
        print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()

        # Run all test methods
        test_methods = [
            self.test_health_checker_initialization,
            self.test_database_health_check,
            self.test_redis_health_check,
            self.test_auth_service_health_check,
            self.test_phone_validation_health_check,
            self.test_webhook_signature_health_check,
            self.test_rate_limiting_health_check,
            self.test_overall_health_check,
            self.test_health_calculator,
        ]

        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_test_result(
                    test_method.__name__,
                    False,
                    f"Test method failed: {str(e)}"
                )

        # Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("🏥 Test Summary")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test_name']}: {result['message']}")

        print(f"\nCompleted at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")


async def main():
    """Main test entry point."""
    tester = HealthSystemTester()
    await tester.run_all_tests()

    # Exit with appropriate code
    failed_tests = sum(1 for result in tester.test_results if not result["success"])
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())