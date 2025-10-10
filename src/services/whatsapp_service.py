import httpx
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Service for interacting with our custom WhatsApp integration"""

    def __init__(self, base_url: str, instance_name: str):
        self.base_url = base_url.rstrip('/')
        self.instance_name = instance_name
        self.timeout = 120.0

    async def send_text_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp"""
        url = f"{self.base_url}/send-message"
        payload = {
            "phone": phone_number,
            "message": message
        }

        # Retry mechanism with different timeout strategies
        for attempt in range(3):
            try:
                # Use a shorter timeout with retries
                timeout = httpx.Timeout(
                    connect=10.0,  # Connection timeout
                    read=30.0,     # Read timeout
                    write=10.0,    # Write timeout
                    pool=30.0      # Connection pool timeout
                )

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    logger.info(f"WhatsApp message sent successfully to {phone_number}")
                    return result

            except httpx.ReadTimeout:
                error_msg = f"ReadTimeout on attempt {attempt + 1}"
                logger.warning(f"WhatsApp service read timeout: {error_msg}")
                if attempt < 2:  # Don't sleep on last attempt
                    await asyncio.sleep(1)  # Brief delay before retry
                continue

            except httpx.ConnectTimeout:
                error_msg = f"ConnectTimeout on attempt {attempt + 1}"
                logger.warning(f"WhatsApp service connection timeout: {error_msg}")
                if attempt < 2:
                    await asyncio.sleep(2)  # Longer delay for connection issues
                continue

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else f"{type(e).__name__}: No error message"
                logger.error(f"Failed to send text message: {error_msg}")
                logger.error(f"URL: {url}, Payload: {payload}")
                return {"success": False, "error": error_msg}

        # All attempts failed
        final_error = "WhatsApp service unavailable after multiple timeout attempts"
        logger.error(f"Final failure for {phone_number}: {final_error}")
        return {"success": False, "error": final_error}

    async def get_connection_status(self) -> Dict[str, Any]:
        """Get WhatsApp connection status"""
        try:
            url = f"{self.base_url}/health"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get connection status: {str(e)}")
            return {"success": False, "error": str(e), "connection": "error"}

    async def get_qr_code(self) -> Optional[str]:
        """Get QR code for WhatsApp connection"""
        try:
            url = f"{self.base_url}/qrcode"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data.get('success') and data.get('qrcode'):
                    return data['qrcode']
                return None

        except Exception as e:
            logger.error(f"Failed to get QR code: {str(e)}")
            return None

    async def send_admin_summary(self, message: str) -> bool:
        """Send admin summary to the admin number"""
        try:
            admin_number = "221773387902"
            result = await self.send_text_message(admin_number, message)
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Failed to send admin summary: {str(e)}")
            return False

    async def is_connected(self) -> bool:
        """Check if WhatsApp is connected"""
        try:
            status = await self.get_connection_status()
            return status.get('connection') == 'connected'
        except Exception:
            return False