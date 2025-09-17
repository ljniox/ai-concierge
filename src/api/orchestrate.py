"""
Orchestration endpoints for AI message processing
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from src.utils.config import get_settings
import structlog

logger = structlog.get_logger()
orchestrate_router = APIRouter()


class OrchestrateRequest(BaseModel):
    """Request model for message orchestration"""
    phone_number: str = Field(..., description="User's phone number")
    message: str = Field(..., description="User message to process")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class OrchestrateResponse(BaseModel):
    """Response model for message orchestration"""
    session_id: str
    response: str
    service: str
    confidence_score: float
    metadata: Dict[str, Any]


@orchestrate_router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate_message(
    request: OrchestrateRequest,
    settings: dict = Depends(get_settings)
):
    """
    Orchestrate message processing using AI services
    """
    try:
        logger.info(
            "orchestration_request",
            phone_number=request.phone_number,
            message=request.message,
            session_id=request.session_id
        )

        # TODO: Implement actual orchestration logic
        # For now, return a mock response
        response_data = {
            "session_id": request.session_id or "mock-session-id",
            "response": "Thank you for your message. This is a mock response.",
            "service": "RENSEIGNEMENT",
            "confidence_score": 0.8,
            "metadata": {
                "language_detected": "fr",
                "intent_confidence": 0.7,
                "processing_time": 0.5
            }
        }

        logger.info(
            "orchestration_response",
            session_id=response_data["session_id"],
            service=response_data["service"],
            confidence_score=response_data["confidence_score"]
        )

        return OrchestrateResponse(**response_data)

    except Exception as e:
        logger.error("orchestration_error", error=str(e))
        raise HTTPException(status_code=500, detail="Orchestration failed")