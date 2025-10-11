"""
Message Normalization Service

This service handles normalization of messages from different platforms
(WhatsApp and Telegram) into a unified format for processing.
Enhanced for Phase 3 with comprehensive message transformation capabilities.
"""

import re
import html
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict

from src.utils.logging import get_logger
from src.utils.exceptions import (
    ValidationError,
    MessageProcessingError
)


@dataclass
class NormalizedMessage:
    """Unified message format for all platforms."""

    # Basic message information
    message_id: str
    platform: str
    platform_user_id: str
    content: str
    content_type: str
    timestamp: datetime

    # User information
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_username: Optional[str] = None
    user_language: Optional[str] = None

    # Message metadata
    chat_id: Optional[str] = None
    chat_type: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    forward_from: Optional[Dict[str, Any]] = None

    # Media information
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    media_caption: Optional[str] = None
    media_metadata: Optional[Dict[str, Any]] = None

    # Location information
    location: Optional[Dict[str, Any]] = None
    venue: Optional[Dict[str, Any]] = None

    # Contact information
    contact: Optional[Dict[str, Any]] = None

    # Processing metadata
    original_data: Optional[Dict[str, Any]] = None
    processing_flags: Optional[Dict[str, bool]] = None
    extracted_entities: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = asdict(self)
        if isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data


class MessageNormalizer:
    """Base class for platform-specific message normalizers."""

    def __init__(self, platform: str):
        self.platform = platform
        self.logger = get_logger(__name__)

    async def normalize(self, raw_message: Dict[str, Any]) -> NormalizedMessage:
        """
        Normalize raw message data.

        Args:
            raw_message: Raw message data from platform

        Returns:
            Normalized message object
        """
        raise NotImplementedError("Subclasses must implement normalize method")


class WhatsAppMessageNormalizer(MessageNormalizer):
    """Normalizer for WhatsApp messages."""

    def __init__(self):
        super().__init__("whatsapp")

    async def normalize(self, raw_message: Dict[str, Any]) -> NormalizedMessage:
        """
        Normalize WhatsApp message data.

        Args:
            raw_message: Raw WhatsApp message data

        Returns:
            Normalized message
        """
        try:
            # Extract basic information
            message_id = raw_message.get('id')
            from_number = raw_message.get('from')
            to_number = raw_message.get('to')
            timestamp = datetime.fromtimestamp(
                int(raw_message.get('timestamp')),
                timezone.utc
            )

            # Extract user information from contacts
            contacts = raw_message.get('contacts', [])
            user_info = {}
            if contacts:
                contact = contacts[0]
                profile = contact.get('profile', {})
                user_info = {
                    'user_name': profile.get('name'),
                    'user_id': from_number
                }

            # Extract message content and type
            content, content_type, media_info = self._extract_content(raw_message)

            # Extract chat information
            chat_id = to_number
            chat_type = "private"  # WhatsApp Business API typically uses private chats

            # Extract reply information
            reply_info = self._extract_reply_info(raw_message)

            # Extract context information
            context = raw_message.get('context', {})
            forward_info = context.get('forwarded', False)
            forward_from = None
            if forward_info:
                forward_from = {
                    'forwarded': True,
                    'forwarding_score': context.get('forwarding_score', 0)
                }

            # Processing flags
            processing_flags = {
                'is_command': self._is_command(content),
                'is_account_creation': self._is_account_creation_request(content),
                'contains_phone': self._contains_phone_number(content),
                'contains_email': self._contains_email(content),
                'is_media_message': media_info is not None
            }

            # Extract entities
            entities = self._extract_entities(content)

            return NormalizedMessage(
                message_id=message_id,
                platform=self.platform,
                platform_user_id=from_number,
                content=content,
                content_type=content_type,
                timestamp=timestamp,
                chat_id=chat_id,
                chat_type=chat_type,
                reply_to_message_id=reply_info.get('message_id') if reply_info else None,
                forward_from=forward_from,
                media_type=media_info['type'] if media_info else None,
                media_url=media_info['url'] if media_info else None,
                media_caption=media_info['caption'] if media_info else None,
                media_metadata=media_info['metadata'] if media_info else None,
                original_data=raw_message,
                processing_flags=processing_flags,
                extracted_entities=entities,
                **user_info
            )

        except Exception as e:
            self.logger.error(f"Error normalizing WhatsApp message: {str(e)}")
            raise MessageProcessingError(f"WhatsApp message normalization failed: {str(e)}")

    def _extract_content(self, message: Dict[str, Any]) -> tuple[str, str, Optional[Dict[str, Any]]]:
        """Extract content, type, and media information from WhatsApp message."""
        if 'text' in message:
            return message['text'].get('body', ''), 'text', None

        elif 'image' in message:
            image = message['image']
            return (
                image.get('caption', '[Image]'),
                'image',
                {
                    'type': 'image',
                    'url': image.get('id'),
                    'caption': image.get('caption'),
                    'metadata': {
                        'mime_type': image.get('mime_type'),
                        'sha256': image.get('sha256'),
                        'file_size': image.get('file_size')
                    }
                }
            )

        elif 'audio' in message:
            audio = message['audio']
            return (
                '[Audio message]',
                'audio',
                {
                    'type': 'audio',
                    'url': audio.get('id'),
                    'metadata': {
                        'mime_type': audio.get('mime_type'),
                        'duration': audio.get('duration'),
                        'sha256': audio.get('sha256'),
                        'file_size': audio.get('file_size')
                    }
                }
            )

        elif 'video' in message:
            video = message['video']
            return (
                video.get('caption', '[Video]'),
                'video',
                {
                    'type': 'video',
                    'url': video.get('id'),
                    'caption': video.get('caption'),
                    'metadata': {
                        'mime_type': video.get('mime_type'),
                        'duration': video.get('duration'),
                        'sha256': video.get('sha256'),
                        'file_size': video.get('file_size')
                    }
                }
            )

        elif 'document' in message:
            document = message['document']
            return (
                f"[Document: {document.get('filename', 'file')}]",
                'document',
                {
                    'type': 'document',
                    'url': document.get('id'),
                    'caption': document.get('caption'),
                    'metadata': {
                        'filename': document.get('filename'),
                        'mime_type': document.get('mime_type'),
                        'sha256': document.get('sha256'),
                        'file_size': document.get('file_size')
                    }
                }
            )

        elif 'interactive' in message:
            interactive = message['interactive']
            if interactive.get('type') == 'button_reply':
                content = interactive['button_reply'].get('title', '[Button reply]')
                return content, 'button_reply', None
            elif interactive.get('type') == 'list_reply':
                content = interactive['list_reply'].get('title', '[List reply]')
                return content, 'list_reply', None

        elif 'location' in message:
            location = message['location']
            return (
                f"[Location: {location.get('latitude', 0)}, {location.get('longitude', 0)}]",
                'location',
                None
            )

        elif 'contacts' in message:
            contacts = message['contacts']
            contact_names = [c.get('name', {}).get('formatted_name', 'Unknown') for c in contacts]
            return f"[Contact: {', '.join(contact_names)}]", 'contact', None

        return '[Unknown message type]', 'unknown', None

    def _extract_reply_info(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract reply information from WhatsApp message."""
        context = message.get('context', {})
        if 'quoted_message_id' in context:
            return {
                'message_id': context['quoted_message_id'],
                'from': context.get('quoted_from')
            }
        return None

    def _is_command(self, content: str) -> bool:
        """Check if content is a command."""
        return content.startswith('/') or content.lower().startswith('!')

    def _is_account_creation_request(self, content: str) -> bool:
        """Check if content indicates an account creation request."""
        keywords = [
            'inscrire', 'inscription', 'compte', 'créer',
            'enregistrer', 'enregistrement', 's\'inscrire',
            'account', 'register', 'create', 'sign up'
        ]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in keywords)

    def _contains_phone_number(self, content: str) -> bool:
        """Check if content contains a phone number."""
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        return bool(re.search(phone_pattern, content))

    def _contains_email(self, content: str) -> bool:
        """Check if content contains an email address."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(email_pattern, content))

    def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract entities from content."""
        entities = []

        # Extract phone numbers
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        for match in re.finditer(phone_pattern, content):
            entities.append({
                'type': 'phone_number',
                'text': match.group(),
                'offset': match.start(),
                'length': match.end() - match.start()
            })

        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, content):
            entities.append({
                'type': 'email',
                'text': match.group(),
                'offset': match.start(),
                'length': match.end() - match.start()
            })

        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        for match in re.finditer(url_pattern, content):
            entities.append({
                'type': 'url',
                'text': match.group(),
                'offset': match.start(),
                'length': match.end() - match.start()
            })

        return entities


class TelegramMessageNormalizer(MessageNormalizer):
    """Normalizer for Telegram messages."""

    def __init__(self):
        super().__init__("telegram")

    async def normalize(self, raw_message: Dict[str, Any]) -> NormalizedMessage:
        """
        Normalize Telegram message data.

        Args:
            raw_message: Raw Telegram message data

        Returns:
            Normalized message
        """
        try:
            # Extract basic information
            message_id = str(raw_message.get('message_id'))
            user = raw_message.get('from', {})
            chat = raw_message.get('chat', {})
            timestamp = datetime.fromtimestamp(
                raw_message.get('date', 0),
                timezone.utc
            )

            # Extract user information
            user_info = {
                'user_id': str(user.get('id')),
                'user_name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                'user_username': user.get('username'),
                'user_language': user.get('language_code')
            }

            # Extract message content and type
            content, content_type, media_info = self._extract_content(raw_message)

            # Extract chat information
            chat_info = {
                'chat_id': str(chat.get('id')),
                'chat_type': chat.get('type')
            }

            # Extract reply information
            reply_info = self._extract_reply_info(raw_message)

            # Extract forward information
            forward_info = self._extract_forward_info(raw_message)

            # Extract location/venue information
            location = None
            venue = None
            if 'location' in raw_message:
                location = raw_message['location']
            if 'venue' in raw_message:
                venue = raw_message['venue']

            # Extract contact information
            contact = raw_message.get('contact')

            # Processing flags
            processing_flags = {
                'is_command': self._is_command(content),
                'is_account_creation': self._is_account_creation_request(content),
                'contains_phone': self._contains_phone_number(content),
                'contains_email': self._contains_email(content),
                'is_media_message': media_info is not None,
                'is_bot_message': user.get('is_bot', False)
            }

            # Extract entities from Telegram message entities
            entities = self._extract_telegram_entities(raw_message)

            return NormalizedMessage(
                message_id=message_id,
                platform=self.platform,
                platform_user_id=user_info['user_id'],
                content=content,
                content_type=content_type,
                timestamp=timestamp,
                reply_to_message_id=reply_info.get('message_id') if reply_info else None,
                forward_from=forward_info,
                location=location,
                venue=venue,
                contact=contact,
                media_type=media_info['type'] if media_info else None,
                media_url=media_info['url'] if media_info else None,
                media_caption=media_info['caption'] if media_info else None,
                media_metadata=media_info['metadata'] if media_info else None,
                original_data=raw_message,
                processing_flags=processing_flags,
                extracted_entities=entities,
                **user_info,
                **chat_info
            )

        except Exception as e:
            self.logger.error(f"Error normalizing Telegram message: {str(e)}")
            raise MessageProcessingError(f"Telegram message normalization failed: {str(e)}")

    def _extract_content(self, message: Dict[str, Any]) -> tuple[str, str, Optional[Dict[str, Any]]]:
        """Extract content, type, and media information from Telegram message."""
        if 'text' in message:
            return message['text'], 'text', None

        elif 'photo' in message:
            photo = message['photo'][-1]  # Get largest photo
            return (
                message.get('caption', '[Photo]'),
                'photo',
                {
                    'type': 'photo',
                    'url': f"photo_{photo.get('file_id')}",
                    'caption': message.get('caption'),
                    'metadata': {
                        'file_id': photo.get('file_id'),
                        'file_unique_id': photo.get('file_unique_id'),
                        'file_size': photo.get('file_size'),
                        'width': photo.get('width'),
                        'height': photo.get('height')
                    }
                }
            )

        elif 'video' in message:
            video = message['video']
            return (
                message.get('caption', '[Video]'),
                'video',
                {
                    'type': 'video',
                    'url': f"video_{video.get('file_id')}",
                    'caption': message.get('caption'),
                    'metadata': {
                        'file_id': video.get('file_id'),
                        'file_unique_id': video.get('file_unique_id'),
                        'file_size': video.get('file_size'),
                        'width': video.get('width'),
                        'height': video.get('height'),
                        'duration': video.get('duration')
                    }
                }
            )

        elif 'audio' in message:
            audio = message['audio']
            return (
                f"[Audio: {audio.get('title', 'file')}]",
                'audio',
                {
                    'type': 'audio',
                    'url': f"audio_{audio.get('file_id')}",
                    'metadata': {
                        'file_id': audio.get('file_id'),
                        'file_unique_id': audio.get('file_unique_id'),
                        'file_size': audio.get('file_size'),
                        'duration': audio.get('duration'),
                        'title': audio.get('title'),
                        'performer': audio.get('performer')
                    }
                }
            )

        elif 'voice' in message:
            voice = message['voice']
            return (
                '[Voice message]',
                'voice',
                {
                    'type': 'voice',
                    'url': f"voice_{voice.get('file_id')}",
                    'metadata': {
                        'file_id': voice.get('file_id'),
                        'file_unique_id': voice.get('file_unique_id'),
                        'file_size': voice.get('file_size'),
                        'duration': voice.get('duration')
                    }
                }
            )

        elif 'document' in message:
            document = message['document']
            return (
                f"[Document: {document.get('file_name', 'file')}]",
                'document',
                {
                    'type': 'document',
                    'url': f"document_{document.get('file_id')}",
                    'caption': message.get('caption'),
                    'metadata': {
                        'file_id': document.get('file_id'),
                        'file_unique_id': document.get('file_unique_id'),
                        'file_name': document.get('file_name'),
                        'mime_type': document.get('mime_type'),
                        'file_size': document.get('file_size')
                    }
                }
            )

        elif 'sticker' in message:
            sticker = message['sticker']
            return (
                f"[Sticker: {sticker.get('emoji', 'sticker')}]",
                'sticker',
                {
                    'type': 'sticker',
                    'url': f"sticker_{sticker.get('file_id')}",
                    'metadata': {
                        'file_id': sticker.get('file_id'),
                        'file_unique_id': sticker.get('file_unique_id'),
                        'width': sticker.get('width'),
                        'height': sticker.get('height'),
                        'emoji': sticker.get('emoji')
                    }
                }
            )

        elif 'animation' in message:
            animation = message['animation']
            return (
                '[Animation/GIF]',
                'animation',
                {
                    'type': 'animation',
                    'url': f"animation_{animation.get('file_id')}",
                    'metadata': {
                        'file_id': animation.get('file_id'),
                        'file_unique_id': animation.get('file_unique_id'),
                        'file_size': animation.get('file_size'),
                        'width': animation.get('width'),
                        'height': animation.get('height'),
                        'duration': animation.get('duration')
                    }
                }
            )

        elif 'location' in message:
            location = message['location']
            return (
                f"[Location: {location.get('latitude', 0)}, {location.get('longitude', 0)}]",
                'location',
                None
            )

        elif 'venue' in message:
            venue = message['venue']
            return (
                f"[Venue: {venue.get('title', '')}]",
                'venue',
                None
            )

        elif 'contact' in message:
            contact = message['contact']
            name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
            return (
                f"[Contact: {name} ({contact.get('phone_number', '')})]",
                'contact',
                None
            )

        elif 'poll' in message:
            poll = message['poll']
            return (
                f"[Poll: {poll.get('question', '')}]",
                'poll',
                None
            )

        return '[Unknown message type]', 'unknown', None

    def _extract_reply_info(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract reply information from Telegram message."""
        if 'reply_to_message' in message:
            reply = message['reply_to_message']
            return {
                'message_id': str(reply.get('message_id')),
                'from': reply.get('from', {}).get('id')
            }
        return None

    def _extract_forward_info(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract forward information from Telegram message."""
        if 'forward_from' in message:
            forward_from = message['forward_from']
            return {
                'forwarded': True,
                'from_user': {
                    'id': forward_from.get('id'),
                    'first_name': forward_from.get('first_name'),
                    'last_name': forward_from.get('last_name'),
                    'username': forward_from.get('username')
                },
                'forward_date': datetime.fromtimestamp(
                    message.get('forward_date', 0),
                    timezone.utc
                ).isoformat()
            }
        elif 'forward_from_chat' in message:
            forward_from_chat = message['forward_from_chat']
            return {
                'forwarded': True,
                'from_chat': {
                    'id': forward_from_chat.get('id'),
                    'title': forward_from_chat.get('title'),
                    'type': forward_from_chat.get('type')
                },
                'forward_date': datetime.fromtimestamp(
                    message.get('forward_date', 0),
                    timezone.utc
                ).isoformat()
            }
        return None

    def _is_command(self, content: str) -> bool:
        """Check if content is a command."""
        return content.startswith('/') or content.lower().startswith('!')

    def _is_account_creation_request(self, content: str) -> bool:
        """Check if content indicates an account creation request."""
        keywords = [
            'inscrire', 'inscription', 'compte', 'créer',
            'enregistrer', 'enregistrement', 's\'inscrire',
            'account', 'register', 'create', 'sign up',
            '/start', '/register', '/create'
        ]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in keywords)

    def _contains_phone_number(self, content: str) -> bool:
        """Check if content contains a phone number."""
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        return bool(re.search(phone_pattern, content))

    def _contains_email(self, content: str) -> bool:
        """Check if content contains an email address."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(email_pattern, content))

    def _extract_telegram_entities(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities from Telegram message entities."""
        entities = []
        content = message.get('text', '')
        message_entities = message.get('entities', [])

        for entity in message_entities:
            entity_type = entity.get('type')
            offset = entity.get('offset', 0)
            length = entity.get('length', 0)

            if offset + length <= len(content):
                text = content[offset:offset + length]

                entities.append({
                    'type': entity_type,
                    'text': text,
                    'offset': offset,
                    'length': length,
                    'language': entity.get('language'),  # For mention or hashtag
                    'url': entity.get('url')  # For text_link
                })

        return entities


class MessageNormalizationService:
    """
    Service for normalizing messages from different platforms.

    This service provides a unified interface for processing messages
    from WhatsApp and Telegram into a standardized format.
    """

    def __init__(self):
        """Initialize message normalization service."""
        self.whatsapp_normalizer = WhatsAppMessageNormalizer()
        self.telegram_normalizer = TelegramMessageNormalizer()
        self.logger = get_logger(__name__)

    async def normalize_message(
        self,
        platform: str,
        raw_message: Dict[str, Any]
    ) -> NormalizedMessage:
        """
        Normalize message from specified platform.

        Args:
            platform: Platform name ('whatsapp' or 'telegram')
            raw_message: Raw message data from platform

        Returns:
            Normalized message
        """
        try:
            if platform.lower() == 'whatsapp':
                return await self.whatsapp_normalizer.normalize(raw_message)
            elif platform.lower() == 'telegram':
                return await self.telegram_normalizer.normalize(raw_message)
            else:
                raise ValidationError(f"Unsupported platform: {platform}")

        except Exception as e:
            self.logger.error(f"Error normalizing message from {platform}: {str(e)}")
            raise MessageProcessingError(f"Message normalization failed: {str(e)}")

    async def normalize_messages_batch(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[NormalizedMessage]:
        """
        Normalize multiple messages in batch.

        Args:
            messages: List of messages with platform and data

        Returns:
            List of normalized messages
        """
        try:
            normalized_messages = []

            for message_data in messages:
                platform = message_data.get('platform')
                raw_message = message_data.get('data')

                if platform and raw_message:
                    normalized = await self.normalize_message(platform, raw_message)
                    normalized_messages.append(normalized)
                else:
                    self.logger.warning(f"Invalid message data: {message_data}")

            return normalized_messages

        except Exception as e:
            self.logger.error(f"Error in batch message normalization: {str(e)}")
            raise MessageProcessingError(f"Batch normalization failed: {str(e)}")

    def extract_account_creation_signals(self, message: NormalizedMessage) -> Dict[str, Any]:
        """
        Extract signals related to account creation from normalized message.

        Args:
            message: Normalized message

        Returns:
            Dictionary of account creation signals
        """
        try:
            signals = {
                'is_account_creation_request': message.processing_flags.get('is_account_creation', False),
                'is_command': message.processing_flags.get('is_command', False),
                'contains_phone': message.processing_flags.get('contains_phone', False),
                'contains_email': message.processing_flags.get('contains_email', False),
                'phone_numbers': [],
                'emails': [],
                'urls': [],
                'keywords': []
            }

            # Extract phone numbers from entities
            if message.extracted_entities:
                for entity in message.extracted_entities:
                    if entity['type'] == 'phone_number':
                        signals['phone_numbers'].append(entity['text'])
                    elif entity['type'] == 'email':
                        signals['emails'].append(entity['text'])
                    elif entity['type'] == 'url':
                        signals['urls'].append(entity['text'])

            # Extract keywords from content
            content_lower = message.content.lower()
            account_keywords = [
                'inscrire', 'inscription', 'compte', 'créer',
                'enregistrer', 'enregistrement', 's\'inscrire',
                'account', 'register', 'create', 'sign up',
                'parent', 'catechese', 'enfant'
            ]

            for keyword in account_keywords:
                if keyword in content_lower:
                    signals['keywords'].append(keyword)

            # Calculate confidence score
            confidence = 0
            if signals['is_account_creation_request']:
                confidence += 0.5
            if signals['is_command']:
                confidence += 0.3
            if signals['phone_numbers']:
                confidence += 0.2
            if signals['keywords']:
                confidence += 0.1 * len(signals['keywords'])

            signals['confidence_score'] = min(confidence, 1.0)

            return signals

        except Exception as e:
            self.logger.error(f"Error extracting account creation signals: {str(e)}")
            return {
                'error': str(e),
                'confidence_score': 0.0
            }


# Factory function for getting message normalization service
def get_message_normalization_service() -> MessageNormalizationService:
    """Get message normalization service instance."""
    return MessageNormalizationService()