"""
Integration Tests for Account Creation Flow

This module contains comprehensive integration tests for the complete
account creation workflow across WhatsApp and Telegram platforms.
Enhanced for Phase 3 with end-to-end testing coverage.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any
from uuid import uuid4

from src.services.account_service import get_account_service, AccountCreationRequest
from src.services.parent_lookup_service import get_parent_lookup_service
from src.services.session_management_service import get_session_management_service
from src.services.user_role_assignment_service import get_user_role_assignment_service
from src.services.welcome_message_service import get_welcome_message_service
from src.services.duplicate_prevention_service import get_duplicate_prevention_service
from src.services.whatsapp_webhook_handler import get_whatsapp_webhook_handler
from src.services.telegram_webhook_handler import get_telegram_webhook_handler
from src.services.message_normalization_service import get_message_normalization_service
from src.services.error_handling_service import get_error_handling_service, ErrorContext
from src.models.user_account import UserAccount, AccountStatus, CreatedVia
from src.utils.exceptions import (
    AccountCreationError,
    ParentNotFoundError,
    DuplicateAccountError
)


class TestAccountCreationIntegration:
    """Integration tests for complete account creation workflow."""

    @pytest.fixture
    async def test_setup(self):
        """Setup test environment and mock data."""
        # Test data
        self.test_phone_number = "+221765005555"
        self.test_parent_code = "PARENT001"
        self.test_platforms = ["whatsapp", "telegram"]

        # Mock parent data
        self.mock_parent_data = {
            "parent_id": "parent_123",
            "parent_code": self.test_parent_code,
            "first_name": "Test",
            "last_name": "Parent",
            "phone_number": self.test_phone_number,
            "email": "test.parent@example.com",
            "children_count": 2,
            "children": [
                {
                    "child_id": "child_1",
                    "full_name": "Child One",
                    "class_name": "CE1"
                },
                {
                    "child_id": "child_2",
                    "full_name": "Child Two",
                    "class_name": "CP"
                }
            ]
        }

        # Initialize services
        self.account_service = get_account_service()
        self.parent_lookup_service = get_parent_lookup_service()
        self.session_service = get_session_management_service()
        self.role_service = get_user_role_assignment_service()
        self.welcome_service = get_welcome_message_service()
        self.duplicate_service = get_duplicate_prevention_service()
        self.whatsapp_handler = get_whatsapp_webhook_handler()
        self.telegram_handler = get_telegram_webhook_handler()
        self.normalization_service = get_message_normalization_service()
        self.error_service = get_error_handling_service()

        yield

        # Cleanup after tests
        await self._cleanup_test_data()

    async def _cleanup_test_data(self):
        """Clean up test data after tests."""
        try:
            # Remove test accounts created during tests
            # In real implementation, this would clean up test data
            pass
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_complete_whatsapp_account_creation_flow(self, test_setup):
        """Test complete account creation flow from WhatsApp webhook."""
        # Step 1: Simulate WhatsApp webhook message
        whatsapp_webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "221765005555",
                            "phone_number_id": "987654321"
                        },
                        "contacts": [{
                            "profile": {"name": "Test Parent"},
                            "wa_id": "221765005555"
                        }],
                        "messages": [{
                            "from": "221765005555",
                            "id": "wamid.test123",
                            "timestamp": "1634567890",
                            "text": {"body": "Bonjour, je souhaite créer un compte"},
                            "type": "text"
                        }]
                    }
                }]
            }]
        }

        # Process webhook
        webhook_result = await self.whatsapp_handler.process_webhook(whatsapp_webhook_data)
        assert webhook_result["status"] == "processed"

        # Step 2: Verify account creation
        account = await self.account_service.get_account_by_phone(self.test_phone_number)
        assert account is not None
        assert account.phone_number == self.test_phone_number
        assert account.created_via == CreatedVia.WHATSAPP
        assert AccountStatus.ACTIVE == account.status

        # Step 3: Verify role assignment
        roles = await self.role_service.get_user_roles(account.id)
        assert len(roles) > 0
        assert any(role.value == "parent" for role in roles)

        # Step 4: Verify session creation
        session = await self.session_service.get_active_session(
            account.id, "whatsapp", self.test_phone_number
        )
        assert session is not None
        assert session.platform == "whatsapp"

        # Step 5: Verify parent lookup
        parent_data = await self.parent_lookup_service.find_parent_by_phone(self.test_phone_number)
        assert parent_data is not None
        assert parent_data["phone_number"] == self.test_phone_number

    @pytest.mark.asyncio
    async def test_complete_telegram_account_creation_flow(self, test_setup):
        """Test complete account creation flow from Telegram webhook."""
        # Step 1: Simulate Telegram webhook message
        telegram_webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 456,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "Parent",
                    "username": "testparent",
                    "language_code": "fr"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "Test",
                    "last_name": "Parent",
                    "username": "testparent",
                    "type": "private"
                },
                "date": 1634567890,
                "text": "Bonjour, je souhaite m'inscrire"
            }
        }

        # Process webhook
        webhook_result = await self.telegram_handler.process_webhook(telegram_webhook_data)
        assert webhook_result["status"] == "processed"

        # Step 2: Verify account creation
        account = await self.account_service.get_account_by_phone(self.test_phone_number)
        assert account is not None
        assert account.created_via == CreatedVia.TELEGRAM
        assert AccountStatus.ACTIVE == account.status

        # Step 3: Verify Telegram user ID is linked
        assert account.telegram_user_id == "987654321"

    @pytest.mark.asyncio
    async def test_duplicate_prevention_across_platforms(self, test_setup):
        """Test duplicate prevention when same user tries from different platforms."""
        # Step 1: Create account via WhatsApp
        whatsapp_request = AccountCreationRequest(
            phone_number=self.test_phone_number,
            platform="whatsapp",
            platform_user_id=self.test_phone_number,
            user_consent=True,
            source="test"
        )

        result1 = await self.account_service.create_account(whatsapp_request)
        assert result1.success is True

        # Step 2: Try to create same account via Telegram
        telegram_request = AccountCreationRequest(
            phone_number=self.test_phone_number,
            platform="telegram",
            platform_user_id="987654321",
            user_consent=True,
            source="test"
        )

        result2 = await self.account_service.create_account(telegram_request)
        assert result2.success is True

        # Step 3: Verify it's the same account with both platforms linked
        account = await self.account_service.get_account_by_phone(self.test_phone_number)
        assert account is not None
        assert account.whatsapp_user_id == self.test_phone_number
        assert account.telegram_user_id == "987654321"

    @pytest.mark.asyncio
    async def test_message_normalization_and_signal_detection(self, test_setup):
        """Test message normalization and account creation signal detection."""
        # Test WhatsApp message normalization
        whatsapp_message = {
            "id": "wamid.test123",
            "from": "221765005555",
            "to": "221765005556",
            "timestamp": "1634567890",
            "text": {"body": "Je veux m'inscrire pour la catéchèse +221765005555"},
            "type": "text",
            "contacts": [{"profile": {"name": "Test Parent"}}]
        }

        normalized = await self.normalization_service.normalize_message("whatsapp", whatsapp_message)
        assert normalized.platform == "whatsapp"
        assert normalized.content_type == "text"
        assert "inscrire" in normalized.content.lower()

        # Extract account creation signals
        signals = self.normalization_service.extract_account_creation_signals(normalized)
        assert signals['is_account_creation_request'] is True
        assert signals['is_command'] is False
        assert signals['contains_phone'] is True
        assert len(signals['keywords']) > 0

    @pytest.mark.asyncio
    async def test_welcome_message_delivery(self, test_setup):
        """Test welcome message delivery after account creation."""
        # Create test account
        account_request = AccountCreationRequest(
            phone_number=self.test_phone_number,
            platform="whatsapp",
            user_consent=True,
            source="test"
        )

        result = await self.account_service.create_account(account_request)
        assert result.success is True

        # Send welcome message
        welcome_result = await self.welcome_service.send_welcome_message(
            result.account.id,
            "whatsapp",
            self.test_phone_number,
            "fr"
        )

        assert welcome_result.success is True
        assert welcome_result.platform == "whatsapp"
        assert welcome_result.template_used is not None

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, test_setup):
        """Test error handling and recovery mechanisms."""
        # Test with invalid phone number
        invalid_request = AccountCreationRequest(
            phone_number="invalid_phone",
            platform="whatsapp",
            user_consent=True,
            source="test"
        )

        result = await self.account_service.create_account(invalid_request)
        assert result.success is False
        assert result.error_code is not None

        # Test error handling service
        context = ErrorContext(
            phone_number="invalid_phone",
            platform="whatsapp",
            operation="account_creation"
        )

        try:
            raise ValidationError("Invalid phone number")
        except ValidationError as e:
            recovery_result = await self.error_service.handle_error(e, context)
            assert recovery_result.action.value is not None

    @pytest.mark.asyncio
    async def test_bulk_account_creation(self, test_setup):
        """Test bulk account creation functionality."""
        # Prepare multiple account requests
        bulk_requests = [
            AccountCreationRequest(
                phone_number="+221765005556",
                platform="whatsapp",
                user_consent=True,
                source="test_bulk"
            ),
            AccountCreationRequest(
                phone_number="+221765005557",
                platform="telegram",
                user_consent=True,
                source="test_bulk"
            )
        ]

        # Process bulk creation
        results = []
        for request in bulk_requests:
            result = await self.account_service.create_account(request)
            results.append(result)

        # Verify results
        assert len(results) == 2
        successful_count = sum(1 for r in results if r.success)
        assert successful_count >= 1  # At least one should succeed

    @pytest.mark.asyncio
    async def test_session_management_integration(self, test_setup):
        """Test session management integration with account creation."""
        # Create account
        account_request = AccountCreationRequest(
            phone_number=self.test_phone_number,
            platform="whatsapp",
            platform_user_id=self.test_phone_number,
            user_consent=True,
            source="test"
        )

        result = await self.account_service.create_account(account_request)
        assert result.success is True

        # Create session
        session = await self.session_service.create_session(
            result.account.id,
            "whatsapp",
            self.test_phone_number
        )

        assert session is not None
        assert session.user_id == result.account.id
        assert session.platform == "whatsapp"

        # Verify session persistence
        retrieved_session = await self.session_service.get_session(session.id)
        assert retrieved_session is not None
        assert retrieved_session.id == session.id

    @pytest.mark.asyncio
    async def test_parent_database_integration(self, test_setup):
        """Test integration with parent database lookup."""
        # Test parent lookup
        parent_data = await self.parent_lookup_service.find_parent_by_phone(self.test_phone_number)

        if parent_data:
            # Verify parent data structure
            assert "parent_id" in parent_data
            assert "parent_code" in parent_data
            assert "phone_number" in parent_data
            assert "children_count" in parent_data

            # Test children lookup
            children = await self.parent_lookup_service.get_parent_children(parent_data["parent_id"])
            assert isinstance(children, list)

    @pytest.mark.asyncio
    async def test_complete_api_flow(self, test_setup):
        """Test complete flow through API endpoints."""
        from fastapi.testclient import TestClient
        from src.api.account_creation_endpoints import router

        # This would test the actual API endpoints
        # For now, test the underlying services
        api_request = {
            "phone_number": "+221765005558",
            "first_name": "API",
            "last_name": "Test",
            "platform": "api",
            "user_consent": True
        }

        # Create account via service (simulating API)
        request = AccountCreationRequest(**api_request)
        result = await self.account_service.create_account(request)

        if result.success:
            # Verify all components worked together
            assert result.account is not None

            # Verify role was assigned
            roles = await self.role_service.get_user_roles(result.account.id)
            assert len(roles) > 0

            # Verify session can be created
            session = await self.session_service.create_session(
                result.account.id,
                "api",
                "api_user"
            )
            assert session is not None

    @pytest.mark.asyncio
    async def test_concurrent_account_creation(self, test_setup):
        """Test concurrent account creation requests."""
        # Simulate multiple concurrent requests for the same phone number
        concurrent_requests = [
            AccountCreationRequest(
                phone_number="+221765005559",
                platform="whatsapp",
                user_consent=True,
                source="test_concurrent"
            )
            for _ in range(3)
        ]

        # Execute concurrently
        tasks = [
            self.account_service.create_account(req)
            for req in concurrent_requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Only one should succeed, others should detect duplicate
        successful_count = sum(1 for r in results if not isinstance(r, Exception) and r.success)
        assert successful_count == 1

    @pytest.mark.asyncio
    async def test_system_health_and_monitoring(self, test_setup):
        """Test system health monitoring components."""
        # Test error statistics
        error_stats = await self.error_service.get_error_statistics(hours=24)
        assert "total_errors" in error_stats
        assert "errors_by_severity" in error_stats
        assert "errors_by_category" in error_stats

        # Test session cleanup
        cleanup_count = await self.session_service.cleanup_expired_sessions()
        assert isinstance(cleanup_count, int)

        # Test duplicate cleanup
        duplicate_cleanup = await self.duplicate_service.cleanup_potential_duplicates()
        assert "potential_duplicates_found" in duplicate_cleanup


class TestMessageNormalizationIntegration:
    """Integration tests for message normalization service."""

    @pytest.mark.asyncio
    async def test_whatsapp_message_normalization(self):
        """Test WhatsApp message normalization."""
        service = get_message_normalization_service()

        whatsapp_message = {
            "id": "wamid.test123",
            "from": "221765005555",
            "to": "221765005556",
            "timestamp": "1634567890",
            "text": {"body": "Bonjour, je veux m'inscrire s'il vous plaît"},
            "type": "text",
            "contacts": [{"profile": {"name": "Test Parent"}}]
        }

        normalized = await service.normalize_message("whatsapp", whatsapp_message)
        assert normalized.platform == "whatsapp"
        assert normalized.content_type == "text"
        assert normalized.user_name == "Test Parent"
        assert "inscrire" in normalized.content.lower()

    @pytest.mark.asyncio
    async def test_telegram_message_normalization(self):
        """Test Telegram message normalization."""
        service = get_message_normalization_service()

        telegram_message = {
            "message_id": 456,
            "from": {
                "id": 987654321,
                "first_name": "Test",
                "last_name": "Parent",
                "username": "testparent"
            },
            "chat": {"id": 987654321, "type": "private"},
            "date": 1634567890,
            "text": "/start inscription"
        }

        normalized = await service.normalize_message("telegram", telegram_message)
        assert normalized.platform == "telegram"
        assert normalized.content_type == "text"
        assert normalized.user_name == "Test Parent"
        assert normalized.processing_flags["is_command"] is True

    @pytest.mark.asyncio
    async def test_media_message_normalization(self):
        """Test media message normalization."""
        service = get_message_normalization_service()

        # Test WhatsApp image message
        whatsapp_image = {
            "id": "wamid.test456",
            "from": "221765005555",
            "timestamp": "1634567890",
            "image": {
                "id": "media_123",
                "caption": "Photo de mon enfant",
                "mime_type": "image/jpeg"
            },
            "type": "image"
        }

        normalized = await service.normalize_message("whatsapp", whatsapp_image)
        assert normalized.content_type == "image"
        assert "Photo" in normalized.content
        assert normalized.media_type == "image"


class TestErrorHandlingIntegration:
    """Integration tests for error handling service."""

    @pytest.mark.asyncio
    async def test_account_creation_error_recovery(self):
        """Test error recovery in account creation."""
        service = get_error_handling_service()

        context = ErrorContext(
            phone_number="+221765005560",
            platform="whatsapp",
            operation="account_creation"
        )

        # Test validation error recovery
        try:
            raise ValidationError("Invalid phone number format")
        except ValidationError as e:
            result = await service.handle_error(e, context)
            assert result.success is True
            assert result.action.value in ["skip", "retry"]

    @pytest.mark.asyncio
    async def test_database_error_recovery(self):
        """Test database error recovery."""
        service = get_error_handling_service()

        context = ErrorContext(
            operation="database_query",
            component="account_service"
        )

        # Test database error recovery
        try:
            raise DatabaseConnectionError("Connection timeout")
        except DatabaseConnectionError as e:
            result = await service.handle_error(e, context)
            assert result.success is True
            assert result.action.value in ["retry", "queue"]

    @pytest.mark.asyncio
    async def test_operation_with_automatic_recovery(self):
        """Test operation execution with automatic recovery."""
        service = get_error_handling_service()

        context = ErrorContext(
            operation="test_operation",
            component="test_service"
        )

        # Define operation that fails initially
        attempt_count = 0
        async def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise DatabaseConnectionError("Temporary failure")
            return "success"

        # Execute with recovery
        result = await service.execute_with_recovery(failing_operation, context)
        assert result == "success"
        assert attempt_count == 2  # Should have retried once


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "-k", "test_complete_whatsapp_account_creation_flow"])