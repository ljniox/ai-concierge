import requests
import logging
import json
from typing import Dict, Any, Optional
from auto_reply_config import auto_reply_config

logger = logging.getLogger(__name__)

class AutoReplyService:
    """Service for sending automatic replies to WhatsApp messages"""

    def __init__(self):
        self.api_key = auto_reply_config.waha_api_key
        self.base_url = auto_reply_config.waha_base_url
        self.session_name = auto_reply_config.session_name

    async def send_reply(self, message_data: Dict[str, Any]) -> bool:
        """Send auto-reply to a received message"""
        try:
            # Check if we should reply
            should_reply_result = auto_reply_config.should_reply(message_data)
            logger.info(f"DEBUG - Should reply result: {should_reply_result}")

            if not should_reply_result:
                logger.info("Auto-reply skipped based on configuration")
                return False

            # Extract message content and sender info
            message_text = self._extract_message_text(message_data)
            # Support both event wrapper with 'payload' and direct payload
            payload = message_data.get('payload', {}) or message_data.get('data', {}) or message_data

            # Try to get phone number from different possible locations
            raw_from = payload.get('from', '')
            media = payload.get('media', {})
            remote_jid = media.get('key', {}).get('remoteJid', '') if isinstance(media, dict) else ''

            # Use remoteJid if available, otherwise fall back to from field
            if remote_jid:
                from_number = remote_jid.replace('@c.us', '').replace('@s.whatsapp.net', '')
                logger.info(f"DEBUG - Using remoteJid: '{remote_jid}'")
            else:
                from_number = raw_from.replace('@c.us', '').replace('@s.whatsapp.net', '')
                logger.info(f"DEBUG - Using from field: '{raw_from}'")

            # Debug logging
            logger.info(f"DEBUG - Extracted phone number: '{from_number}'")
            logger.info(f"DEBUG - Full payload keys: {list(payload.keys())}")
            logger.info(f"DEBUG - Media object type: {type(media)}")
            if isinstance(media, dict):
                logger.info(f"DEBUG - Media keys: {list(media.keys())}")

            if not from_number:
                logger.error("DEBUG - Could not extract sender number; skipping send")
                return False

            # Get appropriate reply
            reply_text = auto_reply_config.get_reply_message(message_text)

            # Send the reply
            success = await self._send_whatsapp_message(from_number, reply_text)

            if success:
                logger.info(f"Auto-reply sent to {from_number}: {reply_text[:50]}...")
                return True
            else:
                logger.error(f"Failed to send auto-reply to {from_number}")
                return False

        except Exception as e:
            logger.error(f"Error in auto-reply service: {e}")
            return False

    def _extract_message_text(self, message_data: Dict[str, Any]) -> str:
        """Extract text content from message"""
        try:
            # WAHA webhook wraps details in 'payload' (preferred) or sometimes 'data'
            payload = message_data.get('payload', {}) or message_data.get('data', {}) or message_data

            # Common places for text content
            # 1) payload.text.body
            if isinstance(payload.get('text'), dict) and 'body' in payload.get('text', {}):
                return payload['text'].get('body', '')

            # 2) payload.body
            if isinstance(payload.get('body'), str) and payload.get('body'):
                return payload.get('body', '')

            # 3) payload.media.message.conversation
            media = payload.get('media', {})
            if isinstance(media, dict):
                message = media.get('message', {})
                if isinstance(message, dict) and 'conversation' in message:
                    return message.get('conversation', '')

            # 4) payload.caption
            if isinstance(payload.get('caption'), str) and payload.get('caption'):
                return payload.get('caption', '')

            return ''
        except Exception as e:
            logger.error(f"Error extracting message text: {e}")
            return ''

    async def _send_whatsapp_message(self, to_number: str, message: str) -> bool:
        """Send WhatsApp message via WAHA API"""
        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "session": self.session_name,
                "chatId": f"{to_number}@c.us",
                "text": message
            }

            response = requests.post(
                f"{self.base_url}/sendText",
                headers=headers,
                json=payload,
                verify=False
            )

            # WAHA returns 201 Created on success; accept any 2xx
            if 200 <= response.status_code < 300:
                result = response.json()
                logger.info(f"Message sent successfully: {result}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    async def send_custom_reply(self, to_number: str, message: str) -> bool:
        """Send a custom message to a specific number"""
        return await self._send_whatsapp_message(to_number, message)

# Global service instance
auto_reply_service = AutoReplyService()
