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

        # Handle WAHA format - check if this is the proper WAHA webhook structure
        if "event" in payload and "session" in payload and "payload" in payload:
            # Standard WAHA webhook format
            event_type = payload.get("event")
            session_name = payload.get("session")
            message_data = payload.get("payload")

            logger.info(
                "waha_webhook_received",
                event_type=event_type,
                session=session_name,
                message_id=message_data.get("id") if message_data else None
            )

            # Handle different event types
            if event_type == "message":
                return await handle_waha_message(message_data, settings, session_name)
            elif event_type == "message.any":
                # Handle all message events including our own
                return await handle_waha_message(message_data, settings, session_name)
            elif event_type == "message.reaction":
                return await handle_waha_reaction(message_data, settings, session_name)
            elif event_type == "message.ack":
                return await handle_waha_ack(message_data, settings, session_name)
            elif event_type == "message.revoked":
                return await handle_waha_revoked(message_data, settings, session_name)
            else:
                logger.warning("unsupported_waha_event", event_type=event_type)
                return {"status": "ignored", "reason": f"Unsupported WAHA event: {event_type}"}

        # Handle legacy/test formats for backward compatibility
        elif "payload" in payload:
            # WAHA format with payload wrapper (no event type)
            message_data = payload["payload"]
            return await handle_waha_message(message_data, settings, "default")
        elif "message" in payload:
            # Direct message format (our test format)
            return await handle_message(payload, settings)
        elif "type" in payload:
            # Alternative format with type at root
            message_type = payload.get("type")
            if message_type == "message":
                return await handle_message(payload, settings)
            elif message_type in ["text", "audio", "image", "video", "document", "location", "contacts"]:
                return await handle_waha_message(payload, settings, "default")
            else:
                logger.warning("unsupported_message_type", message_type=message_type)
                return {"status": "ignored", "reason": f"Unsupported type: {message_type}"}
        else:
            # Try to extract message from any format
            if payload.get("from") and (payload.get("text") or payload.get("type")):
                return await handle_waha_message(payload, settings, "default")
            else:
                logger.warning("unknown_webhook_format", payload_keys=list(payload.keys()))
                return {"status": "ignored", "reason": "Unknown webhook format"}

    except HTTPException:
        # Re-raise HTTPExceptions (like validation errors)
        raise
    except Exception as e:
        logger.error("webhook_processing_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def handle_waha_message(message_data: Dict[str, Any], settings: Settings, session_name: str = "default") -> Dict[str, Any]:
    """
    Process WAHA format message
    """
    from_number = message_data.get("from")
    message_id = message_data.get("id")
    timestamp = message_data.get("timestamp")
    from_me = message_data.get("fromMe", False)
    body = message_data.get("body", "")
    has_media = message_data.get("hasMedia", False)
    media = message_data.get("media", {})

    # Clean phone number (remove @c.us or @s.whatsapp.net)
    if from_number:
        if "@c.us" in from_number:
            from_number = from_number.split("@")[0]
        elif "@s.whatsapp.net" in from_number:
            from_number = from_number.split("@")[0]

    # Handle WAHA format (numbers without + prefix)
    if from_number and from_number.isdigit() and len(from_number) >= 8:
        # Add + prefix for WAHA format numbers
        from_number = f"+{from_number}"

    # Validate phone number
    if not from_number or not isinstance(from_number, str):
        raise HTTPException(status_code=400, detail="Invalid phone number")

    # Determine message type based on content
    message_type = "text"
    message_content = body

    if has_media and media:
        media_url = media.get("url")
        media_mimetype = media.get("mimetype", "")

        if media_url:
            if media_mimetype.startswith("audio/"):
                message_type = "audio"
                message_content = f"[Audio message] {body}" if body else "[Audio message]"
            elif media_mimetype.startswith("image/"):
                message_type = "image"
                message_content = f"[Image message] {body}" if body else "[Image message]"
            elif media_mimetype.startswith("video/"):
                message_type = "video"
                message_content = f"[Video message] {body}" if body else "[Video message]"
            elif "application" in media_mimetype or media_mimetype.startswith("document"):
                message_type = "document"
                message_content = f"[Document message] {body}" if body else "[Document message]"
            else:
                message_type = "media"
                message_content = f"[Media message] {body}" if body else "[Media message]"
        else:
            message_type = "media"
            message_content = f"[Media message] {body}" if body else "[Media message]"

    # Skip processing if fromMe (our own messages) unless it's message.any event
    if from_me:
        logger.info(
            "skipping_own_message",
            phone_number=from_number,
            message_id=message_id,
            message_content=message_content,
            session=session_name
        )
        return {
            "status": "ignored",
            "reason": "Own message",
            "message_id": message_id,
            "phone_number": from_number,
            "session": session_name
        }

    logger.info(
        "processing_waha_message",
        phone_number=from_number,
        message_id=message_id,
        message_type=message_type,
        message_content=message_content,
        session=session_name,
        has_media=has_media
    )

    # Try to process with interaction service if available
    try:
        from src.services.interaction_service import InteractionService
        interaction_service = InteractionService()

        # Create message in the format expected by the interaction service
        message_payload = {
            "message": {
                "from": from_number,
                "id": message_id,
                "type": message_type,
                "timestamp": timestamp,
                "text": {"body": message_content} if message_type == "text" else None,
                "audio": None if message_type != "audio" else {"url": media.get("url")} if has_media else None,
                "image": None if message_type != "image" else {"url": media.get("url")} if has_media else None,
                "video": None if message_type != "video" else {"url": media.get("url")} if has_media else None,
                "document": None if message_type != "document" else {"url": media.get("url")} if has_media else None,
                "media": media if has_media else None
            }
        }

        result = await interaction_service.process_incoming_message(
            phone_number=from_number,
            message=message_content,
            message_type=message_type,
            message_id=message_id
        )
        logger.info("interaction_processed", result=result)

        return {
            "status": "processed",
            "message_id": message_id,
            "phone_number": from_number,
            "session": session_name,
            "message_type": message_type,
            "message_content": message_content,
            "timestamp": timestamp,
            "interaction_result": result
        }

    except Exception as e:
        logger.error("interaction_processing_failed", error=str(e), exc_info=True)

        # Fallback to basic acknowledgment
        return {
            "status": "received",
            "message_id": message_id,
            "phone_number": from_number,
            "session": session_name,
            "message_type": message_type,
            "message_content": message_content,
            "timestamp": timestamp,
            "has_media": has_media,
            "media_url": media.get("url") if has_media else None,
            "note": "WAHA message received but interaction processing failed"
        }


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
    expected_token = settings.webhook_verify_token

    # Debug logging
    logger.info(
        "webhook_verification_attempt",
        provided_token=hub_verify_token,
        expected_token=expected_token,
        hub_challenge=hub_challenge,
        webhook_url=settings.webhook_url
    )

    # WAHA might not send a verify token, so we'll accept the challenge if:
    # 1. No token is expected (not secure, but works) OR
    # 2. The token matches exactly OR
    # 3. WAHA is using a different authentication method

    if hub_challenge:
        # If WAHA sends a challenge, accept it for now
        # We can implement proper authentication later
        if not hub_verify_token or hub_verify_token == expected_token:
            logger.info("webhook_verification_successful", webhook_url=settings.webhook_url)
            return PlainTextResponse(content=hub_challenge)
        else:
            logger.warning("webhook_verification_failed_token_mismatch", provided_token=hub_verify_token, expected_token=expected_token)
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Verification failed - token mismatch",
                    "provided_token": hub_verify_token,
                    "expected_token": expected_token,
                    "challenge_received": hub_challenge
                }
            )
    else:
        logger.warning("webhook_verification_failed_no_challenge", provided_token=hub_verify_token)
        return JSONResponse(
            status_code=400,
            content={
                "error": "Verification failed - no challenge provided",
                "provided_token": hub_verify_token,
                "expected_token": expected_token
            }
        )


@webhook_router.get("/webhook/config")
async def get_webhook_config(settings: Settings = Depends(get_settings)):
    """
    Get current webhook configuration for setup purposes
    """
    return {
        "webhook_url": settings.webhook_url,
        "verify_token": settings.webhook_verify_token,
        "session_name": settings.session_name,
        "waha_session_id": settings.waha_session_id,
        "instructions": "Use this URL and verify token to configure WAHA webhook",
        "supported_events": ["message", "message.any", "message.reaction", "message.ack", "message.revoked"]
    }


async def handle_waha_reaction(message_data: Dict[str, Any], settings: Settings, session_name: str = "default") -> Dict[str, Any]:
    """
    Handle WAHA message reaction events
    """
    reaction_data = message_data.get("reaction", {})
    reaction_text = reaction_data.get("text", "")
    reaction_message_id = reaction_data.get("messageId", "")

    logger.info(
        "waha_reaction_received",
        session=session_name,
        reaction_text=reaction_text,
        reaction_message_id=reaction_message_id,
        from_number=message_data.get("from")
    )

    return {
        "status": "received",
        "event_type": "message.reaction",
        "session": session_name,
        "reaction_text": reaction_text,
        "reaction_message_id": reaction_message_id,
        "note": "WAHA reaction received"
    }


async def handle_waha_ack(message_data: Dict[str, Any], settings: Settings, session_name: str = "default") -> Dict[str, Any]:
    """
    Handle WAHA message acknowledgment events
    """
    ack_value = message_data.get("ack", 0)

    logger.info(
        "waha_ack_received",
        session=session_name,
        ack_value=ack_value,
        message_id=message_data.get("id")
    )

    return {
        "status": "received",
        "event_type": "message.ack",
        "session": session_name,
        "ack_value": ack_value,
        "message_id": message_data.get("id"),
        "note": "WAHA acknowledgment received"
    }


async def handle_waha_revoked(message_data: Dict[str, Any], settings: Settings, session_name: str = "default") -> Dict[str, Any]:
    """
    Handle WAHA message revoked events
    """
    before_data = message_data.get("before", {})
    after_data = message_data.get("after", {})

    logger.info(
        "waha_revoked_received",
        session=session_name,
        message_id=before_data.get("id"),
        before_content=before_data.get("body"),
        after_content=after_data.get("body")
    )

    return {
        "status": "received",
        "event_type": "message.revoked",
        "session": session_name,
        "message_id": before_data.get("id"),
        "before_content": before_data.get("body"),
        "after_content": after_data.get("body"),
        "note": "WAHA message revoked event received"
    }