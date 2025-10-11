"""
WhatsApp Webhook Handler Service

This service handles incoming WhatsApp webhooks with signature verification,
message parsing, and integration with the account creation system.
Enhanced for Phase 3 with comprehensive WhatsApp message processing.
"""

import json
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

from src.services.account_service import get_account_service
from src.services.session_management_service import get_session_management_service
from src.services.audit_service import log_account_creation_event
from src.utils.logging import get_logger
from src.utils.exceptions import (
    ValidationError,
    SecurityError,
    WebhookProcessingError
)


class WhatsAppMessage:
    """Data class for WhatsApp message."""

    def __init__(
        self,
        message_id: str,
        from_number: str,
        to_number: str,
        message_type: str,
        content: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message_id = message_id
        self.from_number = from_number
        self.to_number = to_number
        self.message_type = message_type
        self.content = content
        self.timestamp = timestamp
        self.metadata = metadata or {}


class WhatsAppWebhookHandler:
    """
    Service for handling WhatsApp webhooks with security and validation.

    This service processes incoming WhatsApp webhooks, verifies signatures,
    parses messages, and integrates with the account creation workflow.
    """

    def __init__(
        self,
        webhook_secret: Optional[str] = None,
        account_service=None,
        session_service=None
    ):
        """
        Initialize WhatsApp webhook handler.

        Args:
            webhook_secret: Secret for webhook signature verification
            account_service: Account service instance
            session_service: Session management service instance
        """
        self.webhook_secret = webhook_secret
        self.account_service = account_service or get_account_service()
        self.session_service = session_service or get_session_management_service()
        self.logger = get_logger(__name__)

    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: str
    ) -> bool:
        """
        Verify WhatsApp webhook signature.

        Args:
            payload: Raw webhook payload
            signature: X-Hub-Signature-256 header
            timestamp: X-Hub-Signature-timestamp header

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.webhook_secret:
                raise SecurityError("Webhook secret not configured")

            # Check timestamp freshness (within 5 minutes)
            webhook_time = int(timestamp)
            current_time = int(datetime.now(timezone.utc).timestamp())
            if abs(current_time - webhook_time) > 300:  # 5 minutes
                self.logger.warning("Webhook timestamp too old")
                return False

            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                f"{timestamp}.{payload.decode('utf-8')}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            received_signature = signature.replace('sha256=', '')
            is_valid = hmac.compare_digest(expected_signature, received_signature)

            if not is_valid:
                self.logger.warning("Invalid webhook signature")

            return is_valid

        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {str(e)}")
            return False

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming WhatsApp webhook.

        Args:
            webhook_data: Parsed webhook JSON data

        Returns:
            Processing result with status and response
        """
        try:
            # Log webhook received
            await log_account_creation_event(
                webhook_data=json.dumps(webhook_data, default=str),
                event_type="whatsapp_webhook_received"
            )

            # Handle webhook verification (for Meta's webhook setup)
            if 'hub.challenge' in webhook_data:
                return await self._handle_webhook_verification(webhook_data)

            # Handle incoming messages
            if 'entry' in webhook_data:
                return await self._handle_incoming_messages(webhook_data)

            # Handle message status updates
            if 'statuses' in webhook_data:
                return await self._handle_message_status(webhook_data)

            return {
                "status": "processed",
                "message": "Webhook processed successfully"
            }

        except Exception as e:
            self.logger.error(f"Error processing webhook: {str(e)}")
            raise WebhookProcessingError(f"Webhook processing failed: {str(e)}")

    async def _handle_webhook_verification(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle webhook verification for Meta.

        Args:
            webhook_data: Webhook verification data

        Returns:
            Verification response
        """
        try:
            challenge = webhook_data.get('hub.challenge')
            verify_token = webhook_data.get('hub.verify_token')

            # In production, verify_token should match your configured token
            expected_token = "your_verification_token"

            if verify_token == expected_token:
                self.logger.info("WhatsApp webhook verified successfully")
                return {
                    "status": "verified",
                    "challenge": challenge
                }
            else:
                self.logger.warning("Invalid verify token")
                return {
                    "status": "error",
                    "message": "Invalid verify token"
                }

        except Exception as e:
            self.logger.error(f"Error handling webhook verification: {str(e)}")
            return {
                "status": "error",
                "message": "Verification failed"
            }

    async def _handle_incoming_messages(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming messages from WhatsApp.

        Args:
            webhook_data: Webhook data with message entries

        Returns:
            Processing result
        """
        try:
            entries = webhook_data.get('entry', [])
            processed_messages = []

            for entry in entries:
                changes = entry.get('changes', [])

                for change in changes:
                    if change.get('field') == 'messages':
                        messages = change.get('value', {}).get('messages', [])

                        for message_data in messages:
                            # Skip messages sent by our own number
                            if message_data.get('from') == message_data.get('to'):
                                continue

                            # Parse and process message
                            message = await self._parse_message(message_data)
                            if message:
                                result = await self._process_message(message)
                                processed_messages.append(result)

            return {
                "status": "processed",
                "processed_messages": len(processed_messages),
                "results": processed_messages
            }

        except Exception as e:
            self.logger.error(f"Error handling incoming messages: {str(e)}")
            return {
                "status": "error",
                "message": f"Message processing failed: {str(e)}"
            }

    async def _handle_message_status(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle message status updates.

        Args:
            webhook_data: Webhook data with status updates

        Returns:
            Processing result
        """
        try:
            statuses = webhook_data.get('statuses', [])
            processed_statuses = []

            for status in statuses:
                # Log status updates for debugging
                self.logger.info(
                    f"Message status update: {status.get('id')} -> {status.get('status')}"
                )
                processed_statuses.append(status.get('id'))

            return {
                "status": "processed",
                "processed_statuses": len(processed_statuses)
            }

        except Exception as e:
            self.logger.error(f"Error handling message status: {str(e)}")
            return {
                "status": "error",
                "message": f"Status processing failed: {str(e)}"
            }

    async def _parse_message(self, message_data: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Parse WhatsApp message data.

        Args:
            message_data: Raw message data from webhook

        Returns:
            Parsed message object
        """
        try:
            message_id = message_data.get('id')
            from_number = message_data.get('from')
            to_number = message_data.get('to')
            timestamp = datetime.fromtimestamp(
                int(message_data.get('timestamp')),
                timezone.utc
            )

            # Determine message type and content
            message_type = 'text'
            content = ''

            if 'text' in message_data:
                message_type = 'text'
                content = message_data['text'].get('body', '')

            elif 'audio' in message_data:
                message_type = 'audio'
                content = "[Audio message]"

            elif 'image' in message_data:
                message_type = 'image'
                content = "[Image message]"

            elif 'video' in message_data:
                message_type = 'video'
                content = "[Video message]"

            elif 'document' in message_data:
                message_type = 'document'
                content = "[Document message]"

            elif 'interactive' in message_data:
                message_type = 'interactive'
                interactive_data = message_data['interactive']
                if interactive_data.get('type') == 'button_reply':
                    content = interactive_data['button_reply']['title']
                elif interactive_data.get('type') == 'list_reply':
                    content = interactive_data['list_reply']['title']

            # Extract phone number for account lookup
            contact_info = message_data.get('contacts', [])
            contact_name = None
            if contact_info:
                profile_info = contact_info[0].get('profile', {})
                contact_name = profile_info.get('name')

            metadata = {
                'contact_name': contact_name,
                'raw_data': message_data
            }

            message = WhatsAppMessage(
                message_id=message_id,
                from_number=from_number,
                to_number=to_number,
                message_type=message_type,
                content=content,
                timestamp=timestamp,
                metadata=metadata
            )

            self.logger.info(
                f"Parsed WhatsApp message: {message_type} from {from_number}"
            )
            return message

        except Exception as e:
            self.logger.error(f"Error parsing message: {str(e)}")
            return None

    async def _process_message(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Process parsed message for account creation workflow.

        Args:
            message: Parsed message object

        Returns:
            Processing result
        """
        try:
            # Check if this is an account creation request
            is_account_creation = self._is_account_creation_request(message.content)

            if is_account_creation:
                return await self._handle_account_creation_request(message)
            else:
                return await self._handle_general_message(message)

        except Exception as e:
            self.logger.error(f"Error processing message {message.message_id}: {str(e)}")
            return {
                "message_id": message.message_id,
                "status": "error",
                "error": str(e)
            }

    def _is_account_creation_request(self, content: str) -> bool:
        """
        Check if message content indicates an account creation request.

        Args:
            content: Message content

        Returns:
            True if this appears to be an account creation request
        """
        account_creation_keywords = [
            'inscrire', 'inscription', 'compte', 'créer',
            'enregistrer', 'enregistrement', 's\'inscrire',
            'account', 'register', 'create', 'sign up'
        ]

        content_lower = content.lower().strip()
        return any(keyword in content_lower for keyword in account_creation_keywords)

    async def _handle_account_creation_request(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Handle account creation request from WhatsApp message.

        Args:
            message: WhatsApp message

        Returns:
            Processing result
        """
        try:
            from src.services.account_service import AccountCreationRequest

            # Get contact name for better user experience
            contact_name = message.metadata.get('contact_name')

            # Create account creation request
            request = AccountCreationRequest(
                phone_number=message.from_number,
                platform="whatsapp",
                platform_user_id=message.from_number,
                user_consent=True,  # Message implies consent
                source="whatsapp_webhook",
                metadata={
                    "message_id": message.message_id,
                    "contact_name": contact_name,
                    "message_content": message.content,
                    "message_type": message.message_type
                }
            )

            # Process account creation
            result = await self.account_service.create_account(request)

            # Get or create session
            if result.success and result.account:
                await self.session_service.create_session(
                    user_id=result.account.id,
                    platform="whatsapp",
                    platform_user_id=message.from_number,
                    metadata={"source": "account_creation"}
                )

            # Log the attempt
            await log_account_creation_event(
                phone_number=message.from_number,
                platform="whatsapp",
                platform_user_id=message.from_number,
                event_type="whatsapp_account_creation_attempt",
                success=result.success,
                error_message=result.error_message
            )

            return {
                "message_id": message.message_id,
                "status": "account_creation_processed",
                "success": result.success,
                "error_code": result.error_code,
                "error_message": result.error_message
            }

        except Exception as e:
            self.logger.error(f"Error handling account creation request: {str(e)}")
            return {
                "message_id": message.message_id,
                "status": "error",
                "error": str(e)
            }

    async def _handle_general_message(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Handle general (non-account creation) message.

        Args:
            message: WhatsApp message

        Returns:
            Processing result
        """
        try:
            # Check if user has an active session
            session = await self.session_service.get_active_session(
                user_id=None,  # We don't have user_id yet
                platform="whatsapp",
                platform_user_id=message.from_number
            )

            if session:
                # Update session activity
                await self.session_service.update_session(
                    session.id,
                    metadata={"last_message": message.content}
                )
                session_status = "existing_session"
            else:
                # No active session
                session_status = "no_session"

            # Log general message
            await log_account_creation_event(
                phone_number=message.from_number,
                platform="whatsapp",
                platform_user_id=message.from_number,
                event_type="whatsapp_general_message",
                message_content=message.content,
                session_status=session_status
            )

            return {
                "message_id": message.message_id,
                "status": "general_message_processed",
                "session_status": session_status,
                "message_type": message.message_type
            }

        except Exception as e:
            self.logger.error(f"Error handling general message: {str(e)}")
            return {
                "message_id": message.message_id,
                "status": "error",
                "error": str(e)
            }

    async def send_message(self, to_number: str, content: str, message_type: str = "text") -> Dict[str, Any]:
        """
        Send message via WhatsApp API.

        Args:
            to_number: Recipient phone number
            content: Message content
            message_type: Message type (text, interactive, etc.)

        Returns:
            Send result
        """
        try:
            # This would integrate with your WhatsApp API client
            # For now, just log the attempt
            self.logger.info(f"WhatsApp message prepared for {to_number}: {content[:50]}...")

            # Implementation would go here
            # await self.whatsapp_client.send_message(to_number, content, message_type)

            return {
                "status": "sent",
                "to": to_number,
                "message_type": message_type,
                "content_length": len(content)
            }

        except Exception as e:
            self.logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }


# Factory function for getting WhatsApp webhook handler
def get_whatsapp_webhook_handler(webhook_secret: str = None) -> WhatsAppWebhookHandler:
    """Get WhatsApp webhook handler instance."""
    return WhatsAppWebhookHandler(webhook_secret=webhook_secret)