"""
Telegram Webhook Handler Service

This service handles incoming Telegram webhooks with message parsing,
user authentication, and integration with the account creation system.
Enhanced for Phase 3 with comprehensive Telegram message processing.
"""

import json
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


class TelegramUser:
    """Data class for Telegram user information."""

    def __init__(
        self,
        user_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: Optional[str] = None,
        is_bot: bool = False
    ):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.language_code = language_code
        self.is_bot = is_bot

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        name = self.first_name
        if self.last_name:
            name += f" {self.last_name}"
        return name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "language_code": self.language_code,
            "full_name": self.full_name,
            "is_bot": self.is_bot
        }


class TelegramMessage:
    """Data class for Telegram message."""

    def __init__(
        self,
        message_id: int,
        user: TelegramUser,
        chat_id: int,
        message_type: str,
        content: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message_id = message_id
        self.user = user
        self.chat_id = chat_id
        self.message_type = message_type
        self.content = content
        self.timestamp = timestamp
        self.metadata = metadata or {}

    @property
    def from_user_id(self) -> str:
        """Get platform user ID."""
        return str(self.user.user_id)


class TelegramWebhookHandler:
    """
    Service for handling Telegram webhooks with authentication and validation.

    This service processes incoming Telegram webhooks, authenticates users,
    parses messages, and integrates with the account creation workflow.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        account_service=None,
        session_service=None
    ):
        """
        Initialize Telegram webhook handler.

        Args:
            bot_token: Telegram bot token for authentication
            account_service: Account service instance
            session_service: Session management service instance
        """
        self.bot_token = bot_token
        self.account_service = account_service or get_account_service()
        self.session_service = session_service or get_session_management_service()
        self.logger = get_logger(__name__)

    async def verify_webhook_token(self, token: str) -> bool:
        """
        Verify Telegram webhook setup token.

        Args:
            token: Token from webhook setup

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # In production, this should match your configured secret
            expected_token = "your_telegram_webhook_token"
            is_valid = token == expected_token

            if is_valid:
                self.logger.info("Telegram webhook token verified")
            else:
                self.logger.warning("Invalid Telegram webhook token")

            return is_valid

        except Exception as e:
            self.logger.error(f"Error verifying webhook token: {str(e)}")
            return False

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming Telegram webhook.

        Args:
            webhook_data: Parsed webhook JSON data

        Returns:
            Processing result with status and response
        """
        try:
            # Log webhook received
            await log_account_creation_event(
                webhook_data=json.dumps(webhook_data, default=str),
                event_type="telegram_webhook_received"
            )

            # Handle different update types
            update_type = webhook_data.get('update_type') or self._determine_update_type(webhook_data)

            if update_type == 'message':
                return await self._handle_message(webhook_data)
            elif update_type == 'callback_query':
                return await self._handle_callback_query(webhook_data)
            elif update_type == 'inline_query':
                return await self._handle_inline_query(webhook_data)
            elif update_type == 'pre_checkout_query':
                return await self._handle_pre_checkout_query(webhook_data)
            else:
                # Handle other update types
                return await self._handle_generic_update(webhook_data, update_type)

        except Exception as e:
            self.logger.error(f"Error processing webhook: {str(e)}")
            raise WebhookProcessingError(f"Webhook processing failed: {str(e)}")

    def _determine_update_type(self, webhook_data: Dict[str, Any]) -> str:
        """
        Determine the type of Telegram update.

        Args:
            webhook_data: Webhook data

        Returns:
            Update type string
        """
        if 'message' in webhook_data:
            return 'message'
        elif 'callback_query' in webhook_data:
            return 'callback_query'
        elif 'inline_query' in webhook_data:
            return 'inline_query'
        elif 'pre_checkout_query' in webhook_data:
            return 'pre_checkout_query'
        elif 'channel_post' in webhook_data:
            return 'channel_post'
        elif 'edited_message' in webhook_data:
            return 'edited_message'
        elif 'edited_channel_post' in webhook_data:
            return 'edited_channel_post'
        elif 'shipping_query' in webhook_data:
            return 'shipping_query'
        else:
            return 'unknown'

    async def _handle_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming message from Telegram.

        Args:
            webhook_data: Webhook data with message

        Returns:
            Processing result
        """
        try:
            message_data = webhook_data.get('message', {})
            message = await self._parse_message(message_data)

            if not message:
                return {
                    "status": "error",
                    "message": "Failed to parse message"
                }

            # Skip messages from bots
            if message.user.is_bot:
                return {
                    "status": "skipped",
                    "message": "Bot message ignored"
                }

            # Process the message
            result = await self._process_message(message)

            return {
                "status": "processed",
                "update_id": webhook_data.get('update_id'),
                "message_id": message.message_id,
                "result": result
            }

        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            return {
                "status": "error",
                "message": f"Message handling failed: {str(e)}"
            }

    async def _handle_callback_query(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle callback query from inline keyboard.

        Args:
            webhook_data: Webhook data with callback query

        Returns:
            Processing result
        """
        try:
            callback_data = webhook_data.get('callback_query', {})
            user = callback_data.get('from', {})
            user_id = user.get('id')
            data = callback_data.get('data', '')

            self.logger.info(f"Callback query from user {user_id}: {data}")

            # Process callback data (could be for account creation)
            if data.startswith('account_creation:'):
                return await self._handle_account_creation_callback(callback_data)

            return {
                "status": "processed",
                "callback_data": data,
                "user_id": user_id
            }

        except Exception as e:
            self.logger.error(f"Error handling callback query: {str(e)}")
            return {
                "status": "error",
                "message": f"Callback query handling failed: {str(e)}"
            }

    async def _handle_inline_query(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inline query."""
        return {
            "status": "processed",
            "message": "Inline query received"
        }

    async def _handle_pre_checkout_query(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pre-checkout query."""
        return {
            "status": "processed",
            "message": "Pre-checkout query received"
        }

    async def _handle_generic_update(self, webhook_data: Dict[str, Any], update_type: str) -> Dict[str, Any]:
        """Handle generic update types."""
        self.logger.info(f"Generic update received: {update_type}")
        return {
            "status": "processed",
            "update_type": update_type
        }

    async def _parse_message(self, message_data: Dict[str, Any]) -> Optional[TelegramMessage]:
        """
        Parse Telegram message data.

        Args:
            message_data: Raw message data from webhook

        Returns:
            Parsed message object
        """
        try:
            message_id = message_data.get('message_id')
            chat_data = message_data.get('chat', {})
            user_data = message_data.get('from', {})

            # Parse user information
            user = TelegramUser(
                user_id=user_data.get('id'),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name'),
                username=user_data.get('username'),
                language_code=user_data.get('language_code'),
                is_bot=user_data.get('is_bot', False)
            )

            # Parse timestamp
            timestamp = datetime.fromtimestamp(
                message_data.get('date', 0),
                timezone.utc
            )

            # Determine message type and content
            message_type, content = self._extract_message_content(message_data)

            # Additional metadata
            metadata = {
                'chat_id': chat_data.get('id'),
                'chat_type': chat_data.get('type'),
                'raw_data': message_data
            }

            message = TelegramMessage(
                message_id=message_id,
                user=user,
                chat_id=chat_data.get('id'),
                message_type=message_type,
                content=content,
                timestamp=timestamp,
                metadata=metadata
            )

            self.logger.info(
                f"Parsed Telegram message: {message_type} from {user.user_id} ({user.full_name})"
            )
            return message

        except Exception as e:
            self.logger.error(f"Error parsing message: {str(e)}")
            return None

    def _extract_message_content(self, message_data: Dict[str, Any]) -> tuple[str, str]:
        """
        Extract message type and content from message data.

        Args:
            message_data: Raw message data

        Returns:
            Tuple of (message_type, content)
        """
        if 'text' in message_data:
            return 'text', message_data['text']

        elif 'photo' in message_data:
            photo = message_data['photo'][-1]  # Get largest photo
            caption = message_data.get('caption', '')
            return 'photo', f"[Photo] {caption}" if caption else "[Photo]"

        elif 'video' in message_data:
            caption = message_data.get('caption', '')
            return 'video', f"[Video] {caption}" if caption else "[Video]"

        elif 'audio' in message_data:
            return 'audio', "[Audio message]"

        elif 'voice' in message_data:
            return 'voice', "[Voice message]"

        elif 'document' in message_data:
            document = message_data['document']
            file_name = document.get('file_name', 'document')
            return 'document', f"[Document: {file_name}]"

        elif 'sticker' in message_data:
            return 'sticker', "[Sticker]"

        elif 'animation' in message_data:
            return 'animation', "[Animation/GIF]"

        elif 'contact' in message_data:
            contact = message_data['contact']
            phone = contact.get('phone_number', '')
            name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
            return 'contact', f"[Contact: {name} ({phone})]"

        elif 'location' in message_data:
            location = message_data['location']
            lat = location.get('latitude', 0)
            lon = location.get('longitude', 0)
            return 'location', f"[Location: {lat}, {lon}]"

        elif 'venue' in message_data:
            venue = message_data['venue']
            return 'venue', f"[Venue: {venue.get('title', '')}]"

        elif 'poll' in message_data:
            poll = message_data['poll']
            return 'poll', f"[Poll: {poll.get('question', '')}]"

        elif 'new_chat_members' in message_data:
            members = message_data['new_chat_members']
            return 'new_chat_members', f"[New members: {len(members)}]"

        elif 'left_chat_member' in message_data:
            member = message_data['left_chat_member']
            name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
            return 'left_chat_member', f"[Member left: {name}]"

        else:
            return 'unknown', "[Unknown message type]"

    async def _process_message(self, message: TelegramMessage) -> Dict[str, Any]:
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
            'account', 'register', 'create', 'sign up',
            '/start', '/register', '/create'
        ]

        content_lower = content.lower().strip()
        return any(keyword in content_lower for keyword in account_creation_keywords)

    async def _handle_account_creation_request(self, message: TelegramMessage) -> Dict[str, Any]:
        """
        Handle account creation request from Telegram message.

        Args:
            message: Telegram message

        Returns:
            Processing result
        """
        try:
            from src.services.account_service import AccountCreationRequest

            # Try to get phone number from user profile or ask for it
            phone_number = await self._get_user_phone_number(message.user)

            if not phone_number:
                # Request phone number from user
                await self._request_phone_number(message.chat_id)
                return {
                    "message_id": message.message_id,
                    "status": "phone_number_requested",
                    "user_id": message.from_user_id
                }

            # Create account creation request
            request = AccountCreationRequest(
                phone_number=phone_number,
                platform="telegram",
                platform_user_id=message.from_user_id,
                user_consent=True,  # Message implies consent
                source="telegram_webhook",
                metadata={
                    "message_id": message.message_id,
                    "user_info": message.user.to_dict(),
                    "message_content": message.content,
                    "message_type": message.message_type,
                    "chat_id": message.chat_id
                }
            )

            # Process account creation
            result = await self.account_service.create_account(request)

            # Get or create session
            if result.success and result.account:
                await self.session_service.create_session(
                    user_id=result.account.id,
                    platform="telegram",
                    platform_user_id=message.from_user_id,
                    metadata={"source": "account_creation", "chat_id": message.chat_id}
                )

            # Log the attempt
            await log_account_creation_event(
                phone_number=phone_number,
                platform="telegram",
                platform_user_id=message.from_user_id,
                event_type="telegram_account_creation_attempt",
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

    async def _handle_general_message(self, message: TelegramMessage) -> Dict[str, Any]:
        """
        Handle general (non-account creation) message.

        Args:
            message: Telegram message

        Returns:
            Processing result
        """
        try:
            # Check if user has an active session
            session = await self.session_service.get_active_session(
                user_id=None,  # We don't have user_id yet
                platform="telegram",
                platform_user_id=message.from_user_id
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
                platform_user_id=message.from_user_id,
                platform="telegram",
                event_type="telegram_general_message",
                message_content=message.content,
                session_status=session_status,
                user_info=message.user.to_dict()
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

    async def _get_user_phone_number(self, user: TelegramUser) -> Optional[str]:
        """
        Get user's phone number from cached data or database.

        Args:
            user: Telegram user

        Returns:
            Phone number if available, None otherwise
        """
        try:
            # Look up existing account by platform user ID
            account = await self.account_service.get_account_by_platform(
                "telegram",
                user.user_id
            )

            if account:
                return account.phone_number

            return None

        except Exception as e:
            self.logger.error(f"Error getting user phone number: {str(e)}")
            return None

    async def _request_phone_number(self, chat_id: int) -> None:
        """
        Request phone number from user via Telegram API.

        Args:
            chat_id: Chat ID to send request to
        """
        try:
            # This would integrate with your Telegram bot client
            # For now, just log the action
            self.logger.info(f"Phone number request prepared for chat {chat_id}")

            # Implementation would go here
            # await self.telegram_client.request_phone_number(
            #     chat_id,
            #     "Pour créer votre compte, veuillez partager votre numéro de téléphone."
            # )

        except Exception as e:
            self.logger.error(f"Error requesting phone number: {str(e)}")

    async def _handle_account_creation_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle account creation callback from inline keyboard.

        Args:
            callback_data: Callback query data

        Returns:
            Processing result
        """
        try:
            data = callback_data.get('data', '')
            user = callback_data.get('from', {})

            # Parse callback data
            if data.startswith('account_creation:confirm:'):
                phone_number = data.split(':')[2]
                # Process account creation with confirmed phone number
                return await self._process_confirmed_account_creation(
                    user, phone_number, callback_data
                )

            return {
                "status": "processed",
                "callback_data": data,
                "user_id": user.get('id')
            }

        except Exception as e:
            self.logger.error(f"Error handling account creation callback: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _process_confirmed_account_creation(
        self,
        user: Dict[str, Any],
        phone_number: str,
        callback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process confirmed account creation from callback."""
        try:
            from src.services.account_service import AccountCreationRequest

            # Create account creation request
            request = AccountCreationRequest(
                phone_number=phone_number,
                platform="telegram",
                platform_user_id=str(user.get('id')),
                user_consent=True,
                source="telegram_callback",
                metadata={
                    "user_info": user,
                    "callback_data": callback_data
                }
            )

            # Process account creation
            result = await self.account_service.create_account(request)

            return {
                "status": "account_creation_processed",
                "success": result.success,
                "error_code": result.error_code,
                "error_message": result.error_message
            }

        except Exception as e:
            self.logger.error(f"Error processing confirmed account creation: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def send_message(self, chat_id: int, content: str, message_type: str = "text") -> Dict[str, Any]:
        """
        Send message via Telegram API.

        Args:
            chat_id: Chat ID to send message to
            content: Message content
            message_type: Message type (text, photo, etc.)

        Returns:
            Send result
        """
        try:
            # This would integrate with your Telegram bot client
            # For now, just log the attempt
            self.logger.info(f"Telegram message prepared for chat {chat_id}: {content[:50]}...")

            # Implementation would go here
            # await self.telegram_client.send_message(chat_id, content, message_type)

            return {
                "status": "sent",
                "chat_id": chat_id,
                "message_type": message_type,
                "content_length": len(content)
            }

        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }


# Factory function for getting Telegram webhook handler
def get_telegram_webhook_handler(bot_token: str = None) -> TelegramWebhookHandler:
    """Get Telegram webhook handler instance."""
    return TelegramWebhookHandler(bot_token=bot_token)