import pytest
from fastapi.testclient import TestClient
from app import app
from backend.services.gemini_service import GeminiService
from backend.config import settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_gemini_service():
    """Reset user-configured key before each test."""
    original_key = GeminiService._configured_key
    original_model = GeminiService._configured_model
    yield
    GeminiService._configured_key = original_key
    GeminiService._configured_model = original_model


def test_gemini_settings_get_masked():
    """Verify GET /api/settings/gemini returns masked key and never full key."""
    # Ensure a key is set
    GeminiService.set_configured_key("AIzaSyFakeTestKey9876543210XYZ1234")
    
    response = client.get("/api/settings/gemini")
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert "AIzaSyFakeTestKey" not in data["masked_key"]
    assert data["masked_key"].endswith("1234")
    assert "•" in data["masked_key"]
    assert "api_key" not in data


def test_gemini_settings_post_save_key():
    """Verify POST /api/settings/gemini saves key securely and returns masked key."""
    response = client.post(
        "/api/settings/gemini",
        json={"api_key": "AQ.Ab8UserUpdatedKey9988776655443322", "model": "gemini-2.5-flash"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert "AQ.Ab8UserUpdatedKey" not in data["masked_key"]
    assert data["masked_key"].endswith("3322")
    assert GeminiService.get_active_api_key() == "AQ.Ab8UserUpdatedKey9988776655443322"


def test_key_priority_resolution():
    """Verify configured key takes priority over environment fallback."""
    # 1. Configured key active
    GeminiService.set_configured_key("ConfiguredPriorityKey1111")
    assert GeminiService.get_active_api_key() == "ConfiguredPriorityKey1111"

    # 2. Reset configured key -> falls back to settings.GEMINI_API_KEY
    GeminiService.set_configured_key(None)
    assert GeminiService.get_active_api_key() == settings.GEMINI_API_KEY


def test_gemini_settings_post_invalid_key():
    """Verify validation on empty/invalid keys."""
    response = client.post("/api/settings/gemini", json={"api_key": "   "})
    assert response.status_code in (400, 422)


def test_gemini_connection_test_endpoint():
    """Verify POST /api/settings/gemini/test executes minimal ping safely."""
    # With valid active key
    response = client.post("/api/settings/gemini/test")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert isinstance(data["success"], bool)


def test_gemini_connection_test_no_key():
    """Verify test connection returns clean error when no key is set."""
    GeminiService.set_configured_key(None)
    original_env_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = ""
    try:
        response = client.post("/api/settings/gemini/test")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No Gemini API key is currently configured" in data["message"]
    finally:
        settings.GEMINI_API_KEY = original_env_key


def test_key_not_exposed_in_exception_or_logs():
    """Verify key is not exposed when Gemini throws an error."""
    secret_key = "SuperSecretGeminiKeyDoNotLogMe1234"
    GeminiService.set_configured_key(secret_key)
    
    # Test connection to an invalid model
    result = GeminiService.test_connection(model="invalid-nonexistent-model-xyz")
    assert result["success"] is False
    assert secret_key not in result["message"]
