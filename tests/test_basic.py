"""
Basic tests to verify core functionality
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint():
    """Test root endpoint exists"""
    from src.main import app
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    """Test health endpoint exists"""
    from src.main import app
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data


def test_version_endpoint():
    """Test version endpoint exists"""
    from src.main import app
    client = TestClient(app)
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data


def test_models_import():
    """Test that all models can be imported"""
    from src.models.user import User
    from src.models.session import Session
    from src.models.interaction import Interaction
    from src.models.service import Service

    assert User is not None
    assert Session is not None
    assert Interaction is not None
    assert Service is not None


def test_user_model_validation():
    """Test user model validation"""
    from src.models.user import User, UserCreate
    from datetime import datetime

    user_data = {
        "id": "test-user-id",
        "phone_number": "+221771234567",
        "name": "Test User",
        "preferred_language": "fr",
        "timezone": "Africa/Dakar",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    user = User(**user_data)
    assert user.phone_number == "+221771234567"
    assert user.preferred_language == "fr"


def test_session_model_validation():
    """Test session model validation"""
    from src.models.session import Session, SessionStatus
    from datetime import datetime

    session_data = {
        "id": "test-session-id",
        "user_id": "test-user-id",
        "status": SessionStatus.ACTIVE,
        "current_service": "RENSEIGNEMENT",
        "context": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "last_activity_at": datetime.now(),
        "message_count": 0
    }

    session = Session(**session_data)
    assert session.id == "test-session-id"
    assert session.status == SessionStatus.ACTIVE


def test_interaction_model_validation():
    """Test interaction model validation"""
    from src.models.interaction import Interaction, InteractionType, MessageType
    from datetime import datetime

    interaction_data = {
        "id": "test-interaction-id",
        "session_id": "test-session-id",
        "user_message": "Hello",
        "assistant_response": "Hi there!",
        "service": "RENSEIGNEMENT",
        "interaction_type": InteractionType.MESSAGE,
        "message_type": MessageType.TEXT,
        "confidence_score": 0.9,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    interaction = Interaction(**interaction_data)
    assert interaction.id == "test-interaction-id"
    assert interaction.service == "RENSEIGNEMENT"
    assert interaction.confidence_score == 0.9


def test_service_model_validation():
    """Test service model validation"""
    from src.models.service import Service, ServiceType, ServiceStatus
    from datetime import datetime

    service_data = {
        "id": ServiceType.RENSEIGNEMENT,
        "name": "Service de Renseignement",
        "description": "Handles general inquiries",
        "is_active": True,
        "capabilities": ["answer_questions"],
        "requirements": ["internet_access"],
        "config": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "status": ServiceStatus.ACTIVE,
        "version": "1.0.0"
    }

    service = Service(**service_data)
    assert service.id == ServiceType.RENSEIGNEMENT
    assert service.is_active is True
    assert service.is_available is True