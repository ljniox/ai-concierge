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
            if not auto_reply_config.should_reply(message_data):
                logger.info("Auto-reply skipped based on configuration")
                return False

            # Extract message content and sender info
            message_text = self._extract_message_text(message_data)
            payload = message_data.get('payload', {})
            from_number = payload.get('from', '').replace('@c.us', '').replace('@s.whatsapp.net', '')

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
            # Handle different message types
            if 'text' in message_data:
                return message_data['text'].get('body', '')
            elif 'conversation' in message_data:
                return message_data['conversation']
            elif 'caption' in message_data:
                return message_data['caption']
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

            if response.status_code == 200:
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