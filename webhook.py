from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
from auto_reply_service import auto_reply_service

app = FastAPI(title="WhatsApp Webhook", description="Webhook for receiving WhatsApp messages from WAHA")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "running", "service": "WhatsApp Webhook"}

@app.get("/webhook")
async def webhook_challenge(request: Request):
    """Handle webhook challenge verification"""
    try:
        params = dict(request.query_params)
        mode = params.get('hub.mode')
        challenge = params.get('hub.challenge')
        token = params.get('hub.verify_token')

        # You should set this environment variable
        verify_token = os.getenv('WEBHOOK_VERIFY_TOKEN', 'your-verify-token')

        if mode and challenge and token:
            if mode == 'subscribe' and token == verify_token:
                return JSONResponse(content=int(challenge))
            else:
                logger.warning(f"Webhook verification failed: token mismatch")
                raise HTTPException(status_code=403, detail="Verification failed")

        return {"status": "webhook endpoint active"}

    except Exception as e:
        logger.error(f"Webhook challenge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def receive_message(request: Request):
    """Receive WhatsApp messages from WAHA"""
    try:
        data = await request.json()
        logger.info(f"Received webhook data: {data}")

        # WAHA message format typically includes:
        # - session: session identifier
        # - event: event type (message, etc.)
        # - data: message details

        if isinstance(data, dict):
            # Handle different event types
            event_type = data.get('event', 'unknown')
            session_id = data.get('session', 'unknown')
            message_data = data.get('data', {})

            if event_type == 'message':
                # Process incoming message
                await process_message(message_data, session_id)
            elif event_type == 'session.status':
                # Handle session status updates
                logger.info(f"Session status update for {session_id}: {message_data}")
            else:
                logger.info(f"Received {event_type} event for session {session_id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_message(message_data: Dict[str, Any], session_id: str):
    """Process incoming WhatsApp message"""
    try:
        # Extract message details
        message_type = message_data.get('type', 'text')

        if message_type == 'text':
            # Handle text messages
            text_data = message_data.get('text', {})
            message_body = text_data.get('body', '')
            from_number = message_data.get('from', '')

            logger.info(f"Text message from {from_number}: {message_body}")

            # Send auto-reply (async, non-blocking)
            asyncio.create_task(send_auto_reply_if_needed(message_data))

        elif message_type == 'image':
            # Handle image messages
            image_data = message_data.get('image', {})
            caption = image_data.get('caption', '')
            mime_type = image_data.get('mime_type', '')
            from_number = message_data.get('from', '')

            logger.info(f"Image message from {from_number}: {mime_type} - {caption}")

            # Send auto-reply for images too (based on caption)
            if caption:
                message_data_for_reply = message_data.copy()
                message_data_for_reply['text'] = {'body': caption}
                asyncio.create_task(send_auto_reply_if_needed(message_data_for_reply))

        elif message_type == 'document':
            # Handle document messages
            document_data = message_data.get('document', {})
            filename = document_data.get('filename', '')
            mime_type = document_data.get('mime_type', '')
            from_number = message_data.get('from', '')

            logger.info(f"Document message from {from_number}: {filename} ({mime_type})")

        elif message_type == 'audio':
            # Handle audio messages
            audio_data = message_data.get('audio', {})
            mime_type = audio_data.get('mime_type', '')
            from_number = message_data.get('from', '')

            logger.info(f"Audio message from {from_number}: {mime_type}")

        elif message_type == 'video':
            # Handle video messages
            video_data = message_data.get('video', {})
            mime_type = video_data.get('mime_type', '')
            from_number = message_data.get('from', '')

            logger.info(f"Video message from {from_number}: {mime_type}")

        else:
            logger.info(f"Unknown message type: {message_type}")
            logger.debug(f"Full message data: {message_data}")

    except Exception as e:
        logger.error(f"Error processing message: {e}")

async def send_auto_reply_if_needed(message_data: Dict[str, Any]):
    """Send auto-reply if configured"""
    try:
        success = await auto_reply_service.send_reply(message_data)
        if success:
            logger.info("Auto-reply sent successfully")
        else:
            logger.info("Auto-reply not sent (based on configuration)")
    except Exception as e:
        logger.error(f"Error sending auto-reply: {e}")

@app.get("/sessions")
async def list_sessions():
    """List active WhatsApp sessions"""
    try:
        # This would typically query the WAHA API
        # For now, return a mock response
        return {"sessions": []}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auto-reply/status")
async def get_auto_reply_status():
    """Get auto-reply configuration status"""
    try:
        from auto_reply_config import auto_reply_config

        return {
            "enabled": auto_reply_config.enabled,
            "working_hours_start": auto_reply_config.working_hours_start,
            "working_hours_end": auto_reply_config.working_hours_end,
            "weekend_enabled": auto_reply_config.weekend_enabled,
            "is_working_hours": auto_reply_config.is_working_hours(),
            "custom_replies_count": len(auto_reply_config.custom_replies),
            "blacklisted_contacts": list(auto_reply_config.blacklisted_contacts)
        }
    except Exception as e:
        logger.error(f"Error getting auto-reply status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-reply/toggle")
async def toggle_auto_reply(enabled: bool = True):
    """Toggle auto-reply on/off"""
    try:
        from auto_reply_config import auto_reply_config

        auto_reply_config.enabled = enabled
        logger.info(f"Auto-reply {'enabled' if enabled else 'disabled'}")

        return {"success": True, "enabled": enabled}
    except Exception as e:
        logger.error(f"Error toggling auto-reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-reply/test")
async def test_auto_reply():
    """Send a test auto-reply message"""
    try:
        success = await auto_reply_service.send_custom_reply(
            "221773387902",
            "🧪 Test d'auto-réponse - le système fonctionne parfaitement!"
        )

        return {"success": success, "message": "Test message sent to your number"}
    except Exception as e:
        logger.error(f"Error testing auto-reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-reply/custom-replies")
async def update_custom_replies(replies: dict):
    """Update custom keyword replies"""
    try:
        from auto_reply_config import auto_reply_config

        success = auto_reply_config.save_custom_replies(replies)
        if success:
            return {"success": True, "message": "Custom replies updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save custom replies")
    except Exception as e:
        logger.error(f"Error updating custom replies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )