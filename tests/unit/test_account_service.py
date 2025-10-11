"""
Unit Tests for Account Creation Service

This test suite validates the account creation service functionality,
including phone validation, parent lookup, account creation, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timedelta
import asyncio

from src.services.account_service import (
    AccountService,
    AccountCreationError,
    ParentNotFoundError,
    AccountAlreadyExistsError,
    ValidationError,
    ParentLookupService,
    AccountCreationService
)
from src.models.account import (
    UserAccount,
    AccountCreationRequest,
    AccountCreationResult,
    PlatformAccount
)
from src.models.audit import AccountCreationAudit
from src.utils.phone_validator import PhoneValidator, PhoneNumberValidationResult
from src.utils.audit_logger import AuditLogger
from src.utils.account_errors import (
    AccountCreationErrorCode,
    AccountErrorMessage,
    RecoveryAction
)


class TestAccountService:
    """Test cases for AccountService class."""

    @pytest.fixture
    def mock_phone_validator(self):
        """Create mock phone validator."""
        validator = AsyncMock(spec=PhoneValidator)
        return validator

    @pytest.fixture
    def mock_parent_lookup(self):
        """Create mock parent lookup service."""
        lookup = AsyncMock(spec=ParentLookupService)
        return lookup

    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger."""
        logger = AsyncMock(spec=AuditLogger)
        return logger

    @pytest.fixture
    def account_service(self, mock_phone_validator, mock_parent_lookup, mock_audit_logger):
        """Create AccountService instance with mocked dependencies."""
        return AccountService(
            phone_validator=mock_phone_validator,
            parent_lookup=mock_parent_lookup,
            audit_logger=mock_audit_logger
        )

    @pytest.fixture
    def valid_phone_result(self):
        """Create valid phone validation result."""
        return PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221 76 500 55 55"
        )

    @pytest.fixture
    def invalid_phone_result(self):
        """Create invalid phone validation result."""
        return PhoneNumberValidationResult(
            is_valid=False,
            original_number="invalid",
            error_code="INVALID_FORMAT",
            error_message="Phone number format is invalid"
        )

    @pytest.fixture
    def parent_data(self):
        """Create sample parent data."""
        return {
            "parent_id": "parent_123",
            "parent_code": "PARENT001",
            "first_name": "Aliou",
            "last_name": "Diop",
            "phone_number": "+221765005555",
            "email": "aliou.diop@example.com",
            "children_count": 2,
            "parish": "Saint-Louis"
        }

    @pytest.fixture
    def account_creation_request(self):
        """Create sample account creation request."""
        return AccountCreationRequest(
            phone_number="+221765005555",
            platform="telegram",
            platform_user_id="telegram_user_123",
            source="webhook",
            user_consent=True,
            metadata={"chat_id": "chat_123"}
        )

    @pytest.fixture
    def expected_account(self):
        """Create expected user account."""
        return UserAccount(
            id=1,
            username="aliou_diop",
            phone_number="+221765005555",
            parent_id="parent_123",
            parent_code="PARENT001",
            first_name="Aliou",
            last_name="Diop",
            email="aliou.diop@example.com",
            roles=["parent"],
            is_active=True,
            platform_accounts=[
                PlatformAccount(
                    platform="telegram",
                    platform_user_id="telegram_user_123"
                )
            ]
        )


class TestPhoneValidation:
    """Test phone number validation functionality."""

    async def test_validate_phone_number_success(self, account_service, mock_phone_validator, valid_phone_result):
        """Test successful phone number validation."""
        # Setup
        mock_phone_validator.validate_phone_number.return_value = valid_phone_result

        # Execute
        result = await account_service.validate_phone_number("+221 76 500 55 55", country_code="SN")

        # Assert
        assert result.is_valid is True
        assert result.normalized_number == "+221765005555"
        assert result.country_code == "SN"
        mock_phone_validator.validate_phone_number.assert_called_once_with("+221 76 500 55 55", country_code="SN")

    async def test_validate_phone_number_failure(self, account_service, mock_phone_validator, invalid_phone_result):
        """Test failed phone number validation."""
        # Setup
        mock_phone_validator.validate_phone_number.return_value = invalid_phone_result

        # Execute and Assert
        with pytest.raises(ValidationError) as exc_info:
            await account_service.validate_phone_number("invalid", country_code="SN")

        assert "Phone number format is invalid" in str(exc_info.value)
        mock_phone_validator.validate_phone_number.assert_called_once_with("invalid", country_code="SN")

    async def test_validate_phone_number_without_country_code(self, account_service, mock_phone_validator, valid_phone_result):
        """Test phone validation without explicit country code."""
        # Setup
        mock_phone_validator.validate_phone_number.return_value = valid_phone_result

        # Execute
        result = await account_service.validate_phone_number("+221765005555")

        # Assert
        assert result.is_valid is True
        mock_phone_validator.validate_phone_number.assert_called_once_with("+221765005555", country_code="SN")

    async def test_validate_phone_number_exception_handling(self, account_service, mock_phone_validator):
        """Test exception handling during phone validation."""
        # Setup
        mock_phone_validator.validate_phone_number.side_effect = Exception("Validation service error")

        # Execute and Assert
        with pytest.raises(ValidationError) as exc_info:
            await account_service.validate_phone_number("+221765005555")

        assert "Phone validation failed" in str(exc_info.value)


class TestParentLookup:
    """Test parent lookup functionality."""

    async def test_lookup_parent_success(self, account_service, mock_parent_lookup, parent_data):
        """Test successful parent lookup."""
        # Setup
        mock_parent_lookup.find_parent_by_phone.return_value = parent_data

        # Execute
        result = await account_service.lookup_parent("+221765005555")

        # Assert
        assert result == parent_data
        mock_parent_lookup.find_parent_by_phone.assert_called_once_with("+221765005555")

    async def test_lookup_parent_not_found(self, account_service, mock_parent_lookup):
        """Test parent lookup when parent not found."""
        # Setup
        mock_parent_lookup.find_parent_by_phone.return_value = None

        # Execute and Assert
        with pytest.raises(ParentNotFoundError) as exc_info:
            await account_service.lookup_parent("+221999999999")

        assert "Parent not found for phone number" in str(exc_info.value)
        mock_parent_lookup.find_parent_by_phone.assert_called_once_with("+221999999999")

    async def test_lookup_parent_exception_handling(self, account_service, mock_parent_lookup):
        """Test exception handling during parent lookup."""
        # Setup
        mock_parent_lookup.find_parent_by_phone.side_effect = Exception("Database error")

        # Execute and Assert
        with pytest.raises(AccountCreationError) as exc_info:
            await account_service.lookup_parent("+221765005555")

        assert "Parent lookup failed" in str(exc_info.value)


class TestAccountCreation:
    """Test account creation functionality."""

    async def test_create_account_success(self, account_service, mock_phone_validator, mock_parent_lookup, mock_audit_logger, account_creation_request, parent_data, expected_account):
        """Test successful account creation."""
        # Setup
        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221 76 500 55 55"
        )
        mock_phone_validator.validate_phone_number.return_value = valid_phone_result
        mock_parent_lookup.find_parent_by_phone.return_value = parent_data

        # Mock account creation service
        with patch.object(account_service.account_creation_service, 'create_account', return_value=expected_account) as mock_create:
            # Execute
            result = await account_service.create_account(account_creation_request)

            # Assert
            assert result.success is True
            assert result.account == expected_account
            assert result.error_code is None
            assert result.error_message is None

            # Verify phone validation
            mock_phone_validator.validate_phone_number.assert_called_once()

            # Verify parent lookup
            mock_parent_lookup.find_parent_by_phone.assert_called_once_with("+221765005555")

            # Verify account creation
            mock_create.assert_called_once()

            # Verify audit logging
            mock_audit_logger.log_account_creation_started.assert_called_once()
            mock_audit_logger.log_account_creation_completed.assert_called_once()

    async def test_create_account_invalid_phone(self, account_service, mock_phone_validator, account_creation_request, invalid_phone_result):
        """Test account creation with invalid phone number."""
        # Setup
        mock_phone_validator.validate_phone_number.return_value = invalid_phone_result

        # Execute
        result = await account_service.create_account(account_creation_request)

        # Assert
        assert result.success is False
        assert result.account is None
        assert result.error_code == "INVALID_PHONE_FORMAT"
        assert "Phone number format is invalid" in result.error_message

    async def test_create_account_parent_not_found(self, account_service, mock_phone_validator, mock_parent_lookup, account_creation_request, valid_phone_result):
        """Test account creation when parent not found."""
        # Setup
        mock_phone_validator.validate_phone_number.return_value = valid_phone_result
        mock_parent_lookup.find_parent_by_phone.return_value = None

        # Execute
        result = await account_service.create_account(account_creation_request)

        # Assert
        assert result.success is False
        assert result.account is None
        assert result.error_code == "PARENT_NOT_FOUND"
        assert "Parent not found" in result.error_message

    async def test_create_account_already_exists(self, account_service, mock_phone_validator, mock_parent_lookup, account_creation_request, parent_data, valid_phone_result):
        """Test account creation when account already exists."""
        # Setup
        mock_phone_validator.validate_phone_number.return_value = valid_phone_result
        mock_parent_lookup.find_parent_by_phone.return_value = parent_data

        # Mock account exists check
        with patch.object(account_service, 'account_exists', return_value=True):
            # Execute
            result = await account_service.create_account(account_creation_request)

            # Assert
            assert result.success is False
            assert result.account is None
            assert result.error_code == "ACCOUNT_ALREADY_EXISTS"
            assert "Account already exists" in result.error_message

    async def test_create_account_no_consent(self, account_service, account_creation_request):
        """Test account creation without user consent."""
        # Setup
        account_creation_request.user_consent = False

        # Execute
        result = await account_service.create_account(account_creation_request)

        # Assert
        assert result.success is False
        assert result.account is None
        assert result.error_code == "NO_USER_CONSENT"
        assert "User consent is required" in result.error_message

    async def test_create_account_exception_handling(self, account_service, mock_phone_validator, account_creation_request, valid_phone_result):
        """Test exception handling during account creation."""
        # Setup
        mock_phone_validator.validate_phone_number.return_value = valid_phone_result
        mock_phone_validator.validate_phone_number.side_effect = Exception("Unexpected error")

        # Execute
        result = await account_service.create_account(account_creation_request)

        # Assert
        assert result.success is False
        assert result.account is None
        assert result.error_code == "ACCOUNT_CREATION_ERROR"
        assert "Account creation failed" in result.error_message


class TestAccountManagement:
    """Test account management functionality."""

    async def test_account_exists_true(self, account_service):
        """Test account existence check when account exists."""
        # Setup
        with patch.object(account_service.account_creation_service, 'get_account_by_phone', return_value=UserAccount(id=1, phone_number="+221765005555")):
            # Execute
            exists = await account_service.account_exists("+221765005555")

            # Assert
            assert exists is True

    async def test_account_exists_false(self, account_service):
        """Test account existence check when account doesn't exist."""
        # Setup
        with patch.object(account_service.account_creation_service, 'get_account_by_phone', return_value=None):
            # Execute
            exists = await account_service.account_exists("+221765005555")

            # Assert
            assert exists is False

    async def test_link_platform_account_success(self, account_service, expected_account):
        """Test successful platform account linking."""
        # Setup
        with patch.object(account_service.account_creation_service, 'link_platform_account', return_value=True) as mock_link:
            # Execute
            result = await account_service.link_platform_account(expected_account.id, "whatsapp", "whatsapp_user_456")

            # Assert
            assert result is True
            mock_link.assert_called_once_with(expected_account.id, "whatsapp", "whatsapp_user_456")

    async def test_link_platform_account_failure(self, account_service):
        """Test platform account linking failure."""
        # Setup
        with patch.object(account_service.account_creation_service, 'link_platform_account', return_value=False) as mock_link:
            # Execute
            result = await account_service.link_platform_account(1, "whatsapp", "whatsapp_user_456")

            # Assert
            assert result is False

    async def test_get_account_by_phone_success(self, account_service, expected_account):
        """Test getting account by phone number."""
        # Setup
        with patch.object(account_service.account_creation_service, 'get_account_by_phone', return_value=expected_account) as mock_get:
            # Execute
            result = await account_service.get_account_by_phone("+221765005555")

            # Assert
            assert result == expected_account
            mock_get.assert_called_once_with("+221765005555")

    async def test_get_account_by_phone_not_found(self, account_service):
        """Test getting account by phone number when not found."""
        # Setup
        with patch.object(account_service.account_creation_service, 'get_account_by_phone', return_value=None) as mock_get:
            # Execute
            result = await account_service.get_account_by_phone("+221999999999")

            # Assert
            assert result is None
            mock_get.assert_called_once_with("+221999999999")


class TestBatchOperations:
    """Test batch operations."""

    async def test_validate_phone_numbers_batch(self, account_service, mock_phone_validator):
        """Test batch phone number validation."""
        # Setup
        phone_numbers = ["+221765005555", "+221771234567", "invalid"]

        valid_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221765005555"
        )

        invalid_result = PhoneNumberValidationResult(
            is_valid=False,
            original_number="invalid",
            error_code="INVALID_FORMAT",
            error_message="Phone number format is invalid"
        )

        mock_phone_validator.validate_phone_numbers_batch.return_value = [valid_result, valid_result, invalid_result]

        # Execute
        results = await account_service.validate_phone_numbers_batch(phone_numbers)

        # Assert
        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is True
        assert results[2].is_valid is False
        mock_phone_validator.validate_phone_numbers_batch.assert_called_once_with(phone_numbers, country_code=None)

    async def test_create_accounts_batch(self, account_service, mock_phone_validator, mock_parent_lookup, account_creation_request, parent_data):
        """Test batch account creation."""
        # Setup
        requests = [
            account_creation_request,
            AccountCreationRequest(
                phone_number="+221771234567",
                platform="telegram",
                platform_user_id="telegram_user_456",
                source="webhook",
                user_consent=True
            )
        ]

        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221765005555"
        )

        mock_phone_validator.validate_phone_number.return_value = valid_phone_result
        mock_parent_lookup.find_parent_by_phone.return_value = parent_data

        expected_account = UserAccount(
            id=1,
            username="aliou_diop",
            phone_number="+221765005555",
            parent_id="parent_123",
            roles=["parent"],
            is_active=True
        )

        with patch.object(account_service.account_creation_service, 'create_account', return_value=expected_account):
            # Execute
            results = await account_service.create_accounts_batch(requests)

            # Assert
            assert len(results) == 2
            assert all(result.success for result in results)


class TestErrorHandling:
    """Test error handling and edge cases."""

    async def test_validation_error_handling(self, account_service):
        """Test ValidationError handling."""
        # Setup
        with patch.object(account_service.phone_validator, 'validate_phone_number', side_effect=ValidationError("Test error", "TEST_ERROR")):
            request = AccountCreationRequest(
                phone_number="+221765005555",
                platform="telegram",
                platform_user_id="test",
                source="test",
                user_consent=True
            )

            # Execute
            result = await account_service.create_account(request)

            # Assert
            assert result.success is False
            assert result.error_code == "TEST_ERROR"
            assert "Test error" in result.error_message

    async def test_parent_not_found_error_handling(self, account_service):
        """Test ParentNotFoundError handling."""
        # Setup
        with patch.object(account_service.phone_validator, 'validate_phone_number', return_value=PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221765005555"
        )), \
        patch.object(account_service.parent_lookup, 'find_parent_by_phone', side_effect=ParentNotFoundError("Parent not found")):

            request = AccountCreationRequest(
                phone_number="+221765005555",
                platform="telegram",
                platform_user_id="test",
                source="test",
                user_consent=True
            )

            # Execute
            result = await account_service.create_account(request)

            # Assert
            assert result.success is False
            assert result.error_code == "PARENT_NOT_FOUND"
            assert "Parent not found" in result.error_message

    async def test_database_error_handling(self, account_service):
        """Test database error handling."""
        # Setup
        with patch.object(account_service.phone_validator, 'validate_phone_number', return_value=PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221765005555"
        )), \
        patch.object(account_service.parent_lookup, 'find_parent_by_phone', side_effect=Exception("Database connection failed")):

            request = AccountCreationRequest(
                phone_number="+221765005555",
                platform="telegram",
                platform_user_id="test",
                source="test",
                user_consent=True
            )

            # Execute
            result = await account_service.create_account(request)

            # Assert
            assert result.success is False
            assert result.error_code == "ACCOUNT_CREATION_ERROR"
            assert "Account creation failed" in result.error_message


class TestIntegrationScenarios:
    """Test integration scenarios and complete workflows."""

    async def test_complete_successful_workflow(self, account_service, mock_phone_validator, mock_parent_lookup, mock_audit_logger, account_creation_request, parent_data):
        """Test complete successful account creation workflow."""
        # Setup
        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221 76 500 55 55"
        )

        expected_account = UserAccount(
            id=1,
            username="aliou_diop",
            phone_number="+221765005555",
            parent_id="parent_123",
            parent_code="PARENT001",
            first_name="Aliou",
            last_name="Diop",
            email="aliou.diop@example.com",
            roles=["parent"],
            is_active=True,
            platform_accounts=[
                PlatformAccount(
                    platform="telegram",
                    platform_user_id="telegram_user_123"
                )
            ]
        )

        mock_phone_validator.validate_phone_number.return_value = valid_phone_result
        mock_parent_lookup.find_parent_by_phone.return_value = parent_data

        with patch.object(account_service.account_creation_service, 'create_account', return_value=expected_account), \
             patch.object(account_service, 'account_exists', return_value=False):

            # Execute
            result = await account_service.create_account(account_creation_request)

            # Assert
            assert result.success is True
            assert result.account == expected_account

            # Verify complete workflow
            mock_phone_validator.validate_phone_number.assert_called_once()
            mock_parent_lookup.find_parent_by_phone.assert_called_once()
            mock_audit_logger.log_account_creation_started.assert_called_once()
            mock_audit_logger.log_account_creation_completed.assert_called_once()

    async def test_retry_after_error(self, account_service, mock_phone_validator, mock_parent_lookup, account_creation_request, parent_data):
        """Test retry logic after transient errors."""
        # Setup
        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221765005555"
        )

        mock_phone_validator.validate_phone_number.return_value = valid_phone_result
        mock_parent_lookup.find_parent_by_phone.return_value = parent_data

        # First call fails, second succeeds
        expected_account = UserAccount(id=1, phone_number="+221765005555")

        with patch.object(account_service.account_creation_service, 'create_account', side_effect=[Exception("Transient error"), expected_account]), \
             patch.object(account_service, 'account_exists', return_value=False):

            # Execute
            result = await account_service.create_account(account_creation_request, max_retries=2)

            # Assert
            assert result.success is True
            assert result.account == expected_account
            assert account_service.account_creation_service.create_account.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])