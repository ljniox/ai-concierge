"""
Logging configuration for the automatic account creation system.

This module provides structured JSON logging with request ID tracking,
correlation IDs, and proper log formatting for production environments.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger

# Context variables for request tracing
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
platform: ContextVar[Optional[str]] = ContextVar('platform', default=None)


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with enhanced fields for account creation system."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with additional context."""
        # Get standard log record data
        log_object = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add context variables if available
        if request_id.get():
            log_object['request_id'] = request_id.get()
        if correlation_id.get():
            log_object['correlation_id'] = correlation_id.get()
        if user_id.get():
            log_object['user_id'] = user_id.get()
        if platform.get():
            log_object['platform'] = platform.get()

        # Add exception info if present
        if record.exc_info:
            log_object['exception'] = self.formatException(record.exc_info)

        # Add any extra fields from the record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_object[key] = value

        return json.dumps(log_object, default=str)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup structured JSON logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def set_request_context(request_id_value: Optional[str] = None) -> str:
    """
    Set request ID context for the current request.

    Args:
        request_id_value: Optional request ID. If None, generates a new UUID.

    Returns:
        The request ID that was set
    """
    req_id = request_id_value or str(uuid.uuid4())
    request_id.set(req_id)
    return req_id


def set_correlation_context(correlation_id_value: str) -> None:
    """
    Set correlation ID context for the current request chain.

    Args:
        correlation_id_value: Correlation ID to set
    """
    correlation_id.set(correlation_id_value)


def set_user_context(user_id_value: str, platform_value: str) -> None:
    """
    Set user context for the current request.

    Args:
        user_id_value: User ID
        platform_value: Platform (whatsapp, telegram)
    """
    user_id.set(user_id_value)
    platform.set(platform_value)


def clear_context() -> None:
    """Clear all context variables."""
    request_id.set(None)
    correlation_id.set(None)
    user_id.set(None)
    platform.set(None)


class LoggingContext:
    """Context manager for logging with automatic context setup/cleanup."""

    def __init__(
        self,
        request_id_value: Optional[str] = None,
        correlation_id_value: Optional[str] = None,
        user_id_value: Optional[str] = None,
        platform_value: Optional[str] = None
    ):
        self.request_id_value = request_id_value or str(uuid.uuid4())
        self.correlation_id_value = correlation_id_value
        self.user_id_value = user_id_value
        self.platform_value = platform_value
        self.old_values = {}

    def __enter__(self) -> str:
        """Set up logging context."""
        # Store old values
        self.old_values = {
            'request_id': request_id.get(),
            'correlation_id': correlation_id.get(),
            'user_id': user_id.get(),
            'platform': platform.get(),
        }

        # Set new values
        set_request_context(self.request_id_value)
        if self.correlation_id_value:
            set_correlation_context(self.correlation_id_value)
        if self.user_id_value and self.platform_value:
            set_user_context(self.user_id_value, self.platform_value)

        return self.request_id_value

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Restore previous logging context."""
        request_id.set(self.old_values['request_id'])
        correlation_id.set(self.old_values['correlation_id'])
        user_id.set(self.old_values['user_id'])
        platform.set(self.old_values['platform'])


def log_account_creation_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    phone_number: str,
    platform: str,
    user_id: Optional[str] = None,
    status: str = "initiated",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log account creation events with consistent structure.

    Args:
        logger: Logger instance
        event_type: Type of event (initiated, phone_validated, parent_found, etc.)
        phone_number: Phone number (masked for privacy)
        platform: Platform (whatsapp, telegram)
        user_id: User ID if available
        status: Status of the event
        details: Additional event details
    """
    # Mask phone number for privacy
    masked_phone = mask_phone_number(phone_number)

    log_data = {
        'event_type': 'account_creation',
        'account_creation_event': event_type,
        'phone_number': masked_phone,
        'platform': platform,
        'status': status,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    if user_id:
        log_data['user_id'] = user_id

    if details:
        log_data.update(details)

    logger.info("Account creation event", **log_data)


def log_webhook_event(
    logger: structlog.stdlib.BoundLogger,
    platform: str,
    event_type: str,
    signature_verified: bool,
    processing_status: str = "pending",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log webhook events with security and processing information.

    Args:
        logger: Logger instance
        platform: Platform (whatsapp, telegram)
        event_type: Type of webhook event
        signature_verified: Whether webhook signature was verified
        processing_status: Processing status
        details: Additional event details
    """
    log_data = {
        'event_type': 'webhook',
        'platform': platform,
        'webhook_event_type': event_type,
        'signature_verified': signature_verified,
        'processing_status': processing_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    if details:
        log_data.update(details)

    logger.info("Webhook event received", **log_data)


def mask_phone_number(phone_number: str) -> str:
    """
    Mask phone number for privacy compliance.

    Args:
        phone_number: Phone number to mask

    Returns:
        Masked phone number (e.g., +221*******555)
    """
    if not phone_number:
        return phone_number

    # Keep first 4 characters and last 3 characters
    if len(phone_number) > 7:
        return phone_number[:4] + '*' * (len(phone_number) - 7) + phone_number[-3:]
    elif len(phone_number) > 3:
        return phone_number[:1] + '*' * (len(phone_number) - 3) + phone_number[-2:]
    else:
        return '*' * len(phone_number)


def mask_email(email: str) -> str:
    """
    Mask email address for privacy compliance.

    Args:
        email: Email address to mask

    Returns:
        Masked email address (e.g., ****@domain.com)
    """
    if not email or '@' not in email:
        return email

    local, domain = email.split('@', 1)
    if len(local) > 2:
        masked_local = local[:2] + '*' * (len(local) - 2)
    else:
        masked_local = '*' * len(local)

    return f"{masked_local}@{domain}"


class PerformanceLogger:
    """Context manager for measuring and logging performance metrics."""

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.logger = logger
        self.operation = operation
        self.details = details or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        log_data = {
            'event_type': 'performance',
            'operation': self.operation,
            'duration_ms': round(duration_ms, 2),
            'success': exc_type is None
        }

        if exc_type:
            log_data['error_type'] = exc_type.__name__
            log_data['error_message'] = str(exc_val)

        log_data.update(self.details)

        if duration_ms > 1000:  # Log warning for operations > 1 second
            self.logger.warning("Slow operation detected", **log_data)
        else:
            self.logger.info("Performance metric", **log_data)


# Legacy AccountCreationLogger for backward compatibility
class AccountCreationLogger:
    """Structured logger for account creation events."""

    def __init__(self):
        self.logger = get_logger("account_creation")

    def log_account_creation_started(self, phone_number: str, source: str, platform_user_id: str) -> None:
        """Log the start of account creation process."""
        log_account_creation_event(
            self.logger,
            "account_creation_started",
            phone_number,
            source,
            platform_user_id=platform_user_id,
            details={"source": source}
        )

    def log_phone_validation_result(self, phone_number: str, is_valid: bool, details: Dict[str, Any]) -> None:
        """Log phone number validation results."""
        log_account_creation_event(
            self.logger,
            "phone_validation_completed",
            phone_number,
            "validation",
            status="validated" if is_valid else "failed",
            details={"is_valid": is_valid, **details}
        )

    def log_parent_database_lookup(self, phone_number: str, parent_found: bool, parent_id: int = None) -> None:
        """Log parent database lookup results."""
        log_account_creation_event(
            self.logger,
            "parent_database_lookup_completed",
            phone_number,
            "database",
            status="found" if parent_found else "not_found",
            details={"parent_found": parent_found, "parent_id": parent_id}
        )

    def log_account_created(self, user_id: int, phone_number: str, roles: list, source: str) -> None:
        """Log successful account creation."""
        log_account_creation_event(
            self.logger,
            "account_created_successfully",
            phone_number,
            source,
            user_id=str(user_id),
            status="completed",
            details={"roles": roles}
        )

    def log_account_creation_failed(self, phone_number: str, error_type: str, error_message: str, source: str) -> None:
        """Log failed account creation."""
        log_account_creation_event(
            self.logger,
            "account_creation_failed",
            phone_number,
            source,
            status="failed",
            details={"error_type": error_type, "error_message": error_message}
        )

    def log_role_assignment(self, user_id: int, role_name: str, assigned_by: int = None) -> None:
        """Log role assignment events."""
        self.logger.info(
            "role_assigned",
            user_id=user_id,
            role_name=role_name,
            assigned_by=assigned_by,
            event_type="role_management"
        )

    def log_webhook_received(self, platform: str, user_id: str, message_type: str) -> None:
        """Log incoming webhook events."""
        log_webhook_event(
            self.logger,
            platform,
            message_type,
            signature_verified=False,  # Will be updated during implementation
            processing_status="received",
            details={"user_id": user_id}
        )

    def log_session_created(self, user_id: int, platform: str, session_id: str) -> None:
        """Log session creation."""
        self.logger.info(
            "session_created",
            user_id=user_id,
            platform=platform,
            session_id=session_id[:10] + "***",
            event_type="session_management"
        )

    def log_consent_given(self, user_id: int, consent_type: str) -> None:
        """Log GDPR consent events."""
        self.logger.info(
            "consent_recorded",
            user_id=user_id,
            consent_type=consent_type,
            event_type="consent_management"
        )

    def log_duplicate_account_prevented(self, phone_number: str, existing_user_id: int) -> None:
        """Log prevention of duplicate account creation."""
        log_account_creation_event(
            self.logger,
            "duplicate_account_prevented",
            phone_number,
            "system",
            user_id=str(existing_user_id),
            status="duplicate_prevented"
        )

    def log_rate_limit_exceeded(self, identifier: str, limit_type: str) -> None:
        """Log rate limiting events."""
        self.logger.warning(
            "rate_limit_exceeded",
            identifier=identifier[:10] + "***",
            limit_type=limit_type,
            event_type="security"
        )

    def log_platform_account_linked(self, user_id: int, platform: str, platform_user_id: str) -> None:
        """Log platform account linking."""
        self.logger.info(
            "platform_account_linked",
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id[:10] + "***",
            event_type="account_linking"
        )


# Global logger instance
account_logger = AccountCreationLogger()