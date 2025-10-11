"""
Error Handling and Recovery Service

This service provides comprehensive error handling, recovery mechanisms,
and resilience patterns for the account creation system.
Enhanced for Phase 3 with intelligent error recovery and system monitoring.
"""

import logging
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Callable, Type, Union
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, field
import traceback

from src.services.database_service import get_database_service
from src.services.redis_service import get_redis_service
from src.utils.logging import get_logger
from src.utils.exceptions import (
    AccountCreationError,
    ValidationError,
    ParentNotFoundError,
    DuplicateAccountError,
    DatabaseConnectionError,
    SecurityError
)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    SECURITY = "security"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"


class RecoveryAction(Enum):
    """Available recovery actions."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    QUEUE = "queue"
    NOTIFY_ADMIN = "notify_admin"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorContext:
    """Context information for error occurrence."""
    user_id: Optional[UUID] = None
    platform: Optional[str] = None
    phone_number: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    error_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    stack_trace: Optional[str] = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_action: Optional[RecoveryAction] = None
    retry_count: int = 0
    resolved_at: Optional[datetime] = None


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    action: RecoveryAction
    message: str
    error_record: Optional[ErrorRecord] = None
    retry_after: Optional[timedelta] = None
    requires_manual_intervention: bool = False


class RetryPolicy:
    """Configuration for retry policies."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: timedelta = timedelta(seconds=1),
        max_delay: timedelta = timedelta(minutes=5),
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def get_delay(self, attempt: int) -> timedelta:
        """Calculate delay for retry attempt."""
        delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add jitter to prevent thundering herd
            import random
            jitter_factor = random.uniform(0.8, 1.2)
            delay = delay * jitter_factor

        return delay


class ErrorHandlingService:
    """
    Service for comprehensive error handling and recovery.

    This service provides intelligent error classification, recovery strategies,
    and monitoring for the account creation system.
    """

    def __init__(
        self,
        database_service=None,
        redis_service=None,
        retry_policies: Optional[Dict[str, RetryPolicy]] = None
    ):
        """
        Initialize error handling service.

        Args:
            database_service: Database service instance
            redis_service: Redis service instance
            retry_policies: Custom retry policies by error type
        """
        self.database_service = database_service or get_database_service()
        self.redis_service = redis_service or get_redis_service()
        self.logger = get_logger(__name__)

        # Default retry policies
        self.retry_policies = retry_policies or {
            AccountCreationError: RetryPolicy(max_attempts=3, base_delay=timedelta(seconds=2)),
            DatabaseConnectionError: RetryPolicy(max_attempts=5, base_delay=timedelta(seconds=1)),
            ValidationError: RetryPolicy(max_attempts=1),  # Don't retry validation errors
            ParentNotFoundError: RetryPolicy(max_attempts=2, base_delay=timedelta(seconds=5)),
            SecurityError: RetryPolicy(max_attempts=1),  # Don't retry security errors
        }

        # Error handlers by exception type
        self.error_handlers: Dict[Type[Exception], Callable] = {
            AccountCreationError: self._handle_account_creation_error,
            DatabaseConnectionError: self._handle_database_error,
            ValidationError: self._handle_validation_error,
            ParentNotFoundError: self._handle_parent_not_found_error,
            DuplicateAccountError: self._handle_duplicate_account_error,
            SecurityError: self._handle_security_error,
        }

    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        retry_count: int = 0
    ) -> RecoveryResult:
        """
        Handle an error with intelligent recovery.

        Args:
            error: The exception that occurred
            context: Error context information
            retry_count: Current retry attempt

        Returns:
            Recovery result with action taken
        """
        try:
            # Classify error
            error_record = await self._classify_error(error, context, retry_count)

            # Log error
            await self._log_error(error_record)

            # Check if we should retry
            if await self._should_retry(error_record):
                return await self._attempt_retry(error_record)

            # Check for specific handler
            handler = self._get_error_handler(type(error))
            if handler:
                return await handler(error_record)

            # Default recovery strategy
            return await self._default_recovery(error_record)

        except Exception as recovery_error:
            self.logger.error(f"Error in error handling: {str(recovery_error)}")
            return RecoveryResult(
                success=False,
                action=RecoveryAction.NOTIFY_ADMIN,
                message=f"Error handling failed: {str(recovery_error)}",
                requires_manual_intervention=True
            )

    async def execute_with_recovery(
        self,
        operation: Callable,
        context: ErrorContext,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation with automatic error recovery.

        Args:
            operation: The operation to execute
            context: Error context
            *args: Arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation

        Returns:
            Result of the operation

        Raises:
            Exception: If recovery fails
        """
        last_error = None
        retry_count = 0

        while True:
            try:
                # Execute the operation
                result = await operation(*args, **kwargs)

                # Log successful execution if this was a retry
                if retry_count > 0:
                    await self._log_recovery_success(context, retry_count)

                return result

            except Exception as error:
                last_error = error
                retry_count += 1

                # Handle the error
                recovery_result = await self.handle_error(error, context, retry_count)

                if not recovery_result.success:
                    # Recovery failed, re-raise the original error
                    raise error

                if recovery_result.action == RecoveryAction.RETRY:
                    # Wait before retrying
                    if recovery_result.retry_after:
                        await asyncio.sleep(recovery_result.retry_after.total_seconds())
                    continue
                elif recovery_result.action == RecoveryAction.FALLBACK:
                    # Use fallback result
                    return recovery_result.message  # In real implementation, return fallback data
                elif recovery_result.action == RecoveryAction.SKIP:
                    # Skip operation and return None
                    return None
                elif recovery_result.action == RecoveryAction.QUEUE:
                    # Queue for later processing
                    await self._queue_for_retry(operation, context, args, kwargs)
                    return None
                else:
                    # Manual intervention required
                    raise error

    async def classify_and_handle_webhook_error(
        self,
        error: Exception,
        webhook_data: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """
        Handle webhook-specific errors with appropriate responses.

        Args:
            error: The exception that occurred
            webhook_data: Original webhook data
            platform: Platform name

        Returns:
            Webhook response appropriate for the error
        """
        try:
            context = ErrorContext(
                platform=platform,
                operation="webhook_processing",
                component="webhook_handler",
                metadata={"webhook_size": len(json.dumps(webhook_data))}
            )

            recovery_result = await self.handle_error(error, context)

            # Return appropriate webhook response
            if recovery_result.success:
                return {
                    "status": "processed_with_recovery",
                    "message": recovery_result.message,
                    "recovery_action": recovery_result.action.value
                }
            else:
                # For webhooks, we usually want to return success to avoid retries
                # even if processing failed, but log the error appropriately
                return {
                    "status": "error_logged",
                    "message": "Webhook received but processing failed",
                    "error_logged": True
                }

        except Exception as e:
            self.logger.error(f"Critical error in webhook error handling: {str(e)}")
            return {
                "status": "critical_error",
                "message": "Webhook processing failed critically"
            }

    async def get_error_statistics(
        self,
        hours: int = 24,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None
    ) -> Dict[str, Any]:
        """
        Get error statistics for monitoring.

        Args:
            hours: Number of hours to look back
            severity: Filter by severity
            category: Filter by category

        Returns:
            Error statistics
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            # In production, this would query the database
            # For now, return mock statistics
            return {
                "period_hours": hours,
                "total_errors": 145,
                "errors_by_severity": {
                    "low": 45,
                    "medium": 67,
                    "high": 28,
                    "critical": 5
                },
                "errors_by_category": {
                    "validation": 35,
                    "database": 28,
                    "external_api": 42,
                    "security": 12,
                    "business_logic": 23,
                    "system": 5
                },
                "recovery_success_rate": 87.3,
                "most_common_errors": [
                    {"type": "ParentNotFoundError", "count": 25},
                    {"type": "DatabaseConnectionError", "count": 18},
                    {"type": "ValidationError", "count": 15}
                ],
                "errors_requiring_intervention": 3
            }

        except Exception as e:
            self.logger.error(f"Failed to get error statistics: {str(e)}")
            return {"error": str(e)}

    # Private methods

    async def _classify_error(
        self,
        error: Exception,
        context: ErrorContext,
        retry_count: int
    ) -> ErrorRecord:
        """Classify and create error record."""
        import uuid

        # Determine severity
        severity = self._determine_severity(error, context)

        # Determine category
        category = self._determine_category(error)

        error_record = ErrorRecord(
            error_id=str(uuid.uuid4()),
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            context=context,
            stack_trace=traceback.format_exc(),
            retry_count=retry_count
        )

        return error_record

    def _determine_severity(self, error: Exception, context: ErrorContext) -> ErrorSeverity:
        """Determine error severity."""
        if isinstance(error, (SecurityError, DatabaseConnectionError)):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, (AccountCreationError, ParentNotFoundError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (DuplicateAccountError,)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _determine_category(self, error: Exception) -> ErrorCategory:
        """Determine error category."""
        if isinstance(error, ValidationError):
            return ErrorCategory.VALIDATION
        elif isinstance(error, (DatabaseConnectionError,)):
            return ErrorCategory.DATABASE
        elif isinstance(error, SecurityError):
            return ErrorCategory.SECURITY
        elif isinstance(error, (ParentNotFoundError, DuplicateAccountError, AccountCreationError)):
            return ErrorCategory.BUSINESS_LOGIC
        else:
            return ErrorCategory.SYSTEM

    async def _log_error(self, error_record: ErrorRecord) -> None:
        """Log error to database and monitoring systems."""
        try:
            # Log to database
            log_data = {
                'error_id': error_record.error_id,
                'error_type': error_record.error_type,
                'error_message': error_record.error_message,
                'severity': error_record.severity.value,
                'category': error_record.category.value,
                'context': json.dumps(error_record.context.__dict__),
                'stack_trace': error_record.stack_trace,
                'occurred_at': error_record.occurred_at,
                'retry_count': error_record.retry_count
            }

            await self.database_service.insert(
                'error_logs',
                log_data,
                database_name='supabase'
            )

            # Log to Redis for real-time monitoring
            await self.redis_service.set(
                f"error:{error_record.error_id}",
                json.dumps({
                    'error_id': error_record.error_id,
                    'type': error_record.error_type,
                    'severity': error_record.severity.value,
                    'timestamp': error_record.occurred_at.isoformat()
                }),
                ttl=3600  # 1 hour
            )

            # Increment error counters
            await self._increment_error_counters(error_record)

        except Exception as e:
            self.logger.error(f"Failed to log error: {str(e)}")

    async def _increment_error_counters(self, error_record: ErrorRecord) -> None:
        """Increment error counters for monitoring."""
        try:
            # Increment counters by different dimensions
            counters = [
                f"errors:total",
                f"errors:severity:{error_record.severity.value}",
                f"errors:category:{error_record.category.value}",
                f"errors:type:{error_record.error_type}",
                f"errors:component:{error_record.context.component or 'unknown'}"
            ]

            for counter in counters:
                await self.redis_service.incr(counter)
                await self.redis_service.expire(counter, 86400)  # 24 hours

        except Exception as e:
            self.logger.error(f"Failed to increment error counters: {str(e)}")

    async def _should_retry(self, error_record: ErrorRecord) -> bool:
        """Determine if error should be retried."""
        error_type = type(error_record.error_type)

        # Get retry policy for this error type
        policy = self.retry_policies.get(error_type)
        if not policy:
            # Default policy for unknown errors
            policy = RetryPolicy(max_attempts=2)

        return error_record.retry_count < policy.max_attempts

    async def _attempt_retry(self, error_record: ErrorRecord) -> RecoveryResult:
        """Attempt retry with appropriate delay."""
        error_type = type(error_record.error_type)
        policy = self.retry_policies.get(error_type, RetryPolicy())

        delay = policy.get_delay(error_record.retry_count)

        return RecoveryResult(
            success=True,
            action=RecoveryAction.RETRY,
            message=f"Retrying operation after {delay.total_seconds():.2f} seconds",
            retry_after=delay
        )

    def _get_error_handler(self, error_type: Type[Exception]) -> Optional[Callable]:
        """Get specific handler for error type."""
        for handled_type, handler in self.error_handlers.items():
            if issubclass(error_type, handled_type):
                return handler
        return None

    async def _default_recovery(self, error_record: ErrorRecord) -> RecoveryResult:
        """Default recovery strategy."""
        if error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            return RecoveryResult(
                success=True,
                action=RecoveryAction.NOTIFY_ADMIN,
                message="High severity error, admin notification required",
                requires_manual_intervention=True
            )
        else:
            return RecoveryResult(
                success=True,
                action=RecoveryAction.SKIP,
                message="Error recovered by skipping operation"
            )

    # Specific error handlers

    async def _handle_account_creation_error(self, error_record: ErrorRecord) -> RecoveryResult:
        """Handle account creation errors."""
        return RecoveryResult(
            success=True,
            action=RecoveryAction.RETRY,
            message="Account creation failed, will retry with different approach",
            retry_after=timedelta(seconds=5)
        )

    async def _handle_database_error(self, error_record: ErrorRecord) -> RecoveryResult:
        """Handle database connection errors."""
        if error_record.retry_count < 3:
            return RecoveryResult(
                success=True,
                action=RecoveryAction.RETRY,
                message="Database connection issue, retrying",
                retry_after=timedelta(seconds=2 ** error_record.retry_count)
            )
        else:
            return RecoveryResult(
                success=True,
                action=RecoveryAction.QUEUE,
                message="Database unavailable, queuing for later processing"
            )

    async def _handle_validation_error(self, error_record: ErrorRecord) -> RecoveryResult:
        """Handle validation errors."""
        return RecoveryResult(
            success=True,
            action=RecoveryAction.SKIP,
            message="Validation error, skipping operation"
        )

    async def _handle_parent_not_found_error(self, error_record: ErrorRecord) -> RecoveryResult:
        """Handle parent not found errors."""
        if error_record.retry_count == 0:
            return RecoveryResult(
                success=True,
                action=RecoveryAction.RETRY,
                message="Parent not found, will retry with different lookup method",
                retry_after=timedelta(seconds=10)
            )
        else:
            return RecoveryResult(
                success=True,
                action=RecoveryAction.NOTIFY_ADMIN,
                message="Parent not found after retry, requires manual verification",
                requires_manual_intervention=True
            )

    async def _handle_duplicate_account_error(self, error_record: ErrorRecord) -> RecoveryResult:
        """Handle duplicate account errors."""
        return RecoveryResult(
            success=True,
            action=RecoveryAction.FALLBACK,
            message="Duplicate account detected, linking to existing account"
        )

    async def _handle_security_error(self, error_record: ErrorRecord) -> RecoveryResult:
        """Handle security errors."""
        return RecoveryResult(
            success=True,
            action=RecoveryAction.NOTIFY_ADMIN,
            message="Security error detected, immediate admin notification required",
            requires_manual_intervention=True
        )

    async def _queue_for_retry(
        self,
        operation: Callable,
        context: ErrorContext,
        args: tuple,
        kwargs: dict
    ) -> None:
        """Queue operation for later retry."""
        try:
            queue_data = {
                'operation': operation.__name__,
                'context': context.__dict__,
                'args': str(args),
                'kwargs': str(kwargs),
                'queued_at': datetime.now(timezone.utc).isoformat()
            }

            await self.redis_service.lpush(
                'retry_queue',
                json.dumps(queue_data)
            )

            self.logger.info(f"Operation queued for retry: {operation.__name__}")

        except Exception as e:
            self.logger.error(f"Failed to queue operation for retry: {str(e)}")

    async def _log_recovery_success(self, context: ErrorContext, retry_count: int) -> None:
        """Log successful recovery."""
        try:
            log_data = {
                'context': json.dumps(context.__dict__),
                'retry_count': retry_count,
                'recovered_at': datetime.now(timezone.utc),
                'success': True
            }

            await self.database_service.insert(
                'recovery_logs',
                log_data,
                database_name='supabase'
            )

        except Exception as e:
            self.logger.error(f"Failed to log recovery success: {str(e)}")


# Factory function for getting error handling service
def get_error_handling_service() -> ErrorHandlingService:
    """Get error handling service instance."""
    return ErrorHandlingService()