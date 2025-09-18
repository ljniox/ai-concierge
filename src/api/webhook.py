"""
Webhook endpoints for WhatsApp integration
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional, Dict, Any
from src.utils.config import Settings, get_settings
import structlog

logger = structlog.get_logger()
webhook_router = APIRouter()


@webhook_router.post("/webhook")
async def handle_webhook(
    request: Request,
    settings: Settings = Depends(get_settings)
):
    """
    Handle incoming WhatsApp messages from WAHA
    """
    try:
        # Get JSON payload
        payload = await request.json()
        logger.info("webhook_payload_received", payload=payload)

        # Basic validation
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Invalid payload format")

        # Extract message data
        message_type = payload.get("type")
        if not message_type:
            raise HTTPException(status_code=400, detail="Missing message type")

        # Handle different message types
        if message_type == "message":
            return await handle_message(payload, settings)
        else:
            logger.warning("unsupported_message_type", message_type=message_type)
            return {"status": "ignored", "reason": f"Unsupported type: {message_type}"}

    except HTTPException:
        # Re-raise HTTPExceptions (like validation errors)
        raise
    except Exception as e:
        logger.error("webhook_processing_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def handle_message(payload: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
    """
    Process individual message
    """
    message_data = payload.get("message", {})
    from_number = message_data.get("from")
    message_id = message_data.get("id")

    # Validate phone number
    if not from_number or not isinstance(from_number, str):
        raise HTTPException(status_code=400, detail="Invalid phone number")

    logger.info(
        "processing_message",
        phone_number=from_number,
        message_id=message_id,
        message_type=list(message_data.keys())
    )

    # Extract message content
    message_content = ""
    if "text" in message_data:
        message_content = message_data["text"].get("body", "")
    elif "audio" in message_data:
        message_content = "[Audio message]"
    elif "image" in message_data:
        message_content = "[Image message]"
    elif "video" in message_data:
        message_content = "[Video message]"
    elif "document" in message_data:
        message_content = "[Document message]"
    elif "location" in message_data:
        message_content = "[Location message]"
    elif "contacts" in message_data:
        message_content = "[Contact message]"
    else:
        message_content = "[Unsupported message type]"

    # For now, just log and acknowledge - we'll implement full processing later
    logger.info(
        "message_received",
        phone_number=from_number,
        message_id=message_id,
        message_content=message_content,
        message_type=message_data.get("type", "text")
    )

    return {
        "status": "received",
        "message_id": message_id,
        "phone_number": from_number,
        "timestamp": payload.get("timestamp"),
        "message_content": message_content,
        "note": "Message received but processing not yet implemented"
    }


@webhook_router.get("/webhook")
async def verify_webhook(
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    settings: Settings = Depends(get_settings)
):
    """
    Handle WAHA webhook verification challenge
    """
    expected_token = getattr(settings, 'waha_verify_token', 'test-token')

    if hub_verify_token == expected_token and hub_challenge:
        logger.info("webhook_verification_successful")
        return PlainTextResponse(content=hub_challenge)
    else:
        logger.warning("webhook_verification_failed", token=hub_verify_token)
        raise HTTPException(status_code=403, detail="Verification failed")