"""
Pytest configuration and shared fixtures for WhatsApp AI Concierge tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.utils.config import get_settings


@pytest.fixture
def test_settings():
    """Test settings fixture"""
    from src.utils.config import Settings

    return Settings(
        secret_key="test-secret-key",
        environment="testing",
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-anon-key",
        supabase_service_role_key="test-service-key",
        waha_base_url="https://test-waha.com",
        waha_api_token="test-token",
        anthropic_api_key="test-claude-key",
        redis_url="redis://localhost:6379/1",
        jwt_secret_key="test-jwt-secret",
        log_level="DEBUG"
    )


@pytest.fixture
def client(test_settings):
    """Test client fixture"""
    from src.main import app

    # Override settings dependency
    app.dependency_overrides[get_settings] = lambda: test_settings

    with TestClient(app) as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client fixture"""
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.execute.return_value.data = []
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "test-id"}]
    mock_client.table.return_value.update.return_value.execute.return_value.data = [{"id": "test-id"}]
    mock_client.table.return_value.delete.return_value.execute.return_value.data = []
    return mock_client


@pytest.fixture
def mock_waha_client():
    """Mock WAHA client fixture"""
    mock_client = AsyncMock()
    mock_client.send_message.return_value = {"id": "test-message-id"}
    mock_client.get_chats.return_value = [{"id": "test-chat", "name": "Test Chat"}]
    return mock_client


@pytest.fixture
def mock_claude_client():
    """Mock Claude client fixture"""
    mock_client = AsyncMock()
    mock_client.messages.create.return_value = {
        "id": "test-message-id",
        "content": [{"type": "text", "text": "Test response"}],
        "usage": {"input_tokens": 10, "output_tokens": 5}
    }
    return mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis client fixture"""
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    return mock_client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "id": "test-user-id",
        "phone_number": "+221771234567",
        "name": "Test User",
        "preferred_language": "fr",
        "timezone": "Africa/Dakar",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        "id": "test-session-id",
        "user_id": "test-user-id",
        "status": "active",
        "current_service": "RENSEIGNEMENT",
        "context": {},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_interaction_data():
    """Sample interaction data for testing"""
    return {
        "id": "test-interaction-id",
        "session_id": "test-session-id",
        "user_message": "Hello",
        "assistant_response": "Hello! How can I help you?",
        "service": "RENSEIGNEMENT",
        "confidence_score": 0.9,
        "metadata": {},
        "created_at": "2024-01-01T00:00:00Z"
    }


# Event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()