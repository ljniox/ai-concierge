"""
Claude AI orchestration service for conversation management and AI processing
"""

import json
import httpx
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
from src.utils.config import get_settings
from src.models.session import SessionStatus
import structlog

logger = structlog.get_logger()


class ServiceType(Enum):
    """Service types for AI orchestration"""
    RENSEIGNEMENT = "renseignement"
    CATECHESE = "catechese"
    CONTACT_HUMAIN = "contact_humain"


class ClaudeService:
    """Service for Claude AI API integration and orchestration"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.anthropic_api_key
        self.base_url = self.settings.anthropic_base_url
        self.model = self.settings.claude_model or "claude-3-sonnet-20240229"
        self.max_tokens = self.settings.claude_max_tokens or 1000
        self.temperature = self.settings.claude_temperature or 0.7
        
        # Log configuration for debugging (without exposing sensitive data)
        api_key_status = "SET" if self.api_key and self.api_key != "test-key" else "NOT_SET"
        logger.info(
            "claude_service_initialized",
            base_url=self.base_url,
            model=self.model,
            api_key_status=api_key_status
        )
        
        self.http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01'
            }
        )

    async def send_message(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send message to Claude AI

        Args:
            message: User message
            conversation_history: Previous conversation messages
            system_prompt: Optional system prompt
            tools: Optional tools for function calling
            max_tokens: Maximum tokens for response

        Returns:
            Claude API response
        """
        try:
            url = f"{self.base_url}/v1/messages"

            # Build messages array
            messages = []
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })

            payload = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }

            if system_prompt:
                payload["system"] = system_prompt

            if tools:
                payload["tools"] = tools

            logger.info("claude_message_sent", message_length=len(message), model=self.model)

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            logger.info("claude_message_received", response_id=result.get('id'))
            return result

        except httpx.HTTPStatusError as e:
            logger.error("claude_http_error", status_code=e.response.status_code, error=str(e))
            raise
        except Exception as e:
            logger.error("claude_message_failed", error=str(e))
            raise

    async def classify_user_intent(
        self,
        message: str,
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
            system_prompt = """You are a helpful assistant for the Service Diocésain de la Catéchèse (SDB).

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

Be helpful, informative, and encouraging. If you don't have specific information, guide users to contact the appropriate person.

Always respond in a friendly, professional manner with clear, actionable information."""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=self.max_tokens
            )

            return {
                "service": ServiceType.RENSEIGNEMENT,
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
            system_prompt = """You are a knowledgeable catechism teacher assistant.

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

Always respond with patience, wisdom, and pastoral sensitivity."""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=self.max_tokens
            )

            return {
                "service": ServiceType.CATECHESE,
                "response": response,
                "confidence": 0.8,
                "requires_human_followup": False
            }

        except Exception as e:
            logger.error("catechese_response_failed", error=str(e))
            raise

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
            system_prompt = """You are a compassionate customer service representative for the Service Diocésain de la Catéchèse.

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

Response approach:
- Be warm and reassuring
- Acknowledge the user's feelings
- Explain the process clearly
- Provide specific next steps
- Set realistic expectations"""

            response = await self.send_message(
                message=message,
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                max_tokens=self.max_tokens
            )

            return {
                "service": ServiceType.CONTACT_HUMAIN,
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
        conversation_history: Optional[List[Dict[str, str]]] = None
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
                conversation_history=conversation_history
            )

            intent_type = intent_result.get('intent', 'CONTACT_HUMAIN')
            confidence = intent_result.get('confidence', 0.5)
            extracted_entities = intent_result.get('extracted_entities', {})

            # Step 2: Generate appropriate response based on intent
            if intent_type == ServiceType.RENSEIGNEMENT.value:
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
                    "service": ServiceType.CONTACT_HUMAIN,
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