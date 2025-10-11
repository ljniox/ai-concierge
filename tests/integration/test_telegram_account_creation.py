"""
Integration Tests for Telegram Webhook Account Creation Flow

This test suite validates the complete Telegram webhook integration
for automatic account creation, including webhook processing, authentication,
phone number extraction, and account creation workflow.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import asyncio

from src.api.v1.telegram import router as telegram_router
from src.handlers.telegram_webhook import TelegramWebhookHandler
from src.services.account_service import AccountService, AccountCreationResult
from src.models.account import UserAccount, AccountCreationRequest
from src.models.session import AccountCreationSession
from src.middleware.auth import AuthManager
from src.utils.audit_logger import AuditLogger
from src.utils.phone_validator import PhoneNumberValidationResult


class TestTelegramWebhookIntegration:
    """Integration tests for Telegram webhook account creation."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(telegram_router)

    @pytest.fixture
    def mock_webhook_handler(self):
        """Create mock Telegram webhook handler."""
        handler = AsyncMock(spec=TelegramWebhookHandler)
        return handler

    @pytest.fixture
    def mock_account_service(self):
        """Create mock account service."""
        service = AsyncMock(spec=AccountService)
        return service

    @pytest.fixture
    def mock_auth_manager(self):
        """Create mock auth manager."""
        manager = AsyncMock(spec=AuthManager)
        return manager

    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger."""
        logger = AsyncMock(spec=AuditLogger)
        return logger

    @pytest.fixture
    def valid_telegram_webhook(self):
        """Create valid Telegram webhook payload."""
        return {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 221765005555,
                    "is_bot": False,
                    "first_name": "Aliou",
                    "last_name": "Diop",
                    "username": "aliou_diop",
                    "language_code": "fr"
                },
                "chat": {
                    "id": 221765005555,
                    "first_name": "Aliou",
                    "last_name": "Diop",
                    "username": "aliou_diop",
                    "type": "private"
                },
                "date": 1634567890,
                "text": "Bonjour, je suis un parent du catéchisme"
            }
        }

    @pytest.fixture
    def telegram_webhook_with_contact(self):
        """Create Telegram webhook payload with contact info."""
        return {
            "update_id": 123456789,
            "message": {
                "message_id": 2,
                "from": {
                    "id": 221765005555,
                    "is_bot": False,
                    "first_name": "Aliou",
                    "last_name": "Diop",
                    "username": "aliou_diop"
                },
                "chat": {
                    "id": 221765005555,
                    "first_name": "Aliou",
                    "last_name": "Diop",
                    "username": "aliou_diop",
                    "type": "private"
                },
                "date": 1634567890,
                "contact": {
                    "phone_number": "+221765005555",
                    "first_name": "Aliou",
                    "last_name": "Diop",
                    "user_id": 221765005555
                }
            }
        }

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
            created_at=datetime.utcnow()
        )


class TestWebhookAuthentication:
    """Test webhook authentication and security."""

    @patch('src.api.v1.telegram.auth_manager')
    async def test_webhook_authentication_success(self, mock_auth, client, valid_telegram_webhook):
        """Test successful webhook authentication."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "telegram"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_telegram_webhook,
            headers={"X-Telegram-Bot-Api-Secret-Token": "valid_secret"}
        )

        # Assert
        assert response.status_code == 200
        mock_auth.authenticate_webhook_request.assert_called_once()

    @patch('src.api.v1.telegram.auth_manager')
    async def test_webhook_authentication_failure(self, mock_auth, client, valid_telegram_webhook):
        """Test webhook authentication failure."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": False,
            "error": "Invalid webhook secret"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_telegram_webhook,
            headers={"X-Telegram-Bot-Api-Secret-Token": "invalid_secret"}
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid webhook secret" in response.json()["detail"]

    @patch('src.api.v1.telegram.auth_manager')
    async def test_webhook_rate_limiting(self, mock_auth, client, valid_telegram_webhook):
        """Test webhook rate limiting."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": False,
            "rate_limited": True,
            "error": "Rate limit exceeded"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_telegram_webhook,
            headers={"X-Telegram-Bot-Api-Secret-Token": "valid_secret"}
        )

        # Assert
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]


class TestPhoneNumberExtraction:
    """Test phone number extraction from Telegram messages."""

    @pytest.mark.asyncio
    async def test_extract_phone_from_contact_message(self, mock_webhook_handler, telegram_webhook_with_contact):
        """Test phone number extraction from contact message."""
        # Setup
        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(telegram_webhook_with_contact)

        # Assert
        assert phone_number == "+221765005555"
        mock_webhook_handler.extract_phone_number.assert_called_once_with(telegram_webhook_with_contact)

    @pytest.mark.asyncio
    async def test_extract_phone_from_text_message(self, mock_webhook_handler):
        """Test phone number extraction from text message."""
        # Setup
        message_with_phone = {
            "message": {
                "text": "Mon numéro est le +221 76 50 05 55",
                "from": {"id": 221765005555}
            }
        }
        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(message_with_phone)

        # Assert
        assert phone_number == "+221765005555"

    @pytest.mark.asyncio
    async def test_extract_phone_no_phone_found(self, mock_webhook_handler):
        """Test phone number extraction when no phone found."""
        # Setup
        message_without_phone = {
            "message": {
                "text": "Bonjour, comment allez-vous?",
                "from": {"id": 221765005555}
            }
        }
        mock_webhook_handler.extract_phone_number.return_value = None

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(message_without_phone)

        # Assert
        assert phone_number is None


class TestAccountCreationFlow:
    """Test complete account creation flow."""

    @pytest.mark.asyncio
    async def test_complete_account_creation_success(
        self,
        mock_webhook_handler,
        mock_account_service,
        mock_audit_logger,
        telegram_webhook_with_contact,
        expected_account
    ):
        """Test complete successful account creation flow."""
        # Setup
        phone_number = "+221765005555"
        platform_user_id = "221765005555"

        # Mock phone number extraction
        mock_webhook_handler.extract_phone_number.return_value = phone_number

        # Mock phone validation
        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number=phone_number,
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number=phone_number
        )
        mock_account_service.validate_phone_number.return_value = valid_phone_result

        # Mock account creation
        account_creation_result = AccountCreationResult(
            success=True,
            account=expected_account,
            error_code=None,
            error_message=None
        )
        mock_account_service.create_account.return_value = account_creation_result

        # Mock session creation
        mock_webhook_handler.create_account_creation_session.return_value = AccountCreationSession(
            session_id="session_123",
            platform="telegram",
            platform_user_id=platform_user_id,
            phone_number=phone_number,
            status="created"
        )

        # Execute
        result = await mock_webhook_handler.process_account_creation_flow(telegram_webhook_with_contact)

        # Assert
        assert result.success is True
        assert result.account == expected_account

        # Verify workflow calls
        mock_webhook_handler.extract_phone_number.assert_called_once()
        mock_account_service.validate_phone_number.assert_called_once_with(phone_number, country_code="SN")
        mock_account_service.create_account.assert_called_once()
        mock_audit_logger.log_account_creation_started.assert_called_once()
        mock_audit_logger.log_account_creation_completed.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_creation_invalid_phone(
        self,
        mock_webhook_handler,
        mock_account_service,
        telegram_webhook_with_contact
    ):
        """Test account creation with invalid phone number."""
        # Setup
        phone_number = "invalid_phone"

        mock_webhook_handler.extract_phone_number.return_value = phone_number

        invalid_phone_result = PhoneNumberValidationResult(
            is_valid=False,
            original_number=phone_number,
            error_code="INVALID_FORMAT",
            error_message="Phone number format is invalid"
        )
        mock_account_service.validate_phone_number.return_value = invalid_phone_result

        # Execute
        result = await mock_webhook_handler.process_account_creation_flow(telegram_webhook_with_contact)

        # Assert
        assert result.success is False
        assert result.error_code == "INVALID_PHONE_FORMAT"
        assert "Phone number format is invalid" in result.error_message

        # Verify audit logging
        mock_account_service.audit_logger.log_account_creation_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_creation_parent_not_found(
        self,
        mock_webhook_handler,
        mock_account_service,
        telegram_webhook_with_contact
    ):
        """Test account creation when parent not found."""
        # Setup
        phone_number = "+221765005555"

        mock_webhook_handler.extract_phone_number.return_value = phone_number

        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number=phone_number,
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number=phone_number
        )
        mock_account_service.validate_phone_number.return_value = valid_phone_result

        account_creation_result = AccountCreationResult(
            success=False,
            account=None,
            error_code="PARENT_NOT_FOUND",
            error_message="Parent not found for phone number"
        )
        mock_account_service.create_account.return_value = account_creation_result

        # Execute
        result = await mock_webhook_handler.process_account_creation_flow(telegram_webhook_with_contact)

        # Assert
        assert result.success is False
        assert result.error_code == "PARENT_NOT_FOUND"
        assert "Parent not found" in result.error_message

    @pytest.mark.asyncio
    async def test_account_creation_already_exists(
        self,
        mock_webhook_handler,
        mock_account_service,
        telegram_webhook_with_contact
    ):
        """Test account creation when account already exists."""
        # Setup
        phone_number = "+221765005555"

        mock_webhook_handler.extract_phone_number.return_value = phone_number

        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number=phone_number,
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number=phone_number
        )
        mock_account_service.validate_phone_number.return_value = valid_phone_result

        account_creation_result = AccountCreationResult(
            success=False,
            account=None,
            error_code="ACCOUNT_ALREADY_EXISTS",
            error_message="Account already exists"
        )
        mock_account_service.create_account.return_value = account_creation_result

        # Execute
        result = await mock_webhook_handler.process_account_creation_flow(telegram_webhook_with_contact)

        # Assert
        assert result.success is False
        assert result.error_code == "ACCOUNT_ALREADY_EXISTS"


class TestMessageResponses:
    """Test message response handling."""

    @pytest.mark.asyncio
    async def test_send_welcome_message_success(
        self,
        mock_webhook_handler,
        expected_account
    ):
        """Test sending welcome message after successful account creation."""
        # Setup
        platform_user_id = "221765005555"
        welcome_message = f"Bonjour {expected_account.first_name}! Votre compte a été créé avec succès."

        mock_webhook_handler.send_message.return_value = {"ok": True, "result": {"message_id": 123}}

        # Execute
        result = await mock_webhook_handler.send_welcome_message(platform_user_id, expected_account)

        # Assert
        assert result.success is True
        assert "message_id" in result.response
        mock_webhook_handler.send_message.assert_called_once_with(
            platform_user_id,
            welcome_message,
            parse_mode="HTML"
        )

    @pytest.mark.asyncio
    async def test_send_error_message(
        self,
        mock_webhook_handler
    ):
        """Test sending error message."""
        # Setup
        platform_user_id = "221765005555"
        error_message = "Désolé, nous n'avons pas pu créer votre compte."

        mock_webhook_handler.send_message.return_value = {"ok": True, "result": {"message_id": 124}}

        # Execute
        result = await mock_webhook_handler.send_error_message(platform_user_id, error_message)

        # Assert
        assert result.success is True
        mock_webhook_handler.send_message.assert_called_once_with(
            platform_user_id,
            error_message,
            parse_mode="HTML"
        )

    @pytest.mark.asyncio
    async def test_send_phone_request_message(
        self,
        mock_webhook_handler
    ):
        """Test sending phone number request message."""
        # Setup
        platform_user_id = "221765005555"

        mock_webhook_handler.send_message.return_value = {"ok": True, "result": {"message_id": 125}}

        # Execute
        result = await mock_webhook_handler.send_phone_request_message(platform_user_id)

        # Assert
        assert result.success is True
        mock_webhook_handler.send_message.assert_called_once()

        # Check that the message contains phone request
        call_args = mock_webhook_handler.send_message.call_args
        assert "numéro de téléphone" in call_args[0][1].lower()


class TestSessionManagement:
    """Test session management for account creation flow."""

    @pytest.mark.asyncio
    async def test_create_account_creation_session(
        self,
        mock_webhook_handler
    ):
        """Test creating account creation session."""
        # Setup
        platform = "telegram"
        platform_user_id = "221765005555"
        phone_number = "+221765005555"

        expected_session = AccountCreationSession(
            session_id="session_123",
            platform=platform,
            platform_user_id=platform_user_id,
            phone_number=phone_number,
            status="initiated"
        )

        mock_webhook_handler.session_service.create_session.return_value = expected_session

        # Execute
        session = await mock_webhook_handler.create_account_creation_session(
            platform,
            platform_user_id,
            phone_number
        )

        # Assert
        assert session == expected_session
        mock_webhook_handler.session_service.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_session(
        self,
        mock_webhook_handler
    ):
        """Test getting existing account creation session."""
        # Setup
        platform_user_id = "221765005555"

        existing_session = AccountCreationSession(
            session_id="session_456",
            platform="telegram",
            platform_user_id=platform_user_id,
            phone_number="+221765005555",
            status="phone_provided"
        )

        mock_webhook_handler.session_service.get_active_session.return_value = existing_session

        # Execute
        session = await mock_webhook_handler.get_existing_session(platform_user_id)

        # Assert
        assert session == existing_session
        assert session.status == "phone_provided"

    @pytest.mark.asyncio
    async def test_update_session_status(
        self,
        mock_webhook_handler
    ):
        """Test updating session status."""
        # Setup
        session_id = "session_123"
        new_status = "account_created"

        updated_session = AccountCreationSession(
            session_id=session_id,
            platform="telegram",
            platform_user_id="221765005555",
            phone_number="+221765005555",
            status=new_status
        )

        mock_webhook_handler.session_service.update_session_status.return_value = updated_session

        # Execute
        session = await mock_webhook_handler.update_session_status(session_id, new_status)

        # Assert
        assert session.status == new_status
        mock_webhook_handler.session_service.update_session_status.assert_called_once_with(session_id, new_status)


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_webhook_missing_required_fields(
        self,
        mock_webhook_handler
    ):
        """Test webhook processing with missing required fields."""
        # Setup
        incomplete_webhook = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                # Missing 'from' field
                "text": "Hello"
            }
        }

        # Execute
        result = await mock_webhook_handler.process_webhook(incomplete_webhook)

        # Assert
        assert result.success is False
        assert "missing" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_webhook_service_unavailable(
        self,
        mock_webhook_handler,
        mock_account_service
    ):
        """Test webhook processing when account service is unavailable."""
        # Setup
        webhook_data = {
            "message": {
                "from": {"id": 221765005555},
                "contact": {"phone_number": "+221765005555"}
            }
        }

        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"
        mock_account_service.validate_phone_number.side_effect = Exception("Service unavailable")

        # Execute
        result = await mock_webhook_handler.process_account_creation_flow(webhook_data)

        # Assert
        assert result.success is False
        assert "service unavailable" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_concurrent_account_creation(
        self,
        mock_webhook_handler,
        mock_account_service,
        telegram_webhook_with_contact
    ):
        """Test handling concurrent account creation requests."""
        # Setup
        phone_number = "+221765005555"
        platform_user_id = "221765005555"

        mock_webhook_handler.extract_phone_number.return_value = phone_number

        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number=phone_number,
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number=phone_number
        )
        mock_account_service.validate_phone_number.return_value = valid_phone_result

        # First request succeeds, second fails due to race condition
        expected_account = UserAccount(id=1, phone_number=phone_number)
        first_result = AccountCreationResult(success=True, account=expected_account)
        second_result = AccountCreationResult(success=False, error_code="ACCOUNT_ALREADY_EXISTS")

        mock_account_service.create_account.side_effect = [first_result, second_result]

        # Execute concurrent requests
        tasks = [
            mock_webhook_handler.process_account_creation_flow(telegram_webhook_with_contact),
            mock_webhook_handler.process_account_creation_flow(telegram_webhook_with_contact)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        assert len(results) == 2
        assert results[0].success is True  # First succeeds
        assert results[1].success is False  # Second fails with account already exists


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios."""

    @pytest.mark.asyncio
    async def test_complete_new_parent_registration(
        self,
        mock_webhook_handler,
        mock_account_service,
        mock_audit_logger
    ):
        """Test complete new parent registration workflow."""
        # Setup webhook data - parent sends message with contact
        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 221765005555,
                    "first_name": "Aliou",
                    "last_name": "Diop"
                },
                "chat": {"id": 221765005555, "type": "private"},
                "date": 1634567890,
                "contact": {
                    "phone_number": "+221765005555",
                    "first_name": "Aliou",
                    "last_name": "Diop",
                    "user_id": 221765005555
                }
            }
        }

        # Mock successful validation
        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN",
            carrier="Orange",
            number_type="MOBILE",
            original_number="+221765005555"
        )

        # Mock successful account creation
        expected_account = UserAccount(
            id=1,
            username="aliou_diop",
            phone_number="+221765005555",
            parent_id="parent_123",
            first_name="Aliou",
            last_name="Diop",
            roles=["parent"],
            is_active=True
        )

        account_creation_result = AccountCreationResult(
            success=True,
            account=expected_account
        )

        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"
        mock_account_service.validate_phone_number.return_value = valid_phone_result
        mock_account_service.create_account.return_value = account_creation_result
        mock_webhook_handler.send_welcome_message.return_value = {"ok": True}

        # Execute complete workflow
        result = await mock_webhook_handler.process_webhook(webhook_data)

        # Assert complete success
        assert result.success is True
        assert result.account == expected_account

        # Verify all steps were called
        mock_webhook_handler.extract_phone_number.assert_called_once()
        mock_account_service.validate_phone_number.assert_called_once()
        mock_account_service.create_account.assert_called_once()
        mock_audit_logger.log_account_creation_started.assert_called_once()
        mock_audit_logger.log_account_creation_completed.assert_called_once()
        mock_webhook_handler.send_welcome_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_parent_with_existing_account(
        self,
        mock_webhook_handler,
        mock_account_service
    ):
        """Test handling parent with existing account."""
        # Setup webhook data
        webhook_data = {
            "message": {
                "from": {"id": 221765005555},
                "contact": {"phone_number": "+221765005555"}
            }
        }

        # Mock phone validation success
        valid_phone_result = PhoneNumberValidationResult(
            is_valid=True,
            normalized_number="+221765005555",
            country_code="SN"
        )

        # Mock account already exists
        account_creation_result = AccountCreationResult(
            success=False,
            error_code="ACCOUNT_ALREADY_EXISTS",
            error_message="Account already exists for this phone number"
        )

        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"
        mock_account_service.validate_phone_number.return_value = valid_phone_result
        mock_account_service.create_account.return_value = account_creation_result
        mock_webhook_handler.send_error_message.return_value = {"ok": True}

        # Execute
        result = await mock_webhook_handler.process_webhook(webhook_data)

        # Assert
        assert result.success is False
        assert result.error_code == "ACCOUNT_ALREADY_EXISTS"
        mock_webhook_handler.send_error_message.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])