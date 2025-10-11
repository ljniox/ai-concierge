"""
WhatsApp Webhook Handler for Account Creation

This module handles incoming WhatsApp webhooks (via WAHA) for automatic account creation,
including message processing, phone number extraction, vCard parsing, and account creation workflow.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import re
import json

from src.services.account_service import AccountService, AccountCreationResult, AccountCreationRequest
from src.services.session_service import SessionService, AccountCreationSession
from src.utils.audit_logger import AuditLogger
from src.utils.phone_validator import PhoneNumberValidationResult
from src.models.account import UserAccount


class WhatsAppWebhookHandler:
    """Handler for WhatsApp webhook events (WAHA) related to account creation."""

    def __init__(
        self,
        account_service: AccountService,
        session_service: SessionService,
        audit_logger: Optional[AuditLogger] = None,
        waha_base_url: Optional[str] = None,
        waha_token: Optional[str] = None
    ):
        """
        Initialize WhatsApp webhook handler.

        Args:
            account_service: Account service for creating accounts
            session_service: Session service for managing conversations
            audit_logger: Optional audit logger
            waha_base_url: WAHA API base URL
            waha_token: WAHA API token
        """
        self.account_service = account_service
        self.session_service = session_service
        self.audit_logger = audit_logger
        self.waha_base_url = waha_base_url
        self.waha_token = waha_token
        self.logger = logging.getLogger(__name__)

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming WhatsApp webhook (WAHA format).

        Args:
            webhook_data: WAHA webhook payload

        Returns:
            Processing result
        """
        try:
            # Validate webhook structure
            if "event" not in webhook_data or webhook_data["event"] != "message":
                return self._create_error_result("Not a message event", "NOT_MESSAGE_EVENT")

            if "payload" not in webhook_data:
                return self._create_error_result("No payload in webhook", "NO_PAYLOAD")

            payload = webhook_data["payload"]
            session = webhook_data.get("session", "default")

            # Extract message data
            from_field = payload.get("from", "")
            pushname = payload.get("pushname", "")
            timestamp = payload.get("timestamp", int(datetime.utcnow().timestamp()))

            # Extract platform user ID (remove @c.us suffix)
            platform_user_id = from_field.replace("@c.us", "")
            chat_id = from_field
            user_name = pushname or "Parent"

            # Log webhook received
            if self.audit_logger:
                await self.audit_logger.log_webhook_received(
                    platform="whatsapp",
                    platform_user_id=platform_user_id,
                    event_type="account_creation"
                )

            # Process the message
            result = await self.process_message(payload, platform_user_id, chat_id, user_name, session)

            return result

        except Exception as e:
            self.logger.error(f"Error processing WhatsApp webhook: {str(e)}")
            return self._create_error_result(f"Webhook processing failed: {str(e)}", "PROCESSING_ERROR")

    async def process_message(
        self,
        payload: Dict[str, Any],
        platform_user_id: str,
        chat_id: str,
        user_name: str,
        session: str = "default"
    ) -> Dict[str, Any]:
        """
        Process WhatsApp message for account creation.

        Args:
            payload: WAHA message payload
            platform_user_id: WhatsApp user ID
            chat_id: WhatsApp chat ID
            user_name: User name from WhatsApp
            session: WAHA session name

        Returns:
            Processing result
        """
        try:
            # Extract phone number from message
            phone_number = await self.extract_phone_number(payload)

            if not phone_number:
                # No phone number found, ask for it
                await self.send_phone_request_message(chat_id, session)
                return self._create_success_result("Phone number requested", "PHONE_REQUESTED")

            # Check if there's an existing session
            existing_session = await self.get_existing_session(platform_user_id)
            if existing_session and existing_session.status == "phone_provided":
                # Phone already provided, proceed with account creation
                return await self.process_account_creation_flow(
                    payload, platform_user_id, chat_id, user_name, phone_number, session, existing_session
                )

            # New phone number provided, start account creation
            return await self.process_account_creation_flow(
                payload, platform_user_id, chat_id, user_name, phone_number, session
            )

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return self._create_error_result(f"Message processing failed: {str(e)}", "MESSAGE_PROCESSING_ERROR")

    async def extract_phone_number(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract phone number from WhatsApp message.

        Args:
            payload: WAHA message payload

        Returns:
            Extracted phone number or None
        """
        try:
            message_payload = payload.get("payload", {})
            message_type = message_payload.get("type", "")

            # Method 1: Extract from contact message/vCard
            if message_type == "contact" and "contact" in message_payload:
                contact = message_payload["contact"]

                # Check vCard first
                vcard = contact.get("vcard", "")
                if vcard:
                    phone_number = self._extract_phone_from_vcard(vcard)
                    if phone_number:
                        self.logger.info(f"Phone number extracted from vCard: {phone_number}")
                        return phone_number

                # Check direct phone number field
                phone_number = contact.get("phone_number")
                if phone_number:
                    self.logger.info(f"Phone number extracted from contact: {phone_number}")
                    return phone_number

            # Method 2: Extract from sender info (for WhatsApp, the sender ID is often the phone)
            from_field = payload.get("from", "")
            if from_field and from_field.endswith("@c.us"):
                # Remove @c.us suffix to get phone number
                phone_number = from_field.replace("@c.us", "")
                # Add + if missing and format correctly
                if not phone_number.startswith("+"):
                    phone_number = "+" + phone_number
                self.logger.info(f"Phone number extracted from sender: {phone_number}")
                return phone_number

            # Method 3: Extract from text message
            if message_type == "text" and "text" in message_payload:
                text = message_payload["text"]
                phone_number = self._extract_phone_from_text(text)
                if phone_number:
                    self.logger.info(f"Phone number extracted from text: {phone_number}")
                    return phone_number

            # Method 4: Check interactive message responses
            if message_type in ["button", "list"] and message_payload.get(message_type):
                interactive_data = message_payload[message_type]
                # Look for phone number in interactive response
                text = interactive_data.get("text", "")
                if text:
                    phone_number = self._extract_phone_from_text(text)
                    if phone_number:
                        self.logger.info(f"Phone number extracted from interactive: {phone_number}")
                        return phone_number

            return None

        except Exception as e:
            self.logger.error(f"Error extracting phone number: {str(e)}")
            return None

    def _extract_phone_from_vcard(self, vcard: str) -> Optional[str]:
        """
        Extract phone number from vCard text.

        Args:
            vcard: vCard text

        Returns:
            Phone number or None
        """
        try:
            # Look for TEL;TYPE=CELL pattern in vCard
            tel_pattern = r'TEL;[^:]*:([+0-9\s-]+)'
            match = re.search(tel_pattern, vcard, re.IGNORECASE)
            if match:
                phone_number = match.group(1).strip()
                # Clean up the phone number
                phone_number = re.sub(r'[^\d+]', '', phone_number)
                return phone_number if len(phone_number) >= 8 else None

            # Alternative pattern for simple vCards
            simple_pattern = r'TEL[:\s]*([+0-9\s-]+)'
            match = re.search(simple_pattern, vcard, re.IGNORECASE)
            if match:
                phone_number = match.group(1).strip()
                phone_number = re.sub(r'[^\d+]', '', phone_number)
                return phone_number if len(phone_number) >= 8 else None

            return None

        except Exception as e:
            self.logger.error(f"Error extracting phone from vCard: {str(e)}")
            return None

    def _extract_phone_from_text(self, text: str) -> Optional[str]:
        """
        Extract phone number from text message.

        Args:
            text: Message text

        Returns:
            Phone number or None
        """
        try:
            # Senegal patterns: +221 7X XXX XX XX, 00221 7X XXX XX XX, 7X XXX XX XX
            patterns = [
                r'\+221\s*[7][0-9]\s*\d{3}\s*\d{2}\s*\d{2}',  # +221 7X XXX XX XX
                r'00221\s*[7][0-9]\s*\d{3}\s*\d{2}\s*\d{2}',  # 00221 7X XXX XX XX
                r'[7][0-9]\s*\d{3}\s*\d{2}\s*\d{2}',        # 7X XXX XX XX
                r'\+221\s*[7][0-9]\d{7}',                    # +221 7XXXXXXX
                r'00221\s*[7][0-9]\d{7}',                    # 00221 7XXXXXXX
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    phone_number = match.group().strip()
                    # Format properly with + prefix
                    if not phone_number.startswith("+"):
                        if phone_number.startswith("00221"):
                            phone_number = "+" + phone_number[4:]  # Remove 00221, add +
                        elif phone_number.startswith("221"):
                            phone_number = "+" + phone_number  # Add +
                        else:
                            # Assume Senegal number
                            phone_number = "+221" + phone_number
                    return phone_number

            # Check for common phrases that might contain phone numbers
            common_patterns = [
                r'(?:mon|mon num|numéro|contact|téléphone|tel)\s*[:\s]\s*([+0-9\s-]{8,20})',
                r'(?:c\'est|je suis|appelle moi)\s*([+0-9\s-]{8,20})',
            ]

            for pattern in common_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    phone_number = match.group(1).strip()
                    # Validate if it looks like a phone number
                    if re.match(r'^[+0-9\s-]{8,20}$', phone_number):
                        # Format properly
                        if not phone_number.startswith("+"):
                            if phone_number.startswith("00221"):
                                phone_number = "+" + phone_number[4:]
                            elif phone_number.startswith("221"):
                                phone_number = "+" + phone_number
                            else:
                                phone_number = "+221" + re.sub(r'[^\d]', '', phone_number)
                        return phone_number

            return None

        except Exception as e:
            self.logger.error(f"Error extracting phone from text: {str(e)}")
            return None

    async def process_account_creation_flow(
        self,
        payload: Dict[str, Any],
        platform_user_id: str,
        chat_id: str,
        user_name: str,
        phone_number: str,
        session: str = "default",
        existing_session: Optional[AccountCreationSession] = None
    ) -> Dict[str, Any]:
        """
        Process complete account creation flow.

        Args:
            payload: WAHA message payload
            platform_user_id: WhatsApp user ID
            chat_id: WhatsApp chat ID
            user_name: User name from WhatsApp
            phone_number: Extracted phone number
            session: WAHA session name
            existing_session: Existing session if any

        Returns:
            Processing result
        """
        try:
            # Create or update session
            session_obj = await self.create_account_creation_session(
                platform="whatsapp",
                platform_user_id=platform_user_id,
                phone_number=phone_number
            )

            # Create account creation request
            request = AccountCreationRequest(
                phone_number=phone_number,
                platform="whatsapp",
                platform_user_id=platform_user_id,
                source="webhook",
                user_consent=True,
                metadata={
                    "chat_id": chat_id,
                    "session": session,
                    "user_name": user_name,
                    "timestamp": payload.get("timestamp"),
                    "message_id": payload.get("id")
                }
            )

            # Attempt account creation
            result = await self.account_service.create_account(request)

            if result.success and result.account:
                # Send welcome message
                await self.send_welcome_message(chat_id, result.account, session)

                # Update session status
                if session_obj:
                    await self.update_session_status(session_obj.session_id, "account_created")

                return self._create_success_result(
                    "Account created successfully",
                    "ACCOUNT_CREATED",
                    {"account": result.account.to_dict() if hasattr(result.account, 'to_dict') else str(result.account)}
                )
            else:
                # Send error message
                await self.send_error_message(chat_id, result.error_message or "Account creation failed", session)

                # Update session status
                if session_obj:
                    await self.update_session_status(session_obj.session_id, "creation_failed")

                return self._create_error_result(
                    result.error_message or "Account creation failed",
                    result.error_code or "CREATION_FAILED"
                )

        except Exception as e:
            self.logger.error(f"Error in account creation flow: {str(e)}")
            await self.send_error_message(chat_id, "An error occurred while creating your account. Please try again.", session)
            return self._create_error_result(f"Account creation flow failed: {str(e)}", "FLOW_ERROR")

    async def create_account_creation_session(
        self,
        platform: str,
        platform_user_id: str,
        phone_number: str
    ) -> Optional[AccountCreationSession]:
        """
        Create account creation session.

        Args:
            platform: Platform name
            platform_user_id: Platform user ID
            phone_number: Phone number

        Returns:
            Created session or None
        """
        try:
            session = await self.session_service.create_session(
                platform=platform,
                platform_user_id=platform_user_id,
                session_type="account_creation",
                phone_number=phone_number,
                status="initiated",
                session_data={"waha_session": "default"}
            )

            if self.audit_logger:
                await self.audit_logger.log_session_created(
                    session_id=session.session_id,
                    platform=platform,
                    platform_user_id=platform_user_id,
                    session_type="account_creation"
                )

            return session

        except Exception as e:
            self.logger.error(f"Error creating account creation session: {str(e)}")
            return None

    async def get_existing_session(self, platform_user_id: str) -> Optional[AccountCreationSession]:
        """
        Get existing active session for user.

        Args:
            platform_user_id: Platform user ID

        Returns:
            Existing session or None
        """
        try:
            return await self.session_service.get_active_session(
                platform="whatsapp",
                platform_user_id=platform_user_id
            )
        except Exception as e:
            self.logger.error(f"Error getting existing session: {str(e)}")
            return None

    async def update_session_status(self, session_id: str, status: str) -> bool:
        """
        Update session status.

        Args:
            session_id: Session ID
            status: New status

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session_service.update_session_status(session_id, status)
            return True
        except Exception as e:
            self.logger.error(f"Error updating session status: {str(e)}")
            return False

    async def send_message(self, chat_id: str, text: str, session: str = "default") -> Dict[str, Any]:
        """
        Send message via WAHA API.

        Args:
            chat_id: WhatsApp chat ID
            text: Message text
            session: WAHA session name

        Returns:
            Send result
        """
        try:
            if not self.waha_base_url or not self.waha_token:
                self.logger.warning("WAHA configuration not available, mocking message send")
                return {
                    "id": f"mock_msg_{datetime.utcnow().timestamp()}",
                    "timestamp": int(datetime.utcnow().timestamp())
                }

            # WAHA API endpoint for sending text messages
            url = f"{self.waha_base_url}/api/sendText"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.waha_token}"
            }

            payload = {
                "session": session,
                "chatId": chat_id,
                "text": text
            }

            # This would make an actual HTTP request to WAHA
            # For now, return a mock result
            self.logger.info(f"Sending WAHA message to {chat_id}: {text[:100]}...")

            return {
                "id": f"waha_msg_{datetime.utcnow().timestamp()}",
                "timestamp": int(datetime.utcnow().timestamp())
            }

        except Exception as e:
            self.logger.error(f"Error sending WAHA message: {str(e)}")
            return {"error": str(e)}

    async def send_interactive_message(
        self,
        chat_id: str,
        interactive_content: Dict[str, Any],
        session: str = "default"
    ) -> Dict[str, Any]:
        """
        Send interactive message via WAHA API.

        Args:
            chat_id: WhatsApp chat ID
            interactive_content: Interactive message content
            session: WAHA session name

        Returns:
            Send result
        """
        try:
            if not self.waha_base_url or not self.waha_token:
                self.logger.warning("WAHA configuration not available, mocking interactive message")
                return {
                    "id": f"mock_interactive_{datetime.utcnow().timestamp()}",
                    "timestamp": int(datetime.utcnow().timestamp())
                }

            url = f"{self.waha_base_url}/api/sendInteractive"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.waha_token}"
            }

            payload = {
                "session": session,
                "chatId": chat_id,
                "interactive": interactive_content
            }

            self.logger.info(f"Sending WAHA interactive message to {chat_id}")

            return {
                "id": f"waha_interactive_{datetime.utcnow().timestamp()}",
                "timestamp": int(datetime.utcnow().timestamp())
            }

        except Exception as e:
            self.logger.error(f"Error sending WAHA interactive message: {str(e)}")
            return {"error": str(e)}

    async def send_welcome_message(self, chat_id: str, account: UserAccount, session: str = "default") -> Dict[str, Any]:
        """
        Send welcome message after successful account creation.

        Args:
            chat_id: WhatsApp chat ID
            account: Created user account
            session: WAHA session name

        Returns:
            Send result
        """
        try:
            first_name = account.first_name or account.username or "Parent"

            welcome_text = f"""
🎉 Bienvenue {first_name}!

Votre compte a été créé avec succès sur le système de catéchèse.

📞 Téléphone: {account.phone_number}
👤 Identifiant: {account.username}
🎭 Rôle: Parent
✅ Statut: Actif

Vous pouvez maintenant accéder à toutes les fonctionnalités parentales du service.

Pour commencer, vous pouvez:
• Consulter les informations sur les activités de catéchisme
• Poser des questions sur les horaires et programmes
• Contacter le secrétariat si besoin

Nous sommes ravis de vous avoir parmi nous!
            """.strip()

            return await self.send_message(chat_id, welcome_text, session)

        except Exception as e:
            self.logger.error(f"Error sending welcome message: {str(e)}")
            return {"error": str(e)}

    async def send_error_message(self, chat_id: str, error_message: str, session: str = "default") -> Dict[str, Any]:
        """
        Send error message to user.

        Args:
            chat_id: WhatsApp chat ID
            error_message: Error message
            session: WAHA session name

        Returns:
            Send result
        """
        try:
            error_text = f"""
❌ {error_message}

Si vous pensez qu'il s'agit d'une erreur, veuillez:
• Vérifier que votre numéro de téléphone est correct
• Vous assurer que vous êtes bien inscrit dans la base de données du catéchisme
• Contacter le secrétariat du catéchèse

Vous pouvez réessayer en envoyant à nouveau votre numéro de téléphone.
            """.strip()

            return await self.send_message(chat_id, error_text, session)

        except Exception as e:
            self.logger.error(f"Error sending error message: {str(e)}")
            return {"error": str(e)}

    async def send_phone_request_message(self, chat_id: str, session: str = "default") -> Dict[str, Any]:
        """
        Send message requesting phone number with interactive buttons.

        Args:
            chat_id: WhatsApp chat ID
            session: WAHA session name

        Returns:
            Send result
        """
        try:
            # First send text message
            text_message = """
👋 Bienvenue sur le service de catéchèse!

Pour créer votre compte parent, veuillez nous fournir votre numéro de téléphone.

Veuillez choisir une option ci-dessous:
            """.strip()

            await self.send_message(chat_id, text_message, session)

            # Then send interactive buttons
            interactive_content = {
                "type": "button",
                "body": {
                    "text": "Comment souhaitez-vous fournir votre numéro de téléphone ?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "send_contact",
                                "title": "📱 Envoyer mon contact"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "type_number",
                                "title": "⌨️ Écrire mon numéro"
                            }
                        }
                    ]
                }
            }

            return await self.send_interactive_message(chat_id, interactive_content, session)

        except Exception as e:
            self.logger.error(f"Error sending phone request message: {str(e)}")
            return {"error": str(e)}

    def _create_success_result(
        self,
        message: str,
        result_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create success result."""
        return {
            "success": True,
            "message": message,
            "result_type": result_type,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }

    def _create_error_result(self, message: str, error_code: str) -> Dict[str, Any]:
        """Create error result."""
        return {
            "success": False,
            "message": message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global handler instance (would be initialized with proper dependencies)
whatsapp_webhook_handler = None


def initialize_whatsapp_webhook_handler(
    account_service: AccountService,
    session_service: SessionService,
    audit_logger: Optional[AuditLogger] = None,
    waha_base_url: Optional[str] = None,
    waha_token: Optional[str] = None
) -> WhatsAppWebhookHandler:
    """
    Initialize global WhatsApp webhook handler.

    Args:
        account_service: Account service instance
        session_service: Session service instance
        audit_logger: Optional audit logger
        waha_base_url: WAHA API base URL
        waha_token: WAHA API token

    Returns:
        Initialized handler instance
    """
    global whatsapp_webhook_handler
    whatsapp_webhook_handler = WhatsAppWebhookHandler(
        account_service=account_service,
        session_service=session_service,
        audit_logger=audit_logger,
        waha_base_url=waha_base_url,
        waha_token=waha_token
    )
    return whatsapp_webhook_handler


async def handle_whatsapp_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming WhatsApp webhook (convenience function).

    Args:
        webhook_data: WhatsApp webhook payload

    Returns:
        Processing result
    """
    if not whatsapp_webhook_handler:
        return {
            "success": False,
            "message": "WhatsApp webhook handler not initialized",
            "error_code": "HANDLER_NOT_INITIALIZED"
        }

    return await whatsapp_webhook_handler.process_webhook(webhook_data)