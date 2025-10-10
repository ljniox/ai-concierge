"""
Interaction service for managing conversation interactions and orchestrating conversation flow
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
from supabase import Client
from src.models.interaction import Interaction, InteractionCreate, InteractionUpdate, InteractionWithDetails, InteractionAnalytics, MessageType, InteractionType
from src.models.session import Session, SessionUpdate
from src.models.user import User
from src.services.user_service import UserService
from src.services.session_service import SessionService
from src.services.redis_service import RedisService
from src.services.whatsapp_service import WhatsAppService
from src.services.claude_service import ClaudeService, ServiceType
from src.services.response_formatter import ResponseFormatter
from src.services.profile_service import ProfileService
from src.utils.config import get_settings
import structlog

logger = structlog.get_logger()


class InteractionService:
    """Service for managing interaction operations and orchestrating conversation flow"""

    def __init__(self):
        self.settings = get_settings()
        self.supabase: Optional[Client] = None
        self.user_service = UserService()
        self.session_service = SessionService()
        self.redis_service = RedisService()
        self.whatsapp_service = WhatsAppService(
            base_url=os.getenv('WHATSAPP_API_URL', 'http://whatsapp-service:3001'),
            instance_name=os.getenv('WHATSAPP_SERVICE_NAME', 'gust-ia')
        )
        self.claude_service = ClaudeService()
        self.response_formatter = ResponseFormatter()
        self.profile_service = ProfileService()
        self._initialize_supabase()

    async def initialize_redis(self):
        """Initialize Redis connection"""
        await self.redis_service.initialize()

    def _initialize_supabase(self):
        """Initialize Supabase client"""
        try:
            from supabase import create_client
            # Initialize Supabase with minimal parameters to avoid proxy issues
            self.supabase = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key
            )
            logger.info("supabase_client_initialized")
        except Exception as e:
            logger.error("supabase_initialization_failed", error=str(e))
            # Don't raise - allow application to start without Supabase
            self.supabase = None

    async def create_interaction(self, interaction_data: InteractionCreate) -> Interaction:
        """
        Create a new interaction

        Args:
            interaction_data: Interaction creation data

        Returns:
            Created interaction object
        """
        try:
            logger.info("creating_interaction", session_id=interaction_data.session_id)

            # Verify session exists
            session = await self.session_service.get_session_by_id(interaction_data.session_id)
            if not session:
                raise ValueError(f"Session {interaction_data.session_id} not found")

            # Update session activity
            await self.session_service.update_session_activity(interaction_data.session_id)
            await self.session_service.increment_message_count(interaction_data.session_id)

            # Create interaction
            interaction_dict = {
                "session_id": interaction_data.session_id,
                "user_id": session.user_id,
                "user_message": interaction_data.user_message,
                "assistant_response": interaction_data.assistant_response,
                "service": str(interaction_data.service),
                "interaction_type": interaction_data.interaction_type.value if isinstance(interaction_data.interaction_type, str) else interaction_data.interaction_type,
                "message_type": interaction_data.message_type.value if isinstance(interaction_data.message_type, str) else interaction_data.message_type,
                "confidence_score": interaction_data.confidence_score,
                "metadata": interaction_data.metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            response = self.supabase.table("interactions").insert(interaction_dict).execute()

            if response.data:
                created_interaction = Interaction(
                    id=response.data[0]["id"],
                    session_id=interaction_data.session_id,
                    user_message=interaction_data.user_message,
                    assistant_response=interaction_data.assistant_response,
                    service=str(interaction_data.service),
                    interaction_type=interaction_data.interaction_type,
                    message_type=interaction_data.message_type,
                    confidence_score=interaction_data.confidence_score,
                    metadata=interaction_data.metadata or {},
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    phone_number=None,  # Will be set below
                    language_detected=None,
                    intent_detected=None,
                    sentiment_score=None,
                    processing_time_ms=None
                )

                # Add phone number from user
                user = await self.user_service.get_user_by_id(session.user_id)
                if user:
                    created_interaction.phone_number = user.phone_number

                logger.info("interaction_created_successfully", interaction_id=created_interaction.id)
                return created_interaction
            else:
                raise Exception("Failed to create interaction")

        except Exception as e:
            logger.error("interaction_creation_failed", session_id=interaction_data.session_id, error=str(e))
            raise

    async def get_interaction_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """
        Get interaction by ID

        Args:
            interaction_id: Interaction ID to retrieve

        Returns:
            Interaction object if found, None otherwise
        """
        try:
            logger.info("getting_interaction_by_id", interaction_id=interaction_id)

            response = self.supabase.table("interactions").select("*").eq("id", interaction_id).execute()

            if response.data:
                interaction_data = response.data[0]
                return Interaction(
                    id=interaction_data["id"],
                    session_id=interaction_data["session_id"],
                    user_message=interaction_data["user_message"],
                    assistant_response=interaction_data["assistant_response"],
                    service=interaction_data["service"],
                    interaction_type=interaction_data["interaction_type"],
                    message_type=interaction_data["message_type"],
                    confidence_score=interaction_data["confidence_score"],
                    metadata=interaction_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(interaction_data["created_at"]),
                    updated_at=datetime.fromisoformat(interaction_data["updated_at"]),
                    phone_number=interaction_data.get("phone_number"),
                    language_detected=interaction_data.get("language_detected"),
                    intent_detected=interaction_data.get("intent_detected"),
                    sentiment_score=interaction_data.get("sentiment_score"),
                    processing_time_ms=interaction_data.get("processing_time_ms")
                )
            return None

        except Exception as e:
            logger.error("get_interaction_by_id_failed", interaction_id=interaction_id, error=str(e))
            raise

    async def get_interactions_by_session(self, session_id: str, limit: int = 50) -> List[Interaction]:
        """
        Get interactions for a session

        Args:
            session_id: Session ID
            limit: Maximum number of interactions to return

        Returns:
            List of interaction objects
        """
        try:
            logger.info("getting_interactions_by_session", session_id=session_id, limit=limit)

            response = self.supabase.table("interactions").select("*").eq("session_id", session_id).order("created_at", desc=True).limit(limit).execute()

            interactions = []
            if response.data:
                for interaction_data in response.data:
                    interaction = Interaction(
                        id=interaction_data["id"],
                        session_id=interaction_data["session_id"],
                        user_message=interaction_data["user_message"],
                        assistant_response=interaction_data["assistant_response"],
                        service=interaction_data["service"],
                        interaction_type=interaction_data["interaction_type"],
                        message_type=interaction_data["message_type"],
                        confidence_score=interaction_data["confidence_score"],
                        metadata=interaction_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(interaction_data["created_at"]),
                        updated_at=datetime.fromisoformat(interaction_data["updated_at"]),
                        phone_number=interaction_data.get("phone_number"),
                        language_detected=interaction_data.get("language_detected"),
                        intent_detected=interaction_data.get("intent_detected"),
                        sentiment_score=interaction_data.get("sentiment_score"),
                        processing_time_ms=interaction_data.get("processing_time_ms")
                    )
                    interactions.append(interaction)

            return interactions

        except Exception as e:
            logger.error("get_interactions_by_session_failed", session_id=session_id, error=str(e))
            raise

    async def get_interactions_by_user(self, user_id: str, limit: int = 50) -> List[Interaction]:
        """
        Get interactions for a user

        Args:
            user_id: User ID
            limit: Maximum number of interactions to return

        Returns:
            List of interaction objects
        """
        try:
            logger.info("getting_interactions_by_user", user_id=user_id, limit=limit)

            response = self.supabase.table("interactions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()

            interactions = []
            if response.data:
                for interaction_data in response.data:
                    interaction = Interaction(
                        id=interaction_data["id"],
                        session_id=interaction_data["session_id"],
                        user_message=interaction_data["user_message"],
                        assistant_response=interaction_data["assistant_response"],
                        service=interaction_data["service"],
                        interaction_type=interaction_data["interaction_type"],
                        message_type=interaction_data["message_type"],
                        confidence_score=interaction_data["confidence_score"],
                        metadata=interaction_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(interaction_data["created_at"]),
                        updated_at=datetime.fromisoformat(interaction_data["updated_at"]),
                        phone_number=interaction_data.get("phone_number"),
                        language_detected=interaction_data.get("language_detected"),
                        intent_detected=interaction_data.get("intent_detected"),
                        sentiment_score=interaction_data.get("sentiment_score"),
                        processing_time_ms=interaction_data.get("processing_time_ms")
                    )
                    interactions.append(interaction)

            return interactions

        except Exception as e:
            logger.error("get_interactions_by_user_failed", user_id=user_id, error=str(e))
            raise

    async def update_interaction(self, interaction_id: str, interaction_data: InteractionUpdate) -> Interaction:
        """
        Update interaction information

        Args:
            interaction_id: Interaction ID to update
            interaction_data: Update data

        Returns:
            Updated interaction object
        """
        try:
            logger.info("updating_interaction", interaction_id=interaction_id)

            # Build update dictionary with only provided fields
            update_dict = {}
            for field, value in interaction_data.dict(exclude_unset=True).items():
                if value is not None:
                    update_dict[field] = value

            if update_dict:
                update_dict["updated_at"] = datetime.now().isoformat()

                response = self.supabase.table("interactions").update(update_dict).eq("id", interaction_id).execute()

                if response.data:
                    updated_interaction = await self.get_interaction_by_id(interaction_id)
                    logger.info("interaction_updated_successfully", interaction_id=interaction_id)
                    return updated_interaction
                else:
                    raise Exception("Failed to update interaction")
            else:
                # No fields to update
                return await self.get_interaction_by_id(interaction_id)

        except Exception as e:
            logger.error("interaction_update_failed", interaction_id=interaction_id, error=str(e))
            raise

    async def get_interaction_with_details(self, interaction_id: str) -> Optional[InteractionWithDetails]:
        """
        Get interaction with additional details

        Args:
            interaction_id: Interaction ID to retrieve

        Returns:
            Interaction with details if found, None otherwise
        """
        try:
            logger.info("getting_interaction_with_details", interaction_id=interaction_id)

            # Get basic interaction info
            interaction = await self.get_interaction_by_id(interaction_id)
            if not interaction:
                return None

            # Get session info
            session = await self.session_service.get_session_by_id(interaction.session_id)

            # Get user info
            user = await self.user_service.get_user_by_id(session.user_id) if session else None

            # Determine if follow-up is required
            follow_up_required = (
                interaction.is_low_confidence or
                (interaction.sentiment_score is not None and interaction.sentiment_score < -0.5) or
                interaction.interaction_type.value == "error"
            )

            return InteractionWithDetails(
                **interaction.model_dump() if hasattr(interaction, 'model_dump') else interaction.dict(),
                user_name=user.name if user else None,
                session_status=session.status.value if session else None,
                follow_up_required=follow_up_required
            )

        except Exception as e:
            logger.error("get_interaction_with_details_failed", interaction_id=interaction_id, error=str(e))
            raise

    async def get_interaction_analytics(self, days: int = 30) -> InteractionAnalytics:
        """
        Get interaction analytics

        Args:
            days: Number of days to analyze

        Returns:
            Analytics data
        """
        try:
            logger.info("getting_interaction_analytics", days=days)

            # Calculate date range
            start_date = datetime.now() - timedelta(days=days)
            start_date_str = start_date.isoformat()

            # Get total interactions
            response = self.supabase.table("interactions").select("id").gte("created_at", start_date_str).execute()
            total_interactions = len(response.data) if response.data else 0

            # Get service distribution
            service_distribution = {}
            service_response = self.supabase.table("interactions").select("service").gte("created_at", start_date_str).execute()
            if service_response.data:
                for interaction in service_response.data:
                    service = interaction["service"]
                    service_distribution[service] = service_distribution.get(service, 0) + 1

            # Get confidence distribution
            confidence_distribution = {"low": 0, "medium": 0, "high": 0}
            confidence_response = self.supabase.table("interactions").select("confidence_score").gte("created_at", start_date_str).execute()
            if confidence_response.data:
                for interaction in confidence_response.data:
                    score = interaction["confidence_score"]
                    if score < 0.5:
                        confidence_distribution["low"] += 1
                    elif score < 0.8:
                        confidence_distribution["medium"] += 1
                    else:
                        confidence_distribution["high"] += 1

            # Get sentiment distribution
            sentiment_distribution = {"negative": 0, "neutral": 0, "positive": 0}
            sentiment_response = self.supabase.table("interactions").select("sentiment_score").gte("created_at", start_date_str).not_.is_("sentiment_score", "null").execute()
            if sentiment_response.data:
                for interaction in sentiment_response.data:
                    score = interaction["sentiment_score"]
                    if score < -0.2:
                        sentiment_distribution["negative"] += 1
                    elif score > 0.2:
                        sentiment_distribution["positive"] += 1
                    else:
                        sentiment_distribution["neutral"] += 1

            # Get average processing time
            processing_times = []
            time_response = self.supabase.table("interactions").select("processing_time_ms").gte("created_at", start_date_str).not_.is_("processing_time_ms", "null").execute()
            if time_response.data:
                for interaction in time_response.data:
                    if interaction.get("processing_time_ms"):
                        processing_times.append(interaction["processing_time_ms"])

            average_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

            # Get peak hours
            peak_hours = [0] * 24  # 24 hours
            hour_response = self.supabase.table("interactions").select("created_at").gte("created_at", start_date_str).execute()
            if hour_response.data:
                for interaction in hour_response.data:
                    hour = datetime.fromisoformat(interaction["created_at"]).hour
                    peak_hours[hour] += 1

            # Get top 3 peak hours
            top_hours = sorted(range(24), key=lambda x: peak_hours[x], reverse=True)[:3]

            # Get language distribution
            language_distribution = {}
            lang_response = self.supabase.table("interactions").select("language_detected").gte("created_at", start_date_str).not_.is_("language_detected", "null").execute()
            if lang_response.data:
                for interaction in lang_response.data:
                    lang = interaction["language_detected"]
                    language_distribution[lang] = language_distribution.get(lang, 0) + 1

            return InteractionAnalytics(
                total_interactions=total_interactions,
                service_distribution=service_distribution,
                confidence_distribution=confidence_distribution,
                sentiment_distribution=sentiment_distribution,
                average_processing_time=average_processing_time,
                peak_hours=top_hours,
                language_distribution=language_distribution
            )

        except Exception as e:
            logger.error("get_interaction_analytics_failed", days=days, error=str(e))
            raise

    async def list_interactions(self, limit: int = 50, offset: int = 0, service: Optional[str] = None) -> List[Interaction]:
        """
        List interactions with pagination

        Args:
            limit: Maximum number of interactions to return
            offset: Number of interactions to skip
            service: Filter by service

        Returns:
            List of interaction objects
        """
        try:
            logger.info("listing_interactions", limit=limit, offset=offset, service=service)

            query = self.supabase.table("interactions").select("*")

            if service:
                query = query.eq("service", service)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

            response = query.execute()

            interactions = []
            if response.data:
                for interaction_data in response.data:
                    interaction = Interaction(
                        id=interaction_data["id"],
                        session_id=interaction_data["session_id"],
                        user_message=interaction_data["user_message"],
                        assistant_response=interaction_data["assistant_response"],
                        service=interaction_data["service"],
                        interaction_type=interaction_data["interaction_type"],
                        message_type=interaction_data["message_type"],
                        confidence_score=interaction_data["confidence_score"],
                        metadata=interaction_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(interaction_data["created_at"]),
                        updated_at=datetime.fromisoformat(interaction_data["updated_at"]),
                        phone_number=interaction_data.get("phone_number"),
                        language_detected=interaction_data.get("language_detected"),
                        intent_detected=interaction_data.get("intent_detected"),
                        sentiment_score=interaction_data.get("sentiment_score"),
                        processing_time_ms=interaction_data.get("processing_time_ms")
                    )
                    interactions.append(interaction)

            return interactions

        except Exception as e:
            logger.error("list_interactions_failed", error=str(e))
            raise

    # Conversation Orchestration Methods
    async def process_incoming_message(
        self,
        phone_number: str,
        message: str,
        message_type: str = "text",
        message_id: Optional[str] = None,
        quoted_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process incoming message from WhatsApp

        Args:
            phone_number: Sender's phone number
            message: Message content
            message_type: Type of message (text, image, etc.)
            message_id: WhatsApp message ID
            quoted_message_id: ID of quoted message (if any)

        Returns:
            Processing result
        """
        try:
            logger.info(
                "processing_incoming_message",
                phone_number=phone_number,
                message_length=len(message),
                message_type=message_type
            )

            # Rate limiting check
            rate_limit_result = await self._check_rate_limit(phone_number)
            if not rate_limit_result.get('allowed', True):
                logger.warning("rate_limit_exceeded", phone_number=phone_number)
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "retry_after": rate_limit_result.get('reset_time', 0)
                }

            # Get or create user
            user = await self.user_service.get_or_create_user(phone_number)

            # Get or create session
            session = await self.session_service.create_or_get_session(user.id)

            # Check for admin commands first (before profile commands)
            from src.services.super_admin_service import SuperAdminService
            admin_service = SuperAdminService()

            # Initialize variables
            admin_command_processed = False

            if admin_service.is_super_admin(phone_number):
                try:
                    admin_result = await admin_service.parse_admin_command(message)
                    if admin_result.get('success'):
                        response_text = admin_result.get('response', admin_result.get('message', ''))
                        orchestration_result = {
                            'response': response_text,
                            'service_type': ServiceType.SUPER_ADMIN,
                            'processing_metadata': {
                                'admin_action': True,
                                'admin_command': message,
                                'execution_time': admin_result.get('execution_time', 0)
                            }
                        }
                        admin_command_processed = True
                    else:
                        # Admin command failed, continue with profile processing
                        error_msg = admin_result.get('response', admin_result.get('message', 'Command failed'))
                        logger.info("admin_command_failed", message=message, error=error_msg)
                except Exception as e:
                    logger.error("admin_command_processing_error", message=message, error=str(e))

            # Check for profile-based actions if admin command wasn't processed successfully
            profile_command = None
            action_result = None
            if not admin_command_processed:
                profile_command = await self.profile_service.parse_profile_command(message, phone_number)

                if profile_command and profile_command.get('action') == 'execute_action':
                    # Execute profile-based action
                    action_result = await self.profile_service.execute_action(
                        profile=profile_command['profile'],
                        action_id=profile_command['action_id'],
                        parameters=profile_command['parameters']
                    )

                    if action_result and action_result.get('success'):
                        response_text = action_result.get('response', '')
                        orchestration_result = {
                            'response': response_text,
                            'service_type': ServiceType.RENSEIGNEMENT,
                            'processing_metadata': {
                                'profile_action': True,
                                'action_id': profile_command['action_id'],
                                'execution_time': action_result.get('execution_time', 0)
                            }
                        }
                    else:
                        error_msg = action_result.get('error', 'Erreur inconnue') if action_result else 'Erreur inconnue'
                        response_text = f"❌ Erreur: {error_msg}"
                        orchestration_result = {
                            'response': response_text,
                            'service_type': ServiceType.CONTACT_HUMAIN,
                            'processing_metadata': {
                                'profile_action': True,
                                'action_id': profile_command['action_id'],
                                'error': error_msg
                            }
                        }

                elif profile_command and profile_command.get('action') == 'no_profile':
                    # No profile found, use normal Claude processing
                    response_text = "🔒 Profil non trouvé. Votre numéro n'est pas autorisé à exécuter des actions."
                    orchestration_result = {
                        'response': response_text,
                        'service_type': ServiceType.CONTACT_HUMAIN,
                        'processing_metadata': {
                            'profile_action': False,
                            'no_profile': True
                        }
                    }
                else:
                    # No profile command found, proceed to normal Claude processing
                    # Get conversation history and process with Claude AI
                    conversation_history = await self._get_conversation_history(session.id)

                    orchestration_result = await self.claude_service.orchestrate_conversation(
                    message=message,
                    session_context={"session_id": session.id, "user_id": user.id},
                    conversation_history=conversation_history,
                    phone_number=phone_number
                )

            # Initialize conversation_history for profile actions (not defined in that path)
            if 'conversation_history' not in locals():
                conversation_history = []

            # Check for emergency situations
            emergency_result = await self.claude_service.detect_emergency_situations(
                message=message,
                conversation_history=conversation_history
            )

            # Generate and format response
            response_text = self._extract_response_text(orchestration_result)
            formatted_response = self._format_response_with_gust_ia(response_text, orchestration_result)
            requires_human_followup = orchestration_result.get('processing_metadata', {}).get('requires_human_followup', False)

            # Send response via appropriate platform
            message_to_send = formatted_response if formatted_response else response_text
            if message_to_send and not emergency_result.get('requires_immediate_action', False):
                # Check if this is a Telegram message
                if phone_number.startswith('telegram_'):
                    # For Telegram messages, skip WhatsApp sending (handled by telegram API)
                    wa_response = {"id": "telegram_message_handled_elsewhere"}
                    logger.info("skipping_whatsapp_send_for_telegram", phone_number=phone_number)
                else:
                    # Send via WhatsApp for regular messages
                    wa_response = await self.whatsapp_service.send_text_message(
                        phone_number=phone_number,
                        message=message_to_send
                    )
            else:
                wa_response = {"id": "emergency_no_response"}

            # Create interaction record
            interaction_data = InteractionCreate(
                session_id=session.id,
                user_id=user.id,
                user_message=message,
                assistant_response=response_text,
                service=orchestration_result.get('service_response', {}).get('service', ServiceType.CONTACT_HUMAIN.value),
                interaction_type=InteractionType.MESSAGE,
                message_type=MessageType.TEXT,
                confidence_score=orchestration_result.get('processing_metadata', {}).get('confidence_score', 0.5),
                metadata={
                    "message_type": message_type,
                    "message_id": message_id,
                    "quoted_message_id": quoted_message_id,
                    "wa_response_id": wa_response.get('id'),
                    "orchestration_service": orchestration_result.get('service_response', {}).get('service', ServiceType.CONTACT_HUMAIN.value),
                    "orchestration_confidence": orchestration_result.get('processing_metadata', {}).get('confidence_score', 0.5),
                    "emergency_detected": emergency_result.get('is_emergency', False),
                    "requires_human_followup": requires_human_followup
                }
            )

            interaction = await self.create_interaction(interaction_data)

            # Update session
            await self._update_session_context(session, orchestration_result, requires_human_followup)

            # Cache conversation history
            await self._cache_conversation_history(session.id, conversation_history, message, response_text)

            # Queue for human followup if needed
            if requires_human_followup or emergency_result.get('requires_immediate_action', False):
                await self._queue_human_followup(interaction, emergency_result)

            return {
                "success": True,
                "interaction_id": interaction.id,
                "session_id": session.id,
                "user_id": user.id,
                "response": response_text,
                "response_sent": bool(response_text),
                "requires_human_followup": requires_human_followup,
                "emergency_detected": emergency_result.get('is_emergency', False),
                "service": str(orchestration_result.get('service_response', {}).get('service', ServiceType.CONTACT_HUMAIN))
            }

        except Exception as e:
            logger.error("incoming_message_processing_failed", phone_number=phone_number, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }

    async def handle_user_greeting(self, phone_number: str) -> Dict[str, Any]:
        """
        Handle user greeting (Bonjour, Salut, etc.)

        Args:
            phone_number: User's phone number

        Returns:
            Greeting response
        """
        try:
            logger.info("handling_user_greeting", phone_number=phone_number)

            # Get user and session
            user = await self.user_service.get_or_create_user(phone_number)
            session = await self.session_service.create_or_get_session(user.id)

            # Generate greeting response
            greeting_message = (
                f"Bonjour {user.name or 'cher ami'} ! 👋\n\n"
                f"Je suis votre assistant virtuel pour le Service Diocésain de la Catéchèse.\n\n"
                f"Comment puis-je vous aider aujourd'hui ?\n\n"
                f"Vous pouvez me demander :\n"
                f"• Des informations sur la catéchèse\n"
                f"• Des horaires et lieux des cours\n"
                f"• Les procédures d'inscription\n"
                f"• Du contenu sur la foi et la prière\n"
                f"• Ou parler à un agent humain"
            )

            # Send greeting
            wa_response = await self.whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=greeting_message
            )

            # Create interaction record
            interaction_data = InteractionCreate(
                session_id=session.id,
                user_id=user.id,
                user_message="USER_GREETING",
                assistant_response=greeting_message,
                service="GREETING",
                interaction_type=InteractionType.GREETING,
                message_type=MessageType.TEXT,
                confidence_score=0.9,
                metadata={
                    "greeting_type": "auto_response",
                    "wa_response_id": wa_response.get('id')
                }
            )

            interaction = await self.create_interaction(interaction_data)

            # Update session to reset to selection state
            session_update = SessionUpdate(
                current_service=None,
                context={}
            )
            await self.session_service.update_session(session.id, session_update)

            return {
                "success": True,
                "interaction_id": interaction.id,
                "session_id": session.id,
                "message_id": wa_response.get('id'),
                "greeting_sent": True
            }

        except Exception as e:
            logger.error("greeting_handling_failed", phone_number=phone_number, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }

    async def send_service_menu(self, phone_number: str) -> Dict[str, Any]:
        """
        Send interactive service menu to user

        Args:
            phone_number: User's phone number

        Returns:
            Menu sending result
        """
        try:
            logger.info("sending_service_menu", phone_number=phone_number)

            # Create menu buttons
            buttons = [
                {"id": "renseignement", "text": "ℹ️ Informations"},
                {"id": "catechese", "text": "📖 Catéchèse"},
                {"id": "contact", "text": "👋 Parler à un agent"}
            ]

            menu_message = (
                "Bienvenue au Service Diocésain de la Catéchèse !\n\n"
                "Veuillez choisir le service qui vous intéresse :"
            )

            # Send buttons
            # Note: New WhatsApp service doesn't support buttons yet, send as text
            wa_response = await self.whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=menu_message
            )

            # Get user and session
            user = await self.user_service.get_or_create_user(phone_number)
            session = await self.session_service.create_or_get_session(user.id)

            # Create interaction record
            interaction_data = InteractionCreate(
                session_id=session.id,
                user_id=user.id,
                user_message="SERVICE_MENU",
                assistant_response=menu_message,
                service="MENU",
                interaction_type=InteractionType.MENU,
                message_type=MessageType.TEXT,
                confidence_score=0.9,
                metadata={
                    "menu_type": "service_selection",
                    "buttons": buttons,
                    "wa_response_id": wa_response.get('id')
                }
            )

            interaction = await self.create_interaction(interaction_data)

            return {
                "success": True,
                "interaction_id": interaction.id,
                "session_id": session.id,
                "message_id": wa_response.get('id'),
                "menu_sent": True
            }

        except Exception as e:
            logger.error("menu_sending_failed", phone_number=phone_number, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session

        Args:
            session_id: Session ID
            limit: Maximum number of interactions to return

        Returns:
            List of interactions
        """
        try:
            # Try to get from cache first
            cached_history = await self.redis_service.get(f"conversation_history:{session_id}")
            if cached_history:
                return cached_history[-limit:]

            # Get from database
            interactions = await self.get_interactions_by_session(session_id, limit)

            # Format for conversation
            history = []
            for interaction in interactions:
                if interaction.user_message:
                    history.append({"role": "user", "content": interaction.user_message})
                if interaction.assistant_response:
                    history.append({"role": "assistant", "content": interaction.assistant_response})

            return history

        except Exception as e:
            logger.error("conversation_history_retrieval_failed", session_id=session_id, error=str(e))
            return []

    async def generate_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Generate summary for a session

        Args:
            session_id: Session ID

        Returns:
            Session summary
        """
        try:
            logger.info("generating_session_summary", session_id=session_id)

            # Get conversation history
            conversation_history = await self.get_conversation_history(session_id)

            if not conversation_history:
                return {
                    "session_id": session_id,
                    "summary": "No conversation history",
                    "message_count": 0,
                    "service_effectiveness": 0
                }

            # Get session info
            session = await self.session_service.get_session_by_id(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Generate AI summary
            summary = await self.claude_service.generate_conversation_summary(
                conversation_history=conversation_history,
                session_context={"session_id": session_id, "user_id": session.user_id}
            )

            # Get interaction statistics
            stats = await self._get_session_statistics(session_id)

            return {
                "session_id": session_id,
                "user_id": session.user_id,
                "summary": summary.get("summary", ""),
                "key_points": summary.get("key_points", []),
                "action_items": summary.get("action_items", []),
                "sentiment": summary.get("sentiment", "neutral"),
                "engagement_level": summary.get("engagement_level", "medium"),
                "service_effectiveness": summary.get("service_effectiveness", 3),
                "recommended_next_steps": summary.get("recommended_next_steps", []),
                "message_count": stats.get("total_interactions", 0),
                "duration_minutes": stats.get("duration_minutes", 0),
                "services_used": stats.get("services_used", []),
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error("session_summary_generation_failed", session_id=session_id, error=str(e))
            return {
                "session_id": session_id,
                "summary": f"Error generating summary: {str(e)}",
                "error": str(e)
            }

    async def close_session(self, session_id: str, reason: str = "user_requested") -> Dict[str, Any]:
        """
        Close a session with summary

        Args:
            session_id: Session ID
            reason: Reason for closing

        Returns:
            Session closing result
        """
        try:
            logger.info("closing_session", session_id=session_id, reason=reason)

            # Generate summary before closing
            summary = await self.generate_session_summary(session_id)

            # Close session in database
            await self.session_service.close_session(session_id)

            # Clear cache
            await self.redis_service.delete_session(session_id)
            await self.redis_service.delete(f"conversation_history:{session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "reason": reason,
                "summary": summary
            }

        except Exception as e:
            logger.error("session_closing_failed", session_id=session_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }

    # Helper methods
    async def _check_rate_limit(self, phone_number: str) -> Dict[str, Any]:
        """Check rate limit for user"""
        return await self.redis_service.check_rate_limit(
            key=f"rate_limit:{phone_number}",
            limit=self.settings.rate_limit_per_minute,
            window=60
        )

    async def _get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history from cache or database"""
        cached = await self.redis_service.get(f"conversation_history:{session_id}")
        return cached if cached else []

    def _extract_response_text(self, orchestration_result: Dict[str, Any]) -> str:
        """Extract response text from orchestration result"""
        try:
            content = orchestration_result.get('service_response', {}).get('response', {}).get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                return content[0].get('text', '')
            return ""
        except Exception:
            return ""

    def _format_response_with_gust_ia(self, response_text: str, orchestration_result: Dict[str, Any]) -> str:
        """Format response with Gust-IA prefix and service indicator"""
        try:
            # Get service type
            service_type_str = orchestration_result.get('service_response', {}).get('service', ServiceType.CONTACT_HUMAIN)

            # Convert string to ServiceType enum
            service_type = ServiceType.CONTACT_HUMAIN
            for st in ServiceType:
                if st.value == service_type_str:
                    service_type = st
                    break

            # Check if this is an admin response
            is_admin = service_type == ServiceType.SUPER_ADMIN

            # Get admin result for special formatting
            admin_result = orchestration_result.get('service_response', {}).get('response', {}).get('admin_result', {})

            # Special formatting for different admin response types
            if admin_result.get('is_help'):
                return self.response_formatter.format_admin_help(response_text)
            elif 'categories' in admin_result:
                return self.response_formatter.format_categories_list(
                    admin_result.get('categories', []),
                    admin_result.get('suggestions', [])
                )
            elif 'admins' in admin_result:
                return self.response_formatter.format_admin_list(
                    admin_result.get('admins', []),
                    admin_result.get('suggestions', [])
                )
            elif 'suggestions' in admin_result:
                # Enhanced formatting for list responses with suggestions
                categories = admin_result.get('categories', [])
                return self.response_formatter.format_renseignement_list(
                    [],  # Will be replaced with actual data
                    categories,
                    admin_result.get('suggestions', [])
                )

            # Format response with Gust-IA prefix
            return self.response_formatter.format_response(response_text, service_type, is_admin)

        except Exception as e:
            logger.error("response_formatting_failed", error=str(e))
            # Fallback to simple formatting
            return f"[Gust-IA]\n----------------------------¬\n{response_text}"

    async def _update_session_context(self, session: Session, orchestration_result: Dict[str, Any], requires_followup: bool):
        """Update session context after interaction"""
        service_type = orchestration_result.get('service_response', {}).get('service', ServiceType.CONTACT_HUMAIN.value)
        if isinstance(service_type, str):
            service_type = service_type
        else:
            service_type = service_type.value
        session_update = SessionUpdate(
            current_service=str(service_type) if service_type else None,
            context={
                **(session.context or {}),
                "last_service": str(service_type) if service_type else None,
                "requires_human_followup": requires_followup
            }
        )
        await self.session_service.update_session(session.id, session_update)

    async def _cache_conversation_history(self, session_id: str, history: List[Dict[str, str]], user_message: str, assistant_response: str):
        """Cache updated conversation history"""
        updated_history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ]
        await self.redis_service.set(
            f"conversation_history:{session_id}",
            updated_history[-20:],  # Keep last 20 messages
            expire=3600  # 1 hour
        )

    async def _queue_human_followup(self, interaction: Interaction, emergency_result: Dict[str, Any]):
        """Queue interaction for human followup"""
        followup_data = {
            "interaction_id": interaction.id,
            "session_id": interaction.session_id,
            "user_id": interaction.user_id,
            "priority": "high" if emergency_result.get('is_emergency', False) else "normal",
            "reason": "emergency" if emergency_result.get('is_emergency', False) else "user_request",
            "timestamp": datetime.now().isoformat(),
            "content": interaction.user_message
        }
        await self.redis_service.enqueue_message(
            "human_followup_queue",
            followup_data,
            priority=10 if emergency_result.get('is_emergency', False) else 1
        )

    async def _get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            # Get all interactions for session
            interactions = await self.get_interactions_by_session(session_id, limit=1000)

            if not interactions:
                return {
                    "total_interactions": 0,
                    "duration_minutes": 0,
                    "services_used": []
                }

            # Calculate duration
            start_time = interactions[-1].created_at
            end_time = interactions[0].created_at
            duration = (end_time - start_time).total_seconds() / 60  # Convert to minutes

            # Get services used
            services_used = list(set(interaction.service for interaction in interactions if interaction.service))

            return {
                "total_interactions": len(interactions),
                "duration_minutes": round(duration, 2),
                "services_used": services_used
            }
        except Exception as e:
            logger.error("session_statistics_failed", session_id=session_id, error=str(e))
            return {
                "total_interactions": 0,
                "duration_minutes": 0,
                "services_used": []
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        try:
            health_status = {
                "interaction_service": "healthy",
                "services": {},
                "timestamp": datetime.now().isoformat()
            }

            # Check individual services
            services = [
                ("redis", self.redis_service.ping()),
                ("whatsapp", self.whatsapp_service.is_connected()),
                ("claude", self.claude_service.health_check())
            ]

            for service_name, health_check in services:
                try:
                    if service_name == "claude":
                        result = await health_check
                        health_status["services"][service_name] = "healthy" if result.get("healthy") else "unhealthy"
                    else:
                        is_healthy = await health_check
                        health_status["services"][service_name] = "healthy" if is_healthy else "unhealthy"
                except Exception as e:
                    logger.error(f"{service_name}_health_check_failed", error=str(e))
                    health_status["services"][service_name] = "unhealthy"

            return health_status

        except Exception as e:
            logger.error("interaction_service_health_check_failed", error=str(e))
            return {
                "interaction_service": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def close(self):
        """Close all service connections"""
        # New WhatsApp service doesn't require explicit closing
        pass
        await self.claude_service.close()
        logger.info("interaction_service_closed")