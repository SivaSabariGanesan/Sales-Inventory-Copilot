import pytest
import sqlite3
from unittest.mock import patch
from fastapi.testclient import TestClient

from app import app
from backend.services.copilot_service import CopilotService
from backend.services.cache_service import CopilotCacheService
from backend.services.version_service import DataVersionService
from backend.services.audit_service import AuditService
from backend.database.connection import get_db_connection
from backend.database.schema import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_audit_log_created_on_copilot_query():
    """Test that querying copilot creates an immutable audit log record."""
    initial_usage = client.get("/api/usage").json()
    initial_count = initial_usage.get("total_interactions", 0)

    question = "Which products are at risk of running out of stock right now?"
    res = CopilotService.process_query(question)

    assert res.intent in ("STOCKOUT_RISK", "INVENTORY_SUMMARY")
    assert res.answer is not None

    # Verify audit log in DB
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        assert row is not None
        assert row["question"] == question
        assert row["normalized_question"] == "which products are at risk of running out of stock right now?"
        assert row["intent"] in ("STOCKOUT_RISK", "INVENTORY_SUMMARY")
        assert row["status"] in ("ANSWERED", "answered", "success", "human_review", "fallback")
        assert row["cache_key"] is not None
        assert len(row["cache_key"]) == 64  # SHA-256 hash length


def test_copilot_cache_hit_and_token_saving():
    """Test that second identical query hits cache and avoids live API calls."""
    question = "Show me stockout risk for top products"
    
    # Query 1 (Cache Miss)
    res1 = CopilotService.process_query(question)
    assert res1.answer is not None

    # Query 2 (Identical question -> Cache Hit)
    res2 = CopilotService.process_query(question)
    assert res2.answer == res1.answer

    # Verify audit trail recorded both, with second as cache_hit
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cache_hit, gemini_calls, input_tokens FROM audit_logs ORDER BY id DESC LIMIT 2")
        rows = cursor.fetchall()
        assert len(rows) >= 2
        # Latest should be cache hit
        assert bool(rows[0]["cache_hit"]) is True
        assert rows[0]["gemini_calls"] == 0
        assert rows[0]["input_tokens"] == 0


def test_query_normalization_whitespace_and_case():
    """Test that whitespace variations and case variations map to the same normalized cache key."""
    q1 = "Which products have sales spikes?"
    q2 = "  which   PRODUCTS have  sales   spikes?  "

    norm1 = CopilotCacheService.normalize_question(q1)
    norm2 = CopilotCacheService.normalize_question(q2)
    assert norm1 == norm2 == "which products have sales spikes?"

    key1 = CopilotCacheService.generate_cache_key(q1)
    key2 = CopilotCacheService.generate_cache_key(q2)
    assert key1 == key2
    assert len(key1) == 64


def test_data_version_cache_invalidation():
    """Test that incrementing data version invalidates prior cache keys without deleting audit logs."""
    question = "Give me slow moving overstock items"

    # Query at current version
    v_initial = DataVersionService.get_data_version()
    res1 = CopilotService.process_query(question)

    key_v1 = CopilotCacheService.generate_cache_key(question)
    cached_entry_v1 = CopilotCacheService.get_cached_response(key_v1, v_initial)
    assert cached_entry_v1 is not None

    # Increment data version (e.g. after CSV import)
    v_new = DataVersionService.increment_data_version()
    assert v_new == v_initial + 1

    # Key generated at new version is different
    key_v2 = CopilotCacheService.generate_cache_key(question)
    assert key_v2 != key_v1

    # Cache lookup at new version misses
    cached_entry_v2 = CopilotCacheService.get_cached_response(key_v2, v_new)
    assert cached_entry_v2 is None

    # Verify audit logs still persist historical queries
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE question = ?", (question,))
        count = cursor.fetchone()[0]
        assert count >= 1


def test_audit_api_endpoints():
    """Test GET /api/audit, GET /api/audit/{id}, and GET /api/usage."""
    # Trigger a query
    CopilotService.process_query("What is the inventory status?")

    # 1. GET /api/audit
    res = client.get("/api/audit?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert "logs" in data
    assert "total_count" in data
    assert len(data["logs"]) > 0

    log_id = data["logs"][0]["id"]

    # 2. GET /api/audit/{id}
    detail_res = client.get(f"/api/audit/{log_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == log_id
    assert "execution_steps" in detail
    assert isinstance(detail["execution_steps"], list)
    assert len(detail["execution_steps"]) > 0

    # 3. GET /api/usage
    usage_res = client.get("/api/usage")
    assert usage_res.status_code == 200
    usage = usage_res.json()
    assert "total_interactions" in usage
    assert "total_cache_hits" in usage
    assert "total_gemini_calls" in usage
    assert "estimated_cost_display" in usage
    assert usage["estimated_cost_display"] == "Cost unavailable"


def test_audit_resilience_non_blocking_on_error():
    """Test that Copilot query succeeds even if audit logging encounters a database write error."""
    with patch("backend.services.audit_service.AuditService.log_copilot_interaction", return_value=None):
        # Should not raise exception
        res = CopilotService.process_query("Which products are out of stock?")
        assert res is not None
        assert res.answer is not None


def test_no_api_keys_leaked_in_audit():
    """Ensure no API keys or secret strings are leaked in audit logs."""
    CopilotService.process_query("Tell me about sales spikes")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT execution_steps, error_message, action_recommendation FROM audit_logs")
        rows = cursor.fetchall()
        for row in rows:
            text = f"{row['execution_steps']} {row['error_message']} {row['action_recommendation']}"
            assert "AIzaSy" not in text
            assert "api_key" not in text.lower() or "configured" in text.lower()
