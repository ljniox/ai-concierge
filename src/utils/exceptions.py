"""
Custom Exception Classes for Enrollment System

Provides structured error handling with specific exception types
for different error scenarios. Each exception includes error codes
and detailed messages for API responses.

Constitution Principle: Comprehensive error handling and logging
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class EnrollmentException(Exception):
    """Base exception for enrollment system."""

    def __init__(self, message: str, error_code: str = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(EnrollmentException):
    """Validation errors for input data."""

    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        self.field = field
        self.value = value
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class AuthenticationError(EnrollmentException):
    """Authentication and authorization errors."""

    def __init__(self, message: str, user_id: str = None, **kwargs):
        self.user_id = user_id
        details = kwargs.get('details', {})
        if user_id:
            details['user_id'] = user_id
        super().__init__(message, error_code="AUTHENTICATION_ERROR", details=details)


class PermissionError(EnrollmentException):
    """Permission and authorization errors."""

    def __init__(self, message: str, required_permission: str = None, user_role: str = None, **kwargs):
        self.required_permission = required_permission
        self.user_role = user_role
        details = kwargs.get('details', {})
        if required_permission:
            details['required_permission'] = required_permission
        if user_role:
            details['user_role'] = user_role
        super().__init__(message, error_code="PERMISSION_ERROR", details=details)


class SecurityError(AuthenticationError):
    """Security-related errors including rate limiting and validation."""

    def __init__(self, message: str, security_violation_type: str = None, **kwargs):
        self.security_violation_type = security_violation_type
        details = kwargs.get('details', {})
        if security_violation_type:
            details['security_violation_type'] = security_violation_type
        super().__init__(message, details=details)


class AuthorizationError(AuthenticationError):
    """Authorization errors for insufficient permissions."""

    def __init__(self, message: str, required_permission: str = None, current_role: str = None, **kwargs):
        self.required_permission = required_permission
        self.current_role = current_role
        details = kwargs.get('details', {})
        if required_permission:
            details['required_permission'] = required_permission
        if current_role:
            details['current_role'] = current_role
        super().__init__(message, details=details)


class OCRError(EnrollmentException):
    """OCR processing errors."""

    def __init__(self, message: str, document_id: str = None, file_type: str = None, **kwargs):
        self.document_id = document_id
        self.file_type = file_type
        details = kwargs.get('details', {})
        if document_id:
            details['document_id'] = document_id
        if file_type:
            details['file_type'] = file_type
        super().__init__(message, error_code="OCR_ERROR", details=details)


class DocumentError(EnrollmentException):
    """Document upload and processing errors."""

    def __init__(self, message: str, document_id: str = None, file_size: int = None, file_type: str = None, **kwargs):
        self.document_id = document_id
        self.file_size = file_size
        self.file_type = file_type
        details = kwargs.get('details', {})
        if document_id:
            details['document_id'] = document_id
        if file_size:
            details['file_size'] = file_size
        if file_type:
            details['file_type'] = file_type
        super().__init__(message, error_code="DOCUMENT_ERROR", details=details)


class PaymentError(EnrollmentException):
    """Payment processing errors."""

    def __init__(self, message: str, payment_id: str = None, montant: float = None, **kwargs):
        self.payment_id = payment_id
        self.montant = montant
        details = kwargs.get('details', {})
        if payment_id:
            details['payment_id'] = payment_id
        if montant:
            details['montant'] = montant
        super().__init__(message, error_code="PAYMENT_ERROR", details=details)


class DatabaseError(EnrollmentException):
    """Database operation errors."""

    def __init__(self, message: str, query: str = None, table: str = None, **kwargs):
        self.query = query
        self.table = table
        details = kwargs.get('details', {})
        if query:
            details['query'] = query
        if table:
            details['table'] = table
        super().__init__(message, error_code="DATABASE_ERROR", details=details)


class DatabaseConnectionError(DatabaseError):
    """Database connection errors."""

    def __init__(self, message: str, connection_details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, error_code="DATABASE_CONNECTION_ERROR", details=connection_details or {})


class StorageError(EnrollmentException):
    """File storage (MinIO) errors."""

    def __init__(self, message: str, bucket: str = None, file_path: str = None, **kwargs):
        self.bucket = bucket
        self.file_path = file_path
        details = kwargs.get('details', {})
        if bucket:
            details['bucket'] = bucket
        if file_path:
            details['file_path'] = file_path
        super().__init__(message, error_code="STORAGE_ERROR", details=details)


class CacheError(EnrollmentException):
    """Cache (Redis) operation errors."""

    def __init__(self, message: str, cache_key: str = None, operation: str = None, **kwargs):
        self.cache_key = cache_key
        self.operation = operation
        details = kwargs.get('details', {})
        if cache_key:
            details['cache_key'] = cache_key
        if operation:
            details['operation'] = operation
        super().__init__(message, error_code="CACHE_ERROR", details=details)


class CacheConnectionError(CacheError):
    """Cache connection errors."""

    def __init__(self, message: str, connection_details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, error_code="CACHE_CONNECTION_ERROR", details=connection_details or {})


class RateLimitError(EnrollmentException):
    """Rate limiting errors."""

    def __init__(self, message: str, limit: int = None, window_seconds: int = None, **kwargs):
        self.limit = limit
        self.window_seconds = window_seconds
        details = kwargs.get('details', {})
        if limit:
            details['limit'] = limit
        if window_seconds:
            details['window_seconds'] = window_seconds
        super().__init__(message, error_code="RATE_LIMIT_ERROR", details=details)


class ConfigurationError(EnrollmentException):
    """Configuration and environment errors."""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        self.config_key = config_key
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        super().__init__(message, error_code="CONFIGURATION_ERROR", details=details)


class LegacyDataError(EnrollmentException):
    """Legacy data migration and access errors."""

    def __init__(self, message: str, legacy_table: str = None, legacy_id: str = None, **kwargs):
        self.legacy_table = legacy_table
        self.legacy_id = legacy_id
        details = kwargs.get('details', {})
        if legacy_table:
            details['legacy_table'] = legacy_table
        if legacy_id:
            details['legacy_id'] = legacy_id
        super().__init__(message, error_code="LEGACY_DATA_ERROR", details=details)


class TemporaryPageError(EnrollmentException):
    """Temporary page generation and access errors."""

    def __init__(self, message: str, page_id: str = None, code_acces: str = None, **kwargs):
        self.page_id = page_id
        self.code_acces = code_acces
        details = kwargs.get('details', {})
        if page_id:
            details['page_id'] = page_id
        if code_acces:
            details['code_acces'] = code_acces
        super().__init__(message, error_code="TEMP_PAGE_ERROR", details=details)


class NotificationError(EnrollmentException):
    """WhatsApp/Telegram notification errors."""

    def __init__(self, message: str, channel: str = None, recipient: str = None, **kwargs):
        self.channel = channel
        self.recipient = recipient
        details = kwargs.get('details', {})
        if channel:
            details['channel'] = channel
        if recipient:
            details['recipient'] = recipient
        super().__init__(message, error_code="NOTIFICATION_ERROR", details=details)


class BusinessLogicError(EnrollmentException):
    """Business logic validation errors."""

    def __init__(self, message: str, business_rule: str = None, **kwargs):
        self.business_rule = business_rule
        details = kwargs.get('details', {})
        if business_rule:
            details['business_rule'] = business_rule
        super().__init__(message, error_code="BUSINESS_LOGIC_ERROR", details=details)


# ==============================================================================
# ACCOUNT CREATION SPECIFIC EXCEPTIONS
# ==============================================================================

class AccountCreationException(EnrollmentException):
    """Base exception for account creation errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code or "ACCOUNT_CREATION_ERROR", details)


class PhoneValidationError(AccountCreationException):
    """Exception raised for phone number validation errors."""

    def __init__(
        self,
        message: str,
        phone_number: Optional[str] = None,
        validation_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "PHONE_VALIDATION_ERROR", validation_details)
        self.phone_number = phone_number
        self.validation_details = validation_details or {}


class InvalidPhoneNumberFormatError(PhoneValidationError):
    """Exception raised for invalid phone number format."""

    def __init__(self, phone_number: str, valid_formats: Optional[list] = None):
        message = f"Invalid phone number format: {phone_number}"
        super().__init__(message, phone_number, {"valid_formats": valid_formats or []})


class UnsupportedCountryError(PhoneValidationError):
    """Exception raised for unsupported country codes."""

    def __init__(self, country_code: str, supported_countries: Optional[list] = None):
        message = f"Unsupported country code: {country_code}"
        super().__init__(message, country_code, {
            "supported_countries": supported_countries or [],
            "country_code": country_code
        })


class DuplicateAccountError(AccountCreationException):
    """Exception raised when attempting to create a duplicate account."""

    def __init__(self, phone_number: str, existing_user_id: Optional[str] = None):
        message = f"Account already exists for phone number: {phone_number}"
        super().__init__(message, "DUPLICATE_ACCOUNT", {
            "phone_number": phone_number,
            "existing_user_id": existing_user_id
        })
        self.phone_number = phone_number
        self.existing_user_id = existing_user_id


class ParentNotFoundError(AccountCreationException):
    """Exception raised when parent is not found in the catechism database."""

    def __init__(self, phone_number: str, lookup_details: Optional[Dict[str, Any]] = None):
        message = f"Parent not found in catechism database for phone number: {phone_number}"
        super().__init__(message, "PARENT_NOT_FOUND", {
            "phone_number": phone_number,
            **(lookup_details or {})
        })
        self.phone_number = phone_number


class SessionManagementError(AccountCreationException):
    """Exception raised for session management errors."""

    def __init__(self, message: str, session_id: Optional[str] = None, platform: Optional[str] = None):
        super().__init__(message, "SESSION_MANAGEMENT_ERROR", {
            "session_id": session_id,
            "platform": platform
        })
        self.session_id = session_id
        self.platform = platform


class SessionExpiredError(SessionManagementError):
    """Exception raised when session has expired."""

    def __init__(self, session_id: str, platform: str, expires_at: Optional[str] = None):
        message = f"Session {session_id} has expired"
        super().__init__(message, session_id, platform)
        self.expires_at = expires_at
        self.details["expires_at"] = expires_at


class WebhookSignatureError(AuthenticationError):
    """Exception raised for webhook signature verification errors."""

    def __init__(self, platform: str, signature_details: Optional[Dict[str, Any]] = None):
        message = f"Invalid webhook signature for {platform}"
        super().__init__(message, details=signature_details)
        self.platform = platform
        self.signature_details = signature_details or {}


class RoleManagementError(AccountCreationException):
    """Exception raised for role management errors."""

    def __init__(self, message: str, user_id: Optional[str] = None, role_name: Optional[str] = None):
        super().__init__(message, "ROLE_MANAGEMENT_ERROR", {
            "user_id": user_id,
            "role_name": role_name
        })
        self.user_id = user_id
        self.role_name = role_name


class ConsentError(AccountCreationException):
    """Exception raised for consent-related errors."""

    def __init__(self, message: str, consent_type: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(message, "CONSENT_ERROR", {
            "consent_type": consent_type,
            "user_id": user_id
        })
        self.consent_type = consent_type
        self.user_id = user_id


class DataRetentionError(AccountCreationException):
    """Exception raised for data retention errors."""

    def __init__(self, message: str, data_type: Optional[str] = None, retention_details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATA_RETENTION_ERROR", {
            "data_type": data_type,
            **(retention_details or {})
        })
        self.data_type = data_type


# Exception mapping for HTTP status codes
EXCEPTION_STATUS_MAP = {
    ValidationError: 400,
    AuthenticationError: 401,
    PermissionError: 403,
    RateLimitError: 429,
    OCRError: 422,
    DocumentError: 422,
    PaymentError: 422,
    TemporaryPageError: 422,
    BusinessLogicError: 422,
    PhoneValidationError: 400,
    DuplicateAccountError: 409,
    ParentNotFoundError: 404,
    SessionExpiredError: 401,
    WebhookSignatureError: 401,
    ConsentError: 400,
    DataRetentionError: 422,
    AccountCreationException: 422,
    DatabaseError: 500,
    StorageError: 500,
    ConfigurationError: 500,
    LegacyDataError: 500,
    NotificationError: 500,
    EnrollmentException: 500
}


def log_exception(exception: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log exception with context information.

    Args:
        exception: Exception instance
        context: Additional context information
    """
    context = context or {}

    if isinstance(exception, EnrollmentException):
        # Structured logging for custom exceptions
        logger.error(
            f"{exception.error_code}: {exception.message}",
            extra={
                'error_code': exception.error_code,
                'details': exception.details,
                'context': context,
                'exception_type': exception.__class__.__name__
            }
        )
    else:
        # Standard logging for other exceptions
        logger.error(
            f"Unexpected error: {str(exception)}",
            extra={
                'exception_type': exception.__class__.__name__,
                'context': context
            },
            exc_info=True
        )


def create_error_response(exception: Exception) -> Dict[str, Any]:
    """
    Create standardized error response for API.

    Args:
        exception: Exception instance

    Returns:
        Dict: Error response body
    """
    if isinstance(exception, EnrollmentException):
        return {
            'error': exception.error_code,
            'message': exception.message,
            'details': exception.details
        }
    else:
        return {
            'error': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'details': {
                'exception_type': exception.__class__.__name__
            }
        }


# Exception handler decorator
def handle_exceptions(log_context: Optional[Dict[str, Any]] = None):
    """
    Decorator for handling exceptions in service methods.

    Args:
        log_context: Context information for logging

    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except EnrollmentException as e:
                log_exception(e, log_context)
                raise  # Re-raise for API layer to handle
            except Exception as e:
                log_exception(e, log_context)
                # Wrap unexpected exceptions
                raise EnrollmentException(
                    message=f"Unexpected error in {func.__name__}: {str(e)}",
                    error_code="UNEXPECTED_ERROR",
                    details={'function': func.__name__, 'original_error': str(e)}
                ) from e

        return wrapper
    return decorator


# Validation helpers
def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present in data.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(
            message=f"Required fields missing: {', '.join(missing_fields)}",
            details={'missing_fields': missing_fields}
        )


def validate_email(email: str) -> None:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Raises:
        ValidationError: If email format is invalid
    """
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError(
            message="Invalid email format",
            field="email",
            value=email
        )


def validate_phone_number(phone: str) -> None:
    """
    Validate phone number format (E.164).

    Args:
        phone: Phone number to validate

    Raises:
        ValidationError: If phone format is invalid
    """
    import re
    # Basic E.164 validation
    e164_pattern = r'^\+[1-9]\d{1,14}$'
    if not re.match(e164_pattern, phone):
        raise ValidationError(
            message="Invalid phone number format. Use E.164 format (e.g., +221770000001)",
            field="telephone",
            value=phone
        )


# Account creation specific validation helpers
def validate_account_creation_data(data: Dict[str, Any]) -> None:
    """
    Validate account creation request data.

    Args:
        data: Account creation data to validate

    Raises:
        ValidationError: If validation fails
    """
    required_fields = ['phone_number', 'platform']
    validate_required_fields(data, required_fields)

    # Validate phone number format
    phone = data.get('phone_number', '').strip()
    if not phone:
        raise ValidationError(
            message="Phone number is required",
            field="phone_number"
        )

    try:
        validate_phone_number(phone)
    except ValidationError:
        # Convert to phone validation error
        raise PhoneValidationError(
            message="Invalid phone number format for account creation",
            phone_number=phone,
            validation_details={"field": "phone_number", "value": phone}
        )

    # Validate platform
    platform = data.get('platform', '').lower()
    if platform not in ['whatsapp', 'telegram']:
        raise ValidationError(
            message=f"Invalid platform: {platform}. Must be 'whatsapp' or 'telegram'",
            field="platform",
            value=platform
        )


def validate_role_assignment_data(data: Dict[str, Any]) -> None:
    """
    Validate role assignment request data.

    Args:
        data: Role assignment data to validate

    Raises:
        ValidationError: If validation fails
    """
    required_fields = ['user_id', 'role_name']
    validate_required_fields(data, required_fields)

    # Validate role name format
    role_name = data.get('role_name', '').strip()
    if not role_name or not re.match(r'^[a-z_][a-z0-9_]*$', role_name):
        raise ValidationError(
            message="Invalid role name format. Use lowercase, underscores, and alphanumeric characters",
            field="role_name",
            value=role_name
        )


def validate_session_data(data: Dict[str, Any]) -> None:
    """
    Validate session management data.

    Args:
        data: Session data to validate

    Raises:
        ValidationError: If validation fails
    """
    required_fields = ['platform', 'platform_user_id']
    validate_required_fields(data, required_fields)

    # Validate platform
    platform = data.get('platform', '').lower()
    if platform not in ['whatsapp', 'telegram']:
        raise ValidationError(
            message=f"Invalid platform: {platform}. Must be 'whatsapp' or 'telegram'",
            field="platform",
            value=platform
        )

    # Validate platform user ID
    platform_user_id = data.get('platform_user_id', '').strip()
    if not platform_user_id:
        raise ValidationError(
            message="Platform user ID is required",
            field="platform_user_id"
        )