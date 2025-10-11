"""
Telegram Webhook Handler for Account Creation

This module handles incoming Telegram webhooks for automatic account creation,
including message processing, phone number extraction, and account creation workflow.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import re

from src.services.account_service import AccountService, AccountCreationResult, AccountCreationRequest
from src.services.session_service import SessionService, AccountCreationSession
from src.utils.audit_logger import AuditLogger
from src.utils.phone_validator import PhoneNumberValidationResult
from src.models.account import UserAccount


class TelegramWebhookHandler:
    """Handler for Telegram webhook events related to account creation."""

    def __init__(
        self,
        account_service: AccountService,
        session_service: SessionService,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize Telegram webhook handler.

        Args:
            account_service: Account service for creating accounts
            session_service: Session service for managing conversations
            audit_logger: Optional audit logger
        """
        self.account_service = account_service
        self.session_service = session_service
        self.audit_logger = audit_logger
        self.logger = logging.getLogger(__name__)

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming Telegram webhook.

        Args:
            webhook_data: Telegram webhook payload

        Returns:
            Processing result
        """
        try:
            # Extract message data
            if "message" not in webhook_data:
                return self._create_error_result("No message in webhook", "NO_MESSAGE")

            message = webhook_data["message"]
            from_user = message.get("from", {})
            chat = message.get("chat", {})

            # Extract user info
            platform_user_id = str(from_user.get("id", ""))
            chat_id = str(chat.get("id", ""))
            user_name = from_user.get("first_name", "")

            # Log webhook received
            if self.audit_logger:
                await self.audit_logger.log_webhook_received(
                    platform="telegram",
                    platform_user_id=platform_user_id,
                    event_type="account_creation"
                )

            # Process the message
            result = await self.process_message(message, platform_user_id, chat_id, user_name)

            return result

        except Exception as e:
            self.logger.error(f"Error processing Telegram webhook: {str(e)}")
            return self._create_error_result(f"Webhook processing failed: {str(e)}", "PROCESSING_ERROR")

    async def process_message(
        self,
        message: Dict[str, Any],
        platform_user_id: str,
        chat_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Process Telegram message for account creation.

        Args:
            message: Telegram message object
            platform_user_id: Telegram user ID
            chat_id: Telegram chat ID
            user_name: User name from Telegram

        Returns:
            Processing result
        """
        try:
            # Extract phone number from message
            phone_number = await self.extract_phone_number(message)

            if not phone_number:
                # No phone number found, ask for it
                await self.send_phone_request_message(chat_id)
                return self._create_success_result("Phone number requested", "PHONE_REQUESTED")

            # Check if there's an existing session
            existing_session = await self.get_existing_session(platform_user_id)
            if existing_session and existing_session.status == "phone_provided":
                # Phone already provided, proceed with account creation
                return await self.process_account_creation_flow(
                    message, platform_user_id, chat_id, user_name, phone_number, existing_session
                )

            # New phone number provided, start account creation
            return await self.process_account_creation_flow(
                message, platform_user_id, chat_id, user_name, phone_number
            )

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return self._create_error_result(f"Message processing failed: {str(e)}", "MESSAGE_PROCESSING_ERROR")

    async def extract_phone_number(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Extract phone number from Telegram message.

        Args:
            message: Telegram message object

        Returns:
            Extracted phone number or None
        """
        try:
            # Method 1: Check for contact message
            if "contact" in message:
                contact = message["contact"]
                phone_number = contact.get("phone_number")
                if phone_number:
                    self.logger.info(f"Phone number extracted from contact: {phone_number}")
                    return phone_number

            # Method 2: Check for phone number in text message
            text = message.get("text", "")
            if text:
                # Look for phone number patterns
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
                        self.logger.info(f"Phone number extracted from text: {phone_number}")
                        return phone_number

            # Method 3: Check if user mentioned their number in common formats
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
                        self.logger.info(f"Phone number extracted from context: {phone_number}")
                        return phone_number

            return None

        except Exception as e:
            self.logger.error(f"Error extracting phone number: {str(e)}")
            return None

    async def process_account_creation_flow(
        self,
        message: Dict[str, Any],
        platform_user_id: str,
        chat_id: str,
        user_name: str,
        phone_number: str,
        existing_session: Optional[AccountCreationSession] = None
    ) -> Dict[str, Any]:
        """
        Process complete account creation flow.

        Args:
            message: Telegram message object
            platform_user_id: Telegram user ID
            chat_id: Telegram chat ID
            user_name: User name from Telegram
            phone_number: Extracted phone number
            existing_session: Existing session if any

        Returns:
            Processing result
        """
        try:
            # Create or update session
            session = await self.create_account_creation_session(
                platform="telegram",
                platform_user_id=platform_user_id,
                phone_number=phone_number
            )

            # Create account creation request
            request = AccountCreationRequest(
                phone_number=phone_number,
                platform="telegram",
                platform_user_id=platform_user_id,
                source="webhook",
                user_consent=True,
                metadata={
                    "chat_id": chat_id,
                    "user_name": user_name,
                    "message_id": message.get("message_id"),
                    "timestamp": message.get("date")
                }
            )

            # Attempt account creation
            result = await self.account_service.create_account(request)

            if result.success and result.account:
                # Send welcome message
                await self.send_welcome_message(chat_id, result.account)

                # Update session status
                if session:
                    await self.update_session_status(session.session_id, "account_created")

                return self._create_success_result(
                    "Account created successfully",
                    "ACCOUNT_CREATED",
                    {"account": result.account.to_dict() if hasattr(result.account, 'to_dict') else str(result.account)}
                )
            else:
                # Send error message
                await self.send_error_message(chat_id, result.error_message or "Account creation failed")

                # Update session status
                if session:
                    await self.update_session_status(session.session_id, "creation_failed")

                return self._create_error_result(
                    result.error_message or "Account creation failed",
                    result.error_code or "CREATION_FAILED"
                )

        except Exception as e:
            self.logger.error(f"Error in account creation flow: {str(e)}")
            await self.send_error_message(chat_id, "An error occurred while creating your account. Please try again.")
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
                status="initiated"
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
                platform="telegram",
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

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        """
        Send message to Telegram user.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode (HTML or Markdown)

        Returns:
            Send result
        """
        try:
            # This would integrate with the actual Telegram Bot API
            # For now, return a mock result
            self.logger.info(f"Sending message to {chat_id}: {text[:100]}...")

            return {
                "ok": True,
                "result": {
                    "message_id": f"msg_{datetime.utcnow().timestamp()}",
                    "chat": {"id": chat_id},
                    "text": text,
                    "date": int(datetime.utcnow().timestamp())
                }
            }
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def send_welcome_message(self, chat_id: str, account: UserAccount) -> Dict[str, Any]:
        """
        Send welcome message after successful account creation.

        Args:
            chat_id: Telegram chat ID
            account: Created user account

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

            return await self.send_message(chat_id, welcome_text)

        except Exception as e:
            self.logger.error(f"Error sending welcome message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def send_error_message(self, chat_id: str, error_message: str) -> Dict[str, Any]:
        """
        Send error message to user.

        Args:
            chat_id: Telegram chat ID
            error_message: Error message

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

            return await self.send_message(chat_id, error_text)

        except Exception as e:
            self.logger.error(f"Error sending error message: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def send_phone_request_message(self, chat_id: str) -> Dict[str, Any]:
        """
        Send message requesting phone number.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Send result
        """
        try:
            request_text = """
👋 Bienvenue sur le service de catéchèse!

Pour créer votre compte parent, veuillez nous fournir votre numéro de téléphone.

Vous pouvez:
• Envoyer votre contact depuis votre répertoire
• Écrire votre numéro au format: +221 7X XXX XX XX
• Utiliser les formats: 00221 7X XXX XX XX ou 7X XXX XX XX

Exemples:
• +221 76 500 55 55
• 00221 77 123 45 67
• 78 912 34 56

Une fois votre numéro vérifié, nous créerons automatiquement votre compte.
            """.strip()

            return await self.send_message(chat_id, request_text)

        except Exception as e:
            self.logger.error(f"Error sending phone request message: {str(e)}")
            return {"ok": False, "error": str(e)}

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
telegram_webhook_handler = None


def initialize_telegram_webhook_handler(
    account_service: AccountService,
    session_service: SessionService,
    audit_logger: Optional[AuditLogger] = None
) -> TelegramWebhookHandler:
    """
    Initialize global Telegram webhook handler.

    Args:
        account_service: Account service instance
        session_service: Session service instance
        audit_logger: Optional audit logger

    Returns:
        Initialized handler instance
    """
    global telegram_webhook_handler
    telegram_webhook_handler = TelegramWebhookHandler(
        account_service=account_service,
        session_service=session_service,
        audit_logger=audit_logger
    )
    return telegram_webhook_handler


async def handle_telegram_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming Telegram webhook (convenience function).

    Args:
        webhook_data: Telegram webhook payload

    Returns:
        Processing result
    """
    if not telegram_webhook_handler:
        return {
            "success": False,
            "message": "Telegram webhook handler not initialized",
            "error_code": "HANDLER_NOT_INITIALIZED"
        }

    return await telegram_webhook_handler.process_webhook(webhook_data)