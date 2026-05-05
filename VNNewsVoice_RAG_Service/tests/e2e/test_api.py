"""End-to-end tests for FastAPI endpoints.

Tests /chat and /health endpoints with real HTTP requests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.main import app
from app.api.deps import get_orchestrator
from app.utils.auth_user import get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides = {}
    app.dependency_overrides[get_current_user] = lambda: "test_user@email.com"
    yield
    app.dependency_overrides = {}


@pytest.mark.e2e
def test_health_endpoint():
    """Test /health endpoint returns 200 OK."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy" or data["status"] == "ok"


@pytest.mark.e2e
def test_chat_endpoint_basic():
    """Test /chat endpoint with basic query."""

    async def mock_process_query(*args, **kwargs):
        return Mock(
            query="test query",
            answer="Test answer",
            sources=[],
            retrieval_time_ms=10,
            generation_time_ms=20,
            total_time_ms=30,
            conversation_id="conv-123",
            retrieval_strategy=None,
        )

    mock_orchestrator = Mock()
    mock_orchestrator.process_query = mock_process_query
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

    response = client.post(
        "/api/v1/chat/",
        json={
            "query": "test query",
        },
    )

    print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data


@pytest.mark.e2e
def test_chat_endpoint_adaptive_mode():
    """Test /chat endpoint with adaptive mode enabled."""

    async def mock_process_query(*args, **kwargs):
        return Mock(
            query="test query",
            answer="Adaptive answer",
            sources=[],
            retrieval_time_ms=10,
            generation_time_ms=20,
            total_time_ms=30,
            conversation_id="conv-123",
            retrieval_strategy=Mock(
                retriever_type="hybrid",
                top_k=10,
            ),
        )

    mock_orchestrator = Mock()
    mock_orchestrator.process_query = mock_process_query
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

    response = client.post(
        "/api/v1/chat/",
        json={
            "query": "tin Ukraine hôm nay",
        },
    )

    print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


@pytest.mark.e2e
def test_chat_endpoint_validation():
    """Test /chat endpoint input validation."""
    app.dependency_overrides[get_orchestrator] = lambda: Mock()
    response = client.post(
        "/api/v1/chat/",
        json={
            "query": "test",
            "top_k": -1,
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.e2e
def test_chat_endpoint_error_handling():
    """Test /chat endpoint error handling."""

    async def mock_process_query(*args, **kwargs):
        raise Exception("Test error")

    mock_orchestrator = Mock()
    mock_orchestrator.process_query = mock_process_query
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

    response = client.post(
        "/api/v1/chat/",
        json={
            "query": "test query",
        },
    )

    assert response.status_code == 500


@pytest.mark.e2e
def test_chat_endpoint_unauthorized():
    """Test /chat endpoint without authentication returns 401."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_orchestrator] = lambda: Mock()
    response = client.post(
        "/api/v1/chat/",
        json={
            "query": "test query",
        },
    )
    assert response.status_code == 401
