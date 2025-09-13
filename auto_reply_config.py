import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, time
import re

logger = logging.getLogger(__name__)

class AutoReplyConfig:
    """Configuration for auto-reply functionality"""

    def __init__(self):
        self.enabled = os.getenv('AUTO_REPLY_ENABLED', 'true').lower() == 'true'
        self.waha_api_key = os.getenv('WAHA_API_KEY', '28C5435535C2487DAFBD1164B9CD4E34')
        self.waha_base_url = os.getenv('WAHA_BASE_URL', 'https://waha-core.niox.ovh/api')
        self.session_name = os.getenv('SESSION_NAME', 'default')

        # Time-based controls
        self.working_hours_start = os.getenv('WORKING_HOURS_START', '09:00')
        self.working_hours_end = os.getenv('WORKING_HOURS_END', '18:00')
        self.weekend_enabled = os.getenv('WEEKEND_AUTO_REPLY', 'false').lower() == 'true'

        # Reply settings
        self.default_reply = os.getenv('DEFAULT_REPLY',
            "🤖 Merci pour votre message! Nous avons bien reçu votre demande et vous répondrons dès que possible.\n\n📞 Pour une urgence, contactez-nous directement au: [votre numéro]")

        self.out_of_hours_reply = os.getenv('OUT_OF_HOURS_REPLY',
            "🌙 Bonsoir! Nous sommes actuellement hors de nos heures de bureau.\n\nNos horaires: Lundi-Vendredi 9h-18h\nNous vous répondrons dès notre retour.")

        # Load custom replies from file
        self.custom_replies = self._load_custom_replies()

        # Blacklist contacts that shouldn't get auto-replies
        self.blacklisted_contacts = set(os.getenv('BLACKLISTED_CONTACTS', '').split(','))

        logger.info(f"Auto-reply config loaded - Enabled: {self.enabled}")

    def _load_custom_replies(self) -> Dict[str, str]:
        """Load custom keyword-based replies"""
        custom_replies_file = 'custom_replies.json'
        if os.path.exists(custom_replies_file):
            try:
                with open(custom_replies_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading custom replies: {e}")

        # Default custom replies
        return {
            r'bonjour|salut|hello|hi|hey': "👋 Bonjour! Comment puis-je vous aider aujourd'hui?",
            r'merci|thanks|thank you': "🙏 Avec plaisir! N'hésitez pas si vous avez d'autres questions.",
            r'au revoir|bye|goodbye': "👋 Au revoir! Passez une excellente journée!",
            r'urgence|urgent|help|aide': "🚨 Nous avons bien reçu votre demande d'urgence. Notre équipe va vous contacter rapidement.",
            r'prix|tarif|cost|price': "💰 Pour nos tarifs, merci de consulter notre site web ou de nous contacter directement.",
            r'horaires|ouverture|hours': "🕒 Nous sommes ouverts Lundi-Vendredi de 9h à 18h.",
            r'contact|téléphone|phone|call': "📞 Vous pouvez nous contacter au [votre numéro] pendant les heures de bureau."
        }

    def is_working_hours(self) -> bool:
        """Check if current time is within working hours"""
        try:
            now = datetime.now()

            # Check if weekend
            if now.weekday() >= 5 and not self.weekend_enabled:  # Saturday (5) or Sunday (6)
                return False

            # Parse working hours
            start_time = datetime.strptime(self.working_hours_start, '%H:%M').time()
            # NOTE: fix format string for minutes (was %H:%H)
            end_time = datetime.strptime(self.working_hours_end, '%H:%M').time()
            current_time = now.time()

            return start_time <= current_time <= end_time
        except Exception as e:
            logger.error(f"Error checking working hours: {e}")
            return True  # Default to working hours if error

    def should_reply(self, message_data: Dict[str, Any]) -> bool:
        """Determine if auto-reply should be sent"""
        logger.info(f"DEBUG - should_reply checks starting")

        if not self.enabled:
            logger.info("DEBUG - Auto-reply disabled")
            return False

        # Don't reply to own messages
        payload = message_data.get('payload', {}) or message_data.get('data', {})
        from_me = (
            message_data.get('fromMe')
            or payload.get('fromMe')
            or (payload.get('media', {}).get('key', {}).get('fromMe') if isinstance(payload.get('media', {}), dict) else None)
            or False
        )
        logger.info(f"DEBUG - fromMe check: {from_me}")
        if from_me:
            logger.info("DEBUG - Skipping own message")
            return False

        # Check if contact is blacklisted
        raw_from = payload.get('from', '')
        media = payload.get('media', {})
        remote_jid = media.get('key', {}).get('remoteJid', '') if isinstance(media, dict) else ''

        # Use remoteJid if available, otherwise fall back to from field
        if remote_jid:
            source_jid = remote_jid
            from_number = remote_jid.replace('@c.us', '').replace('@s.whatsapp.net', '')
            logger.info(f"DEBUG - Using remoteJid: '{remote_jid}'")
        else:
            source_jid = raw_from
            from_number = raw_from.replace('@c.us', '').replace('@s.whatsapp.net', '')
            logger.info(f"DEBUG - Using from field: '{raw_from}'")

        logger.info(f"DEBUG - from_number for blacklist: '{from_number}'")

        if any(contact in from_number for contact in self.blacklisted_contacts if contact):
            logger.info("DEBUG - Contact blacklisted")
            return False

        # Don't reply to group messages (optional)
        if isinstance(source_jid, str) and source_jid.endswith('@g.us'):
            logger.info("DEBUG - Group message detected")
            group_reply_enabled = os.getenv('GROUP_AUTO_REPLY', 'false').lower() == 'true'
            logger.info(f"DEBUG - Group reply enabled: {group_reply_enabled}")
            return group_reply_enabled

        logger.info("DEBUG - All checks passed, should reply")
        return True

    def get_reply_message(self, message_text: str) -> str:
        """Get appropriate reply message based on content and time"""
        # Check for custom keyword matches first
        for pattern, reply in self.custom_replies.items():
            if re.search(pattern, message_text, re.IGNORECASE):
                return reply

        # Time-based replies
        if self.is_working_hours():
            return self.default_reply
        else:
            return self.out_of_hours_reply

    def save_custom_replies(self, replies: Dict[str, str]) -> bool:
        """Save custom replies to file"""
        try:
            with open('custom_replies.json', 'w', encoding='utf-8') as f:
                json.dump(replies, f, ensure_ascii=False, indent=2)
            self.custom_replies = replies
            return True
        except Exception as e:
            logger.error(f"Error saving custom replies: {e}")
            return False

# Global config instance
auto_reply_config = AutoReplyConfig()
