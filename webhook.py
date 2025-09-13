from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
from auto_reply_service import auto_reply_service
from session_manager import session_manager
from wa_service import send_text as wa_send_text
from version_info import get_version_info

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
        # - payload: message details (preferred key) or 'data' in some variants

        if isinstance(data, dict):
            # Handle different event types
            event_type = data.get('event', 'unknown')
            session_id = data.get('session', 'unknown')

            if event_type == 'message':
                # Process incoming message (pass full event for robust parsing downstream)
                await process_message(data, session_id)
            elif event_type == 'session.status':
                # Handle session status updates
                logger.info(f"Session status update for {session_id}: {data.get('payload') or data.get('data')}")
            else:
                logger.info(f"Received {event_type} event for session {session_id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _extract_phone_and_text(event_data: Dict[str, Any]) -> (str, str):
    payload = event_data.get('payload') or event_data.get('data') or {}
    # Text
    message_body = (
        (payload.get('text') or {}).get('body')
        or payload.get('body')
        or ((payload.get('media') or {}).get('message') or {}).get('conversation')
        or ''
    )
    # Phone
    raw_from = payload.get('from', '')
    if not raw_from:
        rjid = ((payload.get('media') or {}).get('key') or {}).get('remoteJid', '')
        raw_from = rjid
    phone = raw_from.replace('@c.us', '').replace('@s.whatsapp.net', '')
    return phone, message_body


async def process_message(event_data: Dict[str, Any], session_id: str):
    """Process incoming WhatsApp message (log details and trigger auto-reply)"""
    try:
        phone, message_body = _extract_phone_and_text(event_data)
        logger.info(f"Incoming message from {phone}: {message_body}")

        # New: route via session manager (Service Catalog)
        replies = session_manager.handle_incoming(phone, message_body)
        for r in replies:
            if r:
                logger.info(f"Sending reply to {phone}: {r[:80]}...")
                wa_send_text(phone, r)

        # Optionally, keep legacy auto-reply as fallback (disabled by default)
        # asyncio.create_task(send_auto_reply_if_needed(event_data))

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

@app.get("/version")
async def version():
    try:
        info = get_version_info()
        # Basic connectivity checks (best-effort)
        from supabase_client import supabase_client
        try:
            services = supabase_client.list_services()
            info["supabase_services_count"] = len(services)
        except Exception:
            info["supabase_services_count"] = -1
        return info
    except Exception as e:
        logger.error(f"Error building version info: {e}")
        return {"app": "ai-concierge-webhook", "version": "unknown"}

class ToggleRequest(BaseModel):
    enabled: bool = True


@app.post("/auto-reply/toggle")
async def toggle_auto_reply(req: ToggleRequest):
    """Toggle auto-reply on/off"""
    try:
        from auto_reply_config import auto_reply_config

        auto_reply_config.enabled = req.enabled
        logger.info(f"Auto-reply {'enabled' if req.enabled else 'disabled'}")

        return {"success": True, "enabled": req.enabled}
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
