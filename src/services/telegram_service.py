"""
Telegram Bot Service for WhatsApp AI Concierge
Handles Telegram bot integration and message sending
"""

from typing import Optional, Dict, Any, List
import structlog
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.error import TelegramError
from src.utils.config import get_settings

logger = structlog.get_logger()


class TelegramService:
    """Service for handling Telegram bot operations"""

    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Telegram service

        Args:
            bot_token: Telegram bot token (optional, falls back to settings)
        """
        self.settings = get_settings()
        self.bot_token = bot_token or self.settings.telegram_bot_token
        self.bot: Optional[Bot] = None

        if self.bot_token and self.bot_token != "your-telegram-bot-token":
            try:
                self.bot = Bot(token=self.bot_token)
                logger.info("telegram_bot_initialized", bot_token_length=len(self.bot_token))
            except Exception as e:
                logger.error("telegram_bot_initialization_failed", error=str(e))
                self.bot = None
        else:
            logger.warning("telegram_bot_token_not_configured")

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Send a text message to a Telegram chat

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Message parse mode (MARKDOWN, HTML, or None)
            reply_markup: Inline keyboard markup
            disable_web_page_preview: Disable link previews

        Returns:
            Message info dict if successful, None otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return None

        try:
            logger.info("sending_telegram_message", chat_id=chat_id, text_length=len(text))

            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview
            )

            logger.info("telegram_message_sent", chat_id=chat_id, message_id=message.message_id)

            return {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "text": message.text,
                "date": message.date.isoformat() if message.date else None
            }

        except TelegramError as e:
            logger.error("telegram_send_message_error", chat_id=chat_id, error=str(e))
            return None
        except Exception as e:
            logger.error("telegram_send_message_unexpected_error", chat_id=chat_id, error=str(e))
            return None

    async def send_photo(
        self,
        chat_id: int,
        photo_url: str,
        caption: Optional[str] = None,
        parse_mode: str = ParseMode.MARKDOWN
    ) -> Optional[Dict[str, Any]]:
        """
        Send a photo to a Telegram chat

        Args:
            chat_id: Telegram chat ID
            photo_url: Photo URL or file_id
            caption: Photo caption
            parse_mode: Caption parse mode

        Returns:
            Message info dict if successful, None otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return None

        try:
            logger.info("sending_telegram_photo", chat_id=chat_id, photo_url=photo_url)

            message = await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo_url,
                caption=caption,
                parse_mode=parse_mode
            )

            logger.info("telegram_photo_sent", chat_id=chat_id, message_id=message.message_id)

            return {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "date": message.date.isoformat() if message.date else None
            }

        except TelegramError as e:
            logger.error("telegram_send_photo_error", chat_id=chat_id, error=str(e))
            return None
        except Exception as e:
            logger.error("telegram_send_photo_unexpected_error", chat_id=chat_id, error=str(e))
            return None

    async def send_document(
        self,
        chat_id: int,
        document_url: str,
        caption: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a document to a Telegram chat

        Args:
            chat_id: Telegram chat ID
            document_url: Document URL or file_id
            caption: Document caption
            filename: Document filename

        Returns:
            Message info dict if successful, None otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return None

        try:
            logger.info("sending_telegram_document", chat_id=chat_id, filename=filename)

            message = await self.bot.send_document(
                chat_id=chat_id,
                document=document_url,
                caption=caption,
                filename=filename
            )

            logger.info("telegram_document_sent", chat_id=chat_id, message_id=message.message_id)

            return {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "date": message.date.isoformat() if message.date else None
            }

        except TelegramError as e:
            logger.error("telegram_send_document_error", chat_id=chat_id, error=str(e))
            return None
        except Exception as e:
            logger.error("telegram_send_document_unexpected_error", chat_id=chat_id, error=str(e))
            return None

    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Edit an existing message

        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to edit
            text: New message text
            parse_mode: Message parse mode
            reply_markup: Inline keyboard markup

        Returns:
            Message info dict if successful, None otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return None

        try:
            logger.info("editing_telegram_message", chat_id=chat_id, message_id=message_id)

            message = await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )

            logger.info("telegram_message_edited", chat_id=chat_id, message_id=message_id)

            return {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "text": message.text,
                "date": message.date.isoformat() if message.date else None
            }

        except TelegramError as e:
            logger.error("telegram_edit_message_error", chat_id=chat_id, error=str(e))
            return None
        except Exception as e:
            logger.error("telegram_edit_message_unexpected_error", chat_id=chat_id, error=str(e))
            return None

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        """
        Delete a message

        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return False

        try:
            logger.info("deleting_telegram_message", chat_id=chat_id, message_id=message_id)

            await self.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )

            logger.info("telegram_message_deleted", chat_id=chat_id, message_id=message_id)
            return True

        except TelegramError as e:
            logger.error("telegram_delete_message_error", chat_id=chat_id, error=str(e))
            return False
        except Exception as e:
            logger.error("telegram_delete_message_unexpected_error", chat_id=chat_id, error=str(e))
            return False

    async def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the bot

        Returns:
            Bot info dict if successful, None otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return None

        try:
            me = await self.bot.get_me()

            return {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "can_join_groups": me.can_join_groups,
                "can_read_all_group_messages": me.can_read_all_group_messages,
                "supports_inline_queries": me.supports_inline_queries
            }

        except TelegramError as e:
            logger.error("telegram_get_bot_info_error", error=str(e))
            return None
        except Exception as e:
            logger.error("telegram_get_bot_info_unexpected_error", error=str(e))
            return None

    async def set_webhook(self, webhook_url: str) -> bool:
        """
        Set webhook URL for the bot

        Args:
            webhook_url: Webhook URL to set

        Returns:
            True if successful, False otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return False

        try:
            logger.info("setting_telegram_webhook", webhook_url=webhook_url)

            result = await self.bot.set_webhook(url=webhook_url)

            if result:
                logger.info("telegram_webhook_set_successfully", webhook_url=webhook_url)
            else:
                logger.warning("telegram_webhook_set_failed", webhook_url=webhook_url)

            return result

        except TelegramError as e:
            logger.error("telegram_set_webhook_error", error=str(e))
            return False
        except Exception as e:
            logger.error("telegram_set_webhook_unexpected_error", error=str(e))
            return False

    async def delete_webhook(self) -> bool:
        """
        Delete webhook (switch to polling mode)

        Returns:
            True if successful, False otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return False

        try:
            logger.info("deleting_telegram_webhook")

            result = await self.bot.delete_webhook()

            if result:
                logger.info("telegram_webhook_deleted_successfully")
            else:
                logger.warning("telegram_webhook_delete_failed")

            return result

        except TelegramError as e:
            logger.error("telegram_delete_webhook_error", error=str(e))
            return False
        except Exception as e:
            logger.error("telegram_delete_webhook_unexpected_error", error=str(e))
            return False

    async def get_webhook_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current webhook information

        Returns:
            Webhook info dict if successful, None otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return None

        try:
            info = await self.bot.get_webhook_info()

            return {
                "url": info.url,
                "has_custom_certificate": info.has_custom_certificate,
                "pending_update_count": info.pending_update_count,
                "last_error_date": info.last_error_date.isoformat() if info.last_error_date else None,
                "last_error_message": info.last_error_message,
                "max_connections": info.max_connections,
                "allowed_updates": info.allowed_updates
            }

        except TelegramError as e:
            logger.error("telegram_get_webhook_info_error", error=str(e))
            return None
        except Exception as e:
            logger.error("telegram_get_webhook_info_unexpected_error", error=str(e))
            return None

    def create_inline_keyboard(self, buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
        """
        Create inline keyboard markup

        Args:
            buttons: List of button rows, each row is a list of button dicts
                    with 'text' and either 'callback_data' or 'url'

        Returns:
            InlineKeyboardMarkup object

        Example:
            buttons = [
                [
                    {"text": "Option 1", "callback_data": "opt1"},
                    {"text": "Option 2", "callback_data": "opt2"}
                ],
                [
                    {"text": "Visit Website", "url": "https://example.com"}
                ]
            ]
        """
        keyboard = []

        for row in buttons:
            keyboard_row = []
            for button in row:
                if "callback_data" in button:
                    keyboard_row.append(
                        InlineKeyboardButton(
                            text=button["text"],
                            callback_data=button["callback_data"]
                        )
                    )
                elif "url" in button:
                    keyboard_row.append(
                        InlineKeyboardButton(
                            text=button["text"],
                            url=button["url"]
                        )
                    )
            keyboard.append(keyboard_row)

        return InlineKeyboardMarkup(keyboard)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> bool:
        """
        Answer a callback query from inline keyboard

        Args:
            callback_query_id: Callback query ID
            text: Notification text
            show_alert: Show alert instead of notification

        Returns:
            True if successful, False otherwise
        """
        if not self.bot:
            logger.error("telegram_bot_not_initialized")
            return False

        try:
            await self.bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text,
                show_alert=show_alert
            )

            logger.info("telegram_callback_query_answered", callback_query_id=callback_query_id)
            return True

        except TelegramError as e:
            logger.error("telegram_answer_callback_query_error", error=str(e))
            return False
        except Exception as e:
            logger.error("telegram_answer_callback_query_unexpected_error", error=str(e))
            return False
