"""
Account Service for Automatic Account Creation System

This service handles the core business logic for creating user accounts
based on phone number validation against the parent database.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import phonenumbers
import sqlite3
import json

from src.models.account import (
    UserAccount, AccountCreationRequest, AccountCreationResponse,
    AccountLookupRequest, AccountLookupResponse, PlatformAccountLink,
    AccountStats, AccountSearchFilters, AccountSearchResponse,
    AccountQuery, PlatformAccount
)
from src.models.session import AccountCreationSession, AccountCreationState
from src.models.audit import AccountCreationAudit, AuditEventType, CreationStatus, PhoneValidationResult
from src.utils.logging import account_logger
from src.utils.phone_validator import PhoneNumberValidationResult
from src.utils.audit_logger import AuditLogger


# Custom exceptions for account creation
class AccountCreationError(Exception):
    """Base account creation error."""

    def __init__(self, message: str, error_code: str = "ACCOUNT_CREATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ParentNotFoundError(AccountCreationError):
    """Parent not found error."""

    def __init__(self, message: str = "Parent not found for phone number"):
        super().__init__(message, "PARENT_NOT_FOUND")


class AccountAlreadyExistsError(AccountCreationError):
    """Account already exists error."""

    def __init__(self, message: str = "Account already exists"):
        super().__init__(message, "ACCOUNT_ALREADY_EXISTS")


class ValidationError(AccountCreationError):
    """Validation error."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code)


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
        self.created_at = datetime.utcnow()


class ParentLookupService:
    """Service for looking up parents in the database."""

    def __init__(self, db_manager):
        """Initialize parent lookup service."""
        self.db_manager = db_manager
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

            async with self.db_manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (clean_number, clean_number))
                row = await cursor.fetchone()

                if row:
                    columns = [desc[0] for desc in cursor.description]
                    parent_data = dict(zip(columns, row))

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

    def __init__(self, db_manager):
        """Initialize account creation service."""
        self.db_manager = db_manager
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

            # Create UserAccount with proper structure
            user_account = UserAccount(
                id=hash(f"{phone_number}_{parent_id}_{datetime.utcnow().timestamp()}") % 1000000,  # Generate deterministic ID
                username=username,
                phone_number=phone_number,
                parent_id=parent_id,
                parent_code=account_data.get("parent_code"),
                first_name=account_data.get("first_name"),
                last_name=account_data.get("last_name"),
                email=account_data.get("email"),
                roles=["parent"],
                is_active=True,
                platform_accounts=[
                    PlatformAccount(
                        platform=account_data.get("platform", "unknown"),
                        platform_user_id=account_data.get("platform_user_id")
                    )
                ] if account_data.get("platform_user_id") else [],
                created_at=datetime.utcnow()
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
            # Implementation would query the database
            # For now, return None
            return None
        except Exception as e:
            self.logger.error(f"Error getting account by phone: {str(e)}")
            return None

    async def link_platform_account(self, user_id: int, platform: str, platform_user_id: str) -> bool:
        """
        Link platform account to user.

        Args:
            user_id: User ID
            platform: Platform name
            platform_user_id: Platform user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Implementation would update the database
            # For now, return True
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
        audit_logger=None,
        db_manager=None,
        redis_client=None
    ):
        """
        Initialize the account service.

        Args:
            phone_validator: Phone validator instance
            parent_lookup: Parent lookup service instance
            audit_logger: Audit logger instance
            db_manager: Database manager instance (legacy support)
            redis_client: Optional Redis client for caching (legacy support)
        """
        self.phone_validator = phone_validator
        self.parent_lookup = parent_lookup
        self.audit_logger = audit_logger
        self.db_manager = db_manager
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

        # For backward compatibility, create services if not provided
        if not self.parent_lookup and db_manager:
            self.parent_lookup = ParentLookupService(db_manager)
        if not self.account_creation_service and db_manager:
            self.account_creation_service = AccountCreationService(db_manager)

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
            if self.audit_logger:
                await self.audit_logger.log_account_creation_started(
                    request.phone_number,
                    request.source,
                    request.platform_user_id
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
                if self.audit_logger:
                    await self.audit_logger.log_account_creation_completed(
                        account.id,
                        normalized_phone,
                        request.platform,
                        request.platform_user_id,
                        ["parent"]
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

    async def link_platform_account(self, user_id: int, platform: str, platform_user_id: str) -> bool:
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

    # Legacy methods for backward compatibility
    async def _legacy_get_account_by_phone(self, phone_number: str) -> Optional[UserAccount]:

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

            async with self.db_manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (clean_number, clean_number))
                row = await cursor.fetchone()

                if row:
                    columns = [desc[0] for desc in cursor.description]
                    parent_data = dict(zip(columns, row))

                    self.logger.info(f"Parent found for phone {phone_number[:10]}***: {parent_data['id']}")
                    account_logger.log_parent_database_lookup(
                        phone_number,
                        parent_found=True,
                        parent_id=parent_data['id']
                    )

                    return parent_data
                else:
                    self.logger.warning(f"No parent found for phone {phone_number[:10]}***")
                    account_logger.log_parent_database_lookup(
                        phone_number,
                        parent_found=False
                    )

                    return None

        except Exception as e:
            self.logger.error(f"Error finding parent by phone: {str(e)}")
            account_logger.log_parent_database_lookup(
                phone_number,
                parent_found=False
            )
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
            async with self.db_manager.get_connection('core') as conn:
                cursor = await conn.execute(AccountQuery.select_by_phone_sql(), (phone_number,))
                row = await cursor.fetchone()

                if row:
                    columns = [desc[0] for desc in cursor.description]
                    account_dict = dict(zip(columns, row))

                    # Parse roles
                    if account_dict.get('roles'):
                        account_dict['roles'] = account_dict['roles'].split(',')
                    else:
                        account_dict['roles'] = []

                    return UserAccount(**account_dict)

            return None

        except Exception as e:
            self.logger.error(f"Error getting account by phone: {str(e)}")
            return None

    async def get_account_by_platform(self, platform: str, platform_user_id: str) -> Optional[UserAccount]:
        """
        Get account by platform user ID.

        Args:
            platform: Platform name ('telegram' or 'whatsapp')
            platform_user_id: Platform-specific user ID

        Returns:
            User account if found, None otherwise
        """
        try:
            # Choose the appropriate query based on platform
            if platform == 'telegram':
                query = AccountQuery.select_by_platform_sql()
            elif platform == 'whatsapp':
                query = AccountQuery.select_by_whatsapp_platform_sql()
            else:
                raise ValueError(f"Unsupported platform: {platform}")

            async with self.db_manager.get_connection('core') as conn:
                cursor = await conn.execute(query, (platform_user_id,))
                row = await cursor.fetchone()

                if row:
                    columns = [desc[0] for desc in cursor.description]
                    account_dict = dict(zip(columns, row))

                    # Parse roles
                    if account_dict.get('roles'):
                        account_dict['roles'] = account_dict['roles'].split(',')
                    else:
                        account_dict['roles'] = []

                    return UserAccount(**account_dict)

            return None

        except Exception as e:
            self.logger.error(f"Error getting account by platform: {str(e)}")
            return None

    async def create_account(self, account_data: Dict[str, Any]) -> Optional[UserAccount]:
        """
        Create new user account.

        Args:
            account_data: Account creation data

        Returns:
            Created account if successful, None otherwise
        """
        start_time = datetime.utcnow()

        try:
            # Start transaction
            async with self.db_manager.get_connection('core') as conn:
                # Check for existing account with same phone number
                existing = await self.get_account_by_phone(account_data['phone_number'])
                if existing:
                    self.logger.warning(f"Account already exists for phone {account_data['phone_number'][:10]}***")
                    await self._log_account_creation_event({
                        'phone_number': account_data['phone_number'],
                        'creation_status': CreationStatus.BLOCKED,
                        'creation_source': account_data['created_via'],
                        'error_message': 'Account already exists',
                        'parent_match_found': account_data.get('parent_id') is not None,
                        'parent_id': account_data.get('parent_id'),
                        'processing_time_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    })
                    return existing

                # Insert new account
                cursor = await conn.execute(AccountQuery.insert_account_sql(), (
                    account_data.get('parent_id'),
                    account_data['phone_number'],
                    account_data['phone_country_code'],
                    account_data['phone_national_number'],
                    account_data.get('username'),
                    account_data.get('full_name'),
                    account_data.get('email'),
                    account_data['created_via'],
                    account_data.get('telegram_user_id'),
                    account_data.get('whatsapp_user_id'),
                    account_data.get('consent_given', False),
                    account_data.get('consent_date')
                ))

                user_id = cursor.lastrowid

                # Assign parent role by default
                await self._assign_default_role(conn, user_id, 'parent')

                await conn.commit()

                # Get created account data
                account = await self.get_account_by_phone(account_data['phone_number'])

                if account:
                    processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                    # Log successful creation
                    await self._log_account_creation_event({
                        'user_id': user_id,
                        'phone_number': account_data['phone_number'],
                        'creation_status': CreationStatus.SUCCESS,
                        'creation_source': account_data['created_via'],
                        'parent_match_found': account_data.get('parent_id') is not None,
                        'parent_id': account_data.get('parent_id'),
                        'processing_time_ms': processing_time
                    })

                    account_logger.log_account_created(
                        user_id=user_id,
                        phone_number=account_data['phone_number'],
                        roles=['parent'],
                        source=account_data['created_via']
                    )

                    self.logger.info(f"Account created successfully: user_id={user_id}, phone={account_data['phone_number'][:10]}***")
                    return account
                else:
                    raise Exception("Failed to retrieve created account")

        except Exception as e:
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            error_message = str(e)

            self.logger.error(f"Account creation failed: {error_message}")

            # Log failed creation
            await self._log_account_creation_event({
                'phone_number': account_data['phone_number'],
                'creation_status': CreationStatus.FAILED,
                'creation_source': account_data['created_via'],
                'error_message': error_message,
                'parent_match_found': account_data.get('parent_id') is not None,
                'parent_id': account_data.get('parent_id'),
                'processing_time_ms': processing_time
            })

            account_logger.log_account_creation_failed(
                phone_number=account_data['phone_number'],
                error_type='creation_failed',
                error_message=error_message,
                source=account_data['created_via']
            )

            return None

    async def attempt_account_creation(
        self,
        platform: str,
        platform_user_id: str,
        phone_number: str,
        contact_name: Optional[str] = None
    ) -> AccountCreationResponse:
        """
        Attempt to create account from platform interaction.

        Args:
            platform: Platform name ('telegram' or 'whatsapp')
            platform_user_id: Platform-specific user ID
            phone_number: Phone number from platform
            contact_name: Optional contact name

        Returns:
            Account creation response
        """
        start_time = datetime.utcnow()

        try:
            # Log webhook received
            account_logger.log_webhook_received(platform, platform_user_id, 'account_creation_attempt')

            # Step 1: Validate phone number
            validation = await self.validate_phone_number(phone_number)
            if not validation['is_valid']:
                return AccountCreationResponse(
                    success=False,
                    error_code="INVALID_PHONE",
                    message=f"Invalid phone number: {validation['error']}"
                )

            normalized_phone = validation['e164']

            # Step 2: Check if account already exists
            existing_account = await self.get_account_by_phone(normalized_phone)
            if existing_account:
                # Link platform to existing account
                await self._link_platform_to_account(
                    existing_account.id, platform, platform_user_id
                )

                account_logger.log_duplicate_account_prevented(
                    phone_number=normalized_phone,
                    existing_user_id=existing_account.id
                )

                return AccountCreationResponse(
                    success=True,
                    user_id=existing_account.id,
                    account_id=existing_account.id,
                    phone_number=normalized_phone,
                    username=existing_account.username,
                    full_name=existing_account.full_name,
                    is_active=existing_account.is_active,
                    created_at=existing_account.created_at,
                    roles=existing_account.roles,
                    message="Account already exists. Platform linked successfully."
                )

            # Step 3: Find parent in database
            parent_info = await self.find_parent_by_phone(normalized_phone)
            if not parent_info:
                return AccountCreationResponse(
                    success=False,
                    error_code="PARENT_NOT_FOUND",
                    message="Phone number not found in parent database. Please contact the catechism office."
                )

            # Step 4: Create new account
            account_data = {
                'phone_number': normalized_phone,
                'phone_country_code': validation['country_code'],
                'phone_national_number': validation['national_number'],
                'created_via': platform,
                f'{platform}_user_id': platform_user_id,
                'full_name': contact_name or f"{parent_info.get('prenoms', '')} {parent_info.get('nom', '')}".strip(),
                'parent_id': parent_info['id'],
                'consent_given': True,
                'consent_date': datetime.utcnow().isoformat()
            }

            account = await self.create_account(account_data)

            if account:
                return AccountCreationResponse(
                    success=True,
                    user_id=account.id,
                    account_id=account.id,
                    phone_number=normalized_phone,
                    username=account.username,
                    full_name=account.full_name,
                    is_active=account.is_active,
                    created_at=account.created_at,
                    roles=account.roles,
                    platform_links={
                        'platform': platform,
                        'platform_user_id': platform_user_id
                    },
                    message="Account created successfully. Welcome to the catechism service!"
                )
            else:
                return AccountCreationResponse(
                    success=False,
                    error_code="CREATION_FAILED",
                    message="Failed to create account. Please try again later."
                )

        except Exception as e:
            self.logger.error(f"Account creation attempt failed: {str(e)}")
            return AccountCreationResponse(
                success=False,
                error_code="SYSTEM_ERROR",
                message="A system error occurred. Please try again later."
            )

    async def _assign_default_role(self, conn, user_id: int, role_name: str) -> None:
        """Assign default role to new user."""
        try:
            # Get role ID
            cursor = await conn.execute(
                "SELECT id FROM user_roles WHERE role_name = ? AND is_active = 1",
                (role_name,)
            )
            role_row = await cursor.fetchone()

            if role_row:
                role_id = role_row[0]

                # Insert role assignment
                await conn.execute(
                    "INSERT INTO user_role_assignments (user_id, role_id) VALUES (?, ?)",
                    (user_id, role_id)
                )

                self.logger.info(f"Assigned role '{role_name}' to user {user_id}")

        except Exception as e:
            self.logger.error(f"Failed to assign default role: {str(e)}")

    async def _link_platform_to_account(self, user_id: int, platform: str, platform_user_id: str) -> None:
        """Link platform account to existing user."""
        try:
            platform_field = f"{platform}_user_id"

            async with self.db_manager.get_connection('core') as conn:
                await conn.execute(f"""
                    UPDATE user_accounts
                    SET {platform_field} = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, platform_user_id, user_id)

                await conn.commit()

            account_logger.log_platform_account_linked(user_id, platform, platform_user_id)
            self.logger.info(f"Linked {platform} account {platform_user_id[:10]}*** to user {user_id}")

        except Exception as e:
            self.logger.error(f"Failed to link platform account: {str(e)}")

    async def _log_account_creation_event(self, event_data: Dict[str, Any]) -> None:
        """Log account creation event to audit table."""
        try:
            async with self.db_manager.get_connection('core') as conn:
                await conn.execute("""
                    INSERT INTO account_creation_audit (
                        user_id, phone_number, phone_validation_result,
                        parent_match_found, parent_id, creation_status,
                        creation_source, webhook_data, error_message,
                        processing_time_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_data.get('user_id'),
                    event_data['phone_number'],
                    event_data.get('phone_validation_result', 'valid'),
                    event_data.get('parent_match_found', False),
                    event_data.get('parent_id'),
                    event_data['creation_status'],
                    event_data['creation_source'],
                    event_data.get('webhook_data'),
                    event_data.get('error_message'),
                    event_data.get('processing_time_ms')
                ))
                await conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to log account creation event: {str(e)}")

    def _get_timezone_for_country_code(self, country_code: int) -> str:
        """Get timezone for country code."""
        # Map common country codes to timezones
        timezone_map = {
            221: 'Africa/Dakar',  # Senegal
            33: 'Europe/Paris',   # France
            1: 'America/New_York',  # USA
            44: 'Europe/London',  # UK
        }
        return timezone_map.get(country_code, 'UTC')

    # Additional utility methods will be added here as needed