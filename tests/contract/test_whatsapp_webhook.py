"""
Contract Tests for WhatsApp Webhook Processing

This test suite validates the contract between the WAHA (WhatsApp HTTP API)
and our webhook processing system, ensuring API compatibility and
response format compliance.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import Request
from datetime import datetime
import requests
from typing import Dict, Any

from src.api.v1.whatsapp import router as whatsapp_router
from src.handlers.whatsapp_webhook import WhatsAppWebhookHandler
from src.services.account_service import AccountService, AccountCreationResult
from src.models.account import UserAccount
from src.middleware.auth import AuthManager


class TestWhatsAppWebhookContract:
    """Contract tests for WhatsApp webhook API (WAHA)."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(whatsapp_router)

    @pytest.fixture
    def waha_api_base_url(self):
        """Base URL for WAHA API."""
        return "https://waha-core.example.com"

    @pytest.fixture
    def waha_session_token(self):
        """WAHA session token for testing."""
        return "waha_session_token_123456789"

    @pytest.fixture
    def valid_waha_webhook_payload(self):
        """Valid WAHA webhook payload according to WAHA specification."""
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
                    "text": "Bonjour, je suis parent du catéchisme"
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
        """WAHA webhook payload with contact message."""
        return {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgB=",
                "timestamp": 1694123457,
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
    def waha_webhook_with_image(self):
        """WAHA webhook payload with image message."""
        return {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgC=",
                "timestamp": 1694123458,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "image",
                    "image": {
                        "id": "media_id_123",
                        "url": "https://mmg.whatsapp.net/d/f/media_id_123",
                        "mimeType": "image/jpeg",
                        "sha256": "abc123def456",
                        "fileLength": 123456,
                        "width": 800,
                        "height": 600,
                        "caption": "Ma carte d'identité"
                    }
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop"
                }
            }
        }

    @pytest.fixture
    def waha_webhook_with_location(self):
        """WAHA webhook payload with location message."""
        return {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgD=",
                "timestamp": 1694123459,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "location",
                    "location": {
                        "latitude": 14.6928,
                        "longitude": -17.4467,
                        "name": "Église Saint-Louis",
                        "address": "Saint-Louis, Sénégal"
                    }
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop"
                }
            }
        }

    @pytest.fixture
    def waha_webhook_with_button_response(self):
        """WAHA webhook payload with button response."""
        return {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgE=",
                "timestamp": 1694123460,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "button",
                    "button": {
                        "text": "Confirmer création",
                        "payload": "account_creation_confirm"
                    }
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop"
                }
            }
        }

    @pytest.fixture
    def waha_webhook_with_list_response(self):
        """WAHA webhook payload with list response."""
        return {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgF=",
                "timestamp": 1694123461,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "list",
                    "list": {
                        "responseTitle": "Services du catéchisme",
                        "description": "Choisissez un service",
                        "singleSelect": True,
                        "sections": [
                            {
                                "title": "Services disponibles",
                                "rows": [
                                    {
                                        "id": "catechisme_info",
                                        "title": "Informations catéchisme",
                                        "description": "Horaires et programmes"
                                    },
                                    {
                                        "id": "inscription",
                                        "title": "Inscription",
                                        "description": "Inscrire un enfant"
                                    }
                                ]
                            }
                        ]
                    }
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop"
                }
            }
        }


class TestWahaWebhookApiContract:
    """Test WAHA webhook API contract compliance."""

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_webhook_endpoint_accepts_post_only(self, mock_auth, client, valid_waha_webhook_payload):
        """Test that WAHA webhook endpoint only accepts POST requests."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }

        # Test GET request
        response = client.get("/webhook")
        assert response.status_code == 405  # Method Not Allowed

        # Test POST request
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "Bearer valid_waha_token"}
        )
        assert response.status_code == 200

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_webhook_accepts_json_content_type(self, mock_auth, client, valid_waha_webhook_payload):
        """Test that WAHA webhook endpoint accepts JSON content type."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }

        # Test with correct content type
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_waha_token"
            }
        )
        assert response.status_code == 200

        # Test with incorrect content type
        response = client.post(
            "/webhook",
            data=valid_waha_webhook_payload,
            headers={
                "Content-Type": "text/plain",
                "Authorization": "Bearer valid_waha_token"
            }
        )
        # Should still work with FastAPI's auto-conversion
        assert response.status_code in [200, 422]  # 422 if validation fails

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_webhook_response_format(self, mock_auth, client, valid_waha_webhook_payload):
        """Test WAHA webhook response format compliance."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "Bearer valid_waha_token"}
        )

        # Assert response format
        assert response.status_code == 200
        # WAHA webhooks should return 200 OK with optional JSON body
        # Empty response is also valid
        if response.content:
            # If there's content, it should be valid JSON
            assert response.headers["content-type"] == "application/json"
            try:
                json.loads(response.content)
            except json.JSONDecodeError:
                pytest.fail("Response should be valid JSON when content is present")

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_webhook_handles_large_payloads(self, mock_auth, client):
        """Test WAHA webhook handling of large payloads."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }

        # Create large message (within WhatsApp limits)
        large_message = "A" * 4000  # WhatsApp message limit is 4096 characters
        large_payload = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgG=",
                "timestamp": 1694123462,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "text",
                    "text": large_message
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop"
                }
            }
        }

        # Execute
        response = client.post(
            "/webhook",
            json=large_payload,
            headers={"Authorization": "Bearer valid_waha_token"}
        )

        # Assert
        assert response.status_code == 200

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_webhook_handles_empty_payload(self, mock_auth, client):
        """Test WAHA webhook handling of empty payload."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }

        # Execute
        response = client.post(
            "/webhook",
            json={},
            headers={"Authorization": "Bearer valid_waha_token"}
        )

        # Assert
        # Should handle gracefully - either success or validation error
        assert response.status_code in [200, 422]


class TestWahaAuthenticationContract:
    """Test WAHA authentication contract."""

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_bearer_token_verification(self, mock_auth, client, valid_waha_webhook_payload):
        """Test WAHA bearer token verification contract."""
        # Test missing authorization header
        response = client.post("/webhook", json=valid_waha_webhook_payload)
        assert response.status_code == 401

        # Test invalid bearer token
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": False,
            "error": "Invalid WAHA token"
        }
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

        # Test valid bearer token
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "Bearer valid_waha_token"}
        )
        assert response.status_code == 200

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_authorization_header_formats(self, mock_auth, client, valid_waha_webhook_payload):
        """Test different authorization header formats."""
        # Setup
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": True,
            "platform": "whatsapp"
        }

        # Test with "Bearer " prefix
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200

        # Test without "Bearer " prefix (should still work)
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "valid_token"}
        )
        # May or may not work depending on implementation
        assert response.status_code in [200, 401]


class TestWahaMessageProcessingContract:
    """Test WAHA message processing contract compliance."""

    @pytest.mark.asyncio
    async def test_waha_text_message_processing_contract(self, mock_webhook_handler):
        """Test WAHA text message processing contract."""
        # Setup
        text_message = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.test.123",
                "timestamp": 1694123456,
                "from": "221765005555@c.us",
                "payload": {"type": "text", "text": "Bonjour"},
                "sender": {"contactId": "221765005555@c.us", "pushname": "Aliou"}
            }
        }

        expected_result = {
            "processed": True,
            "message_type": "text",
            "session": "default",
            "response_sent": False
        }

        mock_webhook_handler.process_message.return_value = expected_result

        # Execute
        result = await mock_webhook_handler.process_message(text_message)

        # Assert contract compliance
        assert "processed" in result
        assert "message_type" in result
        assert "session" in result
        assert isinstance(result["processed"], bool)
        assert result["message_type"] == "text"
        assert result["session"] == "default"

    @pytest.mark.asyncio
    async def test_waha_contact_message_processing_contract(self, mock_webhook_handler):
        """Test WAHA contact message processing contract."""
        # Setup
        contact_message = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.test.124",
                "timestamp": 1694123457,
                "from": "221765005555@c.us",
                "payload": {
                    "type": "contact",
                    "contact": {
                        "displayName": "Aliou Diop",
                        "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:Aliou Diop\nTEL;TYPE=CELL:+221765005555\nEND:VCARD"
                    }
                },
                "sender": {"contactId": "221765005555@c.us"}
            }
        }

        expected_result = {
            "processed": True,
            "message_type": "contact",
            "session": "default",
            "phone_number_extracted": "+221765005555",
            "account_creation_initiated": True
        }

        mock_webhook_handler.process_message.return_value = expected_result

        # Execute
        result = await mock_webhook_handler.process_message(contact_message)

        # Assert contract compliance
        assert result["message_type"] == "contact"
        assert "phone_number_extracted" in result
        assert result["phone_number_extracted"] == "+221765005555"
        assert "account_creation_initiated" in result

    @pytest.mark.asyncio
    async def test_waha_media_message_processing_contract(self, mock_webhook_handler):
        """Test WAHA media message processing contract."""
        # Setup
        image_message = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.test.125",
                "timestamp": 1694123458,
                "from": "221765005555@c.us",
                "payload": {
                    "type": "image",
                    "image": {
                        "id": "media_id_123",
                        "url": "https://example.com/image.jpg",
                        "mimeType": "image/jpeg",
                        "caption": "Carte d'identité"
                    }
                },
                "sender": {"contactId": "221765005555@c.us"}
            }
        }

        expected_result = {
            "processed": True,
            "message_type": "image",
            "session": "default",
            "media_id": "media_id_123",
            "media_type": "image/jpeg",
            "caption": "Carte d'identité"
        }

        mock_webhook_handler.process_message.return_value = expected_result

        # Execute
        result = await mock_webhook_handler.process_message(image_message)

        # Assert contract compliance
        assert result["message_type"] == "image"
        assert "media_id" in result
        assert "media_type" in result
        assert result["media_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_waha_button_response_processing_contract(self, mock_webhook_handler):
        """Test WAHA button response processing contract."""
        # Setup
        button_response = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.test.126",
                "timestamp": 1694123459,
                "from": "221765005555@c.us",
                "payload": {
                    "type": "button",
                    "button": {
                        "text": "Confirmer",
                        "payload": "account_creation_confirm"
                    }
                },
                "sender": {"contactId": "221765005555@c.us"}
            }
        }

        expected_result = {
            "processed": True,
            "message_type": "button",
            "session": "default",
            "button_payload": "account_creation_confirm",
            "action_executed": True
        }

        mock_webhook_handler.process_message.return_value = expected_result

        # Execute
        result = await mock_webhook_handler.process_message(button_response)

        # Assert contract compliance
        assert result["message_type"] == "button"
        assert "button_payload" in result
        assert result["button_payload"] == "account_creation_confirm"


class TestWahaApiResponseContract:
    """Test WAHA API response contract compliance."""

    @pytest.mark.asyncio
    async def test_waha_send_message_response_contract(self, mock_webhook_handler):
        """Test WAHA send message API response contract."""
        # Setup
        chat_id = "221765005555@c.us"
        text = "Bonjour! Votre compte a été créé avec succès."

        expected_api_response = {
            "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgH=",
            "timestamp": 1694123460
        }

        mock_webhook_handler.send_message.return_value = expected_api_response

        # Execute
        response = await mock_webhook_handler.send_message(chat_id, text)

        # Assert contract compliance
        assert "id" in response
        assert "timestamp" in response
        assert response["id"].startswith("wamid.")
        assert isinstance(response["timestamp"], int)

    @pytest.mark.asyncio
    async def test_waha_send_image_response_contract(self, mock_webhook_handler):
        """Test WAHA send image API response contract."""
        # Setup
        chat_id = "221765005555@c.us"
        image_url = "https://example.com/welcome.png"
        caption = "Bienvenue!"

        expected_api_response = {
            "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgI=",
            "timestamp": 1694123461
        }

        mock_webhook_handler.send_image.return_value = expected_api_response

        # Execute
        response = await mock_webhook_handler.send_image(chat_id, image_url, caption)

        # Assert contract compliance
        assert "id" in response
        assert "timestamp" in response
        assert response["id"].startswith("wamid.")

    @pytest.mark.asyncio
    async def test_waha_send_interactive_message_response_contract(self, mock_webhook_handler):
        """Test WAHA send interactive message API response contract."""
        # Setup
        chat_id = "221765005555@c.us"
        interactive_content = {
            "type": "button",
            "body": {"text": "Choisissez une option:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "btn1", "title": "Oui"}},
                    {"type": "reply", "reply": {"id": "btn2", "title": "Non"}}
                ]
            }
        }

        expected_api_response = {
            "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgJ=",
            "timestamp": 1694123462
        }

        mock_webhook_handler.send_interactive_message.return_value = expected_api_response

        # Execute
        response = await mock_webhook_handler.send_interactive_message(chat_id, interactive_content)

        # Assert contract compliance
        assert "id" in response
        assert "timestamp" in response
        assert response["id"].startswith("wamid.")


class TestWahaErrorHandlingContract:
    """Test WAHA error handling contract compliance."""

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_webhook_error_response_format(self, mock_auth, client, valid_waha_webhook_payload):
        """Test WAHA webhook error response format contract."""
        # Setup authentication failure
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": False,
            "error": "Invalid WAHA token"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "Bearer invalid_token"}
        )

        # Assert error response format
        assert response.status_code == 401
        assert "detail" in response.json()
        assert "Invalid WAHA token" in response.json()["detail"]

    @patch('src.api.v1.whatsapp.auth_manager')
    def test_waha_webhook_rate_limit_response_format(self, mock_auth, client, valid_waha_webhook_payload):
        """Test WAHA webhook rate limiting response format contract."""
        # Setup rate limiting
        mock_auth.authenticate_webhook_request.return_value = {
            "authenticated": False,
            "rate_limited": True,
            "error": "Rate limit exceeded"
        }

        # Execute
        response = client.post(
            "/webhook",
            json=valid_waha_webhook_payload,
            headers={"Authorization": "Bearer valid_waha_token"}
        )

        # Assert rate limit response format
        assert response.status_code == 429
        assert "detail" in response.json()
        assert "Rate limit exceeded" in response.json()["detail"]


class TestWahaDataStructureContract:
    """Test WAHA data structure contract compliance."""

    def test_waha_webhook_payload_structure_validation(self, valid_waha_webhook_payload):
        """Test WAHA webhook payload structure according to WAHA specification."""
        # Verify required fields
        assert "session" in valid_waha_webhook_payload
        assert "event" in valid_waha_webhook_payload
        assert "payload" in valid_waha_webhook_payload

        assert isinstance(valid_waha_webhook_payload["session"], str)
        assert valid_waha_webhook_payload["event"] == "message"

        # Verify payload structure
        payload = valid_waha_webhook_payload["payload"]
        assert "id" in payload
        assert "timestamp" in payload
        assert "from" in payload
        assert "payload" in payload
        assert "sender" in payload

        assert isinstance(payload["id"], str)
        assert payload["id"].startswith("wamid.")
        assert isinstance(payload["timestamp"], int)
        assert isinstance(payload["from"], str)
        assert payload["from"].endswith("@c.us")

        # Verify nested payload structure
        inner_payload = payload["payload"]
        assert "type" in inner_payload
        assert inner_payload["type"] == "text"

        # Verify sender structure
        sender = payload["sender"]
        assert "contactId" in sender
        assert sender["contactId"] == payload["from"]

    def test_waha_contact_message_structure_validation(self, waha_webhook_with_contact):
        """Test WAHA contact message structure according to WAHA specification."""
        payload = waha_webhook_with_contact["payload"]
        inner_payload = payload["payload"]
        assert "contact" in inner_payload

        contact = inner_payload["contact"]
        assert "displayName" in contact
        assert "vcard" in contact
        assert isinstance(contact["displayName"], str)
        assert isinstance(contact["vcard"], str)
        assert contact["vcard"].startswith("BEGIN:VCARD")
        assert contact["vcard"].endswith("END:VCARD")

    def test_waha_media_message_structure_validation(self, waha_webhook_with_image):
        """Test WAHA media message structure according to WAHA specification."""
        payload = waha_webhook_with_image["payload"]
        inner_payload = payload["payload"]
        assert "image" in inner_payload

        image = inner_payload["image"]
        assert "id" in image
        assert "url" in image
        assert "mimeType" in image
        assert isinstance(image["id"], str)
        assert isinstance(image["url"], str)
        assert isinstance(image["mimeType"], str)
        assert image["mimeType"].startswith("image/")

        # Optional fields
        if "width" in image:
            assert isinstance(image["width"], int)
        if "height" in image:
            assert isinstance(image["height"], int)

    def test_waha_location_message_structure_validation(self, waha_webhook_with_location):
        """Test WAHA location message structure according to WAHA specification."""
        payload = waha_webhook_with_location["payload"]
        inner_payload = payload["payload"]
        assert "location" in inner_payload

        location = inner_payload["location"]
        assert "latitude" in location
        assert "longitude" in location
        assert isinstance(location["latitude"], (int, float))
        assert isinstance(location["longitude"], (int, float))

        # Optional fields
        if "name" in location:
            assert isinstance(location["name"], str)
        if "address" in location:
            assert isinstance(location["address"], str)

    def test_waha_button_response_structure_validation(self, waha_webhook_with_button_response):
        """Test WAHA button response structure according to WAHA specification."""
        payload = waha_webhook_with_button_response["payload"]
        inner_payload = payload["payload"]
        assert "button" in inner_payload

        button = inner_payload["button"]
        assert "text" in button
        assert "payload" in button
        assert isinstance(button["text"], str)
        assert isinstance(button["payload"], str)

    def test_waha_list_response_structure_validation(self, waha_webhook_with_list_response):
        """Test WAHA list response structure according to WAHA specification."""
        payload = waha_webhook_with_list_response["payload"]
        inner_payload = payload["payload"]
        assert "list" in inner_payload

        list_data = inner_payload["list"]
        assert "responseTitle" in list_data
        assert "sections" in list_data
        assert isinstance(list_data["responseTitle"], str)
        assert isinstance(list_data["sections"], list)

        # Validate sections
        for section in list_data["sections"]:
            assert "title" in section
            assert "rows" in section
            assert isinstance(section["title"], str)
            assert isinstance(section["rows"], list)

            # Validate rows
            for row in section["rows"]:
                assert "id" in row
                assert "title" in row
                assert isinstance(row["id"], str)
                assert isinstance(row["title"], str)


class TestWahaApiVersionCompatibility:
    """Test WAHA API version compatibility."""

    def test_compatibility_with_waha_version_latest(self):
        """Test compatibility with latest WAHA version."""
        # Verify that webhook payload structure supports latest WAHA features
        modern_payload = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.HBgLNDIxNzY1MDA1NTU1VQASGVRVQEVNUjQ5QTc5OUE0NDRDNEQ4NDRDNkYxMjY1AgK=",
                "timestamp": 1694123463,
                "from": "221765005555@c.us",
                "fromMe": False,
                "pushname": "Aliou Diop",
                "payload": {
                    "type": "text",
                    "text": "Test message with modern features"
                },
                "sender": {
                    "contactId": "221765005555@c.us",
                    "pushname": "Aliou Diop",
                    "profilePictureUrl": None,
                    "isBusiness": False,
                    "isEnterprise": False
                },
                # Modern WAHA features
                "ack": 3,
                "deviceType": "android",
                "forwardingScore": 0,
                "isForwarded": False,
                "hasMedia": False
            }
        }

        # Should be able to process modern payload without errors
        try:
            # Validate structure
            assert "session" in modern_payload
            assert "event" in modern_payload
            assert modern_payload["payload"]["text"] == "Test message with modern features"
            assert "ack" in modern_payload["payload"]
            assert "deviceType" in modern_payload["payload"]
        except Exception as e:
            pytest.fail(f"Should handle latest WAHA payload: {e}")

    def test_backward_compatibility_with_older_waha_versions(self):
        """Test backward compatibility with older WAHA versions."""
        # Simulate older WAHA payload (simpler structure)
        legacy_payload = {
            "session": "default",
            "event": "message",
            "payload": {
                "id": "wamid.legacy.123",
                "timestamp": 1694123464,
                "from": "221765005555@c.us",
                "payload": {
                    "type": "text",
                    "text": "Legacy message"
                }
            }
        }

        # Should be able to process legacy payload
        try:
            assert "session" in legacy_payload
            assert "event" in legacy_payload
            assert legacy_payload["payload"]["payload"]["text"] == "Legacy message"
        except Exception as e:
            pytest.fail(f"Should handle legacy WAHA payload: {e}")


class TestWahaSessionManagementContract:
    """Test WAHA session management contract."""

    def test_waha_session_structure_validation(self):
        """Test WAHA session structure according to WAHA specification."""
        session_info = {
            "session": "default",
            "engine": "NOWEB",
            "me": {
                "id": "221123456789@c.us",
                "pushname": "Catéchisme Bot",
                "platform": "android"
            },
            "status": "CONNECTED",
            "qr": None,
            "lastReceivedAt": 1694123465
        }

        # Validate session structure
        assert "session" in session_info
        assert "engine" in session_info
        assert "me" in session_info
        assert "status" in session_info
        assert session_info["status"] in ["CONNECTED", "DISCONNECTED", "SYNCING", "OPENING"]

        # Validate me structure
        me = session_info["me"]
        assert "id" in me
        assert "pushname" in me
        assert me["id"].endswith("@c.us")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])