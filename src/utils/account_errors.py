"""
Error Handling Utilities for Account Creation System

This module provides comprehensive error handling utilities for the automatic
account creation feature, including custom exceptions, error responses, and
recovery strategies.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime
from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standard error codes for account creation system."""

    # Validation Errors
    INVALID_PHONE_FORMAT = "INVALID_PHONE_FORMAT"
    PHONE_NOT_MOBILE = "PHONE_NOT_MOBILE"
    UNSUPPORTED_COUNTRY = "UNSUPPORTED_COUNTRY"
    INVALID_PHONE_NUMBER = "INVALID_PHONE_NUMBER"

    # Database Errors
    PARENT_NOT_FOUND = "PARENT_NOT_FOUND"
    ACCOUNT_ALREADY_EXISTS = "ACCOUNT_ALREADY_EXISTS"
    DATABASE_ERROR = "DATABASE_ERROR"
    DUPLICATE_ACCOUNT = "DUPLICATE_ACCOUNT"

    # Authentication Errors
    INVALID_WEBHOOK = "INVALID_WEBHOOK"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # System Errors
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Business Logic Errors
    ACCOUNT_CREATION_FAILED = "ACCOUNT_CREATION_FAILED"
    ROLE_ASSIGNMENT_FAILED = "ROLE_ASSIGNMENT_FAILED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccountCreationError(Exception):
    """Base exception for account creation errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        phone_number: Optional[str] = None,
        platform: Optional[str] = None,
        user_id: Optional[int] = None,
        retry_after: Optional[int] = None,
        suggested_action: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        self.phone_number = phone_number
        self.platform = platform
        self.user_id = user_id
        self.retry_after = retry_after
        self.suggested_action = suggested_action
        self.timestamp = datetime.utcnow()

        super().__init__(self.message)


class ValidationError(AccountCreationError):
    """Error raised during phone number validation."""

    def __init__(
        self,
        message: str,
        phone_number: str,
        error_code: ErrorCode = ErrorCode.INVALID_PHONE_FORMAT,
        details: Optional[Dict[str, Any]] = None,
        suggested_format: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            severity=ErrorSeverity.LOW,
            details=details,
            phone_number=phone_number,
            suggested_action=suggested_format
        )
        self.suggested_format = suggested_format


class DatabaseError(AccountCreationError):
    """Error raised during database operations."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        operation: Optional[str] = None,
        table: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            severity=severity,
            details={
                "operation": operation,
                "table": table
            }
        )
        self.operation = operation
        self.table = table


class AuthenticationError(AccountCreationError):
    """Error raised during authentication."""

    def __init__(
        self,
        message: str,
        platform: str,
        error_code: ErrorCode = ErrorCode.UNAUTHORIZED,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            severity=severity,
            platform=platform,
            retry_after=retry_after
        )


class BusinessLogicError(AccountCreationError):
    """Error raised during business logic execution."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        business_rule: Optional[str] = None,
        recovery_possible: bool = True
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            severity=severity,
            details={
                "business_rule": business_rule,
                "recovery_possible": recovery_possible
            },
            suggested_action="Please contact support if the issue persists"
        )
        self.business_rule = business_rule
        self.recovery_possible = recovery_possible


class ErrorDetails(BaseModel):
    """Error details model for API responses."""

    error_code: ErrorCode
    message: str
    severity: ErrorSeverity
    details: Dict[str, Any] = {}
    phone_number: Optional[str] = None
    platform: Optional[str] = None
    user_id: Optional[int] = None
    retry_after: Optional[int] = None
    suggested_action: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Complete error response model."""

    success: bool = False
    error: ErrorDetails
    request_id: Optional[str] = None
    timestamp: datetime


class ErrorHandler:
    """Centralized error handler for account creation system."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize error handler.

        Args:
            logger: Logger instance for error logging
        """
        self.logger = logger or logging.getLogger(__name__)

    def handle_validation_error(
        self,
        phone_number: str,
        validation_error: Exception,
        platform: Optional[str] = None
    ) -> ErrorResponse:
        """
        Handle phone number validation errors.

        Args:
            phone_number: Invalid phone number
            validation_error: Validation exception
            platform: Platform name

        Returns:
            Error response
        """
        masked_phone = self._mask_phone_number(phone_number)

        if "Invalid phone number format" in str(validation_error):
            error = ValidationError(
                message=f"Invalid phone number format: {masked_phone}",
                phone_number=phone_number,
                error_code=ErrorCode.INVALID_PHONE_FORMAT,
                details={"validation_error": str(validation_error)},
                suggested_format="Please use format: +221 XX XXX XX XX"
            )
        elif "not a mobile" in str(validation_error).lower():
            error = ValidationError(
                message=f"Phone number must be mobile: {masked_phone}",
                phone_number=phone_number,
                error_code=ErrorCode.PHONE_NOT_MOBILE,
                details={"validation_error": str(validation_error)},
                suggested_format="Please provide a mobile phone number"
            )
        else:
            error = ValidationError(
                message=f"Phone number validation failed: {masked_phone}",
                phone_number=phone_number,
                error_code=ErrorCode.INVALID_PHONE_NUMBER,
                details={"validation_error": str(validation_error)}
            )

        return self._create_error_response(error, platform)

    def handle_database_error(
        self,
        operation: str,
        error: Exception,
        table: Optional[str] = None,
        phone_number: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> ErrorResponse:
        """
        Handle database operation errors.

        Args:
            operation: Database operation that failed
            error: Database exception
            table: Table name
            phone_number: Related phone number
            user_id: Related user ID

        Returns:
            Error response
        """
        if "UNIQUE constraint failed" in str(error):
            error_code = ErrorCode.DUPLICATE_ACCOUNT
            message = "Account already exists for this phone number"
            severity = ErrorSeverity.LOW
        elif "FOREIGN KEY constraint failed" in str(error):
            error_code = ErrorCode.PARENT_NOT_FOUND
            message = "Parent not found in database"
            severity = ErrorSeverity.MEDIUM
        else:
            error_code = ErrorCode.DATABASE_ERROR
            message = "Database operation failed"
            severity = ErrorSeverity.HIGH

        db_error = DatabaseError(
            message=message,
            error_code=error_code,
            severity=severity,
            operation=operation,
            table=table,
            phone_number=phone_number,
            user_id=user_id,
            details={"database_error": str(error)}
        )

        return self._create_error_response(db_error)

    def handle_authentication_error(
        self,
        platform: str,
        error: Exception,
        client_ip: Optional[str] = None
    ) -> ErrorResponse:
        """
        Handle authentication errors.

        Args:
            platform: Platform name
            error: Authentication exception
            client_ip: Client IP address

        Returns:
            Error response
        """
        if "Rate limit" in str(error):
            error_code = ErrorCode.RATE_LIMIT_EXCEEDED
            message = "Too many requests. Please try again later."
            retry_after = 60  # 1 minute retry
        else:
            error_code = ErrorCode.UNAUTHORIZED
            message = f"Authentication failed for {platform}"
            retry_after = None

        auth_error = AuthenticationError(
            message=message,
            platform=platform,
            error_code=error_code,
            details={
                "auth_error": str(error),
                "client_ip": client_ip
            },
            retry_after=retry_after
        )

        return self._create_error_response(auth_error)

    def handle_business_logic_error(
        self,
        error: Exception,
        phone_number: Optional[str] = None,
        platform: Optional[str] = None,
        business_rule: Optional[str] = None
    ) -> ErrorResponse:
        """
        Handle business logic errors.

        Args:
            error: Business logic exception
            phone_number: Related phone number
            platform: Platform name
            business_rule: Business rule that was violated

        Returns:
            Error response
        """
        # Map common business logic errors
        error_mapping = {
            "parent not found": (ErrorCode.PARENT_NOT_FOUND, "Phone number not found in parent database"),
            "account creation failed": (ErrorCode.ACCOUNT_CREATION_FAILED, "Unable to create account"),
            "session expired": (ErrorCode.SESSION_EXPIRED, "Session has expired"),
            "consent required": (ErrorCode.CONSENT_REQUIRED, "Consent is required for account creation")
        }

        error_str = str(error).lower()
        error_code = ErrorCode.INTERNAL_ERROR
        message = "Business logic error occurred"

        for pattern, (code, msg) in error_mapping.items():
            if pattern in error_str:
                error_code = code
                message = msg
                break

        business_error = BusinessLogicError(
            message=message,
            error_code=error_code,
            severity=ErrorSeverity.MEDIUM,
            business_rule=business_rule,
            phone_number=phone_number,
            platform=platform,
            details={"business_error": str(error)}
        )

        return self._create_error_response(business_error)

    def handle_system_error(
        self,
        error: Exception,
        component: str,
        phone_number: Optional[str] = None,
        platform: Optional[str] = None
    ) -> ErrorResponse:
        """
        Handle unexpected system errors.

        Args:
            error: System exception
            component: Component where error occurred
            phone_number: Related phone number
            platform: Platform name

        Returns:
            Error response
        """
        system_error = AccountCreationError(
            message="An unexpected error occurred",
            error_code=ErrorCode.INTERNAL_ERROR,
            severity=ErrorSeverity.CRITICAL,
            phone_number=phone_number,
            platform=platform,
            details={
                "component": component,
                "system_error": str(error),
                "error_type": type(error).__name__
            },
            suggested_action="Please try again later or contact support"
        )

        return self._create_error_response(system_error)

    def _create_error_response(
        self,
        error: AccountCreationError,
        platform: Optional[str] = None
    ) -> ErrorResponse:
        """
        Create error response from exception.

        Args:
            error: Account creation exception
            platform: Platform name

        Returns:
            Error response
        """
        # Log the error
        self._log_error(error, platform)

        # Create error details
        error_details = ErrorDetails(
            error_code=error.error_code,
            message=error.message,
            severity=error.severity,
            details=error.details,
            phone_number=self._mask_phone_number(error.phone_number) if error.phone_number else None,
            platform=error.platform,
            user_id=error.user_id,
            retry_after=error.retry_after,
            suggested_action=error.suggested_action,
            timestamp=error.timestamp
        )

        # Create response
        response = ErrorResponse(
            error=error_details,
            timestamp=datetime.utcnow()
        )

        return response

    def _log_error(self, error: AccountCreationError, platform: Optional[str] = None):
        """Log error with appropriate level."""
        log_message = f"{error.error_code.value}: {error.message}"

        if error.phone_number:
            log_message += f" (phone: {self._mask_phone_number(error.phone_number)})"

        if error.platform:
            log_message += f" (platform: {error.platform})"

        if error.details:
            log_message += f" (details: {error.details})"

        # Choose log level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=True)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, exc_info=True)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, exc_info=True)
        else:
            self.logger.info(log_message, exc_info=True)

    def _mask_phone_number(self, phone_number: str) -> str:
        """Mask phone number for logging."""
        if not phone_number or len(phone_number) <= 6:
            return "***"
        return phone_number[:3] + "***" + phone_number[-3:]


class ErrorRecoveryStrategies:
    """Error recovery strategies for different error types."""

    @staticmethod
    def get_retry_strategy(error_code: ErrorCode) -> Dict[str, Any]:
        """
        Get retry strategy for error code.

        Args:
            error_code: Error code

        Returns:
            Retry strategy dictionary
        """
        strategies = {
            ErrorCode.RATE_LIMIT_EXCEEDED: {
                "should_retry": True,
                "retry_after": 60,
                "max_retries": 3,
                "backoff_factor": 2
            },
            ErrorCode.SERVICE_UNAVAILABLE: {
                "should_retry": True,
                "retry_after": 30,
                "max_retries": 5,
                "backoff_factor": 1.5
            },
            ErrorCode.EXTERNAL_SERVICE_ERROR: {
                "should_retry": True,
                "retry_after": 15,
                "max_retries": 3,
                "backoff_factor": 2
            },
            ErrorCode.DATABASE_ERROR: {
                "should_retry": False,
                "retry_after": None,
                "max_retries": 0,
                "backoff_factor": 1
            },
            ErrorCode.PARENT_NOT_FOUND: {
                "should_retry": False,
                "retry_after": None,
                "max_retries": 0,
                "backoff_factor": 1
            },
            ErrorCode.ACCOUNT_ALREADY_EXISTS: {
                "should_retry": False,
                "retry_after": None,
                "max_retries": 0,
                "backoff_factor": 1
            }
        }

        return strategies.get(
            error_code,
            {
                "should_retry": False,
                "retry_after": None,
                "max_retries": 0,
                "backoff_factor": 1
            }
        )

    @staticmethod
    def get_user_friendly_message(error_code: ErrorCode, platform: Optional[str] = None) -> str:
        """
        Get user-friendly error message.

        Args:
            error_code: Error code
            platform: Platform name

        Returns:
            User-friendly message
        """
        messages = {
            ErrorCode.INVALID_PHONE_FORMAT: "The phone number format is incorrect. Please use format: +221 XX XXX XX XX",
            ErrorCode.PHONE_NOT_MOBILE: "Please provide a mobile phone number",
            ErrorCode.PARENT_NOT_FOUND: "Your phone number was not found in our parent database. Please contact the catechism office.",
            ErrorCode.ACCOUNT_ALREADY_EXISTS: "You already have an account. Please continue with your existing account.",
            ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please wait a moment and try again.",
            ErrorCode.UNAUTHORIZED: "Authentication failed. Please try again.",
            ErrorCode.SERVICE_UNAVAILABLE: "The service is temporarily unavailable. Please try again later.",
            ErrorCode.INTERNAL_ERROR: "An unexpected error occurred. Please try again or contact support."
        }

        base_message = messages.get(error_code, "An error occurred. Please try again or contact support.")

        if platform:
            platform_names = {
                "telegram": "Telegram",
                "whatsapp": "WhatsApp"
            }
            platform_name = platform_names.get(platform, platform)
            return f"{base_message} (via {platform_name})"

        return base_message


# Global error handler instance
error_handler = ErrorHandler()


# Utility functions
def handle_exception(
    error: Exception,
    context: str,
    phone_number: Optional[str] = None,
    platform: Optional[str] = None
) -> ErrorResponse:
    """
    Handle exception and return appropriate error response.

    Args:
        error: Exception to handle
        context: Context where error occurred
        phone_number: Related phone number
        platform: Platform name

    Returns:
        Error response
    """
    try:
        if isinstance(error, AccountCreationError):
            return error_handler._create_error_response(error, platform)
        elif "phone" in context.lower() or "validation" in context.lower():
            return error_handler.handle_validation_error(
                phone_number or "unknown", error, platform
            )
        elif "database" in context.lower() or "db" in context.lower():
            return error_handler.handle_database_error(
                context, error, phone_number=phone_number
            )
        elif "auth" in context.lower() or "webhook" in context.lower():
            return error_handler.handle_authentication_error(
                platform or "unknown", error
            )
        elif "business" in context.lower():
            return error_handler.handle_business_logic_error(
                error, phone_number, platform
            )
        else:
            return error_handler.handle_system_error(
                error, context, phone_number, platform
            )
    except Exception as handling_error:
        # Fallback if error handling itself fails
        logging.error(f"Error in error handling: {str(handling_error)}")
        fallback_error = AccountCreationError(
            message="An unexpected error occurred",
            error_code=ErrorCode.INTERNAL_ERROR,
            severity=ErrorSeverity.CRITICAL
        )
        return error_handler._create_error_response(fallback_error)


def create_http_exception(error_response: ErrorResponse) -> HTTPException:
    """
    Create FastAPI HTTPException from error response.

    Args:
        error_response: Error response

    Returns:
        HTTPException
    """
    status_map = {
        ErrorCode.INVALID_PHONE_FORMAT: status.HTTP_400_BAD_REQUEST,
        ErrorCode.PHONE_NOT_MOBILE: status.HTTP_400_BAD_REQUEST,
        ErrorCode.PARENT_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ErrorCode.ACCOUNT_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
        ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    http_status = status_map.get(
        error_response.error.error_code,
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return HTTPException(
        status_code=http_status,
        detail=error_response.dict()
    )