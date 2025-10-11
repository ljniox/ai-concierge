"""
Welcome Message Service

This service handles sending personalized welcome messages to newly created accounts
across different platforms (WhatsApp and Telegram) with rich formatting and options.
Enhanced for Phase 3 with comprehensive message templating and delivery tracking.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum

from src.services.database_service import get_database_service
from src.services.parent_lookup_service import get_parent_lookup_service
from src.utils.logging import get_logger
from src.utils.exceptions import (
    DatabaseConnectionError,
    MessageDeliveryError,
    ValidationError
)


class MessageTemplate(Enum):
    """Available message templates."""
    WELCOME_PARENT = "welcome_parent"
    WELCOME_PARENT_WITH_CHILDREN = "welcome_parent_with_children"
    ACCOUNT_CONFIRMATION = "account_confirmation"
    ONBOARDING_GUIDE = "onboarding_guide"
    SUPPORT_INFO = "support_info"


class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class WelcomeMessageResult:
    """Result of welcome message sending operation."""

    def __init__(
        self,
        success: bool,
        user_id: Optional[UUID] = None,
        message_id: Optional[str] = None,
        platform: Optional[str] = None,
        template_used: Optional[str] = None,
        delivery_status: Optional[MessageStatus] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.user_id = user_id
        self.message_id = message_id
        self.platform = platform
        self.template_used = template_used
        self.delivery_status = delivery_status or MessageStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.timestamp = datetime.now(timezone.utc)


class MessageTemplate:
    """Template for welcome messages with personalization."""

    WELCOME_TEMPLATES = {
        MessageTemplate.WELCOME_PARENT: {
            "fr": """
🎉 **Bienvenue dans le Service de Catéchèse SDB !**

Cher Parent,

Nous sommes ravis de vous accueillir dans notre système de gestion de la catéchèse. Votre compte a été créé avec succès.

📋 **Votre compte est maintenant actif et vous permet de :**
• Voir les informations de vos enfants
• Consulter les emplois du temps
• Communiquer avec les enseignants
• Accéder aux rapports et documents

📱 **Besoin d'aide ?**
Contactez-nous au : +221 77 123 45 67
Ou répondez simplement "aide" à ce message.

Bien cordialement,
L'équipe de la Catéchèse SDB
            """,
            "en": """
🎉 **Welcome to SDB Catechism Service!**

Dear Parent,

We are delighted to welcome you to our catechism management system. Your account has been successfully created.

📋 **Your account is now active and allows you to:**
• View your children's information
• Check schedules
• Communicate with teachers
• Access reports and documents

📱 **Need help?**
Contact us at: +221 77 123 45 67
Or simply reply "help" to this message.

Best regards,
SDB Catechism Team
            """
        },
        MessageTemplate.WELCOME_PARENT_WITH_CHILDREN: {
            "fr": """
🎉 **Bienvenue dans le Service de Catéchèse SDB !**

Cher Parent,

Nous sommes ravis de vous accueillir dans notre système. Votre compte a été créé avec succès.

👨‍👩‍👧‍👦 **Vos enfants trouvés dans notre système :**
{children_list}

📋 **Votre compte vous permet de :**
• Suivre la progression de vos enfants
• Consulter les emplois du temps
• Communiquer avec les enseignants
• Accéder aux documents importants

🎓 **Prochaines étapes :**
1. Explorez les fonctionnalités disponibles
2. Mettez à jour votre profil si nécessaire
3. Contactez-nous pour toute question

📱 **Besoin d'aide ?**
Répondez "aide" à ce message ou appelez-nous au +221 77 123 45 67

Bien cordialement,
L'équipe de la Catéchèse SDB
            """,
            "en": """
🎉 **Welcome to SDB Catechism Service!**

Dear Parent,

We are delighted to welcome you to our system. Your account has been successfully created.

👨‍👩‍👧‍👦 **Your children found in our system:**
{children_list}

📋 **Your account allows you to:**
• Track your children's progress
• Check schedules
• Communicate with teachers
• Access important documents

🎓 **Next steps:**
1. Explore the available features
2. Update your profile if needed
3. Contact us with any questions

📱 **Need help?**
Reply "help" to this message or call us at +221 77 123 45 67

Best regards,
SDB Catechism Team
            """
        },
        MessageTemplate.ACCOUNT_CONFIRMATION: {
            "fr": """
✅ **Confirmation de Création de Compte**

Bonjour {parent_name},

Votre compte a été créé avec succès le {creation_date}.

📊 **Résumé du compte :**
• Nom : {parent_full_name}
• Téléphone : {phone_number}
• Email : {email}
• Rôle : Parent
• Statut : Actif

🔐 **Sécurité :**
• Ce compte est lié à votre numéro de téléphone
• Conservez vos informations de connexion sécurisées

Pour toute question, contactez le support technique.

L'équipe SDB
            """,
            "en": """
✅ **Account Creation Confirmation**

Hello {parent_name},

Your account has been successfully created on {creation_date}.

📊 **Account Summary:**
• Name: {parent_full_name}
• Phone: {phone_number}
• Email: {email}
• Role: Parent
• Status: Active

🔐 **Security:**
• This account is linked to your phone number
• Keep your login information secure

For any questions, contact technical support.

SDB Team
            """
        }
    }


class WelcomeMessageService:
    """
    Service for sending welcome messages to newly created accounts.

    This service handles personalized welcome messages across platforms
    with template-based content and delivery tracking.
    """

    def __init__(
        self,
        database_service=None,
        parent_lookup_service=None,
        whatsapp_client=None,
        telegram_client=None
    ):
        """
        Initialize welcome message service.

        Args:
            database_service: Database service instance
            parent_lookup_service: Parent lookup service instance
            whatsapp_client: WhatsApp API client
            telegram_client: Telegram bot client
        """
        self.database_service = database_service or get_database_service()
        self.parent_lookup_service = parent_lookup_service or get_parent_lookup_service()
        self.whatsapp_client = whatsapp_client
        self.telegram_client = telegram_client
        self.logger = get_logger(__name__)

    async def send_welcome_message(
        self,
        user_id: UUID,
        platform: str,
        platform_user_id: str,
        language: str = "fr",
        template: MessageTemplate = MessageTemplate.WELCOME_PARENT,
        parent_data: Optional[Dict[str, Any]] = None
    ) -> WelcomeMessageResult:
        """
        Send welcome message to newly created user.

        Args:
            user_id: User ID
            platform: Platform name (whatsapp, telegram)
            platform_user_id: Platform-specific user ID
            language: Language for the message (fr, en)
            template: Message template to use
            parent_data: Optional parent data for personalization

        Returns:
            Welcome message result
        """
        try:
            # Get parent data if not provided
            if not parent_data:
                parent_data = await self._get_parent_data(user_id)

            # Generate personalized message
            message_content = await self._generate_message(
                template, language, parent_data
            )

            # Send message via appropriate platform
            message_result = await self._send_platform_message(
                platform, platform_user_id, message_content
            )

            # Log the message delivery
            await self._log_message_delivery(
                user_id, platform, template.value, language, message_result
            )

            return WelcomeMessageResult(
                success=message_result.get('success', False),
                user_id=user_id,
                message_id=message_result.get('message_id'),
                platform=platform,
                template_used=template.value,
                delivery_status=MessageStatus.SENT if message_result.get('success') else MessageStatus.FAILED,
                error_message=message_result.get('error_message')
            )

        except Exception as e:
            self.logger.error(f"Failed to send welcome message to {user_id}: {str(e)}")
            return WelcomeMessageResult(
                success=False,
                user_id=user_id,
                platform=platform,
                error_code="WELCOME_MESSAGE_FAILED",
                error_message=str(e)
            )

    async def send_onboarding_sequence(
        self,
        user_id: UUID,
        platform: str,
        platform_user_id: str,
        language: str = "fr",
        delay_minutes: int = 5
    ) -> List[WelcomeMessageResult]:
        """
        Send a sequence of onboarding messages.

        Args:
            user_id: User ID
            platform: Platform name
            platform_user_id: Platform-specific user ID
            language: Language for messages
            delay_minutes: Delay between messages

        Returns:
            List of welcome message results
        """
        try:
            results = []
            messages = [
                (MessageTemplate.WELCOME_PARENT, 0),
                (MessageTemplate.ACCOUNT_CONFIRMATION, delay_minutes),
                (MessageTemplate.ONBOARDING_GUIDE, delay_minutes * 2)
            ]

            for template, delay in messages:
                if delay > 0:
                    await asyncio.sleep(delay * 60)  # Convert minutes to seconds

                result = await self.send_welcome_message(
                    user_id, platform, platform_user_id, language, template
                )
                results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Failed to send onboarding sequence to {user_id}: {str(e)}")
            return []

    async def send_welcome_to_all_parents(
        self,
        limit: int = 100,
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Send welcome messages to all newly created parents.

        Args:
            limit: Maximum number of messages to send
            language: Default language

        Returns:
            Summary of sending results
        """
        try:
            # Get recently created parent accounts without welcome messages
            query = """
            SELECT ua.id, ua.platform, ua.platform_user_id, ua.metadata,
                   up.first_name, up.last_name, up.email
            FROM user_accounts ua
            LEFT JOIN user_profiles up ON ua.id = up.user_id
            WHERE ua.status = 'ACTIVE' AND ua.created_via IN ('whatsapp', 'telegram')
              AND ua.id NOT IN (
                  SELECT DISTINCT user_id FROM welcome_message_logs
                  WHERE status = 'sent'
              )
            ORDER BY ua.created_at DESC
            LIMIT ?
            """

            results = await self.database_service.fetch_all(
                query,
                (limit,),
                database_name="supabase"
            )

            sent_count = 0
            failed_count = 0
            errors = []

            for user in results:
                try:
                    result = await self.send_welcome_message(
                        user_id=UUID(user['id']),
                        platform=user['platform'],
                        platform_user_id=user['platform_user_id'],
                        language=language
                    )

                    if result.success:
                        sent_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            'user_id': user['id'],
                            'error': result.error_message
                        })

                    # Add small delay to avoid rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    failed_count += 1
                    errors.append({
                        'user_id': user['id'],
                        'error': str(e)
                    })

            summary = {
                'total_processed': len(results),
                'sent_successfully': sent_count,
                'failed': failed_count,
                'errors': errors[:10]  # Limit error details
            }

            self.logger.info(f"Welcome message batch completed: {sent_count} sent, {failed_count} failed")
            return summary

        except Exception as e:
            self.logger.error(f"Failed to send welcome messages batch: {str(e)}")
            return {
                'error': str(e),
                'total_processed': 0,
                'sent_successfully': 0,
                'failed': 0
            }

    async def _generate_message(
        self,
        template: MessageTemplate,
        language: str,
        parent_data: Dict[str, Any]
    ) -> str:
        """
        Generate personalized message from template.

        Args:
            template: Message template
            language: Language code
            parent_data: Parent data for personalization

        Returns:
            Personalized message content
        """
        try:
            # Get template content
            template_content = MessageTemplate.WELCOME_TEMPLATES.get(template, {}).get(language)
            if not template_content:
                template_content = MessageTemplate.WELCOME_TEMPLATES[template]["fr"]  # Fallback to French

            # Prepare replacement variables
            variables = {
                'parent_name': parent_data.get('first_name', 'Parent'),
                'parent_full_name': f"{parent_data.get('first_name', '')} {parent_data.get('last_name', '')}".strip(),
                'phone_number': parent_data.get('phone_number', ''),
                'email': parent_data.get('email', 'Non spécifié'),
                'creation_date': datetime.now(timezone.utc).strftime('%d/%m/%Y'),
                'children_list': await self._format_children_list(parent_data.get('children', []))
            }

            # Replace variables in template
            message = template_content
            for key, value in variables.items():
                message = message.replace(f'{{{key}}}', str(value))

            # Clean up any remaining unreplaced placeholders
            import re
            message = re.sub(r'\{[^}]+\}', '', message)

            return message.strip()

        except Exception as e:
            self.logger.error(f"Failed to generate message: {str(e)}")
            return "Bienvenue ! Votre compte a été créé avec succès."

    async def _format_children_list(self, children: List[Dict[str, Any]]) -> str:
        """Format children list for message."""
        if not children:
            return "Aucun enfant trouvé dans notre système"

        formatted_list = []
        for child in children[:5]:  # Limit to 5 children
            name = child.get('full_name', child.get('first_name', 'Inconnu'))
            class_info = child.get('class_name', f"Classe {child.get('classe_id', '?')}")
            formatted_list.append(f"• {name} - {class_info}")

        if len(children) > 5:
            formatted_list.append(f"• ... et {len(children) - 5} autre(s) enfant(s)")

        return '\n'.join(formatted_list)

    async def _send_platform_message(
        self,
        platform: str,
        platform_user_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Send message via appropriate platform client.

        Args:
            platform: Platform name
            platform_user_id: Platform-specific user ID
            content: Message content

        Returns:
            Send result
        """
        try:
            if platform.lower() == 'whatsapp':
                return await self._send_whatsapp_message(platform_user_id, content)
            elif platform.lower() == 'telegram':
                return await self._send_telegram_message(platform_user_id, content)
            else:
                raise ValidationError(f"Unsupported platform: {platform}")

        except Exception as e:
            self.logger.error(f"Failed to send {platform} message: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }

    async def _send_whatsapp_message(self, user_id: str, content: str) -> Dict[str, Any]:
        """Send message via WhatsApp API."""
        try:
            if not self.whatsapp_client:
                # Mock implementation for testing
                self.logger.info(f"WhatsApp message prepared for {user_id}: {content[:100]}...")
                return {
                    'success': True,
                    'message_id': f"whatsapp_{datetime.now(timezone.utc).timestamp()}",
                    'platform': 'whatsapp'
                }

            # Real implementation would use WhatsApp API client
            result = await self.whatsapp_client.send_message(
                to=user_id,
                text=content,
                message_type="text"
            )

            return {
                'success': True,
                'message_id': result.get('message_id'),
                'platform': 'whatsapp'
            }

        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }

    async def _send_telegram_message(self, user_id: str, content: str) -> Dict[str, Any]:
        """Send message via Telegram API."""
        try:
            if not self.telegram_client:
                # Mock implementation for testing
                self.logger.info(f"Telegram message prepared for {user_id}: {content[:100]}...")
                return {
                    'success': True,
                    'message_id': f"telegram_{datetime.now(timezone.utc).timestamp()}",
                    'platform': 'telegram'
                }

            # Real implementation would use Telegram bot client
            result = await self.telegram_client.send_message(
                chat_id=int(user_id),
                text=content,
                parse_mode="Markdown"
            )

            return {
                'success': True,
                'message_id': str(result.get('message_id')),
                'platform': 'telegram'
            }

        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }

    async def _get_parent_data(self, user_id: UUID) -> Dict[str, Any]:
        """Get parent data for message personalization."""
        try:
            query = """
            SELECT ua.id, ua.phone_number, ua.parent_id, ua.metadata,
                   up.first_name, up.last_name, up.email
            FROM user_accounts ua
            LEFT JOIN user_profiles up ON ua.id = up.user_id
            WHERE ua.id = ?
            """

            result = await self.database_service.fetch_one(
                query,
                (str(user_id),),
                database_name="supabase"
            )

            if result:
                parent_data = dict(result)

                # Get children information if parent_id exists
                if parent_data.get('parent_id'):
                    children = await self.parent_lookup_service.get_parent_children(
                        parent_data['parent_id']
                    )
                    parent_data['children'] = children

                return parent_data

            return {}

        except Exception as e:
            self.logger.error(f"Failed to get parent data: {str(e)}")
            return {}

    async def _log_message_delivery(
        self,
        user_id: UUID,
        platform: str,
        template: str,
        language: str,
        result: Dict[str, Any]
    ) -> None:
        """Log message delivery for tracking."""
        try:
            log_data = {
                'user_id': str(user_id),
                'platform': platform,
                'template_name': template,
                'language': language,
                'message_id': result.get('message_id'),
                'status': 'sent' if result.get('success') else 'failed',
                'error_message': result.get('error_message'),
                'sent_at': datetime.now(timezone.utc)
            }

            await self.database_service.insert(
                'welcome_message_logs',
                log_data,
                database_name='supabase'
            )

        except Exception as e:
            self.logger.error(f"Failed to log message delivery: {str(e)}")

    async def get_message_delivery_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get message delivery statistics."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            query = """
            SELECT platform, template_name, language, status, COUNT(*) as count
            FROM welcome_message_logs
            WHERE sent_at >= ?
            GROUP BY platform, template_name, language, status
            ORDER BY platform, template_name, language
            """

            results = await self.database_service.fetch_all(
                query,
                (cutoff_date,),
                database_name="supabase"
            )

            stats = {
                'period_days': days,
                'total_sent': 0,
                'total_failed': 0,
                'by_platform': {},
                'by_template': {},
                'by_language': {}
            }

            for result in results:
                platform = result['platform']
                template = result['template_name']
                language = result['language']
                status = result['status']
                count = result['count']

                # Update totals
                if status == 'sent':
                    stats['total_sent'] += count
                else:
                    stats['total_failed'] += count

                # Update platform stats
                if platform not in stats['by_platform']:
                    stats['by_platform'][platform] = {'sent': 0, 'failed': 0}
                if status == 'sent':
                    stats['by_platform'][platform]['sent'] += count
                else:
                    stats['by_platform'][platform]['failed'] += count

                # Update template stats
                if template not in stats['by_template']:
                    stats['by_template'][template] = {'sent': 0, 'failed': 0}
                if status == 'sent':
                    stats['by_template'][template]['sent'] += count
                else:
                    stats['by_template'][template]['failed'] += count

                # Update language stats
                if language not in stats['by_language']:
                    stats['by_language'][language] = {'sent': 0, 'failed': 0}
                if status == 'sent':
                    stats['by_language'][language]['sent'] += count
                else:
                    stats['by_language'][language]['failed'] += count

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get message delivery stats: {str(e)}")
            return {}


# Factory function for getting welcome message service
def get_welcome_message_service() -> WelcomeMessageService:
    """Get welcome message service instance."""
    return WelcomeMessageService()