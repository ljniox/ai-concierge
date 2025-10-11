"""
Messaging Service - WhatsApp and Telegram Integration

Handles integration with WhatsApp (WAHA) and Telegram for conversational enrollment workflow.

Features:
- WhatsApp Webhook handling
- Telegram Bot integration
- Message formatting and responses
- File upload processing
- Session management

Constitution Principle IV: Multi-channel support (WhatsApp/Telegram)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import requests

logger = logging.getLogger(__name__)


class MessagingService:
    """
    Unified messaging service for WhatsApp and Telegram integration.

    Provides:
    - WhatsApp webhook processing via WAHA
    - Telegram bot integration
    - Message formatting and routing
    - File upload handling
    - Workflow integration
    """

    def __init__(self):
        self.waha_base_url = os.getenv('WAHA_BASE_URL', 'https://waha-core.niox.ovh')
        self.waha_api_token = os.getenv('WAHA_API_TOKEN', '28C5435535C2487DAFBD1164B9CD4E34')
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus')
        self.telegram_webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL', 'https://cate.sdb-dkr.ovh/api/v1/telegram/webhook')

        # Active sessions
        self.whatsapp_sessions = {}
        self.telegram_sessions = {}

    async def handle_whatsapp_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming WhatsApp webhook from WAHA.

        Args:
            webhook_data: WAHA webhook payload

        Returns:
            Dict: Response data
        """
        try:
            logger.info(f"Received WhatsApp webhook: {webhook_data.get('event', 'unknown')}")

            # Extract message data
            if webhook_data.get('event') == 'message':
                message_data = webhook_data.get('payload', {})
                await self._process_whatsapp_message(message_data)

            return {"status": "processed"}

        except Exception as e:
            logger.error(f"WhatsApp webhook processing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _process_whatsapp_message(self, message_data: Dict[str, Any]):
        """
        Process incoming WhatsApp message.

        Args:
            message_data: Message data from WAHA
        """
        try:
            # Extract basic info
            chat_id = message_data.get('chatId')
            from_number = message_data.get('from')
            message_text = message_data.get('text', '')
            message_type = message_data.get('type', 'text')

            # Determine user from phone number
            user_id = await self._get_user_by_phone(from_number)

            if not user_id:
                # New user, send welcome message
                await self._send_whatsapp_welcome(chat_id, from_number)
                return

            # Check if there's an active workflow
            from .enrollment_workflow_service import get_enrollment_workflow_service
            workflow_service = get_enrollment_workflow_service()

            if workflow_service.get_workflow_status(user_id):
                # User has active workflow, process message
                await self._process_workflow_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    message=message_text,
                    channel="whatsapp"
                )
            else:
                # No active workflow, offer to start new enrollment
                await self._send_whatsapp_menu(chat_id)

        except Exception as e:
            logger.error(f"Failed to process WhatsApp message: {e}")

    async def handle_telegram_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming Telegram update.

        Args:
            update_data: Telegram update data

        Returns:
            Dict: Response data
        """
        try:
            logger.info(f"Received Telegram update")

            # Extract message data
            if 'message' in update_data:
                message_data = update_data['message']
                await self._process_telegram_message(message_data)

            return {"status": "processed"}

        except Exception as e:
            logger.error(f"Telegram update processing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _process_telegram_message(self, message_data: Dict[str, Any]):
        """
        Process incoming Telegram message.

        Args:
            message_data: Message data from Telegram
        """
        try:
            # Extract basic info
            chat_id = message_data['chat']['id']
            from_user = message_data['from']
            user_id = str(from_user['id'])
            message_text = message_data.get('text', '')

            # Get user from Telegram ID
            db_user_id = await self._get_user_by_telegram_id(user_id)

            if not db_user_id:
                # New user, send welcome message
                await self._send_telegram_welcome(chat_id)
                return

            # Check if there's an active workflow
            from .enrollment_workflow_service import get_enrollment_workflow_service
            workflow_service = get_enrollment_workflow_service()

            if workflow_service.get_workflow_status(db_user_id):
                # User has active workflow, process message
                await self._process_workflow_message(
                    user_id=db_user_id,
                    chat_id=chat_id,
                    message=message_text,
                    channel="telegram"
                )
            else:
                # No active workflow, offer to start new enrollment
                await self._send_telegram_menu(chat_id)

        except Exception as e:
            logger.error(f"Failed to process Telegram message: {e}")

    async def _process_workflow_message(self, user_id: str, chat_id: str, message: str, channel: str):
        """
        Process message through enrollment workflow.

        Args:
            user_id: User ID
            chat_id: Chat ID
            message: Message content
            channel: Channel (whatsapp/telegram)
        """
        try:
            from .enrollment_workflow_service import get_enrollment_workflow_service
            workflow_service = get_enrollment_workflow_service()

            result = await workflow_service.process_user_input(
                user_id=user_id,
                user_input=message
            )

            # Send response back to user
            if channel == "whatsapp":
                await self._send_whatsapp_response(chat_id, result)
            else:
                await self._send_telegram_response(chat_id, result)

        except Exception as e:
            logger.error(f"Failed to process workflow message: {e}")
            error_message = "Une erreur s'est produite. Veuillez réessayer."

            if channel == "whatsapp":
                await self._send_whatsapp_text(chat_id, error_message)
            else:
                await self._send_telegram_text(chat_id, error_message)

    async def _get_user_by_phone(self, phone: str) -> Optional[str]:
        """
        Get user ID from phone number.

        Args:
            phone: Phone number

        Returns:
            str or None: User ID
        """
        try:
            from ..database.sqlite_manager import get_sqlite_manager
            manager = get_sqlite_manager()

            # Clean phone number
            clean_phone = phone.replace(' ', '').replace('-', '').replace('+', '')

            query = "SELECT user_id FROM profil_utilisateurs WHERE telephone = ? OR telephone = ?"
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (phone, clean_phone))
                result = await cursor.fetchone()

            return result['user_id'] if result else None

        except Exception as e:
            logger.error(f"Failed to get user by phone: {e}")
            return None

    async def _get_user_by_telegram_id(self, telegram_id: str) -> Optional[str]:
        """
        Get user ID from Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            str or None: User ID
        """
        try:
            from ..database.sqlite_manager import get_sqlite_manager
            manager = get_sqlite_manager()

            query = "SELECT user_id FROM profil_utilisateurs WHERE identifiant_canal = ? AND canal_prefere = 'telegram'"
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (telegram_id,))
                result = await cursor.fetchone()

            return result['user_id'] if result else None

        except Exception as e:
            logger.error(f"Failed to get user by telegram ID: {e}")
            return None

    async def _send_whatsapp_text(self, chat_id: str, text: str):
        """
        Send text message via WhatsApp.

        Args:
            chat_id: WhatsApp chat ID
            text: Message text
        """
        try:
            url = f"{self.waha_base_url}/api/sendText"
            headers = {
                "Authorization": f"Bearer {self.waha_api_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "session": "default",
                "chatId": chat_id,
                "text": text
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            logger.info(f"WhatsApp message sent to {chat_id}: {text[:50]}...")

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")

    async def _send_whatsapp_welcome(self, chat_id: str, phone: str):
        """
        Send welcome message to new WhatsApp user.

        Args:
            chat_id: WhatsApp chat ID
            phone: User's phone number
        """
        welcome_message = (
            "👋 Bienvenue au Service de la catéchèse de Saint Jean Bosco de Nord Foire!\n\n"
            "Je suis Gust-IA, votre assistant pour les inscriptions catéchétiques.\n\n"
            "Pour commencer votre inscription, veuillez créer votre profil d'abord.\n"
            "Contactez notre bureau pour créer votre compte avec ce numéro de téléphone.\n\n"
            "Une fois votre compte créé, je pourrai vous aider avec:\n"
            "• Nouvelles inscriptions\n"
            "• Réinscriptions\n"
            "• Traitement des documents par OCR\n"
            "• Validation des paiements\n\n"
            "Service de la catéchèse de Saint Jean Bosco de Nord Foire 🙏"
        )

        await self._send_whatsapp_text(chat_id, welcome_message)

    async def _send_whatsapp_menu(self, chat_id: str):
        """
        Send menu message to WhatsApp user.

        Args:
            chat_id: WhatsApp chat ID
        """
        menu_message = (
            "📝 Gust-IA - Service d'Inscription\n\n"
            "Que souhaitez-vous faire?\n\n"
            "1. Démarrer une nouvelle inscription\n"
            "2. Contacter le bureau\n"
            "3. Aide\n\n"
            "Répondez avec le numéro de votre choix."
        )

        await self._send_whatsapp_text(chat_id, menu_message)

    async def _send_whatsapp_response(self, chat_id: str, workflow_result: Dict[str, Any]):
        """
        Send workflow response to WhatsApp user.

        Args:
            chat_id: WhatsApp chat ID
            workflow_result: Workflow processing result
        """
        message = workflow_result.get("message", "")
        options = workflow_result.get("options")

        if options:
            message += "\n\nOptions disponibles:\n"
            for option in options:
                message += f"• {option}\n"

        # Format for WhatsApp
        formatted_message = self._format_message_for_whatsapp(message)
        await self._send_whatsapp_text(chat_id, formatted_message)

    async def _send_telegram_text(self, chat_id: int, text: str):
        """
        Send text message via Telegram.

        Args:
            chat_id: Telegram chat ID
            text: Message text
        """
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            logger.info(f"Telegram message sent to {chat_id}: {text[:50]}...")

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def _send_telegram_welcome(self, chat_id: int):
        """
        Send welcome message to new Telegram user.

        Args:
            chat_id: Telegram chat ID
        """
        welcome_message = (
            "👋 *Bienvenue au Service de la catéchèse de Saint Jean Bosco de Nord Foire!*\n\n"
            "Je suis Gust-IA, votre assistant pour les inscriptions catéchétiques.\n\n"
            "Pour commencer votre inscription, veuillez créer votre profil d'abord.\n"
            "Contactez notre bureau pour créer votre compte.\n\n"
            "Une fois votre compte créé, je pourrai vous aider avec:\n"
            "• Nouvelles inscriptions\n"
            "• Réinscriptions\n"
            "• Traitement des documents par OCR\n"
            "• Validation des paiements\n\n"
            "*Service de la catéchèse de Saint Jean Bosco de Nord Foire* 🙏"
        )

        await self._send_telegram_text(chat_id, welcome_message)

    async def _send_telegram_menu(self, chat_id: int):
        """
        Send menu message to Telegram user.

        Args:
            chat_id: Telegram chat ID
        """
        menu_message = (
            "📝 *Gust-IA - Service d'Inscription*\n\n"
            "Que souhaitez-vous faire?\n\n"
            "1️⃣ Démarrer une nouvelle inscription\n"
            "2️⃣ Contacter le bureau\n"
            "3️⃣ Aide\n\n"
            "Répondez avec le numéro de votre choix."
        )

        await self._send_telegram_text(chat_id, menu_message)

    async def _send_telegram_response(self, chat_id: int, workflow_result: Dict[str, Any]):
        """
        Send workflow response to Telegram user.

        Args:
            chat_id: Telegram chat ID
            workflow_result: Workflow processing result
        """
        message = workflow_result.get("message", "")
        options = workflow_result.get("options")

        if options:
            message += "\n\n*Options disponibles:*\n"
            for option in options:
                message += f"• `{option}`\n"

        # Format for Telegram
        formatted_message = self._format_message_for_telegram(message)
        await self._send_telegram_text(chat_id, formatted_message)

    def _format_message_for_whatsapp(self, message: str) -> str:
        """
        Format message for WhatsApp.

        Args:
            message: Original message

        Returns:
            str: Formatted message
        """
        # WhatsApp formatting is simpler
        return message.replace("*", "").replace("_", "")

    def _format_message_for_telegram(self, message: str) -> str:
        """
        Format message for Telegram with Markdown.

        Args:
            message: Original message

        Returns:
            str: Formatted message
        """
        # Add basic formatting for Telegram
        lines = message.split('\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # Add formatting for headings and important info
                if line.startswith('📋') or line.startswith('✅') or line.startswith('❌'):
                    formatted_lines.append(f"*{line}*")
                elif line.endswith(':'):
                    formatted_lines.append(f"**{line}**")
                else:
                    formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    async def setup_telegram_webhook(self):
        """
        Set up Telegram bot webhook.
        """
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/setWebhook"
            payload = {
                "url": self.telegram_webhook_url,
                "allowed_updates": ["message", "callback_query"]
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            webhook_info = response.json()
            logger.info(f"Telegram webhook set up: {webhook_info}")

            return webhook_info

        except Exception as e:
            logger.error(f"Failed to set up Telegram webhook: {e}")
            raise

    async def send_workflow_completion_notification(self, user_id: str, enrollment_data: Dict[str, Any]):
        """
        Send notification when workflow is completed.

        Args:
            user_id: User ID
            enrollment_data: Enrollment data
        """
        try:
            from ..database.sqlite_manager import get_sqlite_manager
            manager = get_sqlite_manager()

            # Get user contact info
            query = "SELECT telephone, canal_prefere, identifiant_canal FROM profil_utilisateurs WHERE user_id = ?"
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (user_id,))
                user_info = await cursor.fetchone()

            if not user_info:
                return

            completion_message = (
                "✅ *Inscription Terminée avec Succès!*\n\n"
                f"Numéro d'inscription: {enrollment_data.get('numero_unique')}\n"
                f"Élève: {enrollment_data.get('nom_enfant')} {enrollment_data.get('prenom_enfant')}\n"
                f"Classe: {enrollment_data.get('classe')}\n"
                f"Année: {enrollment_data.get('annee_catechetique')}\n\n"
                "Votre inscription est maintenant en attente de validation finale.\n"
                "Vous recevrez une confirmation dès que tout sera validé.\n\n"
                "Merci pour votre confiance! 🙏"
            )

            if user_info['canal_prefere'] == 'whatsapp':
                chat_id = user_info['telephone']
                formatted_message = self._format_message_for_whatsapp(completion_message)
                await self._send_whatsapp_text(chat_id, formatted_message)
            else:
                chat_id = int(user_info['identifiant_canal'])
                await self._send_telegram_text(chat_id, completion_message)

            logger.info(f"Workflow completion notification sent to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to send workflow completion notification: {e}")

    async def send_payment_validation_notification(self, user_id: str, validation_data: Dict[str, Any]):
        """
        Send notification when payment is validated.

        Args:
            user_id: User ID
            validation_data: Payment validation data
        """
        try:
            from ..database.sqlite_manager import get_sqlite_manager
            manager = get_sqlite_manager()

            # Get user contact info
            query = "SELECT telephone, canal_prefere, identifiant_canal FROM profil_utilisateurs WHERE user_id = ?"
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (user_id,))
                user_info = await cursor.fetchone()

            if not user_info:
                return

            status = validation_data.get('status', 'unknown')
            if status == 'validated':
                message = (
                    "✅ *Paiement Validé!*\n\n"
                    f"Montant: {validation_data.get('montant')} FCFA\n"
                    f"Référence: {validation_data.get('reference')}\n\n"
                    "Votre inscription est maintenant active!\n"
                    "Bienvenue à la catéchèse! 🙏"
                )
            else:
                message = (
                    "❌ *Paiement Rejeté*\n\n"
                    f"Motif: {validation_data.get('motif', 'Non spécifié')}\n\n"
                    "Veuillez contacter le bureau pour plus d'informations."
                )

            if user_info['canal_prefere'] == 'whatsapp':
                chat_id = user_info['telephone']
                formatted_message = self._format_message_for_whatsapp(message)
                await self._send_whatsapp_text(chat_id, formatted_message)
            else:
                chat_id = int(user_info['identifiant_canal'])
                await self._send_telegram_text(chat_id, message)

            logger.info(f"Payment validation notification sent to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to send payment validation notification: {e}")


# Global service instance
_messaging_service_instance: Optional[MessagingService] = None


def get_messaging_service() -> MessagingService:
    """Get global messaging service instance."""
    global _messaging_service_instance
    if _messaging_service_instance is None:
        _messaging_service_instance = MessagingService()
    return _messaging_service_instance