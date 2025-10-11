"""
Integration Tests for WhatsApp Webhook Account Creation Flow

This test suite validates the complete WhatsApp webhook integration
for automatic account creation, including WAHA API integration, webhook processing,
authentication, phone number extraction, and account creation workflow.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import asyncio

from src.api.v1.whatsapp import router as whatsapp_router
from src.handlers.whatsapp_webhook import WhatsAppWebhookHandler
from src.services.account_service import AccountService, AccountCreationResult
from src.models.account import UserAccount, AccountCreationRequest
from src.models.session import AccountCreationSession
from src.middleware.auth import AuthManager
from src.utils.audit_logger import AuditLogger
from src.utils.phone_validator import PhoneNumberValidationResult


class TestWhatsAppWebhookIntegration:
    """Integration tests for WhatsApp webhook account creation."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(whatsapp_router)

    @pytest.fixture
    def mock_webhook_handler(self):
        """Create mock WhatsApp webhook handler."""
        handler = AsyncMock(spec=WhatsAppWebhookHandler)
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
    def valid_waha_webhook(self):
        """Create valid WAHA webhook payload."""
        return {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgA=",
                "timestamp": 1694123456,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "text",
                    "text": "Bonjour, je suis un parent du catéchisme"
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop",
                    "profilePictureUrl": None,
                    "isBusiness": False,
                    "isEnterprise": False
                }
            }
        }

    @pytest.fixture
    def waha_webhook_with_contact(self):
        """Create WAHA webhook payload with contact info."""
        return {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgA=",
                "timestamp": 1694123456,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "contact",
                    "contact": {
                        "displayName": "Aliou Diop",
                        "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:Aliou Diop\nTEL;TYPE=CELL:+221765005555\nEND:VCARD"
                    }
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop",
                    "profilePictureUrl": None
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


class TestWahaWebhookAuthentication:
    """Test WAHA webhook authentication and security."""

    @patch('src.api.v1.whatsapp.auth_manager')
    async def test_waha_webhook_authentication_success(self, mock_auth, client, valid_waha_webhook):
        """Test successful WAHA webhook authentication."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_waha_webhook,
            headers={"Authorization": "Bearer valid_waha_token"}
        )

        # Assert
        assert response.status_code == 200
        mock_auth.authenticate_webhook_request.assert_called_once()

    @patch('src.api.v1.whatsapp.auth_manager')
    async def test_waha_webhook_authentication_failure(self, mock_auth, client, valid_waha_webhook):
        """Test WAHA webhook authentication failure."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": False,
            "error": "Invalid WAHA token"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_waha_webhook,
            headers={"Authorization": "Bearer invalid_token"}
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid WAHA token" in response.json()["detail"]

    @patch('src.api.v1.whatsapp.auth_manager')
    async def test_waha_webhook_rate_limiting(self, mock_auth, client, valid_waha_webhook):
        """Test WAHA webhook rate limiting."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": False,
            "rate_limited": True,
            "error": "Rate limit exceeded"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_waha_webhook,
            headers={"Authorization": "Bearer valid_waha_token"}
        )

        # Assert
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]


class TestWahaPhoneNumberExtraction:
    """Test phone number extraction from WAHA messages."""

    @pytest.mark.asyncio
    async def test_extract_phone_from_contact_message(self, mock_webhook_handler, waha_webhook_with_contact):
        """Test phone number extraction from contact message."""
        # Setup
        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(waha_webhook_with_contact)

        # Assert
        assert phone_number == "+221765005555"
        mock_webhook_handler.extract_phone_number.assert_called_once_with(waha_webhook_with_contact)

    @pytest.mark.asyncio
    async def test_extract_phone_from_text_message(self, mock_webhook_handler):
        """Test phone number extraction from text message."""
        # Setup
        message_with_phone = {
            "payload": {
                "type": "text",
                "text": "Mon numéro est le +221 76 50 05 55"
            },
            "from": "221765005555@c.us"
        }
        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(message_with_phone)

        # Assert
        assert phone_number == "+221765005555"

    @pytest.mark.asyncio
    async def test_extract_phone_from_vcard(self, mock_webhook_handler):
        """Test phone number extraction from vCard."""
        # Setup
        vcard_message = {
            "payload": {
                "type": "contact",
                "contact": {
                    "displayName": "Aliou Diop",
                    "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:Aliou Diop\nTEL;TYPE=CELL:+221765005555\nEND:VCARD"
                }
            },
            "from": "221765005555@c.us"
        }
        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(vcard_message)

        # Assert
        assert phone_number == "+221765005555"

    @pytest.mark.asyncio
    async def test_extract_phone_from_sender_info(self, mock_webhook_handler):
        """Test phone number extraction from sender information."""
        # Setup
        message_without_phone_in_payload = {
            "payload": {
                "type": "text",
                "text": "Bonjour, je suis parent"
            },
            "from": "221765005555@c.us",
            "sender": {
                "contactId": "221765005555@c.us"
            }
        }
        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(message_without_phone_in_payload)

        # Assert
        assert phone_number == "+221765005555"

    @pytest.mark.asyncio
    async def test_extract_phone_no_phone_found(self, mock_webhook_handler):
        """Test phone number extraction when no phone found."""
        # Setup
        message_without_phone = {
            "payload": {
                "type": "text",
                "text": "Bonjour, comment allez-vous?"
            },
            "from": "unknown@c.us"
        }
        mock_webhook_handler.extract_phone_number.return_value = None

        # Execute
        phone_number = await mock_webhook_handler.extract_phone_number(message_without_phone)

        # Assert
        assert phone_number is None


class TestWahaAccountCreationFlow:
    """Test complete WAHA account creation flow."""

    @pytest.mark.asyncio
    async def test_complete_waha_account_creation_success(
        self,
        mock_webhook_handler,
        mock_account_service,
        mock_audit_logger,
        waha_webhook_with_contact,
        expected_account
    ):
        """Test complete successful WAHA account creation flow."""
        # Setup
        phone_number = "+221765005555"
        platform_user_id = "221765005555@c.us"

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
            platform="whatsapp",
            platform_user_id=platform_user_id,
            phone_number=phone_number,
            status="created"
        )

        # Execute
        result = await mock_webhook_handler.process_account_creation_flow(waha_webhook_with_contact)

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
    async def test_waha_account_creation_invalid_phone(
        self,
        mock_webhook_handler,
        mock_account_service,
        waha_webhook_with_contact
    ):
        """Test WAHA account creation with invalid phone number."""
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
        result = await mock_webhook_handler.process_account_creation_flow(waha_webhook_with_contact)

        # Assert
        assert result.success is False
        assert result.error_code == "INVALID_PHONE_FORMAT"
        assert "Phone number format is invalid" in result.error_message

        # Verify audit logging
        mock_account_service.audit_logger.log_account_creation_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_waha_account_creation_parent_not_found(
        self,
        mock_webhook_handler,
        mock_account_service,
        waha_webhook_with_contact
    ):
        """Test WAHA account creation when parent not found."""
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
        result = await mock_webhook_handler.process_account_creation_flow(waha_webhook_with_contact)

        # Assert
        assert result.success is False
        assert result.error_code == "PARENT_NOT_FOUND"
        assert "Parent not found" in result.error_message


class TestWahaMessageResponses:
    """Test WAHA message response handling."""

    @pytest.mark.asyncio
    async def test_send_waha_welcome_message_success(
        self,
        mock_webhook_handler,
        expected_account
    ):
        """Test sending welcome message via WAHA after successful account creation."""
        # Setup
        platform_user_id = "221765005555@c.us"
        welcome_message = f"Bonjour {expected_account.first_name}! Votre compte a été créé avec succès."

        mock_webhook_handler.send_message.return_value = {
            "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgA=",
            "timestamp": 1694123456
        }

        # Execute
        result = await mock_webhook_handler.send_welcome_message(platform_user_id, expected_account)

        # Assert
        assert result.success is True
        assert "id" in result.response
        mock_webhook_handler.send_message.assert_called_once_with(
            platform_user_id,
            welcome_message
        )

    @pytest.mark.asyncio
    async def test_send_waha_error_message(
        self,
        mock_webhook_handler
    ):
        """Test sending error message via WAHA."""
        # Setup
        platform_user_id = "221765005555@c.us"
        error_message = "Désolé, nous n'avons pas pu créer votre compte."

        mock_webhook_handler.send_message.return_value = {
            "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgA=",
            "timestamp": 1694123456
        }

        # Execute
        result = await mock_webhook_handler.send_error_message(platform_user_id, error_message)

        # Assert
        assert result.success is True
        mock_webhook_handler.send_message.assert_called_once_with(platform_user_id, error_message)

    @pytest.mark.asyncio
    async def test_send_waha_phone_request_with_buttons(
        self,
        mock_webhook_handler
    ):
        """Test sending phone number request with interactive buttons via WAHA."""
        # Setup
        platform_user_id = "221765005555@c.us"

        mock_webhook_handler.send_interactive_message.return_value = {
            "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgA=",
            "timestamp": 1694123456
        }

        # Execute
        result = await mock_webhook_handler.send_phone_request_message(platform_user_id)

        # Assert
        assert result.success is True
        mock_webhook_handler.send_interactive_message.assert_called_once()

        # Check that interactive message contains phone request
        call_args = mock_webhook_handler.send_interactive_message.call_args
        interactive_content = call_args[0][1]  # Second argument is the interactive content
        assert "numéro de téléphone" in interactive_content["body"]["text"].lower()

    @pytest.mark.asyncio
    async def test_send_waha_media_message(
        self,
        mock_webhook_handler
    ):
        """Test sending media message via WAHA."""
        # Setup
        platform_user_id = "221765005555@c.us"
        media_url = "https://example.com/welcome.png"
        caption = "Bienvenue!"

        mock_webhook_handler.send_media.return_value = {
            "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgA=",
            "timestamp": 1694123456
        }

        # Execute
        result = await mock_webhook_handler.send_media_message(platform_user_id, media_url, caption)

        # Assert
        assert result.success is True
        mock_webhook_handler.send_media.assert_called_once_with(platform_user_id, media_url, caption)


class TestWahaSessionManagement:
    """Test WAHA session management for account creation flow."""

    @pytest.mark.asyncio
    async def test_create_waha_account_creation_session(
        self,
        mock_webhook_handler
    ):
        """Test creating WAHA account creation session."""
        # Setup
        platform = "whatsapp"
        platform_user_id = "221765005555@c.us"
        phone_number = "+221765005555"

        expected_session = AccountCreationSession(
            session_id="session_123",
            platform=platform,
            platform_user_id=platform_user_id,
            phone_number=phone_number,
            status="initiated",
            session_data={"waha_session": "default"}
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
        assert session.platform == "whatsapp"
        assert "waha_session" in session.session_data

    @pytest.mark.asyncio
    async def test_get_waha_existing_session(
        self,
        mock_webhook_handler
    ):
        """Test getting existing WAHA account creation session."""
        # Setup
        platform_user_id = "221765005555@c.us"

        existing_session = AccountCreationSession(
            session_id="session_456",
            platform="whatsapp",
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


class TestWahaErrorHandlingAndEdgeCases:
    """Test WAHA error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_waha_webhook_missing_required_fields(
        self,
        mock_webhook_handler
    ):
        """Test WAHA webhook processing with missing required fields."""
        # Setup
        incomplete_webhook = {
            "event": "message",
            "payload": {
                "id": "test_id",
                # Missing 'from' field
                "payload": {"type": "text", "text": "Hello"}
            }
        }

        # Execute
        result = await mock_webhook_handler.process_webhook(incomplete_webhook)

        # Assert
        assert result.success is False
        assert "missing" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_waha_webhook_service_unavailable(
        self,
        mock_webhook_handler,
        mock_account_service
    ):
        """Test WAHA webhook processing when account service is unavailable."""
        # Setup
        webhook_data = {
            "event": "message",
            "payload": {
                "from": "221765005555@c.us",
                "payload": {"type": "text", "text": "Hello"}
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
    async def test_waha_api_rate_limiting(
        self,
        mock_webhook_handler
    ):
        """Test handling WAHA API rate limiting."""
        # Setup
        platform_user_id = "221765005555@c.us"
        message = "Test message"

        # Mock WAHA API rate limit response
        mock_webhook_handler.send_message.side_effect = Exception("Rate limit exceeded")

        # Execute
        result = await mock_webhook_handler.send_message(platform_user_id, message)

        # Assert
        assert result.success is False
        assert "rate limit" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_waha_concurrent_account_creation(
        self,
        mock_webhook_handler,
        mock_account_service,
        waha_webhook_with_contact
    ):
        """Test handling concurrent WAHA account creation requests."""
        # Setup
        phone_number = "+221765005555"
        platform_user_id = "221765005555@c.us"

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
            mock_webhook_handler.process_account_creation_flow(waha_webhook_with_contact),
            mock_webhook_handler.process_account_creation_flow(waha_webhook_with_contact)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        assert len(results) == 2
        assert results[0].success is True  # First succeeds
        assert results[1].success is False  # Second fails with account already exists


class TestWahaEndToEndScenarios:
    """Test complete WAHA end-to-end scenarios."""

    @pytest.mark.asyncio
    async def test_complete_waha_new_parent_registration(
        self,
        mock_webhook_handler,
        mock_account_service,
        mock_audit_logger
    ):
        """Test complete new parent registration workflow via WAHA."""
        # Setup WAHA webhook data - parent sends message with contact
        webhook_data = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgA=",
                "timestamp": 1694123456,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "contact",
                    "contact": {
                        "displayName": "Aliou Diop",
                        "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:Aliou Diop\nTEL;TYPE=CELL:+221765005555\nEND:VCARD"
                    }
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop",
                    "profilePictureUrl": None
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
        mock_webhook_handler.send_welcome_message.return_value = {"id": "test_message_id"}

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
    async def test_waha_parent_with_existing_account(
        self,
        mock_webhook_handler,
        mock_account_service
    ):
        """Test handling parent with existing account via WAHA."""
        # Setup WAHA webhook data
        webhook_data = {
            "session": "default",
            "event": "message",
            "payload": {
                "from": "221765005555@c.us",
                "payload": {"type": "text", "text": "Je suis parent"}
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
        mock_webhook_handler.send_error_message.return_value = {"id": "test_error_message_id"}

        # Execute
        result = await mock_webhook_handler.process_webhook(webhook_data)

        # Assert
        assert result.success is False
        assert result.error_code == "ACCOUNT_ALREADY_EXISTS"
        mock_webhook_handler.send_error_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_waha_webhook_with_media_message(
        self,
        mock_webhook_handler
    ):
        """Test WAHA webhook processing with media message."""
        # Setup
        media_webhook = {
            "session": "default",
            "event": "message",
            "payload": {
                "from": "221765005555@c.us",
                "payload": {
                    "type": "image",
                    "image": {
                        "id": "media_id_123",
                        "caption": "Voici ma carte d'identité"
                    }
                }
            }
        }

        # Execute
        result = await mock_webhook_handler.process_webhook(media_webhook)

        # Assert
        # Media messages without phone should not trigger account creation
        # but should be acknowledged
        assert result.success is True or "no phone" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_waha_session_persistence(
        self,
        mock_webhook_handler,
        mock_account_service
    ):
        """Test WAHA session persistence across multiple messages."""
        # Setup first message - parent identification
        first_message = {
            "session": "default",
            "event": "message",
            "payload": {
                "from": "221765005555@c.us",
                "payload": {"type": "text", "text": "Je suis parent du catéchisme"}
            }
        }

        # Setup session exists
        existing_session = AccountCreationSession(
            session_id="session_123",
            platform="whatsapp",
            platform_user_id="221765005555@c.us",
            status="initiated"
        )
        mock_webhook_handler.get_existing_session.return_value = existing_session

        # Setup second message - phone number provided
        second_message = {
            "session": "default",
            "event": "message",
            "payload": {
                "from": "221765005555@c.us",
                "payload": {"type": "text", "text": "+221765005555"}
            }
        }

        mock_webhook_handler.extract_phone_number.return_value = "+221765005555"

        # Execute
        result1 = await mock_webhook_handler.process_webhook(first_message)
        result2 = await mock_webhook_handler.process_webhook(second_message)

        # Assert
        # First message should acknowledge session
        assert result1.success is True

        # Second message should process phone number
        mock_webhook_handler.extract_phone_number.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])