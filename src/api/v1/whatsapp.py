"""
WhatsApp Webhook API Endpoints

Handles WhatsApp webhook integration via WAHA SDK.
Supports message processing, file uploads, and enrollment workflow integration.

Endpoints:
- POST /webhook - WhatsApp webhook handler
- GET /webhook/status - WhatsApp connection status

Constitution Principle IV: Multi-channel support (WhatsApp/Telegram)
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from ...services.messaging_service import get_messaging_service
from ...services.enrollment_workflow_service import get_enrollment_workflow_service
from ...utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp webhook from WAHA.

    This endpoint processes:
    - Incoming text messages
    - File uploads (documents, images)
    - Message status updates
    - Workflow integration

    Expected WAHA webhook format:
    {
        "event": "message",
        "session": "default",
        "payload": {
            "id": "message_id",
            "from": "221770000001@c.us",
            "to": "14155238886@c.us",
            "timestamp": 1634567890,
            "type": "text",
            "text": "Hello",
            "replyToMessageId": "parent_message_id"
        }
    """
    try:
        # Get webhook data
        webhook_data = await request.json()
        logger.info(f"Received WhatsApp webhook: {webhook_data.get('event', 'unknown')}")

        messaging_service = get_messaging_service()

        # Process the webhook
        result = await messaging_service.handle_whatsapp_webhook(webhook_data)

        return JSONResponse({
            "status": "success",
            "processed": True,
            "event": webhook_data.get("event"),
            "result": result
        })

    except Exception as e:
        logger.error(f"WhatsApp webhook processing failed: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e),
                "processed": False
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/webhook/media")
async def whatsapp_media_webhook(request: Request):
    """
    Handle WhatsApp media/webhook for file uploads.

    Processes:
    - Image uploads for OCR processing
    - Document uploads (PDF, images)
    - Payment proof uploads
    """
    try:
        # Get form data
        form_data = await request.form()
        files = await request.files()

        logger.info(f"WhatsApp media upload: {list(form_data.keys())}, files: {list(files.keys())}")

        # Extract message metadata
        metadata = {}
        for key, value in form_data.items():
            if key != 'file':
                metadata[key] = value

        # Process file if uploaded
        if 'file' in files:
            file = files['file']
            file_content = await file.read()
            filename = file.filename

            # Get user ID from metadata
            user_id = metadata.get('user_id')
            if not user_id:
                # Try to get user from phone number
                from_number = metadata.get('from')
                user_id = await _get_user_by_phone(from_number)

            if user_id:
                workflow_service = get_enrollment_workflow_service()
                result = await workflow_service.process_user_input(
                    user_id=user_id,
                    user_input="",  # No text input, just file
                    file_data=file_content,
                    filename=filename
                )

                return JSONResponse({
                    "status": "success",
                    "processed": True,
                    "filename": filename,
                    "file_size": len(file_content),
                    "workflow_result": result
                })
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found"
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp media webhook failed: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/status")
async def whatsapp_status():
    """
    Get WhatsApp service status.

    Returns:
        Dict: WhatsApp connection status and info
    """
    try:
        waha_base_url = "https://waha-core.niox.ovh"
        waha_api_token = "28C5435535C2487DAFBD1164B9CD4E34"

        # Check WAHA connection
        import requests
        try:
            url = f"{waha_base_url}/api/sessions"
            headers = {
                "Authorization": f"Bearer {waha_api_token}"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            sessions = response.json()

            return JSONResponse({
                "status": "connected",
                "waha_base_url": waha_base_url,
                "sessions": sessions,
                "active_sessions": len([s for s in sessions if s.get('connected', False)])
            })

        except Exception as e:
            logger.error(f"WhatsApp status check failed: {e}")
            return JSONResponse({
                "status": "disconnected",
                "error": str(e),
                "waha_base_url": waha_base_url
            })

    except Exception as e:
        logger.error(f"Failed to get WhatsApp status: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/send")
async def send_whatsapp_message(
    chat_id: str,
    message: str,
    session: str = "default"
):
    """
    Send a WhatsApp message (for testing/admin purposes).

    Args:
        chat_id: WhatsApp chat ID
        message: Message to send
        session: WAHA session name

    Returns:
        Dict: Send result
    """
    try:
        waha_base_url = "https://waha-core.niox.ovh"
        waha_api_token = "28C5435535C2487DAFBD1164B9CD4E34"

        url = f"{waha_base_url}/api/sendText"
        headers = {
            "Authorization": f"Bearer {waha_api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "session": session,
            "chatId": chat_id,
            "text": message
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return JSONResponse({
            "status": "success",
            "chat_id": chat_id,
            "message": message,
            "session": session,
            "result": response.json()
        })

    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
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
        # Simulate a test webhook
        test_webhook = {
            "event": "message",
            "session": "default",
            "payload": {
                "id": "test_message_123",
                "from": "221770000001@c.us",
                "to": "14155238886@c.us",
                "timestamp": 1634567890,
                "type": "text",
                "text": "test message"
            }
        }

        messaging_service = get_messaging_service()
        result = await messaging_service.handle_whatsapp_webhook(test_webhook)

        return JSONResponse({
            "status": "success",
            "test_webhook": test_webhook,
            "processing_result": result,
            "message": "WhatsApp webhook test completed successfully"
        })

    except Exception as e:
        logger.error(f"WhatsApp webhook test failed: {e}")
        return JSONResponse(
            {
                "status": "error",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def _get_user_by_phone(phone: str) -> str:
    """
    Get user ID from phone number.
    """
    try:
        from ...database.sqlite_manager import get_sqlite_manager
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