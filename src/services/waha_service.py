"""
WAHA integration service for WhatsApp messaging operations
"""

import json
import httpx
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from src.utils.config import get_settings
from src.models.message import MessageType, MessageStatus
from src.models.interaction import InteractionCreate
import structlog

logger = structlog.get_logger()


class WAHAService:
    """Service for WAHA WhatsApp API integration"""

    def __init__(self):
        self.settings = get_settings()
        # Use the base URL as provided, the _build_url method handles the API path
        self.base_url = self.settings.waha_base_url.rstrip('/')
        self.api_key = self.settings.waha_api_token
        self.session_id = self.settings.waha_session_id
        
        # Log configuration for debugging (without exposing sensitive data)
        api_key_status = "SET" if self.api_key and self.api_key != "default-token" else "NOT_SET"
        logger.info(
            "waha_service_initialized",
            base_url=self.base_url,
            session_id=self.session_id,
            api_key_status=api_key_status
        )
        
        self.http_client = httpx.AsyncClient(timeout=30.0)

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for WAHA API endpoint"""
        # For WAHA, the correct URL pattern is: {base_url}/api/{endpoint}
        # The session ID is passed in the request body, not the URL
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/api/{endpoint}"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    async def check_session_status(self) -> Dict[str, Any]:
        """
        Check WAHA session status

        Returns:
            Session status information
        """
        try:
            url = self._build_url('/status')
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            status = response.json()
            logger.info("waha_session_status_checked", status=status.get('status'))
            return status
        except Exception as e:
            logger.error("waha_session_status_check_failed", error=str(e))
            return {"status": "error", "error": str(e)}

    async def start_session(self) -> bool:
        """
        Start WAHA session

        Returns:
            True if session started successfully, False otherwise
        """
        try:
            url = self._build_url('/start')
            response = await self.http_client.post(url, headers=self._get_headers())
            response.raise_for_status()
            logger.info("waha_session_started")
            return True
        except Exception as e:
            logger.error("waha_session_start_failed", error=str(e))
            return False

    async def stop_session(self) -> bool:
        """
        Stop WAHA session

        Returns:
            True if session stopped successfully, False otherwise
        """
        try:
            url = self._build_url('/stop')
            response = await self.http_client.post(url, headers=self._get_headers())
            response.raise_for_status()
            logger.info("waha_session_stopped")
            return True
        except Exception as e:
            logger.error("waha_session_stop_failed", error=str(e))
            return False

    async def restart_session(self) -> bool:
        """
        Restart WAHA session

        Returns:
            True if session restarted successfully, False otherwise
        """
        try:
            url = self._build_url('/restart')
            response = await self.http_client.post(url, headers=self._get_headers())
            response.raise_for_status()
            logger.info("waha_session_restarted")
            return True
        except Exception as e:
            logger.error("waha_session_restart_failed", error=str(e))
            return False

    async def send_text_message(
        self,
        phone_number: str,
        message: str,
        quoted_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send text message via WhatsApp

        Args:
            phone_number: Recipient phone number
            message: Message content
            quoted_message_id: Optional message ID to reply to

        Returns:
            Message response data
        """
        try:
            # Validate phone number format
            phone_number = self._format_phone_number(phone_number)

            url = self._build_url('/sendText')
            payload = {
                'session': self.session_id,
                'chatId': f"{phone_number}@c.us",
                'text': message
            }

            if quoted_message_id:
                payload['quotedMessageId'] = quoted_message_id

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info("text_message_sent", phone_number=phone_number, message_id=result.get('id'))
            return result

        except Exception as e:
            logger.error("text_message_send_failed", phone_number=phone_number, error=str(e))
            raise

    async def send_media_message(
        self,
        phone_number: str,
        media_url: str,
        media_type: str,
        caption: Optional[str] = None,
        quoted_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send media message (image, document, audio, video)

        Args:
            phone_number: Recipient phone number
            media_url: URL to media file
            media_type: Type of media (image, document, audio, video)
            caption: Optional caption for media
            quoted_message_id: Optional message ID to reply to

        Returns:
            Message response data
        """
        try:
            phone_number = self._format_phone_number(phone_number)

            if media_type == 'image':
                url = self._build_url('/sendImage')
                payload = {
                    'session': self.session_id,
                    'chatId': f"{phone_number}@c.us",
                    'image': media_url
                }
            elif media_type == 'document':
                url = self._build_url('/sendDocument')
                payload = {
                    'session': self.session_id,
                    'chatId': f"{phone_number}@c.us",
                    'document': media_url
                }
            elif media_type == 'audio':
                url = self._build_url('/sendAudio')
                payload = {
                    'session': self.session_id,
                    'chatId': f"{phone_number}@c.us",
                    'audio': media_url
                }
            elif media_type == 'video':
                url = self._build_url('/sendVideo')
                payload = {
                    'session': self.session_id,
                    'chatId': f"{phone_number}@c.us",
                    'video': media_url
                }
            else:
                raise ValueError(f"Unsupported media type: {media_type}")

            if caption:
                payload['caption'] = caption
            if quoted_message_id:
                payload['quotedMessageId'] = quoted_message_id

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info("media_message_sent", phone_number=phone_number, media_type=media_type, message_id=result.get('id'))
            return result

        except Exception as e:
            logger.error("media_message_send_failed", phone_number=phone_number, media_type=media_type, error=str(e))
            raise

    async def send_location(
        self,
        phone_number: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send location message

        Args:
            phone_number: Recipient phone number
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            name: Optional location name
            address: Optional location address

        Returns:
            Message response data
        """
        try:
            phone_number = self._format_phone_number(phone_number)

            url = self._build_url('/sendLocation')
            payload = {
                'session': self.session_id,
                'chatId': f"{phone_number}@c.us",
                'lat': latitude,
                'lng': longitude
            }

            if name:
                payload['name'] = name
            if address:
                payload['address'] = address

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info("location_message_sent", phone_number=phone_number, message_id=result.get('id'))
            return result

        except Exception as e:
            logger.error("location_message_send_failed", phone_number=phone_number, error=str(e))
            raise

    async def send_contact(
        self,
        phone_number: str,
        contact_name: str,
        contact_phone: str,
        contact_organization: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send contact message

        Args:
            phone_number: Recipient phone number
            contact_name: Contact name to send
            contact_phone: Contact phone number
            contact_organization: Optional contact organization

        Returns:
            Message response data
        """
        try:
            phone_number = self._format_phone_number(phone_number)

            url = self._build_url('/sendContact')
            payload = {
                'session': self.session_id,
                'chatId': f"{phone_number}@c.us",
                'name': contact_name,
                'phone': contact_phone
            }

            if contact_organization:
                payload['organization'] = contact_organization

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info("contact_message_sent", phone_number=phone_number, message_id=result.get('id'))
            return result

        except Exception as e:
            logger.error("contact_message_send_failed", phone_number=phone_number, error=str(e))
            raise

    async def send_buttons(
        self,
        phone_number: str,
        text: str,
        buttons: List[Dict[str, str]],
        title: Optional[str] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive buttons

        Args:
            phone_number: Recipient phone number
            text: Message text
            buttons: List of button objects with 'id' and 'text'
            title: Optional button title
            footer: Optional button footer

        Returns:
            Message response data
        """
        try:
            phone_number = self._format_phone_number(phone_number)

            url = self._build_url('/sendButtons')
            payload = {
                'session': self.session_id,
                'chatId': f"{phone_number}@c.us",
                'text': text,
                'buttons': buttons
            }

            if title:
                payload['title'] = title
            if footer:
                payload['footer'] = footer

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info("buttons_message_sent", phone_number=phone_number, message_id=result.get('id'))
            return result

        except Exception as e:
            logger.error("buttons_message_send_failed", phone_number=phone_number, error=str(e))
            raise

    async def send_list(
        self,
        phone_number: str,
        text: str,
        title: str,
        button_text: str,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send interactive list message

        Args:
            phone_number: Recipient phone number
            text: Message text
            title: List title
            button_text: Button text
            sections: List of sections with rows

        Returns:
            Message response data
        """
        try:
            phone_number = self._format_phone_number(phone_number)

            url = self._build_url('/sendList')
            payload = {
                'session': self.session_id,
                'chatId': f"{phone_number}@c.us",
                'text': text,
                'title': title,
                'buttonText': button_text,
                'sections': sections
            }

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            result = response.json()
            logger.info("list_message_sent", phone_number=phone_number, message_id=result.get('id'))
            return result

        except Exception as e:
            logger.error("list_message_send_failed", phone_number=phone_number, error=str(e))
            raise

    async def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark message as read

        Args:
            message_id: Message ID to mark as read

        Returns:
            True if successful, False otherwise
        """
        try:
            url = self._build_url('/markMessageAsRead')
            payload = {'messageId': message_id, 'session': self.session_id}

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            logger.info("message_marked_as_read", message_id=message_id)
            return True

        except Exception as e:
            logger.error("message_mark_as_read_failed", message_id=message_id, error=str(e))
            return False

    async def delete_message(self, message_id: str, for_everyone: bool = False) -> bool:
        """
        Delete a message

        Args:
            message_id: Message ID to delete
            for_everyone: Whether to delete for everyone (True) or just for me (False)

        Returns:
            True if successful, False otherwise
        """
        try:
            url = self._build_url('/deleteMessage')
            payload = {
                'messageId': message_id,
                'everyone': for_everyone,
                'session': self.session_id
            }

            response = await self.http_client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            logger.info("message_deleted", message_id=message_id, for_everyone=for_everyone)
            return True

        except Exception as e:
            logger.error("message_delete_failed", message_id=message_id, error=str(e))
            return False

    async def get_chat_history(
        self,
        phone_number: str,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a contact

        Args:
            phone_number: Contact phone number
            limit: Maximum number of messages to retrieve
            cursor: Optional cursor for pagination

        Returns:
            List of messages
        """
        try:
            phone_number = self._format_phone_number(phone_number)
            chat_id = f"{phone_number}@c.us"

            url = self._build_url('/chatHistory')
            params = {
                'session': self.session_id,
                'chatId': chat_id,
                'limit': limit
            }

            if cursor:
                params['cursor'] = cursor

            response = await self.http_client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()

            messages = response.json()
            logger.info("chat_history_retrieved", phone_number=phone_number, count=len(messages))
            return messages

        except Exception as e:
            logger.error("chat_history_retrieval_failed", phone_number=phone_number, error=str(e))
            raise

    async def get_chat_info(self, phone_number: str) -> Dict[str, Any]:
        """
        Get chat information for a contact

        Args:
            phone_number: Contact phone number

        Returns:
            Chat information
        """
        try:
            phone_number = self._format_phone_number(phone_number)
            chat_id = f"{phone_number}@c.us"

            url = self._build_url('/chatInfo')
            params = {'session': self.session_id, 'chatId': chat_id}

            response = await self.http_client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()

            chat_info = response.json()
            logger.info("chat_info_retrieved", phone_number=phone_number)
            return chat_info

        except Exception as e:
            logger.error("chat_info_retrieval_failed", phone_number=phone_number, error=str(e))
            raise

    async def get_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all contacts

        Returns:
            List of contacts
        """
        try:
            url = self._build_url('/contacts')

            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()

            contacts = response.json()
            logger.info("contacts_retrieved", count=len(contacts))
            return contacts

        except Exception as e:
            logger.error("contacts_retrieval_failed", error=str(e))
            raise

    async def get_profile_picture(self, phone_number: str) -> Optional[str]:
        """
        Get profile picture URL for a contact

        Args:
            phone_number: Contact phone number

        Returns:
            Profile picture URL or None
        """
        try:
            phone_number = self._format_phone_number(phone_number)
            chat_id = f"{phone_number}@c.us"

            url = self._build_url('/profilePicture')
            params = {'session': self.session_id, 'chatId': chat_id}

            response = await self.http_client.get(
                url,
                params=params,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                picture_url = response.text
                logger.info("profile_picture_retrieved", phone_number=phone_number)
                return picture_url
            elif response.status_code == 404:
                logger.info("no_profile_picture", phone_number=phone_number)
                return None
            else:
                response.raise_for_status()

        except Exception as e:
            logger.error("profile_picture_retrieval_failed", phone_number=phone_number, error=str(e))
            return None

    async def get_qr_code(self) -> Optional[str]:
        """
        Get QR code for session authentication

        Returns:
            QR code image URL or None
        """
        try:
            url = self._build_url('/qr')

            response = await self.http_client.get(url, headers=self._get_headers())

            if response.status_code == 200:
                qr_code_url = response.text
                logger.info("qr_code_retrieved")
                return qr_code_url
            else:
                logger.warning("qr_code_not_available")
                return None

        except Exception as e:
            logger.error("qr_code_retrieval_failed", error=str(e))
            return None

    async def is_session_connected(self) -> bool:
        """
        Check if WAHA session is connected

        Returns:
            True if connected, False otherwise
        """
        try:
            status = await self.check_session_status()
            return status.get('status') == 'WORKING'
        except Exception as e:
            logger.error("session_connection_check_failed", error=str(e))
            return False

    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for WhatsApp

        Args:
            phone_number: Phone number to format

        Returns:
            Formatted phone number
        """
        if not phone_number or phone_number.strip() == "":
            raise ValueError("Phone number cannot be empty")
        
        # Skip special WhatsApp addresses like status@broadcast
        if '@' in phone_number:
            return phone_number
        
        # Remove all non-digit characters
        cleaned = ''.join(c for c in phone_number if c.isdigit())

        if not cleaned:
            raise ValueError(f"Invalid phone number: {phone_number}")

        # Remove leading + or 00
        if cleaned.startswith('00'):
            cleaned = cleaned[2:]
        elif cleaned.startswith('0') and len(cleaned) > 1:
            # Remove leading zero for some countries
            cleaned = cleaned[1:]

        return cleaned

    async def send_message(
        self,
        message_type: MessageType,
        phone_number: str,
        content: Union[str, Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generic message sending method

        Args:
            message_type: Type of message
            phone_number: Recipient phone number
            content: Message content
            **kwargs: Additional parameters

        Returns:
            Message response data
        """
        try:
            if message_type == MessageType.TEXT:
                return await self.send_text_message(
                    phone_number=phone_number,
                    message=str(content),
                    quoted_message_id=kwargs.get('quoted_message_id')
                )

            elif message_type == MessageType.IMAGE:
                return await self.send_media_message(
                    phone_number=phone_number,
                    media_url=kwargs.get('media_url', str(content)),
                    media_type='image',
                    caption=kwargs.get('caption'),
                    quoted_message_id=kwargs.get('quoted_message_id')
                )

            elif message_type == MessageType.DOCUMENT:
                return await self.send_media_message(
                    phone_number=phone_number,
                    media_url=kwargs.get('media_url', str(content)),
                    media_type='document',
                    caption=kwargs.get('caption'),
                    quoted_message_id=kwargs.get('quoted_message_id')
                )

            elif message_type == MessageType.AUDIO:
                return await self.send_media_message(
                    phone_number=phone_number,
                    media_url=kwargs.get('media_url', str(content)),
                    media_type='audio',
                    quoted_message_id=kwargs.get('quoted_message_id')
                )

            elif message_type == MessageType.VIDEO:
                return await self.send_media_message(
                    phone_number=phone_number,
                    media_url=kwargs.get('media_url', str(content)),
                    media_type='video',
                    caption=kwargs.get('caption'),
                    quoted_message_id=kwargs.get('quoted_message_id')
                )

            elif message_type == MessageType.LOCATION:
                location_data = content if isinstance(content, dict) else json.loads(str(content))
                return await self.send_location(
                    phone_number=phone_number,
                    latitude=location_data.get('latitude', 0),
                    longitude=location_data.get('longitude', 0),
                    name=location_data.get('name'),
                    address=location_data.get('address')
                )

            elif message_type == MessageType.CONTACT:
                contact_data = content if isinstance(content, dict) else json.loads(str(content))
                return await self.send_contact(
                    phone_number=phone_number,
                    contact_name=contact_data.get('name', ''),
                    contact_phone=contact_data.get('phone', ''),
                    contact_organization=contact_data.get('organization')
                )

            elif message_type == MessageType.BUTTONS:
                buttons_data = content if isinstance(content, dict) else json.loads(str(content))
                return await self.send_buttons(
                    phone_number=phone_number,
                    text=buttons_data.get('text', ''),
                    buttons=buttons_data.get('buttons', []),
                    title=buttons_data.get('title'),
                    footer=buttons_data.get('footer')
                )

            elif message_type == MessageType.LIST:
                list_data = content if isinstance(content, dict) else json.loads(str(content))
                return await self.send_list(
                    phone_number=phone_number,
                    text=list_data.get('text', ''),
                    title=list_data.get('title', ''),
                    button_text=list_data.get('button_text', ''),
                    sections=list_data.get('sections', [])
                )

            else:
                raise ValueError(f"Unsupported message type: {message_type}")

        except Exception as e:
            logger.error("message_send_failed", message_type=message_type.value, phone_number=phone_number, error=str(e))
            raise

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
        logger.info("waha_service_closed")