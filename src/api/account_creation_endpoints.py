"""
Account Creation API Endpoints

This module provides REST API endpoints for manual account creation
with comprehensive validation, duplicate prevention, and error handling.
Enhanced for Phase 3 with complete account creation workflow.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

from src.services.account_service import get_account_service, AccountCreationRequest
from src.services.duplicate_prevention_service import get_duplicate_prevention_service
from src.services.user_role_assignment_service import get_user_role_assignment_service
from src.services.welcome_message_service import get_welcome_message_service
from src.services.phone_validation_service import get_phone_validation_service
from src.services.audit_service import log_account_creation_event
from src.utils.logging import get_logger
from src.utils.exceptions import (
    AccountCreationError,
    DuplicateAccountError,
    ValidationError,
    ParentNotFoundError
)


# Pydantic models for API requests and responses
class AccountCreationRequest(BaseModel):
    """Request model for account creation."""

    phone_number: str = Field(..., description="Phone number in E.164 format")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    email: Optional[str] = Field(None, description="Email address")
    parent_code: Optional[str] = Field(None, description="Parent code from catechism database")
    platform: str = Field("api", description="Platform source")
    user_consent: bool = Field(True, description="User consent for account creation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('phone_number')
    def validate_phone(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Phone number is required and must be valid')
        return v.strip()

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower().strip() if v else None


class AccountCreationResponse(BaseModel):
    """Response model for account creation."""

    success: bool
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = []
    created_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    welcome_message_sent: bool = False


class AccountLookupRequest(BaseModel):
    """Request model for account lookup."""

    phone_number: str = Field(..., description="Phone number to lookup")
    include_children: bool = Field(False, description="Include children information")
    include_session_info: bool = Field(False, description="Include session information")


class AccountLookupResponse(BaseModel):
    """Response model for account lookup."""

    found: bool
    account: Optional[Dict[str, Any]] = None
    children: Optional[List[Dict[str, Any]]] = None
    sessions: Optional[List[Dict[str, Any]]] = None
    parent_info: Optional[Dict[str, Any]] = None


class BulkAccountCreationRequest(BaseModel):
    """Request model for bulk account creation."""

    accounts: List[AccountCreationRequest] = Field(..., description="List of accounts to create")
    skip_duplicates: bool = Field(True, description="Skip duplicate accounts")
    send_welcome_messages: bool = Field(True, description="Send welcome messages")


class BulkAccountCreationResponse(BaseModel):
    """Response model for bulk account creation."""

    total_processed: int
    successful_creations: int
    failed_creations: int
    skipped_duplicates: int
    results: List[AccountCreationResponse]
    errors: List[str]


# Security
security = HTTPBearer()

# Initialize services
logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/accounts", tags=["Account Creation"])


# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user (placeholder for actual auth)."""
    # In production, implement proper JWT validation
    return {"user_id": "system", "roles": ["admin"]}


async def validate_admin_access(current_user: Dict = Depends(get_current_user)):
    """Validate admin access for sensitive operations."""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# API Endpoints

@router.post("/create", response_model=AccountCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: AccountCreationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(validate_admin_access)
):
    """
    Create a new user account.

    This endpoint creates a new user account with the provided information.
    It includes validation, duplicate prevention, role assignment, and welcome message sending.
    """
    try:
        logger.info(f"Account creation request for phone: {request.phone_number}")

        # Initialize services
        account_service = get_account_service()
        duplicate_service = get_duplicate_prevention_service()
        role_service = get_user_role_assignment_service()
        welcome_service = get_welcome_message_service()

        # Step 1: Validate phone number
        phone_validation = await get_phone_validation_service().validate_phone_number(
            request.phone_number
        )
        if not phone_validation.is_valid:
            return AccountCreationResponse(
                success=False,
                error_code="INVALID_PHONE",
                error_message=f"Invalid phone number: {phone_validation.error_message}"
            )

        normalized_phone = phone_validation.normalized_number

        # Step 2: Check for duplicates
        can_create, existing_account_id, duplicate_result = await duplicate_service.prevent_duplicate_creation(
            {
                "phone_number": normalized_phone,
                "platform": request.platform,
                "email": request.email,
                "first_name": request.first_name,
                "last_name": request.last_name
            }
        )

        if not can_create and existing_account_id:
            logger.info(f"Duplicate account prevented for phone: {normalized_phone}")
            return AccountCreationResponse(
                success=False,
                error_code="DUPLICATE_ACCOUNT",
                error_message="Account already exists for this phone number"
            )

        # Step 3: Create account creation request
        creation_request = AccountCreationRequest(
            phone_number=normalized_phone,
            platform=request.platform,
            user_consent=request.user_consent,
            source="api",
            metadata={
                "created_by": current_user.get("user_id"),
                "request_ip": "API_REQUEST",  # Would get from request in real implementation
                **(request.metadata or {})
            }
        )

        # Step 4: Create account
        creation_result = await account_service.create_account(creation_request)

        if not creation_result.success:
            logger.error(f"Account creation failed: {creation_result.error_message}")
            return AccountCreationResponse(
                success=False,
                error_code=creation_result.error_code or "CREATION_FAILED",
                error_message=creation_result.error_message
            )

        # Step 5: Assign default role
        user_account = creation_result.account
        role_result = await role_service.assign_default_role(
            user_account.id,
            platform=request.platform
        )

        # Step 6: Send welcome message in background
        welcome_sent = False
        if request.metadata and request.metadata.get("send_welcome", True):
            background_tasks.add_task(
                _send_welcome_message,
                user_account.id,
                request.platform,
                user_account.phone_number
            )
            welcome_sent = True

        # Log successful creation
        await log_account_creation_event(
            phone_number=normalized_phone,
            platform=request.platform,
            user_id=str(user_account.id),
            event_type="api_account_created",
            success=True,
            roles=["parent"]
        )

        logger.info(f"Account created successfully: {user_account.id}")

        return AccountCreationResponse(
            success=True,
            user_id=user_account.id,
            username=user_account.username,
            phone_number=user_account.phone_number,
            email=user_account.email,
            roles=user_account.roles,
            created_at=user_account.created_at,
            welcome_message_sent=welcome_sent
        )

    except ValidationError as e:
        logger.warning(f"Validation error in account creation: {str(e)}")
        return AccountCreationResponse(
            success=False,
            error_code="VALIDATION_ERROR",
            error_message=str(e)
        )

    except DuplicateAccountError as e:
        logger.warning(f"Duplicate account detected: {str(e)}")
        return AccountCreationResponse(
            success=False,
            error_code="DUPLICATE_ACCOUNT",
            error_message=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error in account creation: {str(e)}")
        return AccountCreationResponse(
            success=False,
            error_code="INTERNAL_ERROR",
            error_message="An internal error occurred"
        )


@router.post("/lookup", response_model=AccountLookupResponse)
async def lookup_account(
    request: AccountLookupRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Look up an existing account by phone number.

    This endpoint searches for an existing account and returns detailed information
    including children and session data if requested.
    """
    try:
        logger.info(f"Account lookup request for phone: {request.phone_number}")

        account_service = get_account_service()

        # Validate and normalize phone number
        phone_validation = await get_phone_validation_service().validate_phone_number(
            request.phone_number
        )
        if not phone_validation.is_valid:
            return AccountLookupResponse(
                found=False,
                error_code="INVALID_PHONE",
                error_message=f"Invalid phone number: {phone_validation.error_message}"
            )

        normalized_phone = phone_validation.normalized_number

        # Look up account
        account = await account_service.get_account_by_phone(normalized_phone)

        if not account:
            return AccountLookupResponse(found=False)

        # Convert account to dict
        account_dict = {
            "id": str(account.id),
            "username": account.username,
            "phone_number": account.phone_number,
            "email": account.email,
            "first_name": account.first_name,
            "last_name": account.last_name,
            "roles": account.roles,
            "created_at": account.created_at,
            "status": account.status.value,
            "created_via": account.created_via.value
        }

        result = AccountLookupResponse(
            found=True,
            account=account_dict
        )

        # Add children information if requested
        if request.include_children and account.parent_id:
            from src.services.parent_lookup_service import get_parent_lookup_service
            parent_service = get_parent_lookup_service()
            children = await parent_service.get_parent_children(account.parent_id)
            result.children = children

            # Also get parent information
            parent_info = await parent_service.find_parent_by_code(
                account.parent_code or ""
            )
            if parent_info:
                result.parent_info = parent_info

        # Add session information if requested
        if request.include_session_info:
            from src.services.session_management_service import get_session_management_service
            session_service = get_session_management_service()
            sessions = await session_service.get_user_sessions(account.id)
            result.sessions = [
                {
                    "id": str(session.id),
                    "platform": session.platform,
                    "status": session.status.value,
                    "created_at": session.created_at,
                    "last_activity_at": session.last_activity_at
                }
                for session in sessions
            ]

        logger.info(f"Account lookup successful: {account.id}")
        return result

    except Exception as e:
        logger.error(f"Error in account lookup: {str(e)}")
        return AccountLookupResponse(
            found=False,
            error_code="LOOKUP_ERROR",
            error_message="Failed to lookup account"
        )


@router.post("/bulk-create", response_model=BulkAccountCreationResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_accounts(
    request: BulkAccountCreationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(validate_admin_access)
):
    """
    Create multiple accounts in bulk.

    This endpoint allows creating multiple accounts at once with optional duplicate skipping
    and welcome message sending.
    """
    try:
        logger.info(f"Bulk account creation request: {len(request.accounts)} accounts")

        duplicate_service = get_duplicate_prevention_service()

        results = []
        successful = 0
        failed = 0
        skipped = 0
        errors = []

        for account_request in request.accounts:
            try:
                # Check for duplicates if requested
                if request.skip_duplicates:
                    can_create, existing_account_id, _ = await duplicate_service.prevent_duplicate_creation({
                        "phone_number": account_request.phone_number,
                        "platform": account_request.platform,
                        "email": account_request.email,
                        "first_name": account_request.first_name,
                        "last_name": account_request.last_name
                    })

                    if not can_create:
                        skipped += 1
                        results.append(AccountCreationResponse(
                            success=False,
                            error_code="DUPLICATE_SKIPPED",
                            error_message="Duplicate account skipped"
                        ))
                        continue

                # Create account
                result = await create_account(account_request, background_tasks, current_user)
                results.append(result)

                if result.success:
                    successful += 1
                else:
                    failed += 1
                    if result.error_message:
                        errors.append(f"{account_request.phone_number}: {result.error_message}")

            except Exception as e:
                failed += 1
                errors.append(f"{account_request.phone_number}: {str(e)}")
                results.append(AccountCreationResponse(
                    success=False,
                    error_code="BULK_CREATION_ERROR",
                    error_message=str(e)
                ))

        logger.info(f"Bulk creation completed: {successful} successful, {failed} failed, {skipped} skipped")

        return BulkAccountCreationResponse(
            total_processed=len(request.accounts),
            successful_creations=successful,
            failed_creations=failed,
            skipped_duplicates=skipped,
            results=results,
            errors=errors[:10]  # Limit errors in response
        )

    except Exception as e:
        logger.error(f"Error in bulk account creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk account creation failed"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for account creation service."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "service": "account_creation_api"
    }


@router.get("/stats")
async def get_creation_stats(
    days: int = 30,
    current_user: Dict = Depends(validate_admin_access)
):
    """
    Get account creation statistics.

    Returns statistics about account creation over the specified number of days.
    """
    try:
        # This would query the database for actual stats
        # For now, return mock data
        return {
            "period_days": days,
            "total_accounts_created": 150,
            "accounts_by_platform": {
                "whatsapp": 80,
                "telegram": 45,
                "api": 25
            },
            "accounts_by_status": {
                "active": 142,
                "inactive": 8
            },
            "duplicate_preventions": 15,
            "welcome_messages_sent": 135
        }

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )


# Background task functions
async def _send_welcome_message(user_id: UUID, platform: str, phone_number: str):
    """Send welcome message in background."""
    try:
        welcome_service = get_welcome_message_service()

        await welcome_service.send_welcome_message(
            user_id=user_id,
            platform=platform,
            platform_user_id=phone_number,  # For API-created accounts, use phone as platform ID
            language="fr"  # Default to French
        )

        logger.info(f"Welcome message sent to user {user_id}")

    except Exception as e:
        logger.error(f"Failed to send welcome message to {user_id}: {str(e)}")


# Exception handlers
@router.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    return AccountCreationResponse(
        success=False,
        error_code="VALIDATION_ERROR",
        error_message=str(exc)
    )


@router.exception_handler(DuplicateAccountError)
async def duplicate_exception_handler(request, exc):
    """Handle duplicate account errors."""
    return AccountCreationResponse(
        success=False,
        error_code="DUPLICATE_ACCOUNT",
        error_message=str(exc)
    )


@router.exception_handler(ParentNotFoundError)
async def parent_not_found_handler(request, exc):
    """Handle parent not found errors."""
    return AccountCreationResponse(
        success=False,
        error_code="PARENT_NOT_FOUND",
        error_message=str(exc)
    )


# Helper functions
def format_error_response(error_code: str, message: str) -> Dict[str, Any]:
    """Format error response consistently."""
    return {
        "success": False,
        "error_code": error_code,
        "error_message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }