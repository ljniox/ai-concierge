"""
Account Service for Automatic Account Creation System

This service handles the core business logic for creating user accounts
based on phone number validation against the parent database.
Enhanced for Phase 3 with comprehensive account creation workflows.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
import json

# Import required models and services from Phase 2
from src.models.user_account import UserAccount, AccountStatus, CreatedVia
from src.models.user_session import UserSession, SessionStatus, SessionType
from src.models.account_creation_audit import AccountCreationAudit
from src.services.database_service import get_database_service
from src.services.phone_validation_service import get_phone_validation_service, PhoneNumberValidationResult
from src.services.auth_service import get_auth_service
from src.services.audit_service import log_account_creation_event
from src.utils.logging import get_logger
from src.utils.exceptions import (
    AccountCreationError,
    ValidationError,
    ParentNotFoundError,
    DuplicateAccountError,
    DatabaseConnectionError,
    SecurityError
)


# Data classes for account creation
class AccountCreationRequest:
    """Account creation request data structure."""

    def __init__(
        self,
        phone_number: str,
        platform: str = "unknown",
        platform_user_id: Optional[str] = None,
        user_consent: bool = False,
        source: str = "api",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.phone_number = phone_number
        self.platform = platform
        self.platform_user_id = platform_user_id
        self.user_consent = user_consent
        self.source = source
        self.metadata = metadata or {}


class AccountCreationResult:
    """Result of account creation attempt."""

    def __init__(
        self,
        success: bool = False,
        account: Optional[UserAccount] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.account = account
        self.error_code = error_code
        self.error_message = error_message
        self.created_at = datetime.now(timezone.utc)


class ParentLookupService:
    """Service for looking up parents in the database."""

    def __init__(self, database_service=None):
        """Initialize parent lookup service."""
        self.database_service = database_service or get_database_service()
        self.logger = logging.getLogger(__name__)

    async def find_parent_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Find parent in catechese database by phone number.

        Args:
            phone_number: Normalized phone number in E.164 format

        Returns:
            Parent data if found, None otherwise
        """
        try:
            # Clean phone number for matching (remove country code and special characters)
            clean_number = phone_number.replace('+221', '').replace('00221', '')
            clean_number = clean_number.replace(' ', '').replace('-', '').replace('.', '')

            query = """
            SELECT id, code_parent, nom, prenoms, telephone, email, adresse
            FROM parents
            WHERE REPLACE(REPLACE(REPLACE(telephone, ' ', ''), '-', ''), '+221', '') = ?
               OR REPLACE(REPLACE(REPLACE(telephone, ' ', ''), '-', ''), '00221', '') = ?
            LIMIT 1
            """

            # Use the new database service
            result = await self.database_service.fetch_one(
                query,
                (clean_number, clean_number),
                database_name='catechese'
            )

            if result:
                parent_data = dict(result)

                # Convert to expected format
                formatted_data = {
                    "parent_id": str(parent_data["id"]),
                    "parent_code": parent_data["code_parent"],
                    "first_name": parent_data.get("prenoms", "").split()[0] if parent_data.get("prenoms") else "",
                    "last_name": parent_data.get("nom", ""),
                    "phone_number": parent_data.get("telephone", ""),
                    "email": parent_data.get("email", ""),
                    "address": parent_data.get("adresse", ""),
                    "children_count": 0,  # Would need to be queried separately
                    "parish": "Unknown"  # Would need to be queried separately
                }

                self.logger.info(f"Parent found for phone {phone_number[:10]}***: {parent_data['id']}")

                return formatted_data
            else:
                self.logger.warning(f"No parent found for phone {phone_number[:10]}***")
                return None

        except Exception as e:
            self.logger.error(f"Error finding parent by phone: {str(e)}")
            return None


class AccountCreationService:
    """Service for creating accounts."""

    def __init__(self, database_service=None):
        """Initialize account creation service."""
        self.database_service = database_service or get_database_service()
        self.logger = logging.getLogger(__name__)

    async def create_account(self, account_data: Dict[str, Any]) -> Optional[UserAccount]:
        """
        Create new user account.

        Args:
            account_data: Account creation data

        Returns:
            Created account if successful, None otherwise
        """
        try:
            import uuid

            # Generate username from parent data or phone number
            phone_number = account_data.get("phone_number", "")
            parent_id = account_data.get("parent_id", "")

            # Create a meaningful username
            if parent_id:
                username = f"parent_{parent_id}"
            else:
                # Extract last 4 digits of phone number as username
                clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
                username = f"user_{clean_phone[-4:]}" if len(clean_phone) >= 4 else f"user_{hash(phone_number) % 10000}"

            # Create UserAccount with proper Phase 2 structure
            user_account = UserAccount(
                id=uuid.uuid4(),  # Generate UUID primary key
                username=username,
                phone_number=phone_number,
                parent_id=parent_id,
                parent_code=account_data.get("parent_code"),
                first_name=account_data.get("first_name"),
                last_name=account_data.get("last_name"),
                email=account_data.get("email"),
                roles=["parent"],
                is_active=True,
                status=AccountStatus.ACTIVE,
                created_via=CreatedVia[account_data.get("platform", "API").upper()] if account_data.get("platform") else CreatedVia.API,
                metadata=account_data.get("metadata", {}),
                created_at=datetime.now(timezone.utc)
            )

            # Save to database using the new database service
            account_dict = user_account.to_dict()
            await self.database_service.insert(
                "user_accounts",
                account_dict,
                database_name="supabase"
            )

            self.logger.info(f"Account created successfully: {user_account.username} ({user_account.phone_number})")
            return user_account

        except Exception as e:
            self.logger.error(f"Failed to create account: {str(e)}")
            return None

    async def get_account_by_phone(self, phone_number: str) -> Optional[UserAccount]:
        """
        Get account by phone number.

        Args:
            phone_number: Phone number to search for

        Returns:
            User account if found, None otherwise
        """
        try:
            query = "SELECT * FROM user_accounts WHERE phone_number = ? AND is_deleted = FALSE"
            result = await self.database_service.fetch_one(
                query,
                (phone_number,),
                database_name="supabase"
            )

            if result:
                account_dict = dict(result)
                return UserAccount(**account_dict)

            return None

        except Exception as e:
            self.logger.error(f"Error getting account by phone: {str(e)}")
            return None

    async def link_platform_account(self, user_id: UUID, platform: str, platform_user_id: str) -> bool:
        """
        Link platform account to user.

        Args:
            user_id: User ID (UUID)
            platform: Platform name
            platform_user_id: Platform user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update user account with platform link
            update_data = {
                f"{platform}_user_id": platform_user_id,
                "updated_at": datetime.now(timezone.utc)
            }

            await self.database_service.update(
                "user_accounts",
                update_data,
                {"id": user_id},
                database_name="supabase"
            )

            self.logger.info(f"Linked {platform} account {platform_user_id[:10]}*** to user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to link platform account: {str(e)}")
            return False


class AccountService:
    """Service for managing user accounts and automatic account creation."""

    def __init__(
        self,
        phone_validator=None,
        parent_lookup=None,
        account_creation_service=None,
        database_service=None
    ):
        """
        Initialize the account service with Phase 2 services.

        Args:
            phone_validator: Phone validator instance
            parent_lookup: Parent lookup service instance
            account_creation_service: Account creation service instance
            database_service: Database service instance
        """
        self.phone_validator = phone_validator or get_phone_validation_service()
        self.database_service = database_service or get_database_service()
        self.parent_lookup = parent_lookup or ParentLookupService(self.database_service)
        self.account_creation_service = account_creation_service or AccountCreationService(self.database_service)
        self.logger = logging.getLogger(__name__)

    async def validate_phone_number(self, phone_number: str, country_code: str = "SN") -> PhoneNumberValidationResult:
        """
        Validate and normalize phone number using the phone validator.

        Args:
            phone_number: Phone number to validate
            country_code: Default country code (Senegal)

        Returns:
            PhoneNumberValidationResult with validation details

        Raises:
            ValidationError: If validation fails
        """
        try:
            if not self.phone_validator:
                raise ValidationError("Phone validator not configured", "VALIDATION_ERROR")

            result = await self.phone_validator.validate_phone_number(phone_number, country_code)

            if not result.is_valid:
                raise ValidationError(result.error_message or "Phone number validation failed", result.error_code or "VALIDATION_ERROR")

            return result

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Phone validation failed: {str(e)}")
            raise ValidationError(f"Phone validation failed: {str(e)}", "VALIDATION_ERROR")

    async def lookup_parent(self, phone_number: str) -> Dict[str, Any]:
        """
        Lookup parent by phone number.

        Args:
            phone_number: Phone number to lookup

        Returns:
            Parent data dictionary

        Raises:
            ParentNotFoundError: If parent not found
            AccountCreationError: If lookup fails
        """
        try:
            if not self.parent_lookup:
                raise AccountCreationError("Parent lookup service not configured")

            result = await self.parent_lookup.find_parent_by_phone(phone_number)

            if not result:
                raise ParentNotFoundError(f"Parent not found for phone number {phone_number}")

            return result

        except ParentNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Parent lookup failed: {str(e)}")
            raise AccountCreationError(f"Parent lookup failed: {str(e)}")

    async def create_account(self, request: AccountCreationRequest, max_retries: int = 1) -> AccountCreationResult:
        """
        Create account from request.

        Args:
            request: Account creation request
            max_retries: Maximum number of retries

        Returns:
            AccountCreationResult
        """
        try:
            # Step 1: Validate user consent
            if not request.user_consent:
                return AccountCreationResult(
                    success=False,
                    error_code="NO_USER_CONSENT",
                    error_message="User consent is required for account creation"
                )

            # Log account creation started
            await log_account_creation_event(
                phone_number=request.phone_number,
                source=request.source,
                platform_user_id=request.platform_user_id,
                event_type="account_creation_started"
            )

            # Step 2: Validate phone number
            try:
                phone_result = await self.validate_phone_number(request.phone_number)
            except ValidationError as e:
                return AccountCreationResult(
                    success=False,
                    error_code="INVALID_PHONE_FORMAT",
                    error_message=str(e)
                )

            normalized_phone = phone_result.normalized_number

            # Step 3: Check if account already exists
            if await self.account_exists(normalized_phone):
                return AccountCreationResult(
                    success=False,
                    error_code="ACCOUNT_ALREADY_EXISTS",
                    error_message="Account already exists for this phone number"
                )

            # Step 4: Lookup parent
            try:
                parent_data = await self.lookup_parent(normalized_phone)
            except ParentNotFoundError:
                return AccountCreationResult(
                    success=False,
                    error_code="PARENT_NOT_FOUND",
                    error_message="Parent not found for this phone number"
                )

            # Step 5: Create account
            account_data = {
                "phone_number": normalized_phone,
                "parent_id": parent_data["parent_id"],
                "platform": request.platform,
                "platform_user_id": request.platform_user_id,
                "source": request.source,
                "metadata": request.metadata
            }

            account = await self.account_creation_service.create_account(account_data)

            if account:
                # Log successful creation
                await log_account_creation_event(
                    phone_number=normalized_phone,
                    source=request.platform,
                    platform_user_id=request.platform_user_id,
                    event_type="account_creation_completed",
                    user_id=str(account.id),
                    roles=["parent"]
                )

                return AccountCreationResult(
                    success=True,
                    account=account
                )
            else:
                return AccountCreationResult(
                    success=False,
                    error_code="ACCOUNT_CREATION_ERROR",
                    error_message="Failed to create account"
                )

        except Exception as e:
            self.logger.error(f"Account creation failed: {str(e)}")
            return AccountCreationResult(
                success=False,
                error_code="ACCOUNT_CREATION_ERROR",
                error_message=f"Account creation failed: {str(e)}"
            )

    async def account_exists(self, phone_number: str) -> bool:
        """
        Check if account exists for phone number.

        Args:
            phone_number: Phone number to check

        Returns:
            True if account exists, False otherwise
        """
        try:
            if hasattr(self, 'account_creation_service') and self.account_creation_service:
                account = await self.account_creation_service.get_account_by_phone(phone_number)
                return account is not None
            else:
                # Use legacy method
                account = await self.get_account_by_phone(phone_number)
                return account is not None
        except Exception as e:
            self.logger.error(f"Error checking account existence: {str(e)}")
            return False

    async def get_account_by_phone(self, phone_number: str) -> Optional[UserAccount]:
        """
        Get account by phone number.

        Args:
            phone_number: Phone number to search for

        Returns:
            User account if found, None otherwise
        """
        try:
            if hasattr(self, 'account_creation_service') and self.account_creation_service:
                return await self.account_creation_service.get_account_by_phone(phone_number)
            else:
                # Use legacy implementation
                return await self._legacy_get_account_by_phone(phone_number)
        except Exception as e:
            self.logger.error(f"Error getting account by phone: {str(e)}")
            return None

    async def link_platform_account(self, user_id: UUID, platform: str, platform_user_id: str) -> bool:
        """
        Link platform account to existing user.

        Args:
            user_id: User ID
            platform: Platform name
            platform_user_id: Platform user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            if hasattr(self, 'account_creation_service') and self.account_creation_service:
                return await self.account_creation_service.link_platform_account(user_id, platform, platform_user_id)
            else:
                # Use legacy implementation
                return await self._legacy_link_platform_to_account(user_id, platform, platform_user_id)
        except Exception as e:
            self.logger.error(f"Error linking platform account: {str(e)}")
            return False

    async def validate_phone_numbers_batch(self, phone_numbers: List[str], country_code: Optional[str] = None) -> List[PhoneNumberValidationResult]:
        """
        Batch validate phone numbers.

        Args:
            phone_numbers: List of phone numbers to validate
            country_code: Country code for validation

        Returns:
            List of validation results
        """
        try:
            if not self.phone_validator:
                return [PhoneNumberValidationResult(
                    is_valid=False,
                    original_number=phone,
                    error_code="VALIDATION_ERROR",
                    error_message="Phone validator not configured"
                ) for phone in phone_numbers]

            return await self.phone_validator.validate_phone_numbers_batch(phone_numbers, country_code)
        except Exception as e:
            self.logger.error(f"Batch phone validation failed: {str(e)}")
            return [PhoneNumberValidationResult(
                is_valid=False,
                original_number=phone,
                error_code="VALIDATION_ERROR",
                error_message=f"Batch validation failed: {str(e)}"
            ) for phone in phone_numbers]

    async def create_accounts_batch(self, requests: List[AccountCreationRequest]) -> List[AccountCreationResult]:
        """
        Batch create accounts.

        Args:
            requests: List of account creation requests

        Returns:
            List of account creation results
        """
        results = []
        for request in requests:
            result = await self.create_account(request)
            results.append(result)
        return results

    # Utility methods
    def get_account_service_instance(self):
        """Get singleton instance of account service."""
        return self


# Factory function for getting account service instance
def get_account_service() -> AccountService:
    """Get account service instance with all dependencies."""
    return AccountService()


# Factory function for getting parent lookup service
def get_parent_lookup_service() -> ParentLookupService:
    """Get parent lookup service instance."""
    return ParentLookupService()


# Factory function for getting account creation service
def get_account_creation_service() -> AccountCreationService:
    """Get account creation service instance."""
    return AccountCreationService()