"""
Telegram webhook endpoints for AI Concierge integration
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime
from src.utils.config import Settings, get_settings
from src.services.telegram_service import TelegramService
from src.services.interaction_service import InteractionService
from src.services.user_service import UserService
from src.services.session_service import SessionService
from src.models.interaction import InteractionCreate, InteractionType, MessageType
from src.services.claude_service import ServiceType
import structlog

logger = structlog.get_logger()
telegram_router = APIRouter()


async def get_telegram_service(settings: Settings = Depends(get_settings)) -> TelegramService:
    """Dependency to get TelegramService instance"""
    return TelegramService(bot_token=settings.telegram_bot_token)


async def get_interaction_service() -> InteractionService:
    """Dependency to get InteractionService instance"""
    service = InteractionService()
    await service.initialize_redis()
    return service


@telegram_router.get("/telegram/webhook")
async def telegram_webhook_verification():
    """
    Verification endpoint for Telegram webhook
    Telegram makes a GET request to verify the webhook URL before setting it
    """
    return {"status": "ok", "message": "Telegram webhook endpoint"}


@telegram_router.post("/telegram/webhook")
async def handle_telegram_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """
    Handle incoming Telegram updates/messages

    Telegram sends updates in this format:
    {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": false,
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe"
            },
            "chat": {
                "id": 123456789,
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "type": "private"
            },
            "date": 1234567890,
            "text": "Hello bot!"
        }
    }
    """
    try:
        # Get JSON payload
        payload = await request.json()
        logger.info("telegram_webhook_received", payload=payload)

        # Basic validation
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Invalid payload format")

        # Extract update ID
        update_id = payload.get("update_id")
        if not update_id:
            logger.warning("telegram_webhook_missing_update_id", payload=payload)
            return {"status": "ignored", "reason": "Missing update_id"}

        # Handle different update types
        if "message" in payload:
            return await handle_telegram_message(payload["message"], telegram_service)
        elif "edited_message" in payload:
            return await handle_telegram_edited_message(payload["edited_message"], telegram_service)
        elif "callback_query" in payload:
            return await handle_telegram_callback_query(payload["callback_query"], telegram_service)
        elif "channel_post" in payload:
            logger.info("telegram_channel_post_ignored", update_id=update_id)
            return {"status": "ignored", "reason": "Channel posts not supported"}
        else:
            logger.warning("telegram_unsupported_update_type", update_id=update_id, keys=list(payload.keys()))
            return {"status": "ignored", "reason": "Unsupported update type"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("telegram_webhook_processing_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def handle_telegram_message(
    message_data: Dict[str, Any],
    telegram_service: TelegramService
) -> Dict[str, Any]:
    """
    Process a Telegram message

    Args:
        message_data: Telegram message data
        telegram_service: TelegramService instance

    Returns:
        Response dict
    """
    try:
        # Extract message information
        message_id = message_data.get("message_id")
        chat_id = message_data.get("chat", {}).get("id")
        from_user = message_data.get("from", {})
        user_id = from_user.get("id")
        username = from_user.get("username")
        first_name = from_user.get("first_name", "")
        last_name = from_user.get("last_name", "")
        text = message_data.get("text", "")
        date = message_data.get("date")

        # Handle different message types
        photo = message_data.get("photo")
        document = message_data.get("document")
        voice = message_data.get("voice")
        audio = message_data.get("audio")
        video = message_data.get("video")

        logger.info(
            "telegram_message_received",
            message_id=message_id,
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            text_length=len(text) if text else 0,
            has_photo=bool(photo),
            has_document=bool(document),
            has_voice=bool(voice)
        )

        # Validate required fields
        if not chat_id or not user_id:
            raise HTTPException(status_code=400, detail="Missing chat_id or user_id")

        # Determine message type and content
        message_type = "text"
        message_content = text

        if photo:
            message_type = "photo"
            message_content = f"[Photo message] {message_data.get('caption', '')}" if message_data.get('caption') else "[Photo message]"
        elif document:
            message_type = "document"
            doc_name = document.get("file_name", "file")
            message_content = f"[Document: {doc_name}] {message_data.get('caption', '')}" if message_data.get('caption') else f"[Document: {doc_name}]"
        elif voice:
            message_type = "voice"
            message_content = "[Voice message]"
        elif audio:
            message_type = "audio"
            message_content = f"[Audio message] {message_data.get('caption', '')}" if message_data.get('caption') else "[Audio message]"
        elif video:
            message_type = "video"
            message_content = f"[Video message] {message_data.get('caption', '')}" if message_data.get('caption') else "[Video message]"

        # Handle bot commands
        if text and text.startswith("/"):
            return await handle_telegram_command(text, chat_id, telegram_service)

        # Process message through AI Concierge system
        interaction_service = InteractionService()
        await interaction_service.initialize_redis()
        user_service = UserService()
        session_service = SessionService()

        # Create or get user (using Telegram user_id as identifier)
        telegram_identifier = f"telegram_{user_id}"
        full_name = f"{first_name} {last_name}".strip()

        # Get or create user
        user = await user_service.get_user_by_phone(telegram_identifier)
        if not user:
            from src.models.user import UserCreate
            user_create = UserCreate(
                phone_number=telegram_identifier,
                name=full_name or username or f"User_{user_id}",
                metadata={
                    "telegram_id": user_id,
                    "telegram_username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "platform": "telegram"
                }
            )
            user = await user_service.create_user(user_create)
            logger.info("telegram_user_created", user_id=user.id, telegram_id=user_id)

        # Get or create session
        session = await session_service.create_or_get_session(user.id)
        logger.info("telegram_session_retrieved", session_id=session.id, user_id=user.id)

        # Process message through interaction service
        try:
            orchestration_result = await interaction_service.process_incoming_message(
                phone_number=telegram_identifier,
                message=message_content,
                message_type="text",
                message_id=str(message_id)
            )

            # Extract AI response
            ai_response = orchestration_result.get("response", "Désolé, je n'ai pas pu traiter votre message.")
            service_type = orchestration_result.get("service", ServiceType.CONTACT_HUMAIN)

            # Format response for Telegram (convert WhatsApp formatting to Telegram Markdown)
            formatted_response = format_response_for_telegram(ai_response)

            # Send response via Telegram
            sent_message = await telegram_service.send_message(
                chat_id=chat_id,
                text=formatted_response,
                parse_mode="Markdown"
            )

            if sent_message:
                logger.info(
                    "telegram_response_sent",
                    chat_id=chat_id,
                    message_id=sent_message.get("message_id"),
                    service=service_type
                )
            else:
                logger.error("telegram_response_send_failed", chat_id=chat_id)

            return {
                "status": "success",
                "message": "Message processed",
                "session_id": session.id,
                "service": str(service_type),
                "response_sent": bool(sent_message)
            }

        except Exception as e:
            logger.error("telegram_orchestration_error", error=str(e), exc_info=True)
            # Send error message to user
            await telegram_service.send_message(
                chat_id=chat_id,
                text="❌ Désolé, une erreur s'est produite. Veuillez réessayer."
            )
            return {"status": "error", "error": str(e)}

    except Exception as e:
        logger.error("telegram_message_handling_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def handle_telegram_edited_message(
    message_data: Dict[str, Any],
    telegram_service: TelegramService
) -> Dict[str, Any]:
    """
    Handle edited messages

    Args:
        message_data: Edited message data
        telegram_service: TelegramService instance

    Returns:
        Response dict
    """
    logger.info("telegram_edited_message_received", message_id=message_data.get("message_id"))
    # For now, we ignore edited messages
    return {"status": "ignored", "reason": "Edited messages not processed"}


async def handle_telegram_callback_query(
    callback_data: Dict[str, Any],
    telegram_service: TelegramService
) -> Dict[str, Any]:
    """
    Handle callback queries from inline keyboards

    Args:
        callback_data: Callback query data
        telegram_service: TelegramService instance

    Returns:
        Response dict
    """
    try:
        callback_id = callback_data.get("id")
        data = callback_data.get("data")
        message = callback_data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")

        logger.info(
            "telegram_callback_query_received",
            callback_id=callback_id,
            data=data,
            chat_id=chat_id
        )

        # Answer the callback query
        await telegram_service.answer_callback_query(
            callback_query_id=callback_id,
            text="Traitement en cours..."
        )

        # Process callback data based on format
        # TODO: Implement callback handling logic based on your needs
        # For example: "service:CATECHESE", "action:view_notes", etc.

        return {"status": "success", "callback_data": data}

    except Exception as e:
        logger.error("telegram_callback_query_error", error=str(e), exc_info=True)
        return {"status": "error", "error": str(e)}


async def handle_telegram_command(
    command: str,
    chat_id: int,
    telegram_service: TelegramService
) -> Dict[str, Any]:
    """
    Handle Telegram bot commands

    Args:
        command: Command text (e.g., "/start", "/help")
        chat_id: Telegram chat ID
        telegram_service: TelegramService instance

    Returns:
        Response dict
    """
    try:
        logger.info("telegram_command_received", command=command, chat_id=chat_id)

        # Extract command and arguments
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Handle different commands
        if cmd == "/start":
            welcome_message = """
🙏 *Bienvenue au Service Diocésain de la Catéchèse*

Je suis Gust-IA, votre assistant virtuel. Je peux vous aider avec :

📚 *RENSEIGNEMENT* - Informations générales sur la catéchèse
👨‍👩‍👧 *CATECHESE* - Accès aux informations de vos enfants (avec code parent)
👤 *CONTACT_HUMAIN* - Parler à un agent humain

Comment puis-je vous aider aujourd'hui ?
            """
            await telegram_service.send_message(
                chat_id=chat_id,
                text=welcome_message.strip(),
                parse_mode="Markdown"
            )
            return {"status": "success", "command": "start"}

        elif cmd == "/help":
            help_message = """
📖 *Commandes disponibles:*

/start - Commencer une conversation
/help - Afficher cette aide
/services - Voir les services disponibles
/contact - Obtenir les coordonnées
/cancel - Annuler l'opération en cours

💬 Vous pouvez aussi simplement m'envoyer un message et je vous aiderai !
            """
            await telegram_service.send_message(
                chat_id=chat_id,
                text=help_message.strip(),
                parse_mode="Markdown"
            )
            return {"status": "success", "command": "help"}

        elif cmd == "/services":
            services_message = """
🔹 *Services disponibles:*

1️⃣ *RENSEIGNEMENT*
   Informations sur les programmes de catéchèse, horaires, inscriptions

2️⃣ *CATECHESE*
   Accès sécurisé aux informations de vos enfants (code parent requis)
   - Consulter les notes
   - Voir l'emploi du temps
   - Télécharger les attestations

3️⃣ *CONTACT_HUMAIN*
   Parler directement avec un membre de l'équipe

Envoyez-moi un message pour commencer !
            """
            await telegram_service.send_message(
                chat_id=chat_id,
                text=services_message.strip(),
                parse_mode="Markdown"
            )
            return {"status": "success", "command": "services"}

        elif cmd == "/contact":
            contact_message = """
📞 *Contactez-nous:*

📧 Email: contact@sdb-catechese.sn
📱 WhatsApp: +221 76 500 5555
🌐 Site web: www.sdb-catechese.sn

⏰ Horaires d'ouverture:
Lundi - Vendredi: 9h00 - 18h00
Samedi: 9h00 - 13h00

🙏 Service Diocésain de la Catéchèse
            """
            await telegram_service.send_message(
                chat_id=chat_id,
                text=contact_message.strip(),
                parse_mode="Markdown"
            )
            return {"status": "success", "command": "contact"}

        elif cmd == "/cancel":
            await telegram_service.send_message(
                chat_id=chat_id,
                text="✅ Opération annulée. Comment puis-je vous aider ?"
            )
            return {"status": "success", "command": "cancel"}

        else:
            await telegram_service.send_message(
                chat_id=chat_id,
                text=f"❓ Commande inconnue: {cmd}\n\nUtilisez /help pour voir les commandes disponibles."
            )
            return {"status": "unknown_command", "command": cmd}

    except Exception as e:
        logger.error("telegram_command_handling_error", error=str(e), exc_info=True)
        await telegram_service.send_message(
            chat_id=chat_id,
            text="❌ Erreur lors du traitement de la commande."
        )
        return {"status": "error", "error": str(e)}


def format_response_for_telegram(text: str) -> str:
    """
    Format response text for Telegram Markdown

    Args:
        text: Response text (potentially with WhatsApp formatting)

    Returns:
        Telegram-formatted text
    """
    # Convert WhatsApp bold (*text*) to Telegram bold (*text* or **text**)
    # Telegram uses _ for italic and * for bold
    # Keep asterisks as they work for both

    # Ensure text is not too long (Telegram has 4096 char limit)
    if len(text) > 4000:
        text = text[:3997] + "..."

    return text


@telegram_router.get("/telegram/webhook/info")
async def get_telegram_webhook_info(
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Get current Telegram webhook information"""
    try:
        info = await telegram_service.get_webhook_info()
        if info:
            return {"status": "success", "webhook_info": info}
        else:
            return {"status": "error", "message": "Could not retrieve webhook info"}
    except Exception as e:
        logger.error("telegram_get_webhook_info_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@telegram_router.post("/telegram/webhook/set")
async def set_telegram_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Set Telegram webhook URL"""
    try:
        data = await request.json()
        webhook_url = data.get("webhook_url")

        if not webhook_url:
            # Use default webhook URL from settings
            webhook_url = f"{settings.external_base_url}/api/v1/telegram/webhook"

        result = await telegram_service.set_webhook(webhook_url)

        if result:
            return {
                "status": "success",
                "message": "Webhook set successfully",
                "webhook_url": webhook_url
            }
        else:
            return {
                "status": "error",
                "message": "Failed to set webhook"
            }
    except Exception as e:
        logger.error("telegram_set_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@telegram_router.delete("/telegram/webhook")
async def delete_telegram_webhook(
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Delete Telegram webhook (switch to polling mode)"""
    try:
        result = await telegram_service.delete_webhook()

        if result:
            return {"status": "success", "message": "Webhook deleted successfully"}
        else:
            return {"status": "error", "message": "Failed to delete webhook"}
    except Exception as e:
        logger.error("telegram_delete_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@telegram_router.get("/telegram/bot/info")
async def get_telegram_bot_info(
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """Get Telegram bot information"""
    try:
        info = await telegram_service.get_bot_info()
        if info:
            return {"status": "success", "bot_info": info}
        else:
            return {"status": "error", "message": "Could not retrieve bot info"}
    except Exception as e:
        logger.error("telegram_get_bot_info_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
