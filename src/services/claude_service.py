"""
Claude AI orchestration service for conversation management and AI processing
"""

import json
import httpx
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
from enum import Enum
from src.utils.config import get_settings
from src.models.session import SessionStatus
from src.utils.api_key_manager import APIKeyManager, ProviderConfig, AIProviderRegistry
import structlog

logger = structlog.get_logger()


class ServiceType(Enum):
    """Service types for AI orchestration"""
    RENSEIGNEMENT = "RENSEIGNEMENT"
    CATECHESE = "CATECHESE"
    CONTACT_HUMAIN = "CONTACT_HUMAIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class ClaudeService:
    """Service for AI API integration and orchestration with multiple providers"""

    def __init__(self):
        self.settings = get_settings()
        self.provider_registry = AIProviderRegistry()
        self.http_clients = {}

        # Initialize providers
        self._initialize_providers()

        # Log configuration for debugging
        active_providers = self.provider_registry.get_active_providers()
        logger.info(
            "ai_service_initialized",
            default_provider=self.settings.ai_provider,
            active_providers=active_providers,
            total_providers=len(active_providers)
        )

    def _initialize_providers(self):
        """Initialize all configured AI providers"""

        # Anthropic/Claude Provider
        if self.settings.enable_anthropic:
            anthropic_config = ProviderConfig(
                provider_type="anthropic",
                base_url=self.settings.anthropic_base_url,
                model=self.settings.claude_model,
                max_tokens=self.settings.claude_max_tokens,
                temperature=self.settings.claude_temperature
            )

            # Create key manager with single key for Anthropic
            if self.settings.anthropic_auth_token and self.settings.anthropic_auth_token != "test-key":
                key_manager = APIKeyManager([self.settings.anthropic_auth_token], "anthropic")
                anthropic_config.set_key_manager(key_manager)

                # Create HTTP client for Anthropic
                self.http_clients["anthropic"] = httpx.AsyncClient(
                    timeout=60.0,
                    headers={
                        'Content-Type': 'application/json',
                        'anthropic-version': '2023-06-01'
                    }
                )

            is_default = self.settings.ai_provider == "anthropic"
            self.provider_registry.register_provider("anthropic", anthropic_config, is_default)

        # Gemini Provider
        if self.settings.enable_gemini:
            gemini_config = ProviderConfig(
                provider_type="gemini",
                base_url=self.settings.gemini_base_url,
                model=self.settings.gemini_model,
                max_tokens=self.settings.gemini_max_tokens,
                temperature=self.settings.gemini_temperature
            )

            # Create key manager with round-robin for Gemini
            if self.settings.gemini_api_keys:
                key_manager = APIKeyManager(self.settings.gemini_api_keys, "gemini")
                gemini_config.set_key_manager(key_manager)

                # Create HTTP client for Gemini
                self.http_clients["gemini"] = httpx.AsyncClient(
                    timeout=60.0,
                    headers={'Content-Type': 'application/json'}
                )

            is_default = self.settings.ai_provider == "gemini"
            self.provider_registry.register_provider("gemini", gemini_config, is_default)

        # OpenRouter Provider
        if self.settings.enable_openrouter:
            openrouter_config = ProviderConfig(
                provider_type="openrouter",
                base_url=self.settings.openrouter_base_url,
                model=self.settings.openrouter_model,
                max_tokens=self.settings.openrouter_max_tokens,
                temperature=self.settings.openrouter_temperature
            )

            # Create key manager with round-robin for OpenRouter
            if self.settings.openrouter_api_keys:
                key_manager = APIKeyManager(self.settings.openrouter_api_keys, "openrouter")
                openrouter_config.set_key_manager(key_manager)

                # Create HTTP client for OpenRouter
                self.http_clients["openrouter"] = httpx.AsyncClient(
                    timeout=60.0,
                    headers={
                        'Content-Type': 'application/json',
                        'HTTP-Referer': 'https://cate.sdb-dkr.ovh',
                        'X-Title': 'SDB Catechism AI Concierge'
                    }
                )

            is_default = self.settings.ai_provider == "openrouter"
            self.provider_registry.register_provider("openrouter", openrouter_config, is_default)

    def get_active_provider(self, provider_name: Optional[str] = None) -> Optional[ProviderConfig]:
        """Get an active provider, fallback to default if specified provider is unavailable"""
        provider = self.provider_registry.get_provider(provider_name)

        if provider and provider.is_configured():
            return provider

        # Fallback to default provider
        default_provider = self.provider_registry.get_provider()
        if default_provider and default_provider.is_configured():
            logger.warning(f"{provider_name}_provider_fallback",
                          requested=provider_name,
                          fallback=default_provider.provider_type)
            return default_provider

        logger.error("no_active_providers_available")
        return None

    async def _make_api_request(self, provider: ProviderConfig, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to the specified provider with round-robin key management"""

        # Get next API key using round-robin
        api_key = provider.key_manager.get_next_key()
        if not api_key:
            raise ValueError(f"No API keys available for {provider.provider_type}")

        # Set authorization header based on provider type
        headers = {}
        client = self.http_clients.get(provider.provider_type)

        if not client:
            raise ValueError(f"No HTTP client available for {provider.provider_type}")

        if provider.provider_type == "anthropic":
            headers['Authorization'] = f'Bearer {api_key}'
            endpoint = f"{provider.base_url}/v1/messages"
        elif provider.provider_type == "gemini":
            endpoint = f"{provider.base_url}/v1beta/models/{provider.model}:generateContent?key={api_key}"
        elif provider.provider_type == "openrouter":
            headers['Authorization'] = f'Bearer {api_key}'
            endpoint = f"{provider.base_url}/chat/completions"
        else:
            raise ValueError(f"Unsupported provider type: {provider.provider_type}")

        # Log request (without sensitive data)
        logger.info(f"{provider.provider_type}_api_request",
                   model=provider.model,
                   endpoint=endpoint.split('?')[0])  # Remove API key from log

        try:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload
            )

            logger.info(f"{provider.provider_type}_api_response",
                       status_code=response.status_code)

            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if provider.provider_type == "gemini":
                return self._format_gemini_response(result)
            elif provider.provider_type == "openrouter":
                return self._format_openrouter_response(result)
            else:
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"{provider.provider_type}_api_error",
                        status_code=e.response.status_code,
                        error=str(e))
            raise
        except Exception as e:
            logger.error(f"{provider.provider_type}_request_failed",
                        error=str(e))
            raise

    def _format_gemini_response(self, gemini_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format Gemini response to standard format"""
        try:
            content = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': content
                    }
                ]
            }
        except (IndexError, KeyError) as e:
            logger.error("gemini_response_format_failed", error=str(e))
            return {'content': []}

    def _format_openrouter_response(self, openrouter_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format OpenRouter response to standard format"""
        try:
            content = openrouter_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': content
                    }
                ]
            }
        except (IndexError, KeyError) as e:
            logger.error("openrouter_response_format_failed", error=str(e))
            return {'content': []}

    async def send_message(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send message to AI provider

        Args:
            message: User message
            conversation_history: Previous conversation messages
            system_prompt: Optional system prompt
            tools: Optional tools for function calling
            max_tokens: Maximum tokens for response
            provider_name: Specific provider to use (optional)

        Returns:
            AI API response
        """
        try:
            # Get active provider
            provider = self.get_active_provider(provider_name)
            if not provider:
                raise ValueError("No active AI providers available")

            logger.info("ai_message_sending",
                       provider=provider.provider_type,
                       model=provider.model,
                       message_length=len(message))

            # Build payload based on provider type
            if provider.provider_type == "gemini":
                payload = self._build_gemini_payload(message, conversation_history, system_prompt)
            elif provider.provider_type == "openrouter":
                payload = self._build_openrouter_payload(message, conversation_history, system_prompt)
            else:
                payload = self._build_anthropic_payload(message, conversation_history, system_prompt, tools, max_tokens)

            # Override provider defaults if specified
            if max_tokens:
                payload["max_tokens"] = max_tokens

            # Remove max_tokens from root level if generationConfig is present (Gemini requirement)
            if provider.provider_type == "gemini" and "max_tokens" in payload and "generationConfig" in payload:
                del payload["max_tokens"]

            # Log payload for debugging (especially for Gemini 400 errors)
            if provider.provider_type == "gemini":
                logger.info("gemini_payload_debug",
                           payload=payload,
                           system_prompt_present=system_prompt is not None)

            # Make API request
            result = await self._make_api_request(provider, payload)

            # Log response type and structure for debugging
            logger.info(f"{provider.provider_type}_api_response_type",
                       response_type=type(result).__name__,
                       is_list=isinstance(result, list),
                       is_dict=isinstance(result, dict),
                       sample=str(result)[:200] if result else "empty")

            # Handle case where API returns a list instead of dict
            if isinstance(result, list):
                logger.warning(f"{provider.provider_type}_api_returned_list", list_length=len(result))
                if len(result) > 0:
                    result = result[0]
                else:
                    logger.error(f"{provider.provider_type}_api_empty_list",
                               response_text=str(result)[:500])
                    raise ValueError("API returned empty list")

            logger.info(f"{provider.provider_type}_message_received",
                       response_id=result.get('id', 'unknown'))
            return result

        except Exception as e:
            logger.error("ai_message_failed", error=str(e), provider=provider_name)
            raise

    def _build_anthropic_payload(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None,
                                system_prompt: Optional[str] = None, tools: Optional[List[Dict[str, Any]]] = None,
                                max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Build payload for Anthropic API"""
        messages = []
        if conversation_history:
            messages.extend(conversation_history)

        messages.append({
            "role": "user",
            "content": message
        })

        provider = self.get_active_provider("anthropic")
        payload = {
            "model": provider.model,
            "max_tokens": max_tokens or provider.max_tokens,
            "temperature": provider.temperature,
            "messages": messages
        }

        if system_prompt:
            payload["system"] = system_prompt

        if tools:
            payload["tools"] = tools

        return payload

    def _build_gemini_payload(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None,
                             system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Build payload for Gemini API"""
        provider = self.get_active_provider("gemini")

        # Build contents array for Gemini
        contents = []

        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })

        # Add current user message
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": provider.max_tokens,
                "temperature": provider.temperature
            }
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        return payload

    def _build_openrouter_payload(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None,
                                system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Build payload for OpenRouter API"""
        provider = self.get_active_provider("openrouter")

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({
            "role": "user",
            "content": message
        })

        payload = {
            "model": provider.model,
            "max_tokens": provider.max_tokens,
            "temperature": provider.temperature,
            "messages": messages
        }

        return payload

    async def classify_user_intent(
        self,
        message: str,
        phone_number: str = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Classify user intent and determine appropriate service

        Args:
            message: User message
            conversation_history: Previous conversation messages

        Returns:
            Intent classification result
        """
        try:
            # Check if user is Super Admin
            from src.services.super_admin_service import SuperAdminService
            super_admin_service = SuperAdminService()

            if phone_number and super_admin_service.is_super_admin(phone_number):
                return {
                    "intent": ServiceType.SUPER_ADMIN.value,
                    "confidence": 1.0,
                    "reasoning": "Super Admin user detected",
                    "extracted_entities": {"admin_user": True}
                }

            system_prompt = """You are an intelligent conversation classifier for a WhatsApp AI concierge service.

Your task is to analyze user messages and classify them into one of the following categories:

1. RENSEIGNEMENT - Information requests about catechism, schedules, locations, fees, etc.
2. CATECHESE - Specific requests about catechism content, lessons, prayers, bible verses, etc.
3. CONTACT_HUMAIN - Requests to speak with a human, complaints, complex issues, or emotional support.

Respond with a JSON object containing:
{
  "intent": "RENSEIGNEMENT|CATECHESE|CONTACT_HUMAIN",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of classification",
  "extracted_entities": {
    "location": null,
    "time": null,
    "name": null,
    "contact_info": null
  }
}

Be precise and thoughtful in your classification. Consider the context and previous messages."""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=500
            )

            # Extract the classification from the response
            content = response.get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                text_content = content[0].get('text', '')
                try:
                    classification = json.loads(text_content)
                    logger.info("intent_classified", intent=classification.get('intent'), confidence=classification.get('confidence'))
                    return classification
                except json.JSONDecodeError:
                    # Fallback to simple parsing
                    return {
                        "intent": "CONTACT_HUMAIN",  # Default to human contact on error
                        "confidence": 0.5,
                        "reasoning": "Failed to parse AI response, defaulting to human contact",
                        "extracted_entities": {}
                    }

            return {
                "intent": "CONTACT_HUMAIN",
                "confidence": 0.5,
                "reasoning": "No valid response from AI",
                "extracted_entities": {}
            }

        except Exception as e:
            logger.error("intent_classification_failed", error=str(e))
            return {
                "intent": "CONTACT_HUMAIN",
                "confidence": 0.3,
                "reasoning": f"Error during classification: {str(e)}",
                "extracted_entities": {}
            }

    async def generate_renseignement_response(
        self,
        message: str,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response for information requests (RENSEIGNEMENT service)

        Args:
            message: User message
            user_context: User context information
            conversation_history: Previous conversation messages

        Returns:
            Response with service information
        """
        try:
            system_prompt = """You are Gust-IA, a helpful assistant for the Service Diocésain de la Catéchèse (SDB).

Your role is to provide information about:
- Catechism schedules and locations
- Registration procedures and requirements
- Fees and payment methods
- Contact information for different parishes
- General information about the catechism program

Key information to remember:
- Catechism classes are held on weekends
- Main locations: Parishes throughout the diocese
- Registration requires baptism certificate
- Fees are moderate with payment plans available
- Age groups: Children (6-12), Teens (13-17), Adults (18+)

IMPORTANT: Be very concise and direct. Keep responses short and to the point. If you don't have specific information, guide users to contact the appropriate person briefly."""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=self.max_tokens
            )

            return {
                "service": ServiceType.RENSEIGNEMENT.value,
                "response": response,
                "confidence": 0.8,
                "requires_human_followup": False
            }

        except Exception as e:
            logger.error("renseignement_response_failed", error=str(e))
            raise

    async def generate_catechese_response(
        self,
        message: str,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response for catechism content requests (CATECHESE service)

        Args:
            message: User message
            user_context: User context information
            conversation_history: Previous conversation messages

        Returns:
            Response with catechism content
        """
        try:
            system_prompt = """You are Gust-IA, a knowledgeable catechism teacher assistant.

Your role is to help with:
- Bible verses and their explanations
- Catholic prayers and traditions
- Sacrament information and preparation
- Religious education concepts
- Moral and ethical teachings
- Liturgical calendar information

Guidelines:
- Provide accurate, faith-based information
- Include relevant Bible references when appropriate
- Explain concepts in clear, accessible language
- Be respectful of different learning levels
- Encourage deeper understanding of faith
- Suggest prayers or reflections when relevant

IMPORTANT: Keep responses very concise and to the point. Be pastoral but brief."""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=self.max_tokens
            )

            return {
                "service": ServiceType.CATECHESE.value,
                "response": response,
                "confidence": 0.8,
                "requires_human_followup": False
            }

        except Exception as e:
            logger.error("catechese_response_failed", error=str(e))
            raise

    async def generate_super_admin_response(
        self,
        message: str,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response for Super Admin commands

        Args:
            message: User message
            user_context: User context information
            conversation_history: Previous conversation messages

        Returns:
            Response with Super Admin command results
        """
        try:
            from src.services.super_admin_service import SuperAdminService
            super_admin_service = SuperAdminService()

            # Parse and execute admin command
            command_result = await super_admin_service.parse_admin_command(message)

            return {
                "service": ServiceType.SUPER_ADMIN.value,
                "response": {
                    "content": [{"text": command_result.get("message", "Commande exécutée")}],
                    "admin_result": command_result
                },
                "confidence": 1.0,
                "requires_human_followup": False
            }

        except Exception as e:
            logger.error("super_admin_response_failed", error=str(e))
            return {
                "service": ServiceType.SUPER_ADMIN.value,
                "response": {
                    "content": [{"text": f"Erreur lors de l'exécution de la commande: {str(e)}"}],
                    "admin_result": {"success": False, "message": str(e)}
                },
                "confidence": 0.5,
                "requires_human_followup": False
            }

    async def generate_contact_humain_response(
        self,
        message: str,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response for human contact requests (CONTACT_HUMAIN service)

        Args:
            message: User message
            user_context: User context information
            conversation_history: Previous conversation messages

        Returns:
            Response with human contact information
        """
        try:
            system_prompt = """You are Gust-IA, a compassionate customer service representative for the Service Diocésain de la Catéchèse.

Your role is to:
- Acknowledge the user's need for human assistance
- Show empathy and understanding
- Provide appropriate contact information
- Set expectations for response time
- Escalate urgent issues appropriately

Contact information to provide:
- Main office: [Phone number to be added]
- Email: [Email to be added]
- Emergency contact: [Emergency contact if applicable]

IMPORTANT: Keep responses very brief and to the point while being warm and reassuring."""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=self.max_tokens
            )

            return {
                "service": ServiceType.CONTACT_HUMAIN.value,
                "response": response,
                "confidence": 0.9,
                "requires_human_followup": True
            }

        except Exception as e:
            logger.error("contact_humain_response_failed", error=str(e))
            raise

    async def orchestrate_conversation(
        self,
        message: str,
        session_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        phone_number: str = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method for handling user conversations

        Args:
            message: User message
            session_context: Current session context
            conversation_history: Previous conversation messages

        Returns:
            Orchestrated response
        """
        try:
            logger.info("conversation_orchestration_started", message_length=len(message))

            # Step 1: Classify user intent
            intent_result = await self.classify_user_intent(
                message=message,
                phone_number=phone_number,
                conversation_history=conversation_history
            )

            intent_type = intent_result.get('intent', 'CONTACT_HUMAIN')
            confidence = intent_result.get('confidence', 0.5)
            extracted_entities = intent_result.get('extracted_entities', {})

            # Step 2: Generate appropriate response based on intent
            if intent_type == ServiceType.SUPER_ADMIN.value:
                response_result = await self.generate_super_admin_response(
                    message=message,
                    user_context=extracted_entities,
                    conversation_history=conversation_history
                )
            elif intent_type == ServiceType.RENSEIGNEMENT.value:
                response_result = await self.generate_renseignement_response(
                    message=message,
                    user_context=extracted_entities,
                    conversation_history=conversation_history
                )
            elif intent_type == ServiceType.CATECHESE.value:
                response_result = await self.generate_catechese_response(
                    message=message,
                    user_context=extracted_entities,
                    conversation_history=conversation_history
                )
            else:  # CONTACT_HUMAIN
                response_result = await self.generate_contact_humain_response(
                    message=message,
                    user_context=extracted_entities,
                    conversation_history=conversation_history
                )

            # Step 3: Combine results
            orchestration_result = {
                "user_message": message,
                "intent_classification": intent_result,
                "service_response": response_result,
                "session_context": session_context or {},
                "timestamp": datetime.now().isoformat(),
                "conversation_id": session_context.get('conversation_id') if session_context else None,
                "processing_metadata": {
                    "model_used": self.model,
                    "confidence_score": min(confidence, response_result.get('confidence', 0.5)),
                    "requires_human_followup": response_result.get('requires_human_followup', False),
                    "extracted_entities": extracted_entities
                }
            }

            logger.info("conversation_orchestrated", service=response_result.get('service'), confidence=orchestration_result['processing_metadata']['confidence_score'])
            return orchestration_result

        except Exception as e:
            logger.error("conversation_orchestration_failed", error=str(e))
            # Fallback response
            return {
                "user_message": message,
                "intent_classification": {
                    "intent": "CONTACT_HUMAIN",
                    "confidence": 0.3,
                    "reasoning": f"Error during orchestration: {str(e)}",
                    "extracted_entities": {}
                },
                "service_response": {
                    "service": ServiceType.CONTACT_HUMAIN.value,
                    "response": {"content": [{"text": "Je suis désolé, j'ai rencontré une erreur. Un agent humain vous contactera bientôt."}]},
                    "confidence": 0.3,
                    "requires_human_followup": True
                },
                "session_context": session_context or {},
                "timestamp": datetime.now().isoformat(),
                "processing_metadata": {
                    "model_used": self.model,
                    "confidence_score": 0.3,
                    "requires_human_followup": True,
                    "extracted_entities": {},
                    "error": str(e)
                }
            }

    async def generate_conversation_summary(
        self,
        conversation_history: List[Dict[str, str]],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a summary of the conversation

        Args:
            conversation_history: List of conversation messages
            session_context: Session context information

        Returns:
            Conversation summary
        """
        try:
            system_prompt = """You are a conversation summarization assistant.

Analyze the following conversation and provide:
1. A concise summary of what was discussed
2. Key points or decisions made
3. Any action items or follow-ups needed
4. User sentiment/engagement level
5. Service effectiveness rating

Respond with a JSON object containing:
{
  "summary": "Brief conversation overview",
  "key_points": ["point1", "point2"],
  "action_items": ["item1", "item2"],
  "sentiment": "positive|neutral|negative",
  "engagement_level": "high|medium|low",
  "service_effectiveness": 1-5,
  "recommended_next_steps": ["step1", "step2"]
}"""

            # Format conversation for summarization
            conversation_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in conversation_history[-10:]  # Last 10 messages
            ])

            response = await self.send_message(
                message=f"Please summarize this conversation:\n\n{conversation_text}",
                system_prompt=system_prompt,
                max_tokens=800
            )

            # Extract summary from response
            content = response.get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                text_content = content[0].get('text', '')
                try:
                    summary = json.loads(text_content)
                    logger.info("conversation_summary_generated")
                    return summary
                except json.JSONDecodeError:
                    # Fallback
                    return {
                        "summary": text_content,
                        "key_points": [],
                        "action_items": [],
                        "sentiment": "neutral",
                        "engagement_level": "medium",
                        "service_effectiveness": 3,
                        "recommended_next_steps": []
                    }

            return {
                "summary": "Unable to generate summary",
                "key_points": [],
                "action_items": [],
                "sentiment": "neutral",
                "engagement_level": "medium",
                "service_effectiveness": 3,
                "recommended_next_steps": []
            }

        except Exception as e:
            logger.error("conversation_summary_failed", error=str(e))
            return {
                "summary": f"Error generating summary: {str(e)}",
                "key_points": [],
                "action_items": [],
                "sentiment": "neutral",
                "engagement_level": "medium",
                "service_effectiveness": 3,
                "recommended_next_steps": []
            }

    async def detect_emergency_situations(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Detect emergency or urgent situations in user messages

        Args:
            message: User message
            conversation_history: Previous conversation messages

        Returns:
            Emergency detection result
        """
        try:
            system_prompt = """You are an emergency detection assistant for a WhatsApp concierge service.

Analyze the user's message for any signs of:
- Medical emergencies
- Safety concerns
- Urgent pastoral care needs
- Crisis situations
- Immediate emotional distress

Respond with a JSON object:
{
  "is_emergency": true/false,
  "emergency_type": "medical|safety|pastoral|emotional|none",
  "urgency_level": "low|medium|high|critical",
  "requires_immediate_action": true/false,
  "recommended_action": "description of what should be done"
}

Be conservative in your assessment - when in doubt, flag for human review."""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=300
            )

            # Extract emergency assessment from response
            content = response.get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                text_content = content[0].get('text', '')
                try:
                    emergency_result = json.loads(text_content)
                    if emergency_result.get('is_emergency'):
                        logger.warning("emergency_detected", type=emergency_result.get('emergency_type'), urgency=emergency_result.get('urgency_level'))
                    return emergency_result
                except json.JSONDecodeError:
                    pass

            return {
                "is_emergency": False,
                "emergency_type": "none",
                "urgency_level": "low",
                "requires_immediate_action": False,
                "recommended_action": "No action needed"
            }

        except Exception as e:
            logger.error("emergency_detection_failed", error=str(e))
            return {
                "is_emergency": False,
                "emergency_type": "none",
                "urgency_level": "low",
                "requires_immediate_action": False,
                "recommended_action": f"Error in detection: {str(e)}"
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current Claude model

        Returns:
            Model information
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Claude service

        Returns:
            Health status
        """
        try:
            # Simple test message
            test_response = await self.send_message(
                message="Hello, this is a health check. Please respond with 'OK'.",
                max_tokens=10
            )

            is_healthy = test_response.get('content') and len(test_response.get('content', [])) > 0

            return {
                "healthy": is_healthy,
                "model": self.model,
                "response_time": test_response.get('usage', {}).get('input_tokens', 0),
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error("claude_health_check_failed", error=str(e))
            return {
                "healthy": False,
                "model": self.model,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
        logger.info("claude_service_closed")