"""
Webhook API Endpoints

This module provides webhook endpoints for WhatsApp and Telegram platforms
to receive messages and trigger automatic account creation workflows.
Enhanced for Phase 3 with comprehensive webhook processing and security.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, HTTPException, status, BackgroundTasks, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from src.services.whatsapp_webhook_handler import get_whatsapp_webhook_handler
from src.services.telegram_webhook_handler import get_telegram_webhook_handler
from src.services.message_normalization_service import get_message_normalization_service
from src.services.audit_service import log_account_creation_event
from src.utils.logging import get_logger
from src.utils.exceptions import (
    WebhookProcessingError,
    SecurityError,
    ValidationError
)


# Pydantic models for webhook responses
class WebhookResponse(BaseModel):
    """Standard webhook response model."""

    status: str
    message: Optional[str] = None
    processed_messages: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WhatsAppWebhookVerification(BaseModel):
    """WhatsApp webhook verification response."""

    status: str
    challenge: Optional[str] = None


# Initialize services
logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])

# Security for webhook verification
security = HTTPBasic()

# Webhook secrets (should be loaded from environment)
WHATSAPP_WEBHOOK_SECRET = None  # Load from environment in production
TELEGRAM_WEBHOOK_TOKEN = None   # Load from environment in production


# WhatsApp Webhook Endpoints

@router.get("/whatsapp", response_model=WhatsAppWebhookVerification)
async def verify_whatsapp_webhook(
    hub_mode: str = Header(None, alias="hub.mode"),
    hub_challenge: str = Header(None, alias="hub.challenge"),
    hub_verify_token: str = Header(None, alias="hub.verify_token")
):
    """
    Verify WhatsApp webhook endpoint.

    This endpoint handles Meta's webhook verification process for WhatsApp Business API.
    """
    try:
        logger.info("WhatsApp webhook verification request")

        # Check required parameters
        if not all([hub_mode, hub_challenge, hub_verify_token]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required webhook verification parameters"
            )

        # Verify mode
        if hub_mode != "subscribe":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid hub.mode"
            )

        # Verify token (in production, use environment variable)
        expected_token = "your_verification_token"  # Load from env
        if hub_verify_token != expected_token:
            logger.warning("Invalid webhook verify token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid verification token"
            )

        logger.info("WhatsApp webhook verified successfully")

        return WhatsAppWebhookVerification(
            status="verified",
            challenge=hub_challenge
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in WhatsApp webhook verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook verification failed"
        )


@router.post("/whatsapp", response_model=WebhookResponse)
async def process_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_hub_signature_t: Optional[str] = Header(None, alias="X-Hub-Signature-t")
):
    """
    Process incoming WhatsApp webhook.

    This endpoint receives and processes messages from WhatsApp Business API,
    triggering account creation workflows when appropriate.
    """
    try:
        logger.info("WhatsApp webhook received")

        # Get raw request body
        body = await request.body()

        # Verify webhook signature if secret is configured
        if WHATSAPP_WEBHOOK_SECRET and x_hub_signature_256 and x_hub_signature_t:
            webhook_handler = get_whatsapp_webhook_handler(WHATSAPP_WEBHOOK_SECRET)

            if not await webhook_handler.verify_webhook_signature(
                body, x_hub_signature_256, x_hub_signature_t
            ):
                logger.warning("Invalid WhatsApp webhook signature")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )

        # Parse webhook data
        try:
            webhook_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}"
            )

        # Process webhook
        webhook_handler = get_whatsapp_webhook_handler()
        result = await webhook_handler.process_webhook(webhook_data)

        # Log webhook processing
        await log_account_creation_event(
            webhook_data=json.dumps(webhook_data, default=str),
            platform="whatsapp",
            event_type="webhook_processed",
            success=result.get("status") == "processed"
        )

        return WebhookResponse(
            status=result.get("status", "processed"),
            message=result.get("message"),
            processed_messages=result.get("processed_messages"),
            timestamp=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")

        # Return success to WhatsApp even on processing errors
        # to avoid retry loops, but log the error
        return WebhookResponse(
            status="error",
            error=str(e),
            timestamp=datetime.now(timezone.utc)
        )


# Telegram Webhook Endpoints

@router.post("/telegram/{token}")
async def process_telegram_webhook(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Process incoming Telegram webhook.

    This endpoint receives and processes messages from Telegram Bot API,
    triggering account creation workflows when appropriate.
    """
    try:
        logger.info(f"Telegram webhook received for token: {token[:10]}...")

        # Verify webhook token
        if TELEGRAM_WEBHOOK_TOKEN and token != TELEGRAM_WEBHOOK_TOKEN:
            logger.warning("Invalid Telegram webhook token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook token"
            )

        # Parse webhook data
        try:
            body = await request.body()
            webhook_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}"
            )

        # Process webhook
        webhook_handler = get_telegram_webhook_handler()
        result = await webhook_handler.process_webhook(webhook_data)

        # Log webhook processing
        await log_account_creation_event(
            webhook_data=json.dumps(webhook_data, default=str),
            platform="telegram",
            event_type="webhook_processed",
            success=result.get("status") == "processed"
        )

        return WebhookResponse(
            status=result.get("status", "processed"),
            message=result.get("message"),
            timestamp=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}")

        # Return success to Telegram even on processing errors
        return WebhookResponse(
            status="error",
            error=str(e),
            timestamp=datetime.now(timezone.utc)
        )


@router.set_webhook("/telegram/set_webhook")
async def set_telegram_webhook(
    webhook_url: str,
    token: str,
    allowed_updates: Optional[list] = None,
    drop_pending_updates: bool = False
):
    """
    Set Telegram webhook.

    This endpoint configures the Telegram bot webhook URL.
    """
    try:
        # Verify token
        if token != TELEGRAM_WEBHOOK_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # In production, this would make an actual API call to Telegram
        # For now, just return a mock response
        logger.info(f"Setting Telegram webhook to: {webhook_url}")

        return {
            "ok": True,
            "result": True,
            "description": "Webhook was set"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting Telegram webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set webhook"
        )


# Universal Webhook Processing Endpoint

@router.post("/process", response_model=WebhookResponse)
async def process_universal_webhook(
    request: Request,
    platform: str,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    Universal webhook processing endpoint.

    This endpoint can handle webhooks from any platform by specifying
    the platform type in the request.
    """
    try:
        logger.info(f"Universal webhook received for platform: {platform}")

        # Parse webhook data
        try:
            body = await request.body()
            webhook_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}"
            )

        # Route to appropriate handler
        if platform.lower() == "whatsapp":
            handler = get_whatsapp_webhook_handler()
        elif platform.lower() == "telegram":
            handler = get_telegram_webhook_handler()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported platform: {platform}"
            )

        # Process webhook
        result = await handler.process_webhook(webhook_data)

        return WebhookResponse(
            status=result.get("status", "processed"),
            message=result.get("message"),
            processed_messages=result.get("processed_messages"),
            timestamp=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing universal webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# Webhook Management Endpoints

@router.get("/status")
async def get_webhook_status():
    """
    Get webhook configuration status.

    Returns information about webhook configurations for all platforms.
    """
    try:
        # In production, this would check actual webhook status
        # For now, return mock status
        return {
            "status": "active",
            "webhooks": {
                "whatsapp": {
                    "configured": True,
                    "endpoint": "/api/v1/webhooks/whatsapp",
                    "verification_required": True,
                    "last_received": datetime.now(timezone.utc).isoformat()
                },
                "telegram": {
                    "configured": True,
                    "endpoint": "/api/v1/webhooks/telegram/{token}",
                    "token_required": True,
                    "last_received": datetime.now(timezone.utc).isoformat()
                }
            },
            "message_processing": {
                "total_processed": 1250,
                "successful": 1180,
                "failed": 70,
                "success_rate": 94.4
            }
        }

    except Exception as e:
        logger.error(f"Error getting webhook status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook status"
        )


@router.post("/test/{platform}")
async def test_webhook(
    platform: str,
    test_data: Optional[Dict[str, Any]] = None
):
    """
    Test webhook processing with sample data.

    This endpoint allows testing webhook processing without actual platform messages.
    """
    try:
        if platform.lower() not in ["whatsapp", "telegram"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported platform: {platform}"
            )

        # Use default test data if none provided
        if not test_data:
            test_data = _get_test_webhook_data(platform)

        # Process test webhook
        if platform.lower() == "whatsapp":
            handler = get_whatsapp_webhook_handler()
        else:
            handler = get_telegram_webhook_handler()

        result = await handler.process_webhook(test_data)

        return {
            "platform": platform,
            "test_status": "completed",
            "processing_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook test failed"
        )


@router.get("/logs")
async def get_webhook_logs(
    limit: int = 50,
    platform: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Get webhook processing logs.

    Returns recent webhook processing logs with filtering options.
    """
    try:
        # In production, this would query actual logs from database
        # For now, return mock log data
        logs = [
            {
                "id": "log_001",
                "platform": "whatsapp",
                "status": "processed",
                "message_id": "wamid_123",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": 150,
                "account_created": True
            },
            {
                "id": "log_002",
                "platform": "telegram",
                "status": "processed",
                "message_id": 456,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": 200,
                "account_created": False
            }
        ]

        # Apply filters
        if platform:
            logs = [log for log in logs if log["platform"] == platform]
        if status:
            logs = [log for log in logs if log["status"] == status]

        return {
            "logs": logs[:limit],
            "total_count": len(logs),
            "filters": {
                "platform": platform,
                "status": status,
                "limit": limit
            }
        }

    except Exception as e:
        logger.error(f"Error getting webhook logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook logs"
        )


# Helper functions

def _get_test_webhook_data(platform: str) -> Dict[str, Any]:
    """Get test webhook data for the specified platform."""
    if platform.lower() == "whatsapp":
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "221765005555",
                                    "phone_number_id": "987654321"
                                },
                                "contacts": [
                                    {
                                        "profile": {
                                            "name": "Test Parent"
                                        },
                                        "wa_id": "221765005555"
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "221765005555",
                                        "id": "wamid.test123",
                                        "timestamp": "1634567890",
                                        "text": {
                                            "body": "Bonjour, je souhaite créer un compte"
                                        },
                                        "type": "text"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    elif platform.lower() == "telegram":
        return {
            "update_id": 123456789,
            "message": {
                "message_id": 456,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "Parent",
                    "username": "testparent",
                    "language_code": "fr"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "Test",
                    "last_name": "Parent",
                    "username": "testparent",
                    "type": "private"
                },
                "date": 1634567890,
                "text": "Bonjour, je souhaite créer un compte"
            }
        }
    else:
        return {}


# Exception handlers

@router.exception_handler(SecurityError)
async def security_error_handler(request, exc: SecurityError):
    """Handle security-related errors."""
    logger.warning(f"Security error in webhook: {str(exc)}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Security error: {str(exc)}"
    )


@router.exception_handler(WebhookProcessingError)
async def webhook_processing_error_handler(request, exc: WebhookProcessingError):
    """Handle webhook processing errors."""
    logger.error(f"Webhook processing error: {str(exc)}")
    return WebhookResponse(
        status="error",
        error=str(exc),
        timestamp=datetime.now(timezone.utc)
    )


@router.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error in webhook: {str(exc)}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Validation error: {str(exc)}"
    )