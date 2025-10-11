"""
Telegram Bot API Endpoints

Handles Telegram bot integration with enrollment workflow.

Endpoints:
- POST /webhook - Telegram webhook handler
- POST /webhook/set - Set up webhook
- GET /webhook/info - Get webhook info
- POST /send - Send message (testing)

Constitution Principle IV: Multi-channel support (WhatsApp/Telegram)
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging

from ...services.messaging_service import get_messaging_service
from ...services.enrollment_workflow_service import get_enrollment_workflow_service
from ...utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook.

    Processes:
    - Text messages
    - Document uploads
    - Photo uploads
    - Workflow integration

    Expected Telegram update format:
    {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": false,
                "first_name": "John",
                "username": "john_doe",
                "language_code": "en"
            },
            "chat": {
                "id": 123456789,
                "first_name": "John",
                "username": "john_doe",
                "type": "private"
            },
            "date": 1634567890,
            "text": "Hello"
        }
    """
    try:
        # Get update data
        update_data = await request.json()
        logger.info(f"Received Telegram update: {update_data.get('update_id', 'unknown')}")

        messaging_service = get_messaging_service()

        # Process the update
        result = await messaging_service.handle_telegram_update(update_data)

        return JSONResponse({
            "status": "success",
            "processed": True,
            "update_id": update_data.get("update_id"),
            "result": result
        })

    except Exception as e:
        logger.error(f"Telegram webhook processing failed: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e),
                "processed": False
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/webhook/set")
async def set_telegram_webhook():
    """
    Set up Telegram bot webhook.

    Returns:
        Dict: Webhook setup result
    """
    try:
        messaging_service = get_messaging_service()
        result = await messaging_service.setup_telegram_webhook()

        return JSONResponse({
            "status": "success",
            "webhook_info": result,
            "message": "Telegram webhook set up successfully"
        })

    except Exception as e:
        logger.error(f"Failed to set up Telegram webhook: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/webhook/info")
async def get_webhook_info():
    """
    Get current Telegram webhook information.

    Returns:
        Dict: Webhook info
    """
    try:
        telegram_bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        url = f"https://api.telegram.org/bot{telegram_bot_token}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        webhook_info = response.json()

        return JSONResponse({
            "status": "success",
            "webhook_info": webhook_info,
            "is_set": webhook_info.get("url") is not None and webhook_info.get("url") != ""
        })

    except Exception as e:
        logger.error(f"Failed to get Telegram webhook info: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/send")
async def send_telegram_message(
    chat_id: int,
    message: str,
    parse_mode: Optional[str] = "Markdown"
):
    """
    Send a Telegram message (for testing/admin purposes).

    Args:
        chat_id: Telegram chat ID
        message: Message to send
        parse_mode: Parse mode (Markdown or HTML)

    Returns:
        Dict: Send result
    """
    try:
        telegram_bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        return JSONResponse({
            "status": "success",
            "chat_id": chat_id,
            "message": message,
            "parse_mode": parse_mode,
            "result": response.json()
        })

    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/test-webhook")
async def test_webhook_endpoint():
    """
    Test endpoint to verify webhook is working.

    Returns:
        Dict: Test result
    """
    try:
        # Simulate a test update
        test_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "test_user",
                    "language_code": "fr"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "test_user",
                    "type": "private"
                },
                "date": 1634567890,
                "text": "test message"
            }
        }

        messaging_service = get_messaging_service()
        result = await messaging_service.handle_telegram_update(test_update)

        return JSONResponse({
            "status": "success",
            "test_update": test_update,
            "processing_result": result,
            "message": "Telegram webhook test completed successfully"
        })

    except Exception as e:
        logger.error(f"Telegram webhook test failed: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/bot/info")
async def get_bot_info():
    """
    Get Telegram bot information.

    Returns:
        Dict: Bot info
    """
    try:
        telegram_bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        url = f"https://api.telegram.org/bot{telegram_bot_token}/getMe"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        bot_info = response.json()

        return JSONResponse({
            "status": "success",
            "bot_info": bot_info,
            "bot_username": bot_info.get("username"),
            "bot_name": bot_info.get("first_name")
        })

    except Exception as e:
        logger.error(f"Failed to get Telegram bot info: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/status")
async def telegram_status():
    """
    Get Telegram service status.

    Returns:
        Dict: Telegram connection status and info
    """
    try:
        # Get bot info to check connection
        telegram_bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        url = f"https://api.telegram.org/bot{telegram_bot_token}/getMe"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            bot_info = response.json()

            # Get webhook info
            webhook_url = f"https://api.telegram.org/bot{telegram_bot_token}/getWebhookInfo"
            webhook_response = requests.get(webhook_url, timeout=10)
            webhook_info = webhook_response.json()

            return JSONResponse({
                "status": "connected",
                "bot_info": bot_info,
                "webhook_info": webhook_info,
                "webhook_set": webhook_info.get("url") is not None,
                "webhook_url": webhook_info.get("url")
            })
        else:
            return JSONResponse({
                "status": "disconnected",
                "error": "Failed to connect to Telegram API",
                "bot_token": telegram_bot_token[:10] + "..."
            })

    except Exception as e:
        logger.error(f"Failed to get Telegram status: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/delete-webhook")
async def delete_telegram_webhook():
    """
    Delete Telegram webhook (for cleanup).

    Returns:
        Dict: Deletion result
    """
    try:
        telegram_bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        url = f"https://api.telegram.org/bot{telegram_bot_token}/deleteWebhook"
        response = requests.post(url, timeout=10)
        response.raise_for_status()

        webhook_info = response.json()

        return JSONResponse({
            "status": "success",
            "webhook_info": webhook_info,
            "message": "Telegram webhook deleted successfully"
        })

    except Exception as e:
        logger.error(f"Failed to delete Telegram webhook: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/process-message")
async def process_message_manually(
    user_id: str,
    message: str,
    chat_id: Optional[int] = None
):
    """
    Manually process a message through the workflow (for testing).

    Args:
        user_id: User ID
        message: Message to process
        chat_id: Optional chat ID for sending response

    Returns:
        Dict: Processing result
    """
    try:
        workflow_service = get_enrollment_workflow_service()

        # Check if user has active workflow
        workflow_status = workflow_service.get_workflow_status(user_id)

        if not workflow_status:
            return JSONResponse({
                "status": "error",
                "error": "No active workflow found for user",
                "user_id": user_id
            }, status_code=status.HTTP_404_NOT_FOUND)

        # Process the message
        result = await workflow_service.process_user_input(
            user_id=user_id,
            user_input=message
        )

        # Send response if chat_id provided
        if chat_id:
            from ...services.messaging_service import get_messaging_service
            messaging_service = get_messaging_service()
            await messaging_service._send_telegram_response(chat_id, result)

        return JSONResponse({
            "status": "success",
            "user_id": user_id,
            "message": message,
            "result": result
        })

    except Exception as e:
        logger.error(f"Failed to process message manually: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Helper function to get user by Telegram ID
async def _get_user_by_telegram_id(telegram_id: str) -> str:
    """
    Get user ID from Telegram ID.
    """
    try:
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = "SELECT user_id FROM profil_utilisateurs WHERE identifiant_canal = ? AND canal_prefere = 'telegram'"
        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (telegram_id,))
            result = await cursor.fetchone()

        return result['user_id'] if result else None

    except Exception as e:
        logger.error(f"Failed to get user by telegram ID: {e}")
        return None