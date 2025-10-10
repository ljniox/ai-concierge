import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EvolutionAPIService:
    """Service for interacting with Evolution API WhatsApp integration"""

    def __init__(self, base_url: str, api_key: str, instance_name: str, instance_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.instance_name = instance_name
        self.instance_token = instance_token
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': api_key
        }

    async def send_text_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp"""
        try:
            url = f"{self.base_url}/message/sendText/{self.instance_name}"
            payload = {
                "number": phone_number,
                "textMessage": {
                    "text": message
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to send text message: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_qr_code(self) -> Optional[str]:
        """Get QR code for WhatsApp connection"""
        try:
            url = f"{self.base_url}/qrcode"
            params = {"instanceName": self.instance_name}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                return data.get('qrcode', {}).get('base64')

        except Exception as e:
            logger.error(f"Failed to get QR code: {str(e)}")
            return None

    async def get_connection_state(self) -> str:
        """Get WhatsApp connection state"""
        try:
            url = f"{self.base_url}/instance/fetchInstances"
            params = {"instanceName": self.instance_name}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    return data[0].get('connectionStatus', 'unknown')
                return 'unknown'

        except Exception as e:
            logger.error(f"Failed to get connection state: {str(e)}")
            return 'error'

    async def start_instance(self) -> Dict[str, Any]:
        """Start WhatsApp instance and generate QR code"""
        try:
            url = f"{self.base_url}/instance/create"
            payload = {
                "instanceName": self.instance_name,
                "integration": "WHATSAPP-BAILEYS",
                "token": self.instance_token,
                "number": "221765005555",
                "qrcode": true
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to start instance: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_instance_info(self) -> Dict[str, Any]:
        """Get instance information"""
        try:
            url = f"{self.base_url}/instance/fetchInstances"
            params = {"instanceName": self.instance_name}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    return data[0]
                return {}

        except Exception as e:
            logger.error(f"Failed to get instance info: {str(e)}")
            return {}

    async def send_admin_summary(self, message: str) -> bool:
        """Send admin summary to the admin number"""
        try:
            admin_number = "221765005555"
            result = await self.send_text_message(admin_number, message)
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Failed to send admin summary: {str(e)}")
            return False