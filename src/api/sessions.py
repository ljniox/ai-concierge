"""
Session management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from src.utils.config import get_settings
import structlog

logger = structlog.get_logger()
sessions_router = APIRouter()


class SessionResponse(BaseModel):
    """Response model for session data"""
    session_id: str
    phone_number: str
    status: str
    current_service: Optional[str] = None
    context: Dict[str, Any]
    created_at: str
    updated_at: str


class CreateSessionRequest(BaseModel):
    """Request model for creating a session"""
    phone_number: str = Field(..., description="User's phone number")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


@sessions_router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    settings: dict = Depends(get_settings)
):
    """
    Get session information by ID
    """
    try:
        logger.info("get_session_request", session_id=session_id)

        # TODO: Implement actual session retrieval from database
        # For now, return a mock response
        mock_session = {
            "session_id": session_id,
            "phone_number": "+221771234567",
            "status": "active",
            "current_service": "RENSEIGNEMENT",
            "context": {"last_message": "Hello", "language": "fr"},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

        logger.info("session_retrieved", session_id=session_id)
        return SessionResponse(**mock_session)

    except Exception as e:
        logger.error("get_session_error", session_id=session_id, error=str(e))
        raise HTTPException(status_code=404, detail="Session not found")


@sessions_router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    settings: dict = Depends(get_settings)
):
    """
    Create a new session
    """
    try:
        logger.info("create_session_request", phone_number=request.phone_number)

        # TODO: Implement actual session creation in database
        # For now, return a mock response
        mock_session = {
            "session_id": "new-session-id",
            "phone_number": request.phone_number,
            "status": "active",
            "current_service": None,
            "context": request.metadata,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

        logger.info("session_created", session_id=mock_session["session_id"])
        return SessionResponse(**mock_session)

    except Exception as e:
        logger.error("create_session_error", phone_number=request.phone_number, error=str(e))
        raise HTTPException(status_code=400, detail="Failed to create session")